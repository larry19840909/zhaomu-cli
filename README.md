# zhaomu

CLI tool and Python SDK for managing cloud servers and accelerators on [朝暮数据](https://zhaomu.com) (zhaomu).

## Installation

```bash
pip install git+https://github.com/larry19840909/zhaomu-cli.git
```

For local development:

```bash
git clone https://github.com/larry19840909/zhaomu-cli.git
cd zhaomu-cli
pip install -e .
```

Requires Python 3.10+.

## Authentication

Choose one of two methods. When both are present, the config file takes precedence.

### Method 1: Config File

Create a `config.json` in your working directory:

```json
{
  "apikey": "your_zhaomu_api_key"
}
```

Use `-c` to specify a different path:

```bash
zhaomu -c /path/to/config.json cloud list
```

Keep `config.json` in `.gitignore` — it contains secrets. A template is available at `config.json.example`.

### Method 2: Environment Variables

```bash
export ZHAOMU_APIKEY="your_zhaomu_api_key"
```

Windows (PowerShell):

```powershell
$env:ZHAOMU_APIKEY = "your_zhaomu_api_key"
```

## Readable Identifiers

Instead of numeric IDs, most commands accept human-readable values. See [resolvers](zhaomu/cli/resolvers.py) for full implementation.

### Region

`-r / --region` accepts any of the following:

| Form | Example | How it resolves |
|------|---------|----------------|
| Numeric ID | `780` | Used directly |
| City name (Chinese) | `南昌`, `东京` | Substring match on `city` |
| City name (English) | `Singapore`, `Tokyo` | Substring match on `cityEn` |

Run `zhaomu region list` to see all available regions.

### Product

Product identifiers accept:

| Form | Example | How it resolves |
|------|---------|----------------|
| Numeric ID | `9723` | Used directly |
| Spec string | `2C-4G` | Matches CPU + RAM pattern in product list |

When resolving by name, `-r / --region` is required to scope the search to a specific region.

### Instance (Cloud Server / Accelerator)

Instance commands accept ID or IP:

| Form | Example | How it finds |
|------|---------|-------------|
| Numeric ID | `280722` | Direct lookup |
| IPv4 address | `31.210.52.36` | Exact IP match across all instances |

---

## CLI Reference

All commands support `--json` for machine-readable output. Place `--json` before the subcommand:

```bash
zhaomu --json cloud list
```

Global options:

```
-c, --config PATH   Config file path (default: config.json)
--json              Output as JSON
--help              Show help
```

### zhaomu region list

List all available regions (availability zones).

```bash
zhaomu region list
zhaomu --json region list
```

Output columns: ID, City, Country, Continent, Zone.

### zhaomu region info

Show details for a specific region.

```bash
zhaomu region info 780
zhaomu --json region info 780
```

### zhaomu product list

List cloud server products in a region.

```bash
zhaomu product list -r 780
zhaomu product list -r 南昌
zhaomu product list -r Tokyo
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `-r, --region` | *(required)* | Region ID, city name (CN/EN) |

### zhaomu product info

Show product details.

```bash
# By numeric ID — no region needed
zhaomu product info 9723

# By spec name — region required for scoping
zhaomu product info 2C-4G -r 南昌
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `-r, --region` | — | Required for name resolution |

### zhaomu product price

Get product pricing across payment cycles.

```bash
# By numeric ID
zhaomu product price 9723

# By spec name
zhaomu product price 2C-8G -r 南昌
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `-r, --region` | — | Required for name resolution |

### zhaomu product compare

Compare feature support across products in a region.

```bash
zhaomu product compare -r 780
zhaomu product compare -r 南昌
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `-r, --region` | *(required)* | Region ID or name |

### zhaomu cloud list

List all cloud servers.

```bash
zhaomu cloud list
zhaomu --json cloud list
```

Output columns: ID, IP, CPU, RAM, Disk, Image, Status, Start, End.

### zhaomu cloud info

Show cloud server details. Accepts ID or IP.

```bash
zhaomu cloud info 280722
zhaomu cloud info 31.210.52.36
zhaomu --json cloud info 280722
```

### zhaomu cloud images

List OS images available for ordering a product.

```bash
zhaomu cloud images -r 780 -p 9723
zhaomu cloud images -r 南昌 -p 2C-4G
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `-r, --region` | *(required)* | Region |
| `-p, --product` | *(required)* | Product ID or spec name |

### zhaomu cloud order

Order a new cloud server.

```bash
# Minimal
zhaomu cloud order -r 780 -p 9723 -i 167

# Full
zhaomu cloud order -r 南昌 -p 2C-4G -i "Ubuntu Server 22.04" \
    --disk 40 --period 1
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `-r, --region` | *(required)* | Region |
| `-p, --product` | *(required)* | Product ID or spec name |
| `-i, --image` | *(required)* | Image ID or name |
| `--disk` | `20` | System disk size (GB) |
| `--period` | `1` | Payment cycle (1=Monthly, 2=Quarterly, 3=Half-year, 4=Yearly) |

### zhaomu cloud rebuild-images

List OS images available for rebuilding a cloud server.

```bash
zhaomu cloud rebuild-images 280722
zhaomu cloud rebuild-images 31.210.52.36
```

### zhaomu cloud rebuild

Rebuild (reinstall OS) a cloud server.

```bash
zhaomu cloud rebuild 280722 -i 842
zhaomu cloud rebuild 31.210.52.36 -i "Ubuntu 20.04"
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `-i, --image` | *(required)* | Image ID or name |

### zhaomu cloud renew

Renew a cloud server.

```bash
zhaomu cloud renew 280722
zhaomu cloud renew 31.210.52.36 --period 4
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--period` | `1` | Payment cycle |

### zhaomu cloud upgrade

Upgrade cloud server configuration. At least one of `--cpu`, `--ram`, `--disk` is required.

```bash
zhaomu cloud upgrade 280722 --ram 2048
zhaomu cloud upgrade 31.210.52.36 --cpu 2 --ram 4096
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--cpu` | — | vCPU count |
| `--ram` | — | RAM in MB |
| `--disk` | — | System disk in GB |

### zhaomu cloud upgrade-price

Get upgrade price quote without applying changes.

```bash
zhaomu cloud upgrade-price 280722 --disk 50
zhaomu cloud upgrade-price 280722 -p 9730
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `-p, --product` | — | Target product ID |
| `--disk` | — | System disk in GB |
| `--disk-data` | — | Data disk in GB |
| `--bandwidth` | — | Bandwidth in Mbps |

### zhaomu cloud destroy

Destroy (delete) a cloud server.

```bash
zhaomu cloud destroy 280722
zhaomu cloud destroy 31.210.52.36
```

### zhaomu cloud reboot

Reboot or start a cloud server.

```bash
zhaomu cloud reboot 280722
zhaomu cloud reboot 31.210.52.36
```

### zhaomu cloud shutdown

Shutdown a cloud server.

```bash
zhaomu cloud shutdown 280722
zhaomu cloud shutdown 31.210.52.36
```

### zhaomu cloud reset-password

Reset root password for a cloud server.

```bash
zhaomu cloud reset-password 280722 --password "NewP@ssw0rd!"
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--password` | *(required)* | New root password |

### zhaomu cloud console

Get noVNC console URL for a cloud server.

```bash
zhaomu cloud console 280722
zhaomu --json cloud console 280722
```

The URL is returned in the `message` field when available.

### zhaomu cloud auto-renew

Set auto-renew for a cloud server.

```bash
zhaomu cloud auto-renew 280722 1     # enable
zhaomu cloud auto-renew 280722 0     # disable
```

### zhaomu cloud note

Set a user note for a cloud server.

```bash
zhaomu cloud note 280722 "production - main web server"
```

### zhaomu cloud refresh-traffic

Refresh traffic usage data for a cloud server.

```bash
zhaomu cloud refresh-traffic 280722
zhaomu --json cloud refresh-traffic 280722
```

### zhaomu accelerator list

List all overseas server accelerators.

```bash
zhaomu accelerator list
zhaomu --json accelerator list
```

Output columns: ID, IP, Port, Type, Area, Region.

### zhaomu accelerator info

Show accelerator details. Accepts ID or IP.

```bash
zhaomu accelerator info 3928
zhaomu accelerator info 98.98.115.246
```

### zhaomu accelerator order

Order an overseas server accelerator.

```bash
zhaomu accelerator order --region cn-sh2 --ip 31.210.52.36 \
    --port 19855 --area 台湾 --period 1
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `-p, --product` | `1` | 1=Basic, 2=Pro |
| `--region` | *(required)* | Entry region (cn-bj2/cn-sh2/cn-gd) |
| `--ip` | *(required)* | Target server IP |
| `--port` | *(required)* | Application port (not 80/443) |
| `--area` | *(required)* | Server area (Chinese: 香港/新加坡/东京…) |
| `--period` | `1` | Payment cycle |

### zhaomu accelerator renew

Renew an accelerator.

```bash
zhaomu accelerator renew 3928
zhaomu accelerator renew 98.98.115.246 --period 4
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--period` | `1` | Payment cycle |

### zhaomu accelerator upgrade

Upgrade an accelerator.

```bash
zhaomu accelerator upgrade 3928 --period 4
```

### zhaomu accelerator modify-ip

Modify the target server IP for an accelerator.

```bash
zhaomu accelerator modify-ip 3928 --ip 1.2.3.4 --area 香港
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--ip` | *(required)* | New server IP |
| `--area` | *(required)* | Server area (Chinese) |

### zhaomu accelerator modify-port

Modify the application port for an accelerator.

```bash
zhaomu accelerator modify-port 3928 --port 50758
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--port` | *(required)* | New application port |

### zhaomu balance

Show account balance.

```bash
zhaomu balance
zhaomu --json balance
```

---

## Instance Status Codes

| Code | Status |
|------|--------|
| 1 | Provisioning |
| 2 | Running |
| 3 | Stopped |
| 4 | Disabled |
| 5 | Preparing |

---

## Payment Cycles

| Code | Cycle |
|------|-------|
| 1 | Monthly |
| 2 | Quarterly |
| 3 | Half-year |
| 4 | Yearly |
| 5 | Hourly |

---

## JSON Output

Every command supports `--json` for structured output:

```bash
# Filter with jq
zhaomu --json cloud list | jq '.[] | {id, ip, ram, statusName}'

# Scripts
zhaomu --json balance
# → {"balance": 0.8}

zhaomu --json cloud info 280722 | jq '.ip'
# → "31.210.52.36"
```

Write operations (order, renew, destroy, etc.) return `{"success": true/false, "message": "..."}`. List operations return JSON arrays.

---

## Python SDK

You can use `zhaomu` programmatically as a Python library.

### Quick Start

```python
from zhaomu.client import ZhaomuClient

# From config file
client = ZhaomuClient.from_config("config.json")

# Or from environment variables
import os
os.environ["ZHAOMU_APIKEY"] = "..."
client = ZhaomuClient.from_config()  # falls back to ZHAOMU_APIKEY env var
```

### Query Regions

```python
regions = client.region.list()
for r in regions:
    print(f"{r.id}: {r.city} ({r.country}) — {r.zone}")

# Single region
r = client.region.info(780)
print(r.city, r.country)
```

### Query Products

```python
# List products in a region
products = client.product.list(780)
for p in products:
    print(f"{p.id}: {p.cpu}C/{p.ram // 1024}G/{p.disk}G — ¥{p.price}/mo")

# Product details
p = client.product.info(9723)
print(f"Monthly: ¥{p.price}, Quarterly: ¥{p.priceQuarter}")

# Product pricing across cycles
prices = client.product.price(9723)
for cycle, price in prices.items():
    print(f"Cycle {cycle}: ¥{price}")

# Compare features in a region
compare = client.product.compare(780)
for item in compare:
    print(f"{item.name}: {item.explain}")
```

### Query Images

```python
# Images available for ordering a product
images = client.cloud.images(product_id=9723)
for img in images:
    print(f"{img.id}: {img.name} ({img.type})")

# Images available for rebuilding a cloud server
images = client.cloud.rebuild_images(280722)
for img in images:
    print(f"{img.id}: {img.name}")
```

### List & Inspect Instances

```python
# List all cloud servers
servers = client.cloud.list()
for s in servers:
    print(f"{s.id}: {s.ip} — {s.cpu}C/{s.ram // 1024}G/{s.disk}G — {s.statusName}")

# Cloud server detail
s = client.cloud.info(280722)
print(f"IP: {s.ip}, Status: {s.statusName}, Image: {s.image}")
print(f"Traffic: {s.traffic}G, Auto Renew: {s.isAutoRenew}")
```

### Order a Cloud Server

```python
from zhaomu.models.cloud.request import OrderRequest

req = OrderRequest(
    regionId=780,
    productId=9723,
    imageId=842,        # Ubuntu 20.04
    disk=40,
    paymentCycle=1,     # Monthly
)
result = client.cloud.order(req)
if result.success:
    print(f"Order placed: {result.message}")
```

### Manage Cloud Servers

```python
# Rebuild (reinstall OS)
from zhaomu.models.cloud.request import RebuildRequest
client.cloud.rebuild(280722, RebuildRequest(imageId=842))

# Renew
from zhaomu.models.cloud.request import RenewRequest
client.cloud.renew(280722, RenewRequest(paymentCycle=4))  # Yearly

# Upgrade — at least one field required
from zhaomu.models.cloud.request import UpgradeRequest
client.cloud.upgrade(280722, UpgradeRequest(ram=4096))

# Get upgrade price before committing
from zhaomu.models.cloud.request import UpgradePriceRequest
price = client.cloud.upgrade_price(280722, UpgradePriceRequest(disk=50))
print(price.message)

# Power management
client.cloud.reboot(280722)
client.cloud.shutdown(280722)

# Reset password
from zhaomu.models.cloud.request import ResetPasswordRequest
client.cloud.reset_password(280722, ResetPasswordRequest(password="NewP@ssw0rd!"))

# Destroy
client.cloud.destroy(280722)
```

### Settings & Utilities

```python
# Auto-renew
from zhaomu.models.cloud.request import AutoRenewRequest
client.cloud.auto_renew(280722, AutoRenewRequest(isAutoRenew=1))

# User note
from zhaomu.models.cloud.request import NoteRequest
client.cloud.note(280722, NoteRequest(noteUser="production server"))

# Refresh traffic
client.cloud.refresh_traffic(280722)

# noVNC console
result = client.cloud.console(280722)
print(result.message)  # Console URL
```

### Accelerators

```python
# List
accs = client.accelerator.list()
for a in accs:
    print(f"{a.id}: {a.ip}:{a.port} → {a.area} ({a.type})")

# Order
from zhaomu.models.accelerator import AcceleratorOrderRequest
req = AcceleratorOrderRequest(
    productId=1, region="cn-sh2", ip="31.210.52.36",
    port=19855, area="台湾", paymentCycle=1,
)
result = client.accelerator.order(req)

# Renew / Upgrade
client.accelerator.renew(3928, paymentCycle=1)
client.accelerator.upgrade(3928, paymentCycle=4)

# Modify IP / Port
from zhaomu.models.accelerator import AcceleratorModifyRequest, AcceleratorPortRequest
client.accelerator.modify_ip(3928, AcceleratorModifyRequest(ip="1.2.3.4", area="香港"))
client.accelerator.modify_port(3928, AcceleratorPortRequest(port=50758))
```

### Balance

```python
balance = client.balance.get()
print(f"Balance: ¥{balance.balance}")
```

### Error Handling

```python
from zhaomu.errors import AuthError, APIError, NetworkError

try:
    client.cloud.list()
except AuthError:
    print("API key invalid or missing")
except APIError as e:
    print(f"API error: {e}")
except NetworkError:
    print("Network connection failed")
```

---

---

## 文档

| 文档 | 说明 |
|------|------|
| [API 总入口](docs/README.md) | 31 个端点速查表 + API 基本信息 |
| [可用区 API](docs/api/01-regions/) | 2 个端点 — 可用区列表/详情（含实测 Zone/Continent/Country 枚举） |
| [产品 API](docs/api/02-products/) | 4 个端点 — 产品列表/详情/价格/功能比较（含 25 项 target_id 映射） |
| [云服务器生命周期](docs/api/03-cloud-lifecycle/) | 4 个端点 — 列表/详情/订购/镜像（含 status/paymentCycle 枚举） |
| [云服务器管理](docs/api/04-cloud-management/) | 13 个端点 — 续费/升降级/销毁/重装/控制台等 |
| [其他](docs/api/05-other/) | 1 个端点 — 余额查询 |
| [海外加速](docs/api/06-accelerator/) | 7 个端点 — 列表/订购/续费/升级/修改IP端口（含 area/region 枚举） |

## License

MIT — see [LICENSE](LICENSE).
