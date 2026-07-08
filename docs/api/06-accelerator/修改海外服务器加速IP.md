# 修改海外服务器加速IP

## 简要描述

修改某个海外服务器加速的服务器IP和服务器靠近区域

## 请求URL

`https://api.zhaomu.com/accelerator/modify/:id`

## 请求方式

POST

## 路径变量

| 变量名 | 示例值 | 必选 | 类型 | 说明 |
|--------|--------|--------|--------|--------|
| id | 1 | 是 | string | 无 |

## Header

| 字段名 | 示例值 | 必选 | 类型 | 说明 |
|--------|--------|--------|--------|--------|
| Authorization | Bearer <apikey> | 是 | string | API密钥 |

## 请求Body参数

| 参数名 | 示例值 | 必选 | 类型 | 说明 |
|--------|--------|--------|--------|--------|
| ip |  | 是 | string | 服务器IP |
| area |  | 是 | string | 服务器靠近区域 |

## 成功返回示例

```json
复制{
  "success": true,
  "message": "海外服务器加速服务器IP修改成功"
}
```

## 成功返回示例的参数说明

| 参数名 | 类型 | 说明 |
|--------|--------|--------|
| id | int | 海外服务器加速编号 |
| type | string | 类型 |
| domain | int | 加速域名 |
| region | string | 入口区域 |
| ip | string | 服务器IP |
| port | string | 应用端口 |
| area | string | 服务器靠近区域 |
| startTime | string | 开通时间 |
| endTime | string | 到期时间 |
| renewPrice | string | 续费价格 |
| paymentCycle | string | 付款周期 |

## 备注

服务器靠近区域香港、新加坡、东京、洛杉矶、华盛顿、法兰克福、拉各斯
