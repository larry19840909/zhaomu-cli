# Get Rebuild Images

## Description

Get the list of available images for rebuilding a cloud server

## Request URL

`https://api.zhaomu.com/image/cloud/:id`

## Method

GET

## Path Parameters

| Parameter | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| id |  | Yes | int | Cloud server ID. See [List Cloud Servers](../03-cloud-lifecycle/list-servers.md) for lookup |

## Header

| Field | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| Authorization | Bearer <apikey> | Yes | string | API key |

## Success Response

```json
[{
  "id": 5,
  "name": "CentOS 7 64位",
  "type": "CentOS"
},{
  "id": 8,
  "name": "Ubuntu 18.04 64位",
  "type": "Ubuntu"
}]
```

## Response Parameters

| Parameter | Type | Description |
|--------|--------|--------|
| id | int | Image ID. Used to specify imageId when rebuilding |
| name | string | Image name |
| type | string | Image type. Tested values: AlmaLinux, Debian, Ubuntu |

## Notes

None

## Tested Image List

**Rebuild image types (tested):**

| Type | Example Images |
|------|---------|
| AlmaLinux | AlmaLinux 9 (ID:2809), AlmaLinux 8 (ID:2808) |
| Debian | Debian 13 (ID:4423), Debian 12 (ID:2812), Debian 11 (ID:1719) |
| Ubuntu | Ubuntu 24.04 (ID:3349), Ubuntu 22.04 (ID:2713), Ubuntu 20.04 (ID:842) |
