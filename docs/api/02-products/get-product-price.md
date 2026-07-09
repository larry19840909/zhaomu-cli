# Get Cloud Server Product Price

## Brief Description

Get pricing for a cloud server product. Supports querying with custom system disk, data disk, and bandwidth configurations.

## Request URL

`https://api.zhaomu.com/product/price/:id`

## Request Method

GET

## Path Variables

| Variable | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| id |  | Yes | int | Cloud server product ID |

## Header

| Field | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| Authorization | Bearer <apikey> | Yes | string | API key |

## Request Query Parameters

| Parameter | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| disk |  | No | int | Custom system disk size (GB). Uses default spec if omitted |
| diskData |  | No | int | Custom data disk size (GB). Uses default spec if omitted |
| bandwidth |  | No | int | Custom bandwidth (Mbps). Uses default spec if omitted |

## Success Response Example

```json
{
  "1": 10,
  "2": 30,
  "3": 60,
  "4": 120,
  "5": 0.02
}
```

## Success Response Parameter Description

| Parameter | Type | Description |
|--------|--------|--------|
| 1 | int | Monthly price (key = payment cycle ID: 1=Monthly) |
| 2 | int | Quarterly price (key = payment cycle ID: 2=Quarterly) |
| 3 | int | Semi-annual price (key = payment cycle ID: 3=Semi-annual) |
| 4 | int | Annual price (key = payment cycle ID: 4=Annual) |
| 5 | number | Hourly price (key = payment cycle ID: 5=Hourly; only available for some products) |

## Notes

1. If disk, data disk, and bandwidth parameters are omitted, the default spec pricing is returned, which matches the data from the "Get Cloud Server Product Info" endpoint.
2. Some products do not support hourly billing, so the hourly price key will not appear. Some products have a minimum payment cycle other than monthly, so the monthly price key may not appear.

## Observed Enum Values

**Payment cycle mapping (observed):**

| paymentCycle | Cycle | Example Price (Product 9723) | Example Price (Product 6910) |
|-------------|------|-------------------|-------------------|
| 1 (price field) | Monthly | ¥148 | ¥95 |
| 2 | Quarterly | ¥361 | ¥285 |
| 3 | Semi-annual | ¥721 | ¥570 |
| 4 | Annual | ¥1226 | ¥1140 |
