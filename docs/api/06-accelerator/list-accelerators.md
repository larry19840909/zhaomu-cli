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

## Successful Response Example

```json
[{
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
}]
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
