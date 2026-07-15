# Get Overseas Server Accelerator Info

## Brief Description

Get information about a specific overseas server accelerator.

## Request URL

`https://api.zhaomu.com/accelerator/:id`

## Request Method

GET

## Path Variables

| Variable | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| id | 3928 | Yes | string | Accelerator ID. See [List Accelerators](list-accelerators.md) |

## Header

| Field | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| Authorization | Bearer <apikey> | Yes | string | API key |

## Success Response Example

**Note:** `type` and `area` values are returned in Chinese by the API.

```json
{
  "id": 3928,
  "type": "专业型",
  "domain": "98.98.115.246_30896.ipssh.net",
  "region": "cn-sh2",
  "ip": "98.98.115.246",
  "port": 19855,
  "area": "台湾",
  "startTime": "2026-07-07 16:01:12",
  "endTime": "2026-08-07 16:01:12",
  "renewPrice": 80,
  "paymentCycle": 1
}
```

## Response Parameter Description

| Parameter | Type | Description |
|--------|--------|--------|
| id | int | Accelerator ID (instance ID) |
| type | string | Product type. API returns Chinese: `基础型` (Basic), `专业型` (Pro) |
| domain | string | Acceleration domain |
| region | string | Entry region. `cn-bj2`=Beijing, `cn-sh2`=Shanghai, `cn-gd`=Guangzhou |
| ip | string | Target server IP address (accelerated server) |
| port | int | Application port. Ports 80/443 are not supported |
| area | string | Server area (Chinese). API returns e.g. `香港`, `台湾`, `东京`, `新加坡`, `洛杉矶` |
| startTime | string | Activation time (YYYY-MM-DD HH:mm:ss) |
| endTime | string | Expiration time (YYYY-MM-DD HH:mm:ss) |
| renewPrice | number | Renewal price, in CNY |
| paymentCycle | int | Payment cycle: `1`=Monthly, `2`=Quarterly, `3`=Half-year, `4`=Yearly |

## Notes

- Entry regions: `cn-bj2` (Beijing), `cn-sh2` (Shanghai), `cn-gd` (Guangzhou)
- Payment cycles: `1`=Monthly, `2`=Quarterly, `3`=Half-year, `4`=Yearly
- `type` values: `基础型` (Basic), `专业型` (Pro)
- `area` values (Chinese): `香港`, `台湾`, `东京`, `新加坡`, `洛杉矶`, `法兰克福`, `华盛顿`, `伦敦`
