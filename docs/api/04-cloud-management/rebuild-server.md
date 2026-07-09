# Rebuild Cloud Server

## Description

Rebuild (reinstall OS) a cloud server

## Request URL

`https://api.zhaomu.com/cloud/rebuild/:id`

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
| imageId | 13 | Yes | int | Image ID. See [Get Rebuild Images](get-rebuild-images.md) or [Get Order Images](../03-cloud-lifecycle/get-order-images.md) for tested image lists |

## Success Response

```json
{
  "success": true,
  "message": "重装系统命令发送成功，大约需要5分钟时间，Windows操作系统需要10分钟左右"
}
```

## Response Parameters

| Parameter | Type | Description |
|--------|--------|--------|
| success | boolean | Success/Failure |
| message | string | Response message |

## Notes

None
