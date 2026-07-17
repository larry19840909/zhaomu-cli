# Code Review — Server Management Refactoring

**Date:** 2026-07-17
**Scope:** 6 production files (db.py, orders.py, servers.py, shared.py, ServerManage.tsx, ProductSelect.tsx) + test files
**Reviewer:** Automated strategic review

---

## Overall Assessment

The refactoring successfully extends the data model with geo/credentials/spec fields, adds a detail endpoint with password masking, server-side filtering, and a richer frontend (tabs, filters, detail modal). The migration approach is idempotent and test coverage for the new endpoints is strong. However there are **three concrete defects**: (1) a broken test that no longer matches the AuthError behavior, (2) plaintext password leakage in the list endpoint contradicting the detail endpoint masking, and (3) a non-functional password-copy button in the frontend. Several performance concerns (per-request migrations, N+1 API calls) and dead code (unused server-side filters) should also be addressed before shipping.

**Verdict:** Do not merge until P1-1 (failing test) is resolved. P1-2 and P1-3 are strongly recommended before release.

---

## Findings

### P1-1 — Test SC6 broken: expects HTTP 500 but code returns 401

**File:** admin/tests/test_orders_routes.py:403  vs  admin/api_routes/orders.py:171-181

**Confirmed failing** — ran `pytest admin/tests/test_orders_routes.py::TestAuthErrorNoPartialWrites` and got 1 failed.

The `create_orders` handler was changed so that on `AuthError` it returns a **401** JSONResponse carrying a partial-result body (success_count, batch_id, results, aborted) instead of the old behavior of raising a 500. But the test `test_auth_error_returns_500_no_partial_writes` still asserts the old contract:

```python
assert resp.status_code == 500
assert "认证失败" in resp.json()["detail"]   # KeyError: response has no 'detail' key
```

The new 401 response has no `detail` field (it returns success_count/results/aborted), so the second assertion raises `KeyError`, not merely a status mismatch.

**Suggestion:** Update the test to match the new contract. The 401 + partial-result behavior is arguably better (it preserves already-successful orders). Rename to reflect intent, e.g. `test_auth_error_returns_401_with_partial_results`:

```python
assert resp.status_code == 401
data = resp.json()
assert data["aborted"] is True
assert data["success_count"] == 0
# DB still empty: AuthError fired before any create_server_record
```

The code comment at orders.py:99 ("认证失败不再丢弃已成功的结果") confirms the 401 path is intentional, so the test is the stale artifact.

---

### P1-2 — Plaintext password leaked in GET /api/servers list response

**File:** admin/api_routes/servers.py:117 (`_server_to_dict`) and :262 (all-servers inline dict)

The detail endpoint `GET /api/servers/{id}/detail` carefully masks the password:

```python
result["password"] = "**"
```

But the **list** endpoint returns the plaintext password through BOTH code paths:
- account-scoped branch (line 201): `_server_to_dict(rec, ...)` emits `"password": rec.password`
- all-servers branch (line 262): `"password": r.get("password", "")`

Once a user opens the detail modal once (which caches the real password into the v8 `password` column), every subsequent `GET /api/servers` response carries the plaintext root password for that server. Test SC10 (test_servers_routes.py:489) even codifies the leak by asserting `rec["password"] == "secret123"`. The frontend `Server` interface never consumes `password`, so this is pure unnecessary exposure — it sits in browser memory, proxy logs, and any response logging.

The API is behind Bearer-token auth (admin/server.py:154-194), so this is not an open leak, but it is an avoidable inconsistency that defeats the masking done in the detail endpoint.

**Suggestion:** Strip `password` (and consider `root`) from list responses in both branches. Either drop the key from `_server_to_dict` and the inline dict, or mask it as empty string. Update SC10 to assert the password is NOT present (or is masked) rather than equal to the plaintext.

```python
# In _server_to_dict and the inline dict:
result.pop("password", None)   # or: "password": "",
```

---

### P1-3 — Frontend password-copy button is non-functional

**File:** admin/frontend/src/pages/ServerManage.tsx:188-210, 478-487

The detail modal renders a copy-password button bound to `d.password_raw`:

```tsx
<Tooltip title={d.password_raw ? '复制真实密码' : '暂无可复制的密码'}>
  <Button disabled={!d.password_raw} onClick={() => handleCopyPassword(d.password_raw)} />
</Tooltip>
```

But the backend `get_server_detail` endpoint **never sends `password_raw`**. It returns `_server_to_dict(rec)` (which sets `password` to the real value) and then immediately overwrites `result["password"] = "**"`. There is no code path that populates `password_raw`. As a result the button is **permanently disabled** and the tooltip always reads "暂无可复制的密码" — the entire copy-password feature is dead.

