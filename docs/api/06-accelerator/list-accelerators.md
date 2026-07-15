# List Overseas Server Accelerators

## Brief Description

Get the complete list of overseas server accelerators for the user.

## Request URL

`https://api.zhaomu.com/accelerator`

## Request Method

GET

## Header

| Field | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| Authorization | Bearer <apikey> | Yes | string | API key |

## Success Response Example

**Note:** `type` and `area` values are returned in Chinese by the API.

```json
[{
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
}]
```

## Response Parameter Description

| Parameter | Type | Description |
|--------|--------|--------|
| id | int | Accelerator ID (instance ID) |
| type | string | Product type. API returns Chinese: `基础型` (Basic), `专业型` (Pro) |
| domain | string | Acceleration domain |
| region | string | Entry region identifier. `cn-bj2`=Beijing, `cn-sh2`=Shanghai, `cn-gd`=Guangzhou |
| ip | string | Target server IP address (accelerated server) |
| port | int | Application port. Ports 80/443 are not supported |
| area | string | Server area (Chinese). API returns e.g. `香港`, `台湾`, `东京`, `新加坡`, `洛杉矶` |
| startTime | string | Activation time (YYYY-MM-DD HH:mm:ss) |
| endTime | string | Expiration time (YYYY-MM-DD HH:mm:ss) |
| renewPrice | number | Renewal price, in CNY |
| paymentCycle | int | Payment cycle: `1`=Monthly, `2`=Quarterly, `3`=Half-year, `4`=Yearly |

## Notes

- Entry region IDs: `cn-bj2` (Beijing), `cn-sh2` (Shanghai), `cn-gd` (Guangzhou)
- Payment cycles: `1`=Monthly, `2`=Quarterly, `3`=Half-year, `4`=Yearly
- `type` values: `基础型` (Basic), `专业型` (Pro)
- `area` values (Chinese): `香港`, `台湾`, `东京`, `新加坡`, `洛杉矶`, `法兰克福`, `华盛顿`, `伦敦`
