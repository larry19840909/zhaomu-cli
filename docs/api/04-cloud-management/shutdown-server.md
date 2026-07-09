# Shutdown Cloud Server

## Description

Shutdown a cloud server

## Request URL

`https://api.zhaomu.com/cloud/shutdown/:id`

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

## Success Response

```json
{
  "success": true,
  "message": "关机命令发送成功，大约需要2分钟时间"
}
```

## Response Parameters

| Parameter | Type | Description |
|--------|--------|--------|
| success | boolean | Success/Failure |
| message | string | Response message |

## Notes

None
