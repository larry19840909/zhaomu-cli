# List Regions

## Brief Description

Get all available regions.

## Request URL

`https://api.zhaomu.com/region`

## Request Method

GET

## Header

| Field | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| Authorization | Bearer <apikey> | Yes | string | API Key |

## Success Response Example

**Note:** `continent`, `country`, `area`, `province`, `city` values are returned in Chinese. English fields (`continentEn`, `countryEn`, etc.) are typically empty strings.

```json
[{
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
}, {
  "id": 8,
  "continent": "北美洲",
  "continentEn": "",
  "country": "美国",
  "countryEn": "",
  "area": "美东",
  "areaEn": "",
  "province": "纽约州",
  "provinceEn": "",
  "city": "纽约",
  "cityEn": "",
  "zone": "V"
}]
```

## Response Parameter Description

| Parameter | Type | Description |
|--------|--------|--------|
| id | int | Region ID. Used for product queries |
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
| zone | string | Zone code. See Zone Enum below |

## Zone Enum (from real API)

Zone values are composite strings combining ISP + line type:

| Zone Pattern | Description |
|-------------|-------------|
| `电信C2` | China Telecom C2 line |
| `电信A` | China Telecom A line |
| `移动M` | China Mobile M line |
| `多线W` | Multi-line W |
| `CN2` | China Telecom CN2 (premium) |
| V | V-line (single letter for overseas) |
| R | R-line |
| X | X-line |
| AT | AT-line |
| Z | Z-line |
| N | N-line |
| PL | PL-line |
| S | S-line |
| O | O-line |
| i | i-line |
| L | L-line |
| SU | SU-line |
| LH | LH-line |
| PW | PW-line |
| T / T2 | Unicom T-line |

Chinese zones use composite names (e.g. `电信C2`). Overseas zones use single letters (e.g. `V`).

## Continent Enum

| API Value | English |
|-----------|---------|
| `亚洲` | Asia |
| `欧洲` | Europe |
| `北美洲` | North America |
| `南美洲` | South America |
| `非洲` | Africa |
| `大洋洲` | Oceania |

## Country Enum (Partial)

| API Value | English |
|-----------|---------|
| `中国` | China |
| `日本` | Japan |
| `新加坡` | Singapore |
| `美国` | United States |
| `英国` | United Kingdom |
| `德国` | Germany |
| `韩国` | South Korea |
| `加拿大` | Canada |
| `澳大利亚` | Australia |
| `俄罗斯` | Russia |
| `法国` | France |
| `荷兰` | Netherlands |
| `印度` | India |
| `巴西` | Brazil |
| `越南` | Vietnam |
| `泰国` | Thailand |
| `台湾` | Taiwan |
| `香港` | Hong Kong |

## Region Model — All Fields

| Field | Type | Description | Example |
|------|------|------|------|
| id | int | Region ID | `780` |
| city | str | City (Chinese) | `南昌` |
| cityEn | str | City (English) | `""` |
| continent | str | Continent (Chinese) | `亚洲` |
| continentEn | str | Continent (English) | `""` |
| country | str | Country (Chinese) | `中国` |
| countryEn | str | Country (English) | `""` |
| area | str | Area (Chinese) | `华东` |
| areaEn | str | Area (English) | `""` |
| province | str | Province (Chinese) | `江西` |
| provinceEn | str | Province (English) | `""` |
| zone | str | Zone code | `电信C2` |
