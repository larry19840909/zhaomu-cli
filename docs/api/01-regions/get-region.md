# Get Region Info

## Brief Description

Get information for a specific region.

## Request URL

`https://api.zhaomu.com/region/:id`

## Request Method

GET

## Path Parameters

| Parameter | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| id | 780 | Yes | int | Region ID. See [List Regions](list-regions.md) |

## Header

| Field | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| Authorization | Bearer <apikey> | Yes | string | API Key |

## Success Response Example

**Note:** `continent`, `country`, `area`, `province`, `city` values are Chinese. English fields are usually empty.

```json
{
  "id": 780,
  "continent": "亚洲",
  "continentEn": "",
  "country": "中国",
  "countryEn": "",
  "area": "华东",
  "areaEn": "",
  "province": "江西",
  "provinceEn": "",
  "city": "南昌",
  "cityEn": "",
  "zone": "电信C2"
}
```

## Response Parameter Description

| Parameter | Type | Description |
|--------|--------|--------|
| id | int | Region ID |
| continent | string | Continent (Chinese) |
| continentEn | string | Continent (English). Usually empty |
| country | string | Country (Chinese) |
| countryEn | string | Country (English). Usually empty |
| area | string | Area (Chinese) |
| areaEn | string | Area (English). Usually empty |
| province | string | Province (Chinese) |
| provinceEn | string | Province (English). Usually empty |
| city | string | City (Chinese) |
| cityEn | string | City (English). Usually empty |
| zone | string | Zone code. See zone enum in [List Regions](list-regions.md) |

## Notes

Enum values for continent/country/zone are documented in [List Regions](list-regions.md).
