# List Regions



## Brief Description



Get all available regions



## Request URL



`https://api.zhaomu.com/region`



## Request Method



GET



## Header



| Field | Example | Required | Type | Description |

|--------|--------|--------|--------|--------|

| Authorization | Bearer <apikey> | Yes | string | API Key |



## Success Response Example



```json

复制[{

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

},{

  "id": 5,

  "continent": "亚洲",

  "continentEn": "asia",

  "country": "日本",

  "countryEn": "jp",

  "area": "",

  "areaEn": "",

  "province": "",

  "provinceEn": "",

  "city": "东京",

  "cityEn": "tokyo",

  "zone": "V"

}]

```



## Response Parameter Description



| Parameter | Type | Description |

|--------|--------|--------|

| id | int | Region ID. Used for product queries etc. |

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

| zone | string | Zone name. See Zone enum values below |



## Notes



None



## Observed Enum Values



### Continent Enum



| Value | Description |

|----|------|

| 亚洲 | Asia |

| 欧洲 | Europe |

| 北美洲 | North America |

| 南美洲 | South America |

| 非洲 | Africa |

| 大洋洲 | Oceania |



### Zone Enum (Partial)



| Zone | Description |

|------|------|

| C2 | Telecom C2 |

| M | Mobile |

| A | Telecom A |

| U | U-line |

| T/T2 | Unicom T |

| CN2 | Telecom CN2 |

| V | V-line |

| O | O-line |

| S | S-line |

| PL/PW | PL/PW |

| SU | SU |

| i | i-line |

| N | N-line |

| L | L-line |

| LH | LH |

| Z | Z-line |



### Country Enum (Partial)



| Value | Description |

|----|------|

| 中国 | China |

| 日本 | Japan |

| 新加坡 | Singapore |

| 美国 | United States |

| 英国 | United Kingdom |

| 德国 | Germany |

| 韩国 | South Korea |

| 加拿大 | Canada |

| 澳大利亚 | Australia |

| 俄罗斯 | Russia |

| 法国 | France |

| 荷兰 | Netherlands |

| 印度 | India |

| 巴西 | Brazil |

| 越南 | Vietnam |

| 泰国 | Thailand |

| 台湾 | Taiwan |

| 香港 | Hong Kong |



### Region Model — All Fields



| Field | Type | Description | Example |

|------|------|------|------|

| id | int | Region ID | 780 |

| city | str | City (Chinese) | 南昌 |

| cityEn | str | City (English) | "" |

| continent | str | Continent (Chinese) | 亚洲 |

| continentEn | str | Continent (English) | "" |

| country | str | Country (Chinese) | 中国 |

| countryEn | str | Country (English) | "" |

| area | str | Area | 华东 |

| areaEn | str | Area (English) | "" |

| province | str | Province | 江西 |

| provinceEn | str | Province (English) | "" |

| zone | str | Zone | 电信C2 |



