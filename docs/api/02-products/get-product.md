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
| id |  | Yes | int | Cloud server product ID |

## Header

| Field | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| Authorization | Bearer <apikey> | Yes | string | API key |

## Success Response Example

```json
{
  "id": 35,
  "cpu": 1,
  "ram": 1024,
  "disk": 25,
  "diskMax": 25,
  "diskData": 0,
  "diskDataMax": 40000,
  "diskMedia": "SSD",
  "bandwidth": null,
  "bandwidthMax": null,
  "traffic": 1000,
  "priceHour": 0.1,
  "price": 49,
  "priceQuarter": 147,
  "priceHalfYear": 294,
  "priceYear": 588,
  "tags": "",
  "outOfStock": 0,
  "noWindows": null,
  "region_id": 3
}
```

## Success Response Parameter Description

| Parameter | Type | Description |
|--------|--------|--------|
| id | int | Product ID. Used for ordering, pricing, and other operations |
| cpu | int | vCPU cores. Observed range: 1-24 cores |
| ram | int | Memory in MB. Observed range: 1024-393216 (1 GB-384 GB) |
| disk | int | System disk in GB. Observed range: 10-2048 GB |
| diskMax | int | Maximum selectable system disk size (GB) |
| diskData | int | Data disk in GB. 0 means no data disk |
| diskDataMax | int | Maximum selectable data disk size (GB) |
| diskMedia | string | Disk media type. Observed values: SSD, NORMAL |
| bandwidth | int/null | Bandwidth in Mbps. Typically null in observed responses |
| bandwidthMax | int/null | Maximum selectable bandwidth in Mbps. Typically null in observed responses |
| traffic | int/null | Monthly traffic quota in GB. null means unlimited. Observed range: 1000-15000 GB |
| priceHour | number/null | Hourly price in CNY. null means hourly billing not supported |
| price | number | Monthly price in CNY |
| priceQuarter | number | Quarterly price in CNY |
| priceHalfYear | number | Semi-annual price in CNY |
| priceYear | number | Annual price in CNY |
| minPaymentCycle | int | Minimum payment cycle. 1=Monthly, 2=Quarterly, 3=Semi-annual, 4=Annual, 5=Hourly |
| tags | string | Tags. Observed values: "" (empty), "Native IP", "Supports Windows" |
| outOfStock | int | Stock status. 0=In stock, 1=Out of stock |
| noWindows | int/null | Whether Windows is unsupported. null=Supported, 1=Unsupported |
| region_id | int | Region ID. See [Get Region List](../01-regions/list-regions.md) for enumerated values |

## Notes

None

## Observed Response Example

```json
{
  "id": 6910,
  "cpu": 2,
  "ram": 2048,
  "disk": 50,
  "traffic": 1000,
  "diskMedia": "SSD",
  "price": 95,
  "priceHour": null,
  "priceQuarter": 285,
  "priceHalfYear": 570,
  "priceYear": 1140,
  "tags": "Native IP"
}
```

## Observed Field Description

| Field | Type | Description | Example |
|------|------|------|------|
| id | int | Product ID | 6910 |
| cpu | int | vCPU cores | 2 |
| ram | int | Memory (MB) | 2048 |
| disk | int | System disk (GB) | 50 |
| traffic | int or null | Traffic (GB) | 1000 |
| diskMedia | str | Disk type | SSD |
| price | float | Monthly price | 95 |
| priceHour | float or null | Hourly price | null |
| priceQuarter | float | Quarterly price | 285 |
| priceHalfYear | float | Semi-annual price | 570 |
| priceYear | float | Annual price | 1140 |
| tags | str | Tags | Native IP |
