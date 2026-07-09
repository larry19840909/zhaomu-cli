# Set Auto-Renew

## Description

Enable or disable auto-renew for a cloud server

## Request URL

`https://api.zhaomu.com/cloud/auto-renew/:id`

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
| enable | 1 | Yes | int | 1=Enable, 0=Disable |

## Success Response

```json
{
  "success": true,
  "message": "自动续费启用成功"
}
```

## Response Parameters

| Parameter | Type | Description |
|--------|--------|--------|
| success | boolean | Success/Failure |
| message | string | Response message |

## Notes

None
