# CLI 最佳实践

从零开始，完成配置→选型→订购→销毁的完整流程。

## 1. 初始化配置

首次使用需要 API Key，任选一种方式：

```bash
# 方式一：配置文件
echo '{"apikey": "your_zhaomu_api_key"}' > config.json
zhaomu -c config.json cloud list

# 方式二：环境变量（Windows PowerShell）
$env:ZHAOMU_APIKEY = "your_zhaomu_api_key"
```

## 2. 了解可用机房

```bash
zhaomu region list
```

输出所有可用区，关注 `City`、`Country`、`Zone` 列。记下目标城市的名称（如 `纽约`）。

## 3. 对比同城各可用区特性

同一城市可能有多个 zone（线路），功能差异很大。先对比再看产品：

```bash
zhaomu product compare -r 纽约
```

输出 per-zone 对照表，重点关注：

| 需关注 | 对应行 |
|--------|--------|
| 是否支持退款 | 销毁退款 |
| IP 类型 | IP属性（原生IP / 机房IP） |
| 操作系统 | Windows系统 |
| 端口限制 | 端口限制（是否禁用25端口） |

选出符合需求的 zone（如 V 和 R）。

## 4. 查看产品列表

```bash
zhaomu product list -r 纽约 --zone V,R
```

输出按 **zone → 月费升序** 排列。关注 `Tags` 列（原生IP、住宅IP 等）和 `Zone` 列。

## 5. 查看可选镜像

```bash
zhaomu cloud images -r 纽约 --zone R -p 10781
```

确认目标操作系统（如 Ubuntu 20.04）的镜像 ID。

## 6. 检查余额

```bash
zhaomu balance
```

确保余额 ≥ 目标产品月费。使用 `--json` 可精确获取数值：

```bash
zhaomu --json balance
# → {"balance": 100.5}
```

## 7. 订购

```bash
zhaomu cloud order -r 纽约 --zone R -p 10781 \
    --image 4074 --disk 40 --period 1
```

参数说明：

| 参数 | 含义 | 可选值 |
|------|------|--------|
| `-r` | 城市名或 region ID | `纽约`, `780` |
| `--zone` | zone 码 | `V`, `R`, `V,R` |
| `-p` | 产品 ID 或 spec | `10781`, `1C-1G` |
| `--image` | 镜像 ID | `4074` |
| `--disk` | 系统盘 GB | `20`~`40` |
| `--period` | 付款周期 | `1`=月付, `2`=季付, `3`=半年付, `4`=年付 |

## 8. 查看状态

```bash
zhaomu cloud info 281516
```

关注 `Status` 字段：`Running` 表示已就绪，`Provisioning` 表示开通中。

```bash
# 列出所有实例
zhaomu cloud list
```

## 9. 销毁

```bash
zhaomu cloud destroy 281516
```

> **注意**：仅支持退款的 zone 销毁后余额会退回。销毁前在 `product compare` 中确认「销毁退款」为"是"。

## 其他常用操作

```bash
# 重装系统
zhaomu cloud rebuild-images 281516          # 查看可重装镜像
zhaomu cloud rebuild 281516 --image 842     # 执行重装

# 开关机
zhaomu cloud reboot 281516                  # 重启/开机
zhaomu cloud shutdown 281516                # 关机

# 重置密码
zhaomu cloud reset-password 281516          # 交互式输入新密码

# 升降级
zhaomu cloud upgrade-price 281516 --disk 50 # 询价
zhaomu cloud upgrade 281516 --disk 50       # 执行

# VNC 控制台
zhaomu cloud console 281516

# 续费
zhaomu cloud renew 281516 --period 4        # 年付续费

# 备注
zhaomu cloud note 281516 "production-web"
```

## JSON 模式

所有命令支持 `--json`（放在子命令前面），适合脚本：

```bash
zhaomu --json balance | jq '.balance'
zhaomu --json cloud list | jq '.[] | {id, ip, status}'
```
