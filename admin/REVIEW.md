# Admin Panel Code Review — `D:\work\zhaomu\admin\`

**Date:** 2026-07-14
**Reviewer:** Strategic Technical Advisor
**Scope:** Backend (`api_routes/`, `server.py`, `db.py`, `crypto.py`) + Frontend (`frontend/src/`)

---

## P0 — Critical Bugs / Security Issues (Must Fix Before Use)

### P0-1: `shared.get_db` hardcodes `admin.db`, breaking test isolation (铁律 #5.5 violation)

**File:** `admin/api_routes/shared.py`, lines 55–63
**Severity:** P0 — Critical

**Description:**
There are **two different `get_db` functions** in the codebase:

| Function | Location | Signature | DB Path |
|----------|----------|-----------|---------|
| `admin.db.get_db` | `db.py:94` | `get_db(db_path="admin.db")` — context manager | Respects `db_path` arg |
| `admin.api_routes.shared.get_db` | `shared.py:55` | `get_db()` — FastAPI dependency | **Hardcoded `"admin.db"`** |

`server.py` imports `get_db` from `admin.db` (line 29) and uses it with `db_path` for token management — this respects `ADMIN_DB_PATH`.

All route handlers import `get_db` from `admin.api_routes.shared` (e.g., `filter.py:7`, `products.py:9`, `orders.py:15`, `servers.py:9`, `balance.py:7`, `settings.py:21`). This version hardcodes `aiosqlite.connect("admin.db")` at line 63, completely ignoring the `ADMIN_DB_PATH` environment variable.

