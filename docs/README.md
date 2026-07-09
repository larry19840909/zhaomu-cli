# zhaomu API Reference

> Complete REST API reference for zhaomu (朝暮数据). Extracted from ShowDoc by `scripts/extract_docs.py` — 31 endpoints.

## Quick Start

```python
from zhaomu.client import ZhaomuClient
client = ZhaomuClient.from_config("config.json")
```

## API Basics

- **Base URL**: `https://api.zhaomu.com`
- **Authentication**: `Authorization: Bearer <apikey>` (static API key, no token refresh)
- **HTTP Methods**: REST style (GET / POST / DELETE)
- **Response Format**:
  - **List endpoints** → JSON array `[{...}]`
  - **Action endpoints** → `{"success": true/false, "message": "..."}`
- **Instance Status**: 1=Provisioning 2=Running 3=Stopped 4=Disabled 5=Preparing
- **Payment Cycles**: 1=Monthly 2=Quarterly 3=Semi-annual 4=Annual 5=Hourly

## Endpoint Quick Reference

| Category | Method | Path | Description | Doc |
|----------|--------|------|-------------|-----|
| Regions | GET | `/region` | List regions | [→](api/01-regions/list-regions.md) |
| Regions | GET | `/region/:id` | Get region info | [→](api/01-regions/get-region.md) |
| Products | GET | `/product/region/:id` | List products in region | [→](api/02-products/list-products.md) |
| Products | GET | `/product/:id` | Get product info | [→](api/02-products/get-product.md) |
| Products | GET | `/product/price/:id` | Get product price | [→](api/02-products/get-product-price.md) |
| Products | GET | `/compare/region/:id` | Compare product features | [→](api/02-products/compare-products.md) |
| Servers | GET | `/cloud` | List cloud servers | [→](api/03-cloud-lifecycle/list-servers.md) |
| Servers | GET | `/cloud/:id` | Get server info | [→](api/03-cloud-lifecycle/get-server.md) |
| Servers | POST | `/cloud/order` | Order server | [→](api/03-cloud-lifecycle/order-server.md) |
| Servers | GET | `/image/product/:id` | Get order images | [→](api/03-cloud-lifecycle/get-order-images.md) |
| Servers | POST | `/cloud/renew/:id` | Renew server | [→](api/04-cloud-management/renew-server.md) |
| Servers | POST | `/cloud/upgrade/:id` | Upgrade server | [→](api/04-cloud-management/upgrade-server.md) |
| Servers | POST | `/cloud/upgrade-price/:id` | Get upgrade price | [→](api/04-cloud-management/get-upgrade-price.md) |
| Servers | DELETE | `/cloud/destroy/:id` | Destroy server | [→](api/04-cloud-management/destroy-server.md) |
| Servers | POST | `/cloud/reboot/:id` | Reboot / start | [→](api/04-cloud-management/reboot-server.md) |
| Servers | POST | `/cloud/shutdown/:id` | Shutdown | [→](api/04-cloud-management/shutdown-server.md) |
| Servers | POST | `/cloud/rebuild/:id` | Rebuild (reinstall OS) | [→](api/04-cloud-management/rebuild-server.md) |
| Servers | GET | `/image/cloud/:id` | Get rebuild images | [→](api/04-cloud-management/get-rebuild-images.md) |
| Servers | POST | `/cloud/password/:id` | Reset password | [→](api/04-cloud-management/reset-password.md) |
| Servers | GET | `/cloud/novnc/:id` | noVNC console | [→](api/04-cloud-management/get-console.md) |
| Management | POST | `/cloud/auto-renew/:id` | Set auto-renew | [→](api/04-cloud-management/set-auto-renew.md) |
| Management | POST | `/cloud/note/:id` | Set user note | [→](api/04-cloud-management/set-note.md) |
| Management | POST | `/cloud/traffic/:id` | Refresh traffic | [→](api/04-cloud-management/refresh-traffic.md) |
| Other | GET | `/other/balance` | Get balance | [→](api/05-other/get-balance.md) |
| Accelerator | POST | `/accelerator/order` | Order accelerator | [→](api/06-accelerator/order-accelerator.md) |
| Accelerator | GET | `/accelerator` | List accelerators | [→](api/06-accelerator/list-accelerators.md) |
| Accelerator | GET | `/accelerator/:id` | Get accelerator info | [→](api/06-accelerator/get-accelerator.md) |
| Accelerator | POST | `/accelerator/renew/:id` | Renew accelerator | [→](api/06-accelerator/renew-accelerator.md) |
| Accelerator | POST | `/accelerator/upgrade/:id` | Upgrade accelerator | [→](api/06-accelerator/upgrade-accelerator.md) |
| Accelerator | POST | `/accelerator/modify/:id` | Modify accelerator IP | [→](api/06-accelerator/modify-accelerator-ip.md) |
| Accelerator | POST | `/accelerator/port/:id` | Modify accelerator port | [→](api/06-accelerator/modify-accelerator-port.md) |

## Directory Structure

```
docs/
├── README.md                     # This file — API reference index
└── api/
    ├── 01-regions/               # Regions (2 endpoints)
    ├── 02-products/              # Products (4 endpoints)
    ├── 03-cloud-lifecycle/       # Server lifecycle (4 endpoints)
    ├── 04-cloud-management/      # Server management (13 endpoints)
    ├── 05-other/                 # Other (1 endpoint)
    └── 06-accelerator/           # Accelerator (7 endpoints)
```

## Updating Docs

After API doc changes, re-extract with:

```bash
python scripts/extract_docs.py
```

The script discovers all pages from the ShowDoc sidebar and extracts them as markdown.
