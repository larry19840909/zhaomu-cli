# CLI Best Practices

End-to-end walkthrough: setup → select → order → destroy.

## 1. Configuration

You need an API key. Pick one method:

```bash
# Option A: config file
echo '{"apikey": "your_zhaomu_api_key"}' > config.json
zhaomu -c config.json cloud list

# Option B: environment variable (Windows PowerShell)
$env:ZHAOMU_APIKEY = "your_zhaomu_api_key"
```

## 2. Browse Regions

```bash
zhaomu region list
```

Scan the `City`, `Country`, and `Zone` columns. Note your target city name (e.g. `纽约`).

## 3. Compare Zones Within a City

A city can have multiple zones (network routes) with very different features. Compare before browsing products:

```bash
zhaomu product compare -r 纽约
```

The per-zone table shows key differentiators:

| What to check | Look for |
|---------------|----------|
| Refund on destroy | 销毁退款 (是/否) |
| IP type | IP属性 (原生IP / 机房IP / 住宅IP) |
| Windows support | Windows系统 (是/否) |
| Port restrictions | 端口限制 (is port 25 blocked?) |

Pick the zones that meet your needs (e.g. V and R).

## 4. Browse Products

```bash
zhaomu product list -r 纽约 --zone V,R
```

Sorted by **zone → price ascending**. Pay attention to the `Tags` and `Zone` columns.

## 5. Check Available Images

```bash
zhaomu cloud images -r 纽约 --zone R -p 10781
```

Note the image ID for your target OS (e.g. Ubuntu 20.04).

## 6. Check Balance

```bash
zhaomu balance
```

Make sure your balance covers the product's monthly price. Use `--json` for scripts:

```bash
zhaomu --json balance
# → {"balance": 100.5}
```

## 7. Order

```bash
zhaomu cloud order -r 纽约 --zone R -p 10781 \
    --image 4074 --disk 40 --period 1
```

| Option | Meaning | Values |
|--------|---------|--------|
| `-r` | City name or region ID | `纽约`, `780` |
| `--zone` | Zone code(s) | `V`, `R`, `V,R` |
| `-p` | Product ID or spec | `10781`, `1C-1G` |
| `--image` | Image ID | `4074` |
| `--disk` | System disk GB | `20`–`40` |
| `--period` | Billing cycle | `1`=Monthly, `2`=Quarterly, `3`=Semi-annual, `4`=Annual |

## 8. Check Status

```bash
zhaomu cloud info 281516
```

Watch the `Status` field: `Running` = ready, `Provisioning` = setting up.

```bash
# List all instances
zhaomu cloud list
```

## 9. Destroy

```bash
zhaomu cloud destroy 281516
```

> **Note**: Only zones with 销毁退款 (refund on destroy) return the balance. Verify with `product compare` first.

## Other Common Operations

```bash
# Reinstall OS
zhaomu cloud rebuild-images 281516          # list rebuild images
zhaomu cloud rebuild 281516 --image 842     # execute

# Power management
zhaomu cloud reboot 281516                  # reboot / start
zhaomu cloud shutdown 281516                # shutdown

# Reset password (interactive)
zhaomu cloud reset-password 281516

# Upgrade / downgrade
zhaomu cloud upgrade-price 281516 --disk 50 # quote
zhaomu cloud upgrade 281516 --disk 50       # apply

# VNC console
zhaomu cloud console 281516

# Renew
zhaomu cloud renew 281516 --period 4        # annual renewal

# Note / label
zhaomu cloud note 281516 "production-web"
```

## JSON Mode

All commands support `--json` (placed before the subcommand). Ideal for scripting:

```bash
zhaomu --json balance | jq '.balance'
zhaomu --json cloud list | jq '.[] | {id, ip, status}'
```
