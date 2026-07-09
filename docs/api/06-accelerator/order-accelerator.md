# Order Overseas Server Accelerator

## Brief Description

Order an overseas server accelerator, provisioned instantly.

## Request URL

`https://api.zhaomu.com/accelerator/order`

## Request Method

POST

## Header

| Field | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| Authorization | Bearer <apikey> | Yes | string | API key |

## Request Body Parameters

| Parameter | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| productId | 1 | Yes | int | Product ID (1=Basic, 2=Pro). See the [Product Type](#observed-enum-values) enum table below |
| region |  | Yes | string | Entry region. cn-bj2=Beijing, cn-sh2=Shanghai, cn-gd=Guangzhou. See observed enum values below |
| ip |  | Yes | string | Target server IP address (accelerated server) |
| port |  | Yes | int | Application port. Ports 80/443 are not supported |
| area |  | Yes | string | Server proximity area (Chinese). Observed values: Hong Kong, Taiwan, Tokyo, Los Angeles, Singapore, Frankfurt, Washington, London. See observed enum values below |
| paymentCycle | 1 | Yes | int | Payment cycle. 1=Monthly, 2=Quarterly, 3=Half-year, 4=Yearly. See observed enum values below |

## Successful Response Example

```json
{
  "success": true,
  "message": "Ordered cloud server: Canada Toronto Zone V\n1 vCPU 1GB, 1 month",
  "info": {
    "id": 21299,
    "renewPrice": 49,
    "paymentCycle": "1",
    "startTime": "2022-09-12T12:53:44.630419Z",
    "endTime": "2022-10-12T12:53:44.630419Z",
    "region_id": 18,
    "ip": "Pending",
    "root": "root",
    "password": "",
    "cpu": 1,
    "ram": 1024,
    "disk": 25,
    "diskData": 0,
    "bandwidth": null,
    "diskMedia": "SSD",
    "traffic": 1000,
    "image": "CentOS 7 64-bit",
    "imageIdentity": "167",
    "price": 49,
    "priceQuarter": 147,
    "priceHalfYear": 294,
    "priceYear": 588,
    "status": 1
  }
}
```

## Response Parameter Description

| Parameter | Type | Description |
|--------|--------|--------|
| success | boolean | Success / failure |
| message | string | Response message |
| id | int | Cloud server ID |

## Notes

Product IDs: 1=Basic, 2=Pro

Entry regions: cn-bj2=Beijing, cn-sh2=Shanghai, cn-gd=Guangzhou

Payment cycles: 1=Monthly, 2=Quarterly, 3=Half-year, 4=Yearly

Server proximity areas: Hong Kong, Singapore, Tokyo, Los Angeles, Washington, Frankfurt, Lagos

## Observed Enum Values

**Entry region (region) enum:**

| Value | Description |
|----|------|
| cn-bj2 | Beijing |
| cn-sh2 | Shanghai |
| cn-gd | Guangzhou |

**Server proximity area (area) — observed values (Chinese):**

| Value |
|-----|
| Hong Kong |
| Taiwan |
| Tokyo |
| Los Angeles |
| Singapore |
| Frankfurt |
| Washington |
| London |

**Product type (productId):**

| Value | Description |
|----|------|
| 1 | Basic |
| 2 | Pro |

**Payment cycle (paymentCycle):**

| Value | Description |
|----|------|
| 1 | Monthly |
| 2 | Quarterly |
| 3 | Half-year |
| 4 | Yearly |
