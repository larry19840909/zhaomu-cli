# Get Cloud Server Console

## Description

Get the noVNC console information for a cloud server

## Request URL

`https://api.zhaomu.com/cloud/novnc/:id`

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
{
  "success": true,
  "message": "http://www.mysuperdns.com/novnc/xxx"
}
```

## Response Parameters

| Parameter | Type | Description |
|--------|--------|--------|
| success | boolean | Success/Failure |
| message | string | Console URL |

## Notes

None
