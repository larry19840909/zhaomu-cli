# Compare Feature Parameters

## Brief Description

Get feature parameter comparison for a region.

## Request URL

`https://api.zhaomu.com/compare/region/:id`

## Request Method

GET

## Path Variables

| Variable | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| id |  | Yes | string | Region ID. See [Get Region List](../01-regions/list-regions.md) for enumerated values |

## Header

| Field | Example | Required | Type | Description |
|--------|--------|--------|--------|--------|
| Authorization | Bearer <apikey> | Yes | string | API key |

## Success Response Example

```json
[
  {
    "target_id": "1",
    "name": "Instant Provisioning",
    "explain": "Supported"
  },
  {
    "target_id": "2",
    "name": "Online Reboot",
    "explain": "Supported"
  },
  {
    "target_id": "3",
    "name": "Online Shutdown",
    "explain": "Supported"
  }
]
```

## Success Response Parameter Description

| Parameter | Type | Description |
|--------|--------|--------|
| target_id | int | Feature parameter ID. See the [Observed Feature Enumeration](#observed-feature-enumeration) table below for the complete 25-item ID-to-name mapping |
| name | string | Feature parameter name |
| explain | string | Feature support status. Possible values: Supported / Unsupported / Submit Ticket / Within Validity Period / Displayed / Blocks Ports 80,443,25 / Provisioning Within 6 Hours / Shows Actual IP / Native IP |

## Notes

None

## Observed Feature Enumeration

**Product comparison features (25 items observed; target_id values are the feature IDs returned by the API):**

| target_id | Feature Name | Description |
|-----------|---------|------|
| 1 | Instant Provisioning | Provisioning within 6 hours |
| 2 | Online Reboot | Supported |
| 3 | Online Shutdown | Supported |
| 4 | OS Reinstall | Supported |
| 5 | Plan Upgrade | Supported |
| 6 | noVNC Console | Supported |
| 7 | Data Backup | Submit Ticket |
| 8 | Password Reset | Supported |
| 9 | ICP Filing Info | Submit Ticket |
| 10 | Open Ports | Unsupported |
| 12 | Test IP | Shows Actual IP |
| 13 | Windows System | Supported |
| 15 | Hardware Replacement | Within Validity Period |
| 16 | Snapshot Backup | Unsupported |
| 17 | Hourly Billing | Unsupported |
| 18 | Dedicated IP | Unsupported |
| 19 | Shared Bandwidth IP | Unsupported |
| 20 | Intra-VPC Networking | Unsupported |
| 21 | IPv6 | Unsupported |
| 22 | Auto Memory Scaling | Submit Ticket |
| 23 | Auto CPU Scaling | Unsupported |
| 24 | Bandwidth Upgrade | Unsupported |
| 25 | Traffic Statistics | Displayed |
| 26 | Port Restrictions | Blocks Ports 80/443/25 |
| 27 | IP Type | Native IP |

Possible values in the Description column: Supported / Unsupported / Submit Ticket / Within Validity Period / Displayed / Blocks Ports 80/443/25 / Provisioning Within 6 Hours / Shows Actual IP / Native IP
