# Renew Cloud Server

## Description

Renew a cloud server

## Request URL

`https://api.zhaomu.com/cloud/renew/:id`

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
| paymentCycle | 1 | Yes | int | Payment cycle. 1=Monthly, 2=Quarterly, 3=Semi-annual, 4=Annual |

## Success Response

```json
{
  "success": true,
  "message": "续费云服务器：155.138.139.237，1个月"
}
```

## Response Parameters

| Parameter | Type | Description |
|--------|--------|--------|
| success | boolean | Success/Failure |
| message | string | Response message |

## Notes

None
