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
| id | 1 | Yes | string | Accelerator ID. See [List Overseas Server Accelerators](list-accelerators.md) for lookup |

## Header

| Field | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| Authorization | Bearer <apikey> | Yes | string | API key |

## Successful Response Example

```json
{
  "id": 1,
  "type": "Basic",
  "domain": "123.123.123.123_30896.ipssh.net",
  "region": "cn-sh2",
  "ip": "123.123.123.123",
  "port": 8888,
  "area": "Hong Kong",
  "startTime": "2026-01-01 15:12:01",
  "endTime": "2026-04-01 15:12:01",
  "renewPrice": 30,
  "paymentCycle": 1
}
```

## Response Parameter Description

| Parameter | Type | Description |
|--------|--------|--------|
| id | int | Accelerator ID (instance ID) |
| type | string | Product type. Observed values: Basic, Pro |
| domain | string | Acceleration domain |
| region | string | Entry region. cn-bj2=Beijing, cn-sh2=Shanghai, cn-gd=Guangzhou |
| ip | string | Target server IP address (accelerated server) |
| port | int | Application port. Ports 80/443 are not supported |
| area | string | Server proximity area (Chinese). Observed values: Hong Kong, Taiwan, Tokyo, Los Angeles, Singapore, Frankfurt, Washington, London |
| startTime | string | Activation time |
| endTime | string | Expiration time |
| renewPrice | number | Renewal price, in CNY |
| paymentCycle | int | Payment cycle. 1=Monthly, 2=Quarterly, 3=Half-year, 4=Yearly |

## Notes

Entry regions: cn-bj2=Beijing, cn-sh2=Shanghai, cn-gd=Guangzhou

Payment cycles: 1=Monthly, 2=Quarterly, 3=Half-year, 4=Yearly

## Actual Response Example

```json
{
  "id": 3928,
  "ip": "98.98.115.246",
  "port": 19855,
  "type": "Pro",
  "area": "Taiwan",
  "region": "cn-sh2",
  "domain": "98.98.115.246_30896.ipssh.net",
  "startTime": "2026-07-07 16:01:12",
  "endTime": "2026-08-07 16:01:12",
  "renewPrice": 80,
  "paymentCycle": 1
}
```

## Actual Field Description

| Parameter | Type | Description |
|--------|--------|--------|
| id | int | Accelerator natural primary key |
| ip | string | Target server IP address (accelerated server) |
| port | int | Application port |
| type | string | Product type name ("Basic" or "Pro") |
| area | string | Server proximity area (Chinese) |
| region | string | Entry region identifier (cn-bj2/cn-sh2/cn-gd) |
| domain | string | Acceleration domain |
| startTime | string | Activation time (YYYY-MM-DD HH:mm:ss) |
| endTime | string | Expiration time (YYYY-MM-DD HH:mm:ss) |
| renewPrice | int | Renewal price (CNY) |

## Notes

Entry regions:
- cn-bj2: Beijing
- cn-sh2: Shanghai
- cn-gd: Guangzhou

Payment cycles:
- 1: Monthly
- 2: Quarterly
- 3: Half-year
- 4: Yearly
