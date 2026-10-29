# 模型服务商选择

2026-10-29 用户明确选择先使用 DeepSeek，因此不再自行替用户比较并选择其他服务商。

- 官方地址：https://api.deepseek.com；可接受官方 /v1 前缀。
- 默认模型 deepseek-flash，来自本日核查的[官方入门](https://api-docs.deepseek.com/)。旧的 deepseek-chat 不作为本次默认。
- 使用 POST /chat/completions、JSON object 输出和非流式回复，参见[接口文档](https://api-docs.deepseek.com/api/create-chat-completion/)与[JSON 模式](https://api-docs.deepseek.com/guides/json_mode/)。
- 请求适配已通过本地模拟传输测试；当前没有获得实际密钥调用的证据。
- 价格、账号可用模型、保留期限、训练使用条款、处理地区和真实用户用途适用性仍需用户按正式协议确认。未填当前价格或编造预算。
- 只允许虚构材料。需要月度预算封顶时先在供应商账号设置，并结合程序统计核对账单；未代用户购买或充值。
