# Upgrade Overseas Server Accelerator

## Brief Description

Upgrade a specific overseas server accelerator.

## Request URL

`https://api.zhaomu.com/accelerator/upgrade/:id`

## Request Method

POST

## Path Variables

| Variable | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| id | 1 | Yes | string | Accelerator ID. See [List Overseas Server Accelerators](list-accelerators.md) for lookup |

## Header

| Field | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| Authorization | Bearer <apikey> | Yes | string | API key |

## Request Body Parameters

| Parameter | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| paymentCycle | 1 | Yes | int | Payment cycle. 1=Monthly, 2=Quarterly, 3=Half-year, 4=Yearly |

## Successful Response Example

```json
{
  "success": true,
  "message": "Overseas server accelerator upgraded successfully"
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

None
