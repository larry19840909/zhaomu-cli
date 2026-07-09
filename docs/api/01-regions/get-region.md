# Get Region Info

## Brief Description

Get information for a specific region

## Request URL

`https://api.zhaomu.com/region/:id`

## Request Method

GET

## Path Parameters

| Parameter | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| id | 3 | Yes | int | Region ID. See observed enum values in [List Regions](list-regions.md) |

## Header

| Field | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| Authorization | Bearer <apikey> | Yes | string | API Key |

## Success Response Example

```json
复制{
  "id": 3,
  "continent": "北美洲",
  "continentEn": "north-america",
  "country": "美国",
  "countryEn": "us",
  "area": "美西",
  "areaEn": "us-west",
  "province": "加州",
  "provinceEn": "california",
  "city": "洛杉矶",
  "cityEn": "los-angeles",
  "zone": "V"
}
```

## Response Parameter Description

| Parameter | Type | Description |
|--------|--------|--------|
| id | int | Region ID. See observed enum values in [List Regions](list-regions.md) |
| continent | string | Continent |
| continentEn | string | Continent (English) |
| country | string | Country |
| countryEn | string | Country (English) |
| area | string | Area |
| areaEn | string | Area (English) |
| province | string | Province |
| provinceEn | string | Province (English) |
| city | string | City |
| cityEn | string | City (English) |
| zone | string | Zone name. See Zone enum values in [List Regions](list-regions.md) |

## Notes

None

## Observed Response Example

```json
{
  "id": 780,
  "city": "南昌",
  "cityEn": "",
  "continent": "亚洲",
  "continentEn": "",
  "country": "中国",
  "countryEn": "",
  "area": "华东",
  "areaEn": "",
  "province": "江西",
  "provinceEn": "",
  "zone": "电信C2"
}
```


Enum details: For Zone/Continent/Country/Area/Province enum values, see the observed enum values section in [List Regions](list-regions.md).