This is either an unfinished feature (intended: a separate authenticated reveal-password call) or a deliberate security gate with leftover dead UI.

**Suggestion:** Pick one explicitly.
- **(Recommended) Remove the dead UI:** Drop the copy button and `password_raw` from `ServerDetail`; keep only the masked `**` display. This matches the backend masking intent and avoids promising functionality that does not exist.
- **(If copy is genuinely desired):** Add a dedicated endpoint `POST /api/servers/{id}/reveal-password` that returns the raw password (rate-limited and audit-logged), and have the frontend call it on copy-click. Do NOT send `password_raw` in list/detail responses.

Either way the current state ships a button that visibly does nothing.

---

### P2-1 — migrate_db runs on every HTTP request (performance regression worsened by v8)

**File:** admin/api_routes/shared.py:63 (`await migrate_db(conn)` inside get_db)

The FastAPI `get_db` dependency calls `migrate_db(conn)` on **every request**. `_MIGRATIONS` now contains about 28 statements; v8 added 13. On every request each of the 13 `ALTER TABLE ... ADD COLUMN` statements executes and raises `OperationalError: duplicate column name`, which is caught and swallowed (db.py:167-171). That is 13 failing SQL round-trips plus the v4/v5/v7 UPDATE statements re-executing as no-ops on **every single API call**.

This was acceptable when migrations were few; v8 roughly doubled the count into noticeable-overhead territory, and SQLite serializes writes while migrate_db commits (db.py:172).

Note: the standalone `admin.db.get_db` context manager (db.py:175-201) does **not** run migrations at all — so the two `get_db` functions have divergent behavior, itself a latent bug.

**Suggestion:** Run migrations once at application startup in the lifespan handler (admin/server.py:128-135), not per-request:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.admin_db_path = db_path
    async with admin_get_db(db_path) as db:
        await migrate_db(db)   # once, at startup
    # ... load session, pwd hash, username ...
    yield
```

Then remove `await migrate_db(conn)` from `shared.get_db`. This also reconciles the two get_db paths.

---

### P2-2 — Live enrichment + DB writes during a GET request; N accounts x API call

**File:** admin/api_routes/servers.py:206-243

`GET /api/servers` (no account_id) fans out: for each account it calls `client.cloud.list` (an external zhaomu API call), and inside the loop it calls `update_server_status` (which commits) for every server whose status changed. With M accounts and S servers this is M external API calls plus up to S commits, all during what is semantically a read.

Concerns:
- Mixing read and write in a GET makes the endpoint non-idempotent and harder to reason about.
- S commits during a single list call causes SQLite write-lock contention under concurrent refreshes.
- The M external API calls are sequential (the loop is `for aid, recs in by_account.items()`).

**Suggestion:**
- Move status reconciliation into the existing background poller (the 30s setInterval already calls /poll and re-fetches) rather than doing it inline on every list call.
- If inline enrichment must stay, batch the status updates into a single UPDATE ... WHERE id IN (...) or defer to one commit at the end.
- Consider asyncio.gather over accounts (mind zhaomu rate limits).

---

### P2-3 — N+1 API calls in order loop: region.info called once per ordered unit

**File:** admin/api_routes/orders.py:198-207

Inside the per-unit loop, `client.region.info` is called after every successful order to fetch country/city. If a single OrderItem has quantity=10, this fires 10 identical region.info calls for the same product.region_id. For a batch of multiple items it compounds. The same pattern affects `product.info` at line 115 when quantity > 1.

**Suggestion:** Hoist the region lookup outside the quantity loop using a small cache dict keyed by region_id. Then the per-unit inner loop reads from the cache. Apply the same caching to product.info (keyed by product_id) so a batch of identical products is not re-queried.

---

### P2-4 — Duplicate field-list construction (maintenance hazard)

**File:** admin/api_routes/servers.py:94-127 (`_server_to_dict`) and 245-274 (inline dict in list_servers)

The same 25+ fields are enumerated in two places. `_server_to_dict` takes a ServerRecord; the all-servers branch works on dict rows from `list_servers_all`, so it re-lists every field inline. Adding or removing a column requires touching both sites, and the two branches already risk drifting (e.g., the inline path attaches `live` but `_server_to_dict` does not).

**Suggestion:** Make `list_servers_all` return ServerRecord objects (via `_row_to_server`, with account_name joined separately or attached), then route both branches through `_server_to_dict`. Or write a single `_row_dict_to_response(row_dict, account_name, live)` used by the inline path and delete the duplication.

---

### P2-5 — Server-side filter params are dead code (frontend never sends them)

**File:** admin/api_routes/servers.py:154-163 (7 Query params) plus `_apply_filters` (48-91)

The backend supports 7 optional filter query params (account_name, country, city, os, has_refund, ip_type, deploy_status) with AND logic. But the frontend fetchServers (ServerManage.tsx:94) calls `apiClient.get('/api/servers')` with **no query params** and does all filtering client-side via Ant Design filterDropdown/onFilter. So `_apply_filters` and the 7 params are exercised only by tests (SC11-14), never by the UI.

This is either intentionally redundant (defense in depth) or accidental. If intentional, add a comment documenting why. If not, the server-side filter code plus its tests are maintenance burden for no product value.

**Suggestion:** Decide explicitly.
- Drop server-side filtering (and SC11-14) since the client filters locally — simpler backend, less duplication. The `_get_field`/`_apply_filters` dual-type handling goes away too.
- Or adopt server-side filtering in the frontend (pass selected filter values as query params) to support large datasets or pagination.

Do not leave both systems half-wired.

---

### P3-1 — Column naming inconsistency (snake_case vs camelCase)

**File:** admin/db.py:56-61, 109-114

The v8 columns mix conventions: country, city, ip_type are snake_case but diskData, diskMedia, startTime, endTime, isAutoRenew are camelCase (matching the zhaomu API JSON keys). The pre-existing schema is entirely snake_case. This makes ad-hoc SQL and future ORM mapping error-prone.

**Suggestion:** Not worth a migration to fix now, but document the rationale (camelCase columns intentionally mirror upstream API field names to simplify _row_to_server and detail caching). Pick one convention for future columns and stick to it.

---

### P3-2 — Overly broad except Exception for region lookup in orders

**File:** admin/api_routes/orders.py:205-207

```python
except Exception:
    country = ""
    city = ""