**Impact:** Setting `ADMIN_DB_PATH=test_admin.db` for Playwright/automated tests (as required by 铁律 #5.5) causes:
- Token auth to use `test_admin.db` (correct)
- All route handlers (accounts, products, orders, servers, balance, settings) to use `admin.db` (production database)

Tests would read and write to the production database, potentially corrupting real API keys, SOS tokens, and server records.

**Recommended Fix:**
Remove `get_db` from `shared.py` entirely. Have all route handlers depend on `admin.db.get_db` via a FastAPI-compatible dependency wrapper that reads the path from `app.state`:

```python
# In shared.py — replace get_db with a dependency that uses app state
from fastapi import Request
import aiosqlite

async def get_db(request: Request):
    db_path = request.app.state.admin_db_path
    conn = await aiosqlite.connect(db_path)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA foreign_keys = ON")
    await conn.commit()
    try:
        yield conn
    finally:
        await conn.close()
```

Table creation should happen once at startup (in `lifespan`), not on every request.

---

### P0-2: Synchronous `requests` calls inside `async def` handlers block the event loop

**Files:** All route handlers — `filter.py`, `products.py`, `orders.py`, `servers.py`, `balance.py`
**Severity:** P0 — Critical (performance/architecture)

**Description:**
`ZhaomuClient` uses the synchronous `requests` library (per AGENTS.md: `requests>=2.28`). All route handlers are `async def` and call blocking methods directly:

```python
# filter.py:47
all_regions = client.region.list()  # blocks event loop

# products.py:84
products = client.product.list(rid)  # blocks event loop

# orders.py:169
op_result = client.cloud.order(req)  # blocks event loop

# servers.py:94
servers = client.cloud.list()  # blocks event loop
```

While any single request waits for the zhaomu API (which can take 1–5 seconds), **the entire FastAPI server is unresponsive** — no other request can be processed, including health checks, static file serving, and concurrent user actions.

This is especially severe in `products.py:list_products` (lines 82–88), which loops over multiple `region_id`s sequentially — each `client.product.list(rid)` call blocks the event loop, potentially for 10+ seconds with 5 zones.

**Recommended Fix (minimal):** Wrap all sync calls in `asyncio.to_thread()`:

```python
import asyncio
all_regions = await asyncio.to_thread(client.region.list)
```

**Recommended Fix (proper):** Replace `requests` with `httpx.AsyncClient` in `ZhaomuClient` so all HTTP calls are natively async.

**Effort:** Medium (1–2 days for `to_thread` approach; Large for httpx migration)

---

## P1 — Significant Issues (Will Cause Problems in Production)

### P1-1: `orders.py` — `OrderRequest` missing `regionId`

**File:** `admin/api_routes/orders.py`, lines 163–168
**Severity:** P1

**Description:**
The `OrderRequest` is constructed without `regionId`:

```python
req = OrderRequest(
    productId=item.product_id,
    disk=item.disk,
    imageId=item.image_id,
    paymentCycle=item.payment_cycle,
)
```

The SDK documentation (README.md) shows `OrderRequest(regionId=780, productId=9723, ...)`. The product's `region_id` is available at line 133 (`product = client.product.info(item.product_id)`) and line 192 (`product.region_id`), but is never passed to the request.

**Impact:** Orders may fail, deploy to the wrong region, or rely on undocumented server-side inference from `productId`.

**Recommended Fix:**
```python
req = OrderRequest(
    regionId=product.region_id,
    productId=item.product_id,
    disk=item.disk,
    imageId=item.image_id,
    paymentCycle=item.payment_cycle,
)
```

---

### P1-2: `orders.py` — `AuthError` mid-batch orphans already-created servers

**File:** `admin/api_routes/orders.py`, lines 170–172
**Severity:** P1

**Description:**
When processing a batch of orders, if items 1–3 succeed (servers created on zhaomu + DB records written) and item 4 raises `AuthError`, the handler immediately raises `HTTPException(401)`, discarding all previous results:

```python
except AuthError as e:
    raise HTTPException(status_code=401, detail=f"认证失败: {e}") from e
```

The user sees a 401 error and `success_count`/`results` are never returned. The already-created servers exist on zhaomu and in the DB, but the user has no record of them. Retrying the batch creates duplicate servers.

**Recommended Fix:**
On `AuthError`, return partial results with a 401 status instead of discarding:

```python
except AuthError as e:
    results.append({
        "server_id": 0, "success": False,
        "message": f"认证失败（后续订单未处理）: {e}",
    })
    return JSONResponse(
        status_code=401,
        content={"success_count": success_count, "results": results, "aborted": True},
    )
```

---

### P1-3: `orders.py` — No server-side validation of `quantity` bounds

**File:** `admin/api_routes/orders.py`, line 35
**Severity:** P1

**Description:**
```python
class OrderItem(BaseModel):
    quantity: int = 1
```

The frontend limits quantity to 1–5 (`ProductSelect.tsx:249`: `min={1} max={5}`), but the API accepts any positive integer. A direct API call with `quantity: 10000` would attempt to create 10,000 servers.

**Recommended Fix:**
```python
class OrderItem(BaseModel):
    quantity: int = Field(default=1, ge=1, le=10)
```

Also validate total batch size: `if len(orders) > 20: raise HTTPException(400, ...)`.

---

### P1-4: `servers.py` — `assert rec is not None` in production code

**File:** `admin/api_routes/servers.py`, line 154
**Severity:** P1

**Description:**
```python
rec = await get_server_record(db, server_db_id)
assert rec is not None  # 刚更新，一定存在
```

Python assertions are stripped when running with `-O` flag. If the record is deleted between the `update_server_status` call and the `get_server_record` call (race condition), this would silently pass in optimized mode and return `None`, causing a downstream crash.

**Recommended Fix:**
```python
rec = await get_server_record(db, server_db_id)
if rec is None:
    raise HTTPException(status_code=404, detail="server record disappeared after update")
```

---

### P1-5: Password stored as sha256 hash = auth token (DB compromise = full access)

**Files:** `admin/server.py:37–43` (`_compute_token`), `admin/api_routes/settings.py:135–138` (`set_password`), `admin/server.py:155` (middleware comparison)
**Severity:** P1

**Description:**
The auth token is `base64(sha256(password))`. This value is:
1. Stored in the DB as `admin_password_hash`
2. Returned to the user as the bearer token
3. Compared by the middleware on every request

This means the value stored in the database **IS a valid authentication credential**. `crypto.py` provides argon2id `hash_password`/`verify_password` (lines 33–55), but these are **never used** for the admin password. An attacker with read access to `admin.db` obtains the `admin_password_hash` setting and can authenticate directly — no password cracking needed.

Additionally, sha256 is a fast hash (billions of iterations/second on GPU), making offline brute-force trivial if the password is weak.

**Recommended Fix (minimal):** Store argon2 hash; issue random session tokens:
1. On login: `verify_password(input, stored_argon2_hash)` → generate random UUID token → store token in DB with expiry
2. Middleware checks token against DB (or in-memory cache with TTL)
3. `set_password` uses `hash_password()` instead of sha256

**Effort:** Medium (1–2 days)

---

### P1-6: `servers.py` — `deploy_server` sends root password to third-party API

**File:** `admin/api_routes/servers.py`, line 234
**Severity:** P1

**Description:**
```python
vps_info = VpsLoginInfo(
    password=inst.password,  # cloud server root password
    ...
)
```

The cloud server's root password is sent to the MetroVPN deploy API via `DeployClient(sos_token).create_deploy(deploy_req)`. If `DeployClient` does not use HTTPS, or if MetroVPN logs request bodies, the root password is exposed.

**Recommended Fix:**
1. Verify `DeployClient` uses HTTPS (check `zhaomu_deploy.client` implementation)
2. Consider generating a temporary password specifically for deploy rather than reusing the root password
3. Add a comment documenting that password transmission to MetroVPN is intentional

---

### P1-7: `server.py` — Multi-worker token inconsistency

**File:** `admin/server.py`, lines 101–102, 140 (settings.py)
**Severity:** P1 (for multi-worker deployments)

**Description:**
`app.state.admin_token` is loaded once in `lifespan` (line 102) and stored in process memory. When `set_password` updates the token (settings.py:140: `request.app.state.admin_token = token`), only the worker handling that request sees the update. Other workers continue using the old token.

**Impact:** After changing the password, requests routed to other workers may fail with 401 (old token) or succeed with the old token (security gap — old password still works on some workers).

**Recommended Fix:**
- For single-worker (current): document `--workers 1` requirement
- For multi-worker: store token in DB and check on every request, or use a shared cache (Redis) with short TTL

---

## P2 — Improvements (Code Quality, Maintainability)

### P2-1: `products.py` — Dead code: `_make_dedup_key` and `_filter_by_traffic`

**File:** `admin/api_routes/products.py`, lines 15–42
**Severity:** P2

**Description:**
`_make_dedup_key` (lines 15–17) and `_filter_by_traffic` (lines 20–42) are defined but never called. The actual `list_products` function uses inline filtering (lines 110–123) and per-zone rows (no dedup). These are leftovers from a previous cross-zone dedup implementation.

**Recommended Fix:** Delete lines 15–42.

---

### P2-2: `shared.py` — `get_db` creates tables on every request

**File:** `admin/api_routes/shared.py`, lines 66–97
**Severity:** P2

**Description:**
Every request creates a new SQLite connection, runs three `CREATE TABLE IF NOT EXISTS` statements, commits, and closes the connection. While `IF NOT EXISTS` is idempotent, this adds unnecessary latency to every API call.

**Recommended Fix:** Move table creation to `lifespan` startup. `get_db` should only `connect` + `PRAGMA foreign_keys = ON`.

---

### P2-3: `shared.py` — `_client_cache` has no TTL or invalidation

**File:** `admin/api_routes/shared.py`, line 14
**Severity:** P2

**Description:**
```python
_client_cache: dict[int, ZhaomuClient] = {}
```

The cache never expires. If a zhaomu API key is rotated externally (e.g., via the zhaomu web console), the cached client uses the old key indefinitely. `clear_client` is only called on account deletion (settings.py:183), not on any other DB modification.

**Recommended Fix:** Add a TTL (e.g., 10 minutes) or timestamp-based invalidation. Alternatively, remove caching entirely — the DPAPI decrypt is fast (~1ms).

---

### P2-4: `ProductSelect.tsx` — `handlePrepare` fetches images sequentially

**File:** `admin/frontend/src/pages/ProductSelect.tsx`, lines 137–151
**Severity:** P2

**Description:**
```typescript
for (const key of selectedKeys) {
    const r = await apiClient.get(`/api/orders/prepare/${pid}?account_id=${accountId}`);
    // ...
}
```

If 5 products are selected, this makes 5 sequential HTTP calls. Each call hits the zhaomu API twice (`product.info` + `cloud.images`), so 5 products = 10 sequential upstream calls = potentially 10+ seconds of waiting.

**Recommended Fix:**
```typescript
const results = await Promise.all(
    selectedKeys.map(key => {
        const pid = Number(key);
        return apiClient.get(`/api/orders/prepare/${pid}?account_id=${accountId}`)
            .then(r => ({ pid, data: r.data }));
    })
);
```

---

### P2-5: `ProductSelect.tsx` — `prod` non-null assertion can crash

**File:** `admin/frontend/src/pages/ProductSelect.tsx`, line 238
**Severity:** P2

**Description:**
```typescript
const prod = products.find(p => p.id === pid)!;
```

If `products` is refetched (e.g., by the effect at line 91) while the order modal is open, the selected product may no longer be in the list. The `!` assertion would produce `undefined`, and `prod.cpu` would throw.

**Recommended Fix:**
```typescript
const prod = products.find(p => p.id === pid);
if (!prod) return null; // or skip rendering this item
```

---

### P2-6: `Layout.tsx` — Balance always fetched for first account

**File:** `admin/frontend/src/components/Layout.tsx`, lines 19–26
**Severity:** P2

**Description:**
```typescript
apiClient.get('/api/accounts').then(r => {
    const list = r.data || [];
    if (list.length > 0) {
        return apiClient.get(`/api/balance?account_id=${list[0].id}`);
    }
})
```

The balance is always fetched for `list[0]` (first account by ID). If the user is operating on account 2, the header shows account 1's balance. The balance is also fetched only once on mount and never refreshed.

**Recommended Fix:** Lift `accountId` state to Layout (or a context), pass it down to pages, and fetch balance for the selected account. Alternatively, fetch balance when accountId changes in each page and emit it via a callback.

---

### P2-7: `ServerManage.tsx` — Polling effect resets timer on every `servers` change

**File:** `admin/frontend/src/pages/ServerManage.tsx`, lines 43–53
**Severity:** P2

**Description:**
```typescript
useEffect(() => {
    const ps = servers.filter(s => s.status === 'provisioning');
    // ...
    const t = setInterval(async () => {
        for (const s of ps) { /* poll each */ }
        fetchServers();  // updates servers → retriggers this effect
    }, 30000);
    return () => clearInterval(t);
}, [servers, accountId, fetchServers]);
```

Every time `fetchServers()` updates `servers`, this effect re-runs: the old interval is cleared and a new 30-second timer starts. If polling completes in 2 seconds, the timer never fires — it's constantly reset. Additionally, `ps` is captured at effect creation; if a new provisioning server appears between polls, it won't be polled until the next `servers` update.

**Recommended Fix:** Separate the polling list from the `servers` state:
```typescript
const [pollTargets, setPollTargets] = useState<number[]>([]);
useEffect(() => {
    setPollTargets(servers.filter(s => s.status === 'provisioning').map(s => s.id));
}, [servers]);

useEffect(() => {
    if (pollTargets.length === 0 || accountId === null) return;
    const t = setInterval(async () => {
        await Promise.all(pollTargets.map(id =>
            apiClient.get(`/api/servers/${id}/poll?account_id=${accountId}`).catch(() => {})
        ));
        fetchServers();
    }, 30000);
    return () => clearInterval(t);
}, [pollTargets, accountId, fetchServers]);
```

---

### P2-8: `ServerManage.tsx` — `handleDestroy` has no loading state

**File:** `admin/frontend/src/pages/ServerManage.tsx`, lines 66–69
**Severity:** P2

**Description:**
```typescript
const handleDestroy = async (dbId: number) => {
    if (accountId === null) return;
    try { await apiClient.delete(`/api/servers/${dbId}?account_id=${accountId}`); ... } catch { }
};
```

No loading indicator during the destroy API call. The user can click the destroy button multiple times, potentially sending duplicate destroy requests.

**Recommended Fix:** Add a `destroying` Set (like `deploying`) and disable the button while in-flight.

---

### P2-9: `balance.py` and `orders.py` — Missing explicit `AuthError` handling

**Files:**
- `admin/api_routes/balance.py`, lines 22–25
- `admin/api_routes/orders.py`, lines 61–64 (`prepare_order`)

**Severity:** P2

**Description:**
`balance.py` only catches `ZhaomuError` (which includes `AuthError` as a subclass), returning 502 for all errors. An invalid API key returns 502 instead of 401. Other routes (`filter.py`, `products.py`) correctly catch `AuthError` separately and return 401.

`orders.py:prepare_order` (lines 61–64) catches `APIError` and `ZhaomuError` but not `AuthError` explicitly — `AuthError` falls through to the `ZhaomuError` handler and returns 502.

**Recommended Fix:** Add `except AuthError` before `except ZhaomuError` in both files:
```python
except AuthError:
    raise HTTPException(status_code=401, detail="API Key 无效，请检查账户设置") from None
except ZhaomuError as e:
    raise HTTPException(status_code=502, detail=f"zhaomu API 出错: {e}") from e
```

---

### P2-10: `filter.py` — Magic number `target_id == 27`

**File:** `admin/api_routes/filter.py`, line 24
**Severity:** P2

**Description:**
```python
if "ip" in name_lower or target_id == 27:
    return "ip_type"
```

The constant `27` is undocumented. According to `docs/api/02-products/compare-products.md`, there are 25 `target_id` mappings. The magic number makes this fragile — if zhaomu renumbers their IDs, this silently breaks.

**Recommended Fix:** Extract to a named constant with a comment:
```python
# target_id 27 = IP 类型（原生IP/住宅IP），来自 zhaomu compare API
_TARGET_ID_IP_TYPE = 27

if "ip" in name_lower or target_id == _TARGET_ID_IP_TYPE:
    return "ip_type"
```

---

### P2-11: `server.py` — `login` endpoint lacks Pydantic validation

**File:** `admin/server.py`, lines 180–181
**Severity:** P2

**Description:**
```python
body: dict[str, Any] = await request.json()
password = str(body.get("password", ""))
```

Raw dict parsing instead of a Pydantic model. If the body is not valid JSON, `request.json()` raises an unhandled `JSONDecodeError` (500). If `password` is a number (e.g., `12345`), `str()` coerces it, which may not match the stored hash.

**Recommended Fix:**
```python
from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    password: str = Field(..., min_length=1)

@auth_router.post("/api/auth/login")
async def login(body: LoginRequest, request: Request) -> dict[str, str]:
    ...
```

---

### P2-12: `servers.py` — `inst.image.lower()` may fail on None

**File:** `admin/api_routes/servers.py`, line 236
**Severity:** P2

**Description:**
```python
os=inst.image.lower(),
```

If the zhaomu API returns `image` as `None` (e.g., for a server that's still provisioning), `.lower()` raises `AttributeError`. This would cause the deploy to fail with a 500 error.

**Recommended Fix:**
```python
os=(inst.image or "").lower(),
```

---

### P2-13: `servers.py` — Broad `except Exception` in deploy leaks internal details

**File:** `admin/api_routes/servers.py`, lines 251–254
**Severity:** P2

**Description:**
```python
except Exception as e:
    raise HTTPException(
        status_code=500, detail=f"MetroVPN deploy API 出错：{e}"
    ) from e
```

Catching `Exception` broadly includes `TypeError`, `AttributeError`, `KeyError`, etc. — all of which expose internal implementation details in the error message. This could leak file paths, internal field names, or stack trace fragments.

**Recommended Fix:** Catch specific exceptions from `DeployClient` (e.g., `requests.RequestException`) and return a generic message:
```python
except requests.RequestException as e:
    raise HTTPException(status_code=502, detail=f"MetroVPN API 网络错误: {e}") from e
except Exception:
    raise HTTPException(status_code=500, detail="MetroVPN deploy 内部错误") from None
```

---

### P2-14: `filter.py` — Private symbol import `_REGION_LOOKUP`

**File:** `admin/api_routes/filter.py`, line 14
**Severity:** P2

**Description:**
```python
from zhaomu_deploy.client import _REGION_LOOKUP  # pyright: ignore[reportPrivateUsage]
```

Importing a private symbol (prefixed with `_`) creates tight coupling to `zhaomu_deploy`'s internal implementation. The `# pyright: ignore` comment acknowledges this. If the symbol is renamed or restructured, this breaks at runtime (caught by `ImportError`, which degrades to empty dict — silent failure).

**Recommended Fix:** Request `zhaomu_deploy` to expose a public function (e.g., `get_supported_regions()`) or make `_REGION_LOOKUP` public by renaming it to `REGION_LOOKUP`.

---

### P2-15: `orders.py` — `db_records_written` is dead code

**File:** `admin/api_routes/orders.py`, lines 127, 198, 213
**Severity:** P2

**Description:**
`db_records_written` is initialized (line 127), incremented (line 198), but never included in the response (line 213 only returns `success_count` and `results`).

**Recommended Fix:** Either include it in the response (`"db_records_written": db_records_written`) or delete the variable.

---

### P2-16: `server.py` — SPA fallback lacks cache headers for static assets

**File:** `admin/server.py`, lines 235–246
**Severity:** P2

**Description:**
```python
if file_path.exists():
    return FileResponse(file_path)
```

Static assets (JS/CSS with hashed filenames from Vite build) are served without `Cache-Control` headers. Browsers re-fetch on every page load. Vite produces content-hashed filenames (e.g., `index-abc123.js`) specifically to enable long-term caching.

**Recommended Fix:**
```python
from starlette.responses import FileResponse

if file_path.exists():
    return FileResponse(
        file_path,
        headers={"Cache-Control": "public, max-age=31536000, immutable"}
        if "." in path.split("/")[-1] else {}
    )
```

---

### P2-17: `orders.py` — No validation of `disk` against `diskMax` or `payment_cycle` range

**File:** `admin/api_routes/orders.py`, lines 33–35
**Severity:** P2

**Description:**
`OrderItem` accepts any `disk` and `payment_cycle` values. The `disk` is validated against `minPaymentCycle` (line 150) but:
- `disk` is not validated against `product.diskMax` — the zhaomu API may reject it, but the error is opaque
- `payment_cycle` is not validated to be in range 1–5

**Recommended Fix:**
```python
if item.disk < product.disk or item.disk > product.diskMax:
    results.append({"server_id": 0, "success": False,
        "message": f"磁盘 {item.disk}G 超出范围 [{product.disk}, {product.diskMax}]"})
    continue
if item.payment_cycle < 1 or item.payment_cycle > 5:
    results.append({"server_id": 0, "success": False,
        "message": f"支付周期 {item.payment_cycle} 无效（1-5）"})
    continue
```

---

### P2-18: `products.py` — Sequential per-region API calls in async handler

**File:** `admin/api_routes/products.py`, lines 82–88
**Severity:** P2

**Description:**
```python
for rid in rid_list:
    try:
        products = client.product.list(rid)  # blocking, sequential
```

Each `client.product.list(rid)` is a synchronous HTTP call (see P0-2). With 5 zones, this is 5 sequential blocking calls. Combined with P0-2, this can block the server for 10+ seconds.

**Recommended Fix:** Use `asyncio.to_thread` with `asyncio.gather` for parallelism:
```python
import asyncio
results = await asyncio.gather(
    *[asyncio.to_thread(client.product.list, rid) for rid in rid_list],
    return_exceptions=True,
)
```

---

## P3 — Nitpicks (Style, Minor Suggestions)

### P3-1: `Login.tsx` — Username collected but never sent to server

**File:** `admin/frontend/src/pages/Login.tsx`, lines 20, 35
**Severity:** P3

**Description:**
Both `onSetup` and `onLogin` collect `values.username` but only send `{ password: values.password }` to the API. The username is stored in `localStorage` (`admin_user`) but never validated or used by the backend. The username form field is purely decorative.

**Recommended Fix:** Either remove the username field, or implement username-based auth (would require backend changes). If keeping it for UX, add a comment noting it's cosmetic.

---

### P3-2: `ProductSelect.tsx` — `ram / 1024` may show floating-point artifacts

**File:** `admin/frontend/src/pages/ProductSelect.tsx`, line 176
**Severity:** P3

**Description:**
```typescript
render: (v: number) => v >= 1024 ? `${v / 1024}G` : `${v}M`,
```

If `ram` is 1536, `1536 / 1024 = 1.5` → "1.5G" (fine). But if `ram` is 3072, `3072 / 1024 = 3` → "3G" (fine). Edge case: `ram = 2560` → "2.5G" (fine). JavaScript floating-point could theoretically produce "2.4999999G" for certain values, though unlikely with powers of 2.

**Recommended Fix:** Use `Math.round(v / 1024 * 10) / 10` or `v % 1024 === 0 ? v / 1024 : (v / 1024).toFixed(1)`.

---

### P3-3: `server.py` — CORS hardcoded to `localhost:5173`

**File:** `admin/server.py`, line 112
**Severity:** P3

**Description:**
```python
allow_origins=["http://localhost:5173"],
```

Only Vite's default port is allowed. If the dev server runs on a different port (e.g., 5174 due to port conflict), CORS blocks all requests. In production, the SPA is served from the same origin, so CORS is unnecessary.

**Recommended Fix:** Make it configurable:
```python
import os
dev_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(CORSMiddleware, allow_origins=dev_origins, ...)
```

---

### P3-4: `products.py` — `outOfStock` camelCase in Python

**File:** `admin/api_routes/products.py`, line 91
**Severity:** P3

**Description:**
```python
if p.outOfStock != 0:
```

`outOfStock` is camelCase, which is unconventional in Python (PEP 8 prefers `out_of_stock`). This matches the zhaomu API model field name, so changing it would require updating the model. Acceptable as-is, but worth noting for consistency.

---

### P3-5: `ServerManage.tsx` — `handleDestroy` swallows `fetchServers` errors silently

**File:** `admin/frontend/src/pages/ServerManage.tsx`, line 68
**Severity:** P3

**Description:**
```typescript
try { await apiClient.delete(...); message.success('已销毁'); fetchServers(); } catch { }
```

If `apiClient.delete` succeeds but `fetchServers()` fails, the success message is shown but the list isn't refreshed. The `fetchServers` error is caught by the empty `catch` and swallowed (the API client interceptor does show the error, but the user sees both "已销毁" and an error toast, which is confusing).

**Recommended Fix:** Separate the try/catch:
```typescript
try {
    await apiClient.delete(...);
    message.success('已销毁');
} catch { /* handled by interceptor */ }
fetchServers().catch(() => {});  // silent refresh
```

---

### P3-6: `ProductSelect.tsx` — Effect dependency uses `zoneIds.join(',')` workaround

**File:** `admin/frontend/src/pages/ProductSelect.tsx`, line 108
**Severity:** P3

**Description:**
```typescript
}, [zoneIds.join(','), accountId]);
```

Using `zoneIds.join(',')` as a dependency is a workaround for array reference inequality. It works but is fragile — if `zoneIds` is `[1]` then `[]` then `[1]` again, the join changes `"1"` → `""` → `"1"`, triggering correctly. But it's non-obvious and would confuse ESLint's `react-hooks/exhaustive-deps` rule.

**Recommended Fix:** Use a `useMemo` to stabilize the reference, or extract `zoneIds` computation into a custom hook with stable identity.

---

### P3-7: `orders.py` — `image` stored as `str(item.image_id)` instead of image name

**File:** `admin/api_routes/orders.py`, line 193
**Severity:** P3

**Description:**
```python
image=str(item.image_id),
```

The `image` field in the DB stores the numeric image ID as a string (e.g., `"842"`) rather than the human-readable image name (e.g., `"Ubuntu 20.04"`). The `ServerManage.tsx` table displays this field (line 79: `{ title: '镜像', dataIndex: 'image' }`), showing `"842"` instead of `"Ubuntu 20.04"`.

**Recommended Fix:** Pass the image name from the frontend, or look it up from the `images` list in `prepare_order`.

---

### P3-8: `client.ts` — No request timeout

**File:** `admin/frontend/src/api/client.ts`, lines 4–6
**Severity:** P3

**Description:**
```typescript
const apiClient = axios.create({
    baseURL: '',
});
```

No `timeout` configured. If the backend hangs (e.g., due to P0-2 blocking), the frontend waits indefinitely with no user feedback.

**Recommended Fix:**
```typescript
const apiClient = axios.create({
    baseURL: '',
    timeout: 30000,  // 30 seconds
});
```

---

## Summary

| Severity | Count | Key Themes |
|----------|-------|------------|
| **P0** | 2 | Test isolation broken (hardcoded DB path), event-loop blocking (sync HTTP in async) |
| **P1** | 7 | Missing `regionId` in orders, batch orphaning, no quantity validation, `assert` in prod, weak password hashing, root password exposure, multi-worker token drift |
| **P2** | 18 | Dead code, no cache TTL, sequential fetches, missing null checks, missing AuthError handling, magic numbers, no input validation |
| **P3** | 8 | Cosmetic username, floating-point display, hardcoded CORS, image ID vs name |

### Top 3 Priority Fixes

1. **P0-1:** Fix `shared.get_db` to respect `ADMIN_DB_PATH` — this is a 铁律 #5.5 violation and makes testing unsafe.
2. **P0-2:** Wrap sync `ZhaomuClient` calls in `asyncio.to_thread()` — the server is currently single-request-capable under load.
3. **P1-1:** Add `regionId=product.region_id` to `OrderRequest` — orders may be failing or going to wrong regions.

---

