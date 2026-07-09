# Set User Note

## Description

Set a user note for a cloud server

## Request URL

`https://api.zhaomu.com/cloud/note/:id`

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
| note | 测试云服务器 | Yes | string | User note |

## Success Response

```json
{
  "success": true,
  "message": "用户备注修改成功"
}
```

## Response Parameters

| Parameter | Type | Description |
|--------|--------|--------|
| success | boolean | Success/Failure |
| message | string | Response message |

## Notes

None
