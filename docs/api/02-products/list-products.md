# List Cloud Server Products

## Brief Description

Get the list of cloud server products in a region.

## Request URL

`https://api.zhaomu.com/product/region/:id`

## Request Method

GET

## Path Variables

| Variable | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| id |  | Yes | string | Region ID. See [Get Region List](../01-regions/list-regions.md) for enumerated values |

## Header

| Field | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| Authorization | Bearer <apikey> | Yes | string | API key |

## Success Response Example

```json
[{
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
},{
  "id": 36,
  "cpu": 1,
  "ram": 2048,
  "disk": 55,
  "diskMax": 55,
  "diskData": 0,
  "diskDataMax": 40000,
  "diskMedia": "SSD",
  "bandwidth": null,
  "bandwidthMax": null,
  "traffic": 2000,
  "priceHour": 0.2,
  "price": 99,
  "priceQuarter": 297,
  "priceHalfYear": 594,
  "priceYear": 1188,
  "tags": "Supports Windows",
  "outOfStock": 0,
  "noWindows": null,
  "region_id": 3
}]
```

## Success Response Parameter Description

| Parameter | Type | Description |
|--------|--------|--------|
| id | int | Product ID. Used for ordering, pricing, and other operations |
| cpu | int | vCPU cores. Observed range: 1-24 cores |
| ram | int | Memory in MB. Observed range: 1024-393216 (1 GB-384 GB) |
| disk | int | System disk in GB. Observed range: 10-2048 GB |
| diskMax | int | Maximum system disk size (GB) |
| diskData | int | Data disk in GB |
| diskDataMax | int | Maximum data disk size (GB) |
| diskMedia | string | Disk media type. Observed values: SSD, NORMAL |
| bandwidth | int/null | Bandwidth in Mbps. Typically null in observed responses |
| bandwidthMax | int/null | Maximum bandwidth in Mbps. Typically null in observed responses |
| traffic | int/null | Monthly traffic quota in GB. null means unlimited. Observed range: 1000-15000 GB |
| priceHour | number/null | Hourly price in CNY. null means hourly billing not supported |
| price | number | Monthly price in CNY |
| priceQuarter | number | Quarterly price in CNY |
| priceHalfYear | number | Semi-annual price in CNY |
| priceYear | number | Annual price in CNY |
| tags | string | Tags. Observed values: "" (empty), "Native IP", "Supports Windows" |
| outOfStock | int | Stock status. 0=In stock, 1=Out of stock |
| noWindows | int/null | Whether Windows is unsupported. null=Supported, 1=Unsupported |
| region_id | int | Region ID. See [Get Region List](../01-regions/list-regions.md) for enumerated values |

## Notes

None
