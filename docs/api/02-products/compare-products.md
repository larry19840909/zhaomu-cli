# Compare Feature Parameters

## Brief Description

Get feature parameter comparison for a region. Returns per-feature support status for the specified region.

## Request URL

`https://api.zhaomu.com/compare/region/:id`

## Request Method

GET

## Path Variables

| Variable | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| id | 8 | Yes | string | Region ID. See [Get Region List](../01-regions/list-regions.md) for enumerated values |

## Header

| Field | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| Authorization | Bearer <apikey> | Yes | string | API key |

## Success Response Example

**Note:** The `name` field is returned in Chinese by the API. English translations are provided for reference only.

```json
[
  {
    "target_id": 1,
    "name": "实时开通",
    "explain": "24小时内开通"
  },
  {
    "target_id": 10,
    "name": "销毁退款",
    "explain": "支持"
  },
  {
    "target_id": 12,
    "name": "测试IP",
    "explain": "108.61.149.182"
  },
  {
    "target_id": 27,
    "name": "IP属性",
    "explain": "原生IP"
  }
]
```

## Success Response Parameter Description

| Parameter | Type | Description |
|--------|--------|--------|
| target_id | int | Feature parameter ID. See the [Complete Feature Enumeration](#complete-feature-enumeration) table below for the full ID-to-name mapping (26 items) |
| name | string | Feature name in **Chinese** (API returns Chinese names) |
| explain | string | Feature support status. Per-feature semantics vary: `支持`/`不支持`/`提交工单` for boolean features; SSD type for hardware; IP address for test IP; `原生IP`/`住宅IP` for IP type |

## Notes

- The API response is localized to Chinese. Field names (`target_id`, `name`, `explain`) are fixed; the `name` and `explain` values are Chinese strings.
- **26 feature IDs observed** across regions (IDs 11 and 14 are unused/gaps).
- `explain` is NOT a simple boolean — it can be `支持`, `不支持`, `提交工单`, an IP address, a description string, or HTML (e.g., `<br>` for line breaks).

## Complete Feature Enumeration

**26 items verified against live API responses from 仰光 (id=517) and 纽约 (id=8).**

| target_id | 中文名称 (API) | English | Typical explain Values |
|-----------|---------------|---------|----------------------|
| 1 | 实时开通 | Instant Provisioning | `24小时内开通` / `支持` |
| 2 | 在线重启 | Online Reboot | `支持` / `提交工单` |
| 3 | 在线关机 | Online Shutdown | `支持` / `提交工单` |
| 4 | 重装系统 | OS Reinstall | `支持` / `提交工单<br>每月免费3次` |
| 5 | 在线重置密码 | Online Password Reset | `支持` / `提交工单` / `不支持` |
| 6 | noVNC控制台 | noVNC Console | `支持` / `不支持` |
| 7 | 备份快照 | Backup & Snapshot | `支持` / `提交工单` |
| 8 | 升级配置 | Plan Upgrade | `支持` / `提交工单` |
| 9 | 监控信息 | Monitoring Info | `提交工单` / descriptive text |
| **10** | **销毁退款** | **Destroy Refund** | **`支持` / `不支持`** |
| 12 | 测试IP | Test IP | IP address (e.g. `108.61.149.182`) |
| 13 | Windows系统 | Windows System | `支持` / `不支持` |
| 15 | 硬盘类型 | Disk Type (SSD) | `SSD云盘` |
| 16 | 降级配置 | Plan Downgrade | `支持` / `不支持` |
| 17 | 按小时付费 | Hourly Billing | `支持` / `不支持` |
| 18 | 增加IP | Add Extra IP | `每台最多增加2个IP<br>20元/个/月` / `不支持` |
| 19 | 更换主IP | Change Primary IP | `增加IP后手动更换` / `不支持` |
| 20 | 反向解析 | Reverse DNS (PTR) | `支持` / `不支持` |
| 21 | IPv6 | IPv6 Support | `支持` / `不支持` |
| 22 | 创建自定义镜像 | Create Custom Image | `支持` / `提交工单` / `不支持` |
| 23 | 上传自定义镜像 | Upload Custom Image | `不支持` |
| 24 | 增加流量 | Add Traffic | `支持` / `不支持` |
| 25 | 流量统计 | Traffic Statistics | `双向` / `单向` |
| 26 | 端口限制 | Port Restrictions | `全部开放` / `禁用25端口` |
| 27 | IP属性 | IP Type | `原生IP` / `住宅IP` |

## explain 值速查

| explain 值 | 含义 |
|-----------|------|
| `支持` | Supported |
| `不支持` | Not supported |
| `提交工单` | Requires ticket submission |
| `24小时内开通` | Provisioned within 24 hours |
| `SSD云盘` | SSD cloud disk |
| `原生IP` | Native IP |
| `住宅IP` | Residential IP |
| `全部开放` | All ports open |
| `双向` / `单向` | Bidirectional / Unidirectional traffic counting |
