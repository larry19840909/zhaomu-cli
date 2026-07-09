# Get Cloud Server Info

## Brief Description

Get information about a specific cloud server

## Request URL

`https://api.zhaomu.com/cloud/:id`

## Method

GET

## Path Parameters

| Parameter | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| id |  | Yes | int | Cloud server product ID |

## Header

| Field | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| Authorization | Bearer <apikey> | Yes | string | API key |

## Success Response Example

```json
复制{
  "id": 21299,
  "ip": "155.138.139.237",
  "root": "root",
  "password": "xxxxxx",
  "cpu": 1,
  "ram": 1024,
  "disk": 25,
  "diskData": 0,
  "diskMedia": "SSD",
  "bandwidth": null,
  "traffic": 1000,
  "image": "CentOS 7 64-bit",
  "renewPrice": 49,
  "paymentCycle": 1,
  "priceHour": null,
  "price": 49,
  "priceQuarter": 147,
  "priceHalfYear": 294,
  "priceYear": 588,
  "startTime": "2022-09-12 20:53:44",
  "endTime": "2022-11-12 20:53:44",
  "status": 2,
  "note": null,
  "noteUser": null,
  "isAutoRenew": 0,
  "region_id": 18,
}
```

## Response Parameter Description

| Parameter | Type | Description |
|--------|--------|--------|
| id | int | Cloud server ID (instance ID) |
| ip | string | IP address |
| root | string | Username |
| password | string | root password (only returned by the info endpoint; not returned by the list endpoint) |
| cpu | int | vCPU count |
| ram | int | Memory (MB) |
| disk | int | System disk (GB) |
| diskData | int | Data disk (GB). 0 means no data disk |
| diskMedia | string | Disk media type. Observed values: SSD, NORMAL |
| bandwidth | int/null | Bandwidth (Mbps). Often null in practice |
| traffic | int | Monthly traffic quota (GB) |
| image | string | Image name. See [Get Order Images](get-order-images.md) |
| renewPrice | number | Renewal price, in CNY |
| paymentCycle | int | Payment cycle. 1=Monthly, 2=Quarterly, 3=Semi-annual, 4=Annual, 5=Hourly |
| priceHour | number/null | Hourly price, in CNY. null means hourly billing is not supported |
| price | number | Monthly price, in CNY |
| priceQuarter | number | Quarterly price, in CNY |
| priceHalfYear | number | Semi-annual price, in CNY |
| priceYear | number | Annual price, in CNY |
| startTime | string | Provisioning time |
| endTime | string | Expiration time |
| status | int | Instance status. 1=Provisioning, 2=Running, 3=Stopped, 4=Disabled, 5=Preparing. See observed enum values below |
| note | object | Admin note |
| noteUser | object | User note |
| isAutoRenew | int | Auto-renew. 0=Disabled, 1=Enabled |
| region_id | int | Region ID. See observed enum values in [List Regions](../01-regions/list-regions.md) |

## Notes

Status codes: 1 Provisioning, 2 Running, 3 Stopped, 4 Disabled, 5 Preparing

## Observed Response Example

```json
{
  "id": 280722,
  "ip": "31.210.52.36",
  "root": "root",
  "cpu": 1,
  "ram": 1024,
  "disk": 20,
  "diskData": 0,
  "diskMedia": "SSD",
  "traffic": 1000,
  "image": "Ubuntu 20.04",
  "status": 2,
  "startTime": "2026-07-03 10:10:14",
  "endTime": "2026-08-03 10:10:14",
  "isAutoRenew": 0,
  "noteUser": null,
  "region_id": 506
}
```

Note: The observed response reflects the current instance state. Some fields (e.g. bandwidth, renewPrice, price* series) may be omitted.

**Cloud server detail fields (observed):**

| Field | Type | Description | Example |
|------|------|------|------|
| id | int | Instance ID | 280722 |
| ip | str | IP address | 31.210.52.36 |
| root | str | Username | root |
| cpu | int | vCPU count | 1 |
| ram | int | Memory (MB) | 1024 |
| disk | int | System disk (GB) | 20 |
| diskData | int | Data disk (GB) | 0 |
| diskMedia | str | Disk media type | SSD |
| traffic | int | Traffic (GB/month) | 1000 |
| image | str | Image name | Ubuntu 20.04 |
| status | int | Status code | 2 |
| startTime | str | Provisioning time | 2026-07-03 10:10:14 |
| endTime | str | Expiration time | 2026-08-03 10:10:14 |
| isAutoRenew | int | Auto-renew (0=No, 1=Yes) | 0 |
| noteUser | str\|null | User note | null |
| region_id | int | Region ID. See observed enum values in [List Regions](../01-regions/list-regions.md) | 506 |
