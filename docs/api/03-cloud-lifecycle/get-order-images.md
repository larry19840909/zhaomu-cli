# Get Order Images

## Brief Description

Get the list of available images when ordering a cloud server

## Request URL

`https://api.zhaomu.com/image/product/:id`

## Method

GET

## Path Parameters

| Parameter | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| id |  | Yes | int | Cloud server product ID. See [List Cloud Server Products](../02-products/list-products.md) for specific specs |

## Header

| Field | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| Authorization | Bearer <apikey> | Yes | string | API key |

## Success Response Example

```json
复制[{
  "id": 5,
  "name": "CentOS 7 64-bit",
  "type": "CentOS"
},{
  "id": 8,
  "name": "Ubuntu 18.04 64-bit",
  "type": "Ubuntu"
}]
```

## Response Parameter Description

| Parameter | Type | Description |
|--------|--------|--------|
| id | int | Image ID. Used as the `imageId` parameter when ordering |
| name | string | Image name |
| type | string | Image type. Observed values: CentOS, Debian, Ubuntu, Windows, AlmaLinux |

## Notes

None

## Observed Image List

**Available image types:**

| Type | Example Images |
|------|---------|
| CentOS | CentOS Stream 9, CentOS Stream 8, CentOS Linux 7.9 |
| Debian | Debian 12.8, Debian 11.1 |
| Ubuntu | Ubuntu Server 24.04, Ubuntu Server 22.04, Ubuntu Server 20.04 |
| Windows | Windows Server 2022, Windows Server 2019, Windows Server 2016 |
| AlmaLinux | AlmaLinux 9, AlmaLinux 8 |

Note: Image availability varies by region and product. Windows images are only supported in select regions.
