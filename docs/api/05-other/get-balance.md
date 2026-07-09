# Get Account Balance

## Brief Description

Get the user's account balance.

## Request URL

`https://api.zhaomu.com/other/balance`

## Request Method

GET

## Header

| Field | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| Authorization | Bearer <apikey> | Yes | string | API key |

## Successful Response Example

```json
{
  "balance": 1000
}
```

## Response Parameter Description

| Parameter | Type | Description |
|--------|--------|--------|
| balance | number | User balance |

## Notes

None

## Actual Response Example

```json
{
  "balance": 0.8
}
```

## Actual Field Description

| Field | Type | Description |
|------|------|------|
| balance | float | Account balance (unit: CNY) |
