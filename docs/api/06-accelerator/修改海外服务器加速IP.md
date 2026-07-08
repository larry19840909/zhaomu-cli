# 修改海外服务器加速IP

## 简要描�?

修改某个海外服务器加速的服务器IP和服务器靠近区域

## 请求URL

`https://api.zhaomu.net/accelerator/modify/:id`

## 请求方式

POST

## 路径变量

| 变量�?| 示例�?| 必�?| 类型 | 说明 |
|--------|--------|--------|--------|--------|
| id | 1 | �?| string | �?|

## Header

| 字段�?| 示例�?| 必�?| 类型 | 说明 |
|--------|--------|--------|--------|--------|
| Authorization | Bearer <apikey> | �?| string | API密钥 |

## 请求Body参数

| 参数�?| 示例�?| 必�?| 类型 | 说明 |
|--------|--------|--------|--------|--------|
| ip |  | �?| string | 服务器IP |
| area |  | �?| string | 服务器靠近区�?|

## 成功返回示例

```json
{
  "success": true,
  "message": "海外服务器加速服务器IP修改成功"
}
```

## 成功返回示例的参数说�?

| 参数�?| 类型 | 说明 |
|--------|--------|--------|
| id | int | 海外服务器加速编�?|
| type | string | 类型 |
| domain | int | 加速域�?|
| region | string | 入口区域 |
| ip | string | 服务器IP |
| port | string | 应用端口 |
| area | string | 服务器靠近区�?|
| startTime | string | 开通时�?|
| endTime | string | 到期时间 |
| renewPrice | string | 续费价格 |
| paymentCycle | string | 付款周期 |

## 备注

服务器靠近区�?
香港、新加坡、东京、洛杉矶、华盛顿、法兰克福、拉各斯
