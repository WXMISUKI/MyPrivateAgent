请根据用户输入的 `query_url` 和 `user_input`，判断用户意图。
如果 `query_url` 指向特定智能体或服务，请返回对应的路由指令。
如果 `user_input` 包含自然语言问题，请调用大模型生成一个合适的回复。
确保输出符合 `outputs` 定义的 JSON 结构。
