# Order Cloud Server

## Brief Description

Order a cloud server. After execution, use the Get Cloud Server Info endpoint to check provisioning status.

## Request URL

`https://api.zhaomu.com/cloud/order`

## Method

POST

## Header

| Field | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| Authorization | Bearer <apikey> | Yes | string | API key |

## Request Body Parameters

| Parameter | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| productId | 91 | Yes | int | Product ID. See [List Cloud Server Products](../02-products/list-products.md) |
| disk | 40 | Yes | int | System disk size, in GB |
| diskData | 0 | Yes | int | Data disk size (GB). 0 means no data disk |
| bandwidth | 0 | Yes | int | Bandwidth. Set to 0 for unlimited |
| imageId | 5 | Yes | int | Image ID. See the observed image list in [Get Order Images](get-order-images.md) |
| paymentCycle | 1 | Yes | int | Payment cycle. 1=Monthly, 2=Quarterly, 3=Semi-annual, 4=Annual, 5=Hourly |

## Success Response Example

```json
{
  "success": true,
  "message": "Cloud server ordered: Toronto, Canada Zone V\n1 vCPU, 1GB RAM, 1 month",
  "info": {
    "id": 21299,
    "renewPrice": 49,
    "paymentCycle": "1",
    "startTime": "2022-09-12T12:53:44.630419Z",
    "endTime": "2022-10-12T12:53:44.630419Z",
    "region_id": 18,
    "ip": "Pending assignment",
    "root": "root",
    "password": "",
    "cpu": 1,
    "ram": 1024,
    "disk": 25,
    "diskData": 0,
    "bandwidth": null,
    "diskMedia": "SSD",
    "traffic": 1000,
    "image": "CentOS 7 64-bit",
    "imageIdentity": "167",
    "price": 49,
    "priceQuarter": 147,
    "priceHalfYear": 294,
    "priceYear": 588,
    "status": 1,
  }
}
```

## Response Parameter Description

| Parameter | Type | Description |
|--------|--------|--------|
| success | boolean | Success / Failure |
| message | string | Response message |
| id | int | Cloud server ID |

## Notes

Payment cycles: 1=Monthly, 2=Quarterly, 3=Semi-annual, 4=Annual, 5=Hourly