```

`except Exception` swallows everything including programming errors (AttributeError, TypeError from a malformed response). The rest of the file catches specific ZhaomuError subtypes.

**Suggestion:** Narrow to `except ZhaomuError:` for consistency; let unexpected errors surface since they indicate a real bug worth noticing, not merely a degraded geo field.

---

### P3-3 — handleRefresh fakes a loading spinner during cooldown

**File:** admin/frontend/src/pages/ServerManage.tsx:101-110

```tsx
if (now - lastRefreshRef.current < REFRESH_COOLDOWN) {
  setLoading(true);
  setTimeout(() => setLoading(false), 400);
  return;
}
```

Clicking refresh during the 15s cooldown spins the loading indicator for 400ms without actually refreshing. This mimics responsiveness but can mislead users into thinking a refresh happened. The detail-modal refresh (lines 177-186) correctly shows a "请 N 秒后再试" warning instead.

**Suggestion:** Replace the fake spinner with a `message.warning` showing remaining cooldown seconds, matching handleDetailRefresh for consistency.

---

### P3-4 — Redundant result["ordered_at"] assignment in detail endpoint

**File:** admin/api_routes/servers.py:404

```python
result = _server_to_dict(rec)   # already sets result["ordered_at"] at line 110
result["password"] = "**"
result["ordered_at"] = rec.ordered_at   # redundant no-op
```

**Suggestion:** Delete line 404.

---

## Summary Table

| # | Severity | File | Issue | Effort |
|---|----------|------|-------|--------|
| P1-1 | P1 | orders.py / test_orders_routes.py | SC6 test fails: expects 500, code returns 401 (AuthError path changed, confirmed) | Quick |
| P1-2 | P1 | servers.py:117,262 | Plaintext password leaked in GET /api/servers list response | Quick |
| P1-3 | P1 | ServerManage.tsx:478-487 | Copy-password button always disabled; password_raw never sent by backend | Short |
| P2-1 | P2 | shared.py:63 | migrate_db runs every request (~28 SQL stmts); v8 worsened it | Short |
| P2-2 | P2 | servers.py:206-243 | Live enrichment + DB commits during GET; M accounts x API call | Medium |
| P2-3 | P2 | orders.py:198-207 | N+1: region.info called per ordered unit (quantity times) | Quick |
| P2-4 | P2 | servers.py:94-127,245-274 | Duplicate 25+ field enumeration in two code paths | Short |
| P2-5 | P2 | servers.py:154-163 | 7 server-side filter params unused by frontend (dead code) | Short |
| P3-1 | P3 | db.py:56-61 | Mixed snake_case/camelCase column naming | — |
| P3-2 | P3 | orders.py:205 | Bare except Exception for region lookup | Quick |
| P3-3 | P3 | ServerManage.tsx:101 | Fake loading spinner during cooldown (misleading) | Quick |
| P3-4 | P3 | servers.py:404 | Redundant ordered_at assignment | Quick |

**Effort legend:** Quick (under 1h), Short (1-4h), Medium (1-2d), Large (3d+)
