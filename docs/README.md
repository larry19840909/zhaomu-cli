# zhaomu API 文档

> 服务商朝暮数据（zhaomu）的 REST API 完整参考。由 `scripts/extract_docs.py` �?ShowDoc 自动提取，共 31 个端点�?
## 快速开�?
```python
from zhaomu.client import ZhaomuClient
# 从配置文件或环境变量创建客户�?client = ZhaomuClient.from_config("config.json")
```

## API 基本信息

- **Base URL**：`https://api.zhaomu.net`
- **认证方式**：`Authorization: Bearer <apikey>`（静�?API Key，无需 token 刷新�?- **HTTP 方法**：REST 风格（GET / POST / DELETE�?- **响应格式**�?  - **列表接口** �?直接返回 JSON 数组 `[{...}]`
  - **操作接口** �?`{"success": true/false, "message": "..."}`
- **实例状态码**�?=开通中 2=运行�?3=已关�?4=已禁�?5=准备�?- **付款周期**�?=月付 2=季付 3=半年�?4=年付 5=按小�?
## 端点速查

| 分类 | 方法 | 路径 | 说明 | 文档 |
|------|------|------|------|------|
| 可用�?| GET | `/region` | 可用区列�?| [→](api/01-regions/获取可用区列�?md) |
| 可用�?| GET | `/region/:id` | 可用区信�?| [→](api/01-regions/获取可用区信�?md) |
| 产品 | GET | `/product/region/:id` | 某可用区产品列表 | [→](api/02-products/获取云服务器产品列表.md) |
| 产品 | GET | `/product/:id` | 产品信息 | [→](api/02-products/获取云服务器产品信息.md) |
| 产品 | GET | `/product/price/:id` | 产品价格 | [→](api/02-products/获取云服务器产品价格.md) |
| 产品 | GET | `/compare/region/:id` | 产品参数比较 | [→](api/02-products/获取功能参数比较.md) |
| 实例 | GET | `/cloud` | 云服务器列表 | [→](api/03-cloud-lifecycle/获取云服务器列表.md) |
| 实例 | GET | `/cloud/:id` | 云服务器信息 | [→](api/03-cloud-lifecycle/获取云服务器信息.md) |
| 实例 | POST | `/cloud/order` | 订购云服务器 | [→](api/03-cloud-lifecycle/订购云服务器.md) |
| 实例 | GET | `/image/product/:id` | 获取可订购镜�?| [→](api/03-cloud-lifecycle/获取订购云服务器的镜�?md) |
| 实例 | POST | `/cloud/renew/:id` | 续费 | [→](api/04-cloud-management/续费云服务器.md) |
| 实例 | POST | `/cloud/upgrade/:id` | 变更配置 | [→](api/04-cloud-management/变更云服务器.md) |
| 实例 | POST | `/cloud/upgrade-price/:id` | 变更价格 | [→](api/04-cloud-management/获取变更云服务器价格.md) |
| 实例 | DELETE | `/cloud/destroy/:id` | 销�?| [→](api/04-cloud-management/销毁云服务�?md) |
| 实例 | POST | `/cloud/reboot/:id` | 重启/开�?| [→](api/04-cloud-management/重启_开机云服务�?md) |
| 实例 | POST | `/cloud/shutdown/:id` | 关机 | [→](api/04-cloud-management/关机云服务器.md) |
| 实例 | POST | `/cloud/rebuild/:id` | 重装系统 | [→](api/04-cloud-management/重装云服务器.md) |
| 实例 | GET | `/image/cloud/:id` | 可重装镜�?| [→](api/04-cloud-management/获取重装云服务器的镜�?md) |
| 实例 | POST | `/cloud/password/:id` | 重置密码 | [→](api/04-cloud-management/重置云服务器密码.md) |
| 实例 | GET | `/cloud/novnc/:id` | noVNC 控制�?| [→](api/04-cloud-management/获取云服务器控制�?md) |
| 管理 | POST | `/cloud/auto-renew/:id` | 设置自动续费 | [→](api/04-cloud-management/设置云服务器自动续费.md) |
| 管理 | POST | `/cloud/note/:id` | 修改用户备注 | [→](api/04-cloud-management/修改云服务器用户备注.md) |
| 管理 | POST | `/cloud/traffic/:id` | 刷新流量 | [→](api/04-cloud-management/刷新云服务器流量.md) |
| 其他 | GET | `/other/balance` | 获取用户余额 | [→](api/05-other/获取用户余额.md) |
| 加�?| POST | `/accelerator/order` | 订购海外加�?| [→](api/06-accelerator/订购海外服务器加�?md) |
| 加�?| GET | `/accelerator` | 海外加速列�?| [→](api/06-accelerator/获取海外服务器加速列�?md) |
| 加�?| GET | `/accelerator/:id` | 海外加速信�?| [→](api/06-accelerator/获取海外服务器加速信�?md) |
| 加�?| POST | `/accelerator/renew/:id` | 续费海外加�?| [→](api/06-accelerator/续费海外服务器加�?md) |
| 加�?| POST | `/accelerator/upgrade/:id` | 升级海外加�?| [→](api/06-accelerator/升级海外服务器加�?md) |
| 加�?| POST | `/accelerator/modify/:id` | 修改加�?IP | [→](api/06-accelerator/修改海外服务器加速IP.md) |
| 加�?| POST | `/accelerator/port/:id` | 修改加速端�?| [→](api/06-accelerator/修改海外服务器加速应用端�?md) |

## 文档目录

```
docs/
├── README.md                     # 本文�?�?API 总入�?└── api/
    ├── 01-regions/               # 可用区（2 个端点）
    ├── 02-products/              # 产品�? 个端点）
    ├── 03-cloud-lifecycle/       # 云服务器生命周期�? 个端点）
    ├── 04-cloud-management/      # 云服务器管理�?3 个端点）
    ├── 05-other/                 # 其他�? 个端点）
    └── 06-accelerator/           # 海外服务器加速（7 个端点）
```

## 更新文档

API 文档变更后，运行脚本重新提取�?
```bash
python scripts/extract_docs.py
```

该脚本自动从 ShowDoc 侧边栏发现所有页面并提取�?markdown�?