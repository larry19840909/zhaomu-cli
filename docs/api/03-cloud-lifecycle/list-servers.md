# List Cloud Servers

## Brief Description

Get the full list of cloud servers for the user

## Request URL

`https://api.zhaomu.com/cloud`

## Method

GET

## Header

| Field | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| Authorization | Bearer <apikey> | Yes | string | API key |

## Success Response Example

```json
复制[{
  "id": 21299,
  "ip": "155.138.139.237",
  "root": "root",
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
},
{
  "id": 21299,
  "ip": "155.138.139.237",
  "root": "root",
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
}]
```

## Response Parameter Description

| Parameter | Type | Description |
|--------|--------|--------|
| id | int | Cloud server ID (instance ID). Used for info/rebuild/renew/destroy operations |
| ip | string | IP address |
| root | string | Username |
| password | string | root password (usually not returned by the list endpoint; only available via info endpoint) |
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

## Observed Enum Values

**Instance status (status) enum:**

| Value | statusName | Description |
|----|------------|------|
| 1 | Provisioning | Provisioning |
| 2 | Running | Running |
| 3 | Stopped | Stopped |
| 4 | Disabled | Disabled |
| 5 | Preparing | Preparing |

**Cloud server list item fields (observed):**

| Field | Type | Description | Example |
|------|------|------|------|
| id | int | Instance ID | 280722 |
| ip | str | IP address | 31.210.52.36 |
| cpu | int | vCPU count | 1 |
| ram | int | Memory (MB) | 1024 |
| disk | int | System disk (GB) | 20 |
| image | str | Image name | "" |
| status | int | Status code | 2 |
| statusName | str | Status name | Running |
| startTime | str | Provisioning time | 2026-07-03 10:10:14 |
| endTime | str | Expiration time | 2026-08-03 10:10:14 |
