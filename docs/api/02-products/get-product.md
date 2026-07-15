# Get Cloud Server Product Info

## Brief Description

Get details of a specific cloud server product.

## Request URL

`https://api.zhaomu.com/product/:id`

## Request Method

GET

## Path Variables

| Variable | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| id | 9723 | Yes | int | Cloud server product ID |

## Header

| Field | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| Authorization | Bearer <apikey> | Yes | string | API key |

## Success Response Example

**Note:** `diskMedia` values are English (`SSD`, `NORMAL`). `tags` values are Chinese (`原生IP`, `住宅IP`).

```json
{
  "id": 9723,
  "cpu": 2,
  "ram": 4096,
  "disk": 40,
  "diskMax": 1000,
  "diskData": 0,
  "diskDataMax": 32000,
  "diskMedia": "NORMAL",
  "bandwidth": 1,
  "bandwidthMax": 200,
  "traffic": null,
  "priceHour": null,
  "price": 90,
  "priceQuarter": 270,
  "priceHalfYear": 540,
  "priceYear": 1080,
  "tags": "原生IP",
  "outOfStock": 0,
  "noWindows": 1,
  "minPaymentCycle": 1,
  "region_id": 8
}
```

## Success Response Parameter Description

| Parameter | Type | Description |
|--------|--------|--------|
| id | int | Product ID |
| cpu | int | vCPU cores |
| ram | int | Memory in MB |
| disk | int | System disk in GB |
| diskMax | int | Maximum system disk size (GB) |
| diskData | int | Data disk in GB. 0 means no data disk |
| diskDataMax | int | Maximum data disk size (GB) |
| diskMedia | string | Disk media type. API returns English: `SSD`, `NORMAL` |
| bandwidth | int/null | Bandwidth in Mbps |
| bandwidthMax | int/null | Maximum bandwidth in Mbps |
| traffic | int/null | Monthly traffic quota in GB. `null` means unlimited |
| priceHour | number/null | Hourly price in CNY. `null` means hourly billing not supported |
| price | number | Monthly price in CNY |
| priceQuarter | number | Quarterly price in CNY |
| priceHalfYear | number | Semi-annual price in CNY |
| priceYear | number | Annual price in CNY |
| tags | string | Tags (Chinese). API returns e.g. `原生IP`, `住宅IP`, `""` (empty) |
| outOfStock | int | Stock status. `0`=In stock, `1`=Out of stock |
| noWindows | int/null | Windows support. `null`=Supported, `1`=Unsupported |
| minPaymentCycle | int | Minimum payment cycle. `1`=Monthly, `2`=Quarterly, `3`=Half-year, `4`=Annual, `5`=Hourly |
| region_id | int | Region ID. See [List Regions](../01-regions/list-regions.md) |
