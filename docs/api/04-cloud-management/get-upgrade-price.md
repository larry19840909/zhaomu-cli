# Get Upgrade Price

## Description

Get the price for upgrading a cloud server configuration

## Request URL

`https://api.zhaomu.com/cloud/upgrade-price/:id`

## Method

POST

## Path Parameters

| Parameter | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| id | 21299 | Yes | int | Cloud server ID. See [List Cloud Servers](../03-cloud-lifecycle/list-servers.md) for lookup |

## Header

| Field | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| Authorization | Bearer <apikey> | Yes | string | API key |

## Request Body

| Parameter | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| productId | 1 | No | int | Target product ID. See [List Cloud Server Products](../02-products/list-products.md) |
| disk | 40 | No | int | Target system disk size (GB) |
| diskData | 20 | No | int | Target data disk size (GB) |
| bandwidth | 5 | No | int | Target bandwidth (Mbps) |

## Success Response

```json
{
  "success": true,
  "message": 989
}
```

## Response Parameters

| Parameter | Type | Description |
|--------|--------|--------|
| success | boolean | Success/Failure |
| message | string | Response message |

## Notes

None
