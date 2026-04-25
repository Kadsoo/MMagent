# MMagent

MMagent 是一个可运行的 JSON Tool Calling Agent 演示项目。它面向简历和面试展示，重点体现如何构建 Agent Runtime、工具注册中心、Mock/真实 LLM 适配层，以及前端执行轨迹可视化。

## 目录结构

```text
MMagent/
  backend/
    app/
      agent/        # runtime 循环、memory、system prompt
      api/          # FastAPI 路由
      core/         # 配置和日志
      data/         # 本地知识库和待办数据
      llm/          # BaseLLMAdapter、MockLLMAdapter、OpenAI 兼容适配器
      schemas/      # Pydantic JSON tool calling 协议
      services/     # 真实工具服务：天气、网络查询、文档、todo
      tools/        # 工具注册中心和内置工具
      utils/        # 安全计算器求值器
    requirements.txt
  frontend/
    src/
      components/   # 聊天、trace、tools、JSON 展示组件
      hooks/
      services/
      types/
    package.json
  .env.example
  README.md
```

## 核心特性

- Agent Runtime：实现带最大步数限制的多步“推理-执行-观察”闭环。
- JSON Tool Calling Protocol：使用 Pydantic 定义 `tool_call`、`tool_result` 和 `final_answer`。
- Tool Registry：工具按名称、描述、输入 schema 和执行函数注册。
- LLM Adapter Layer：本地 `MockLLMAdapter` 无需 API key 即可运行；`OpenAICompatibleAdapter` 可接入真实 chat-completion 模型。
- 可观测性：每次模型输出、解析后的 JSON 调用、工具结果和最终回答都会作为 trace 数据返回，并在 React 前端中展示。
- 真实工具服务：天气、网络查询、时间、文档、todo 和计算器都通过 registry 调用真实 service。
- 可扩展性：service 层保持工具可替换，后续可加入游戏工具、浏览器工具或工作流自动化工具，而无需修改 runtime。

## JSON Tool Calling 协议

工具调用：

```json
{
  "type": "tool_call",
  "tool_name": "get_weather",
  "arguments": {
    "city": "Nanjing"
  },
  "thought": "Need weather info before answering"
}
```

工具结果：

```json
{
  "type": "tool_result",
  "tool_name": "get_weather",
  "status": "success",
  "result": {
    "city": "Nanjing",
    "temperature": "26C",
    "condition": "Sunny"
  }
}
```

最终回答：

```json
{
  "type": "final_answer",
  "answer": "The weather in Nanjing is Sunny and 26C."
}
```

## 内置工具

- `get_weather`：通过 Open-Meteo 或 OpenWeather 按城市获取真实当前天气。
- `get_time`：按城市或 IANA timezone 返回本地时间。
- `calculator`：安全计算 `+`、`-`、`*`、`/` 和括号表达式。
- `search_docs`：对 `backend/app/data/knowledge.md` 进行关键词搜索。
- `web_search`：通过 DuckDuckGo Instant Answer 加 HTML fallback 进行网络查询。
- `todo_add`：为当前用户添加待办事项，配置 MySQL 后写入数据库。
- `todo_list`：列出当前用户的待办事项。
- `todo_delete`：按 1-based index 删除当前用户的待办事项。
- `get_system_status`：查看运行时状态。

## 本地运行

Windows 一键启动：

```bat
start-local.bat
```

该脚本会自动创建/修复后端虚拟环境，按需安装后端和前端依赖，并打开两个终端窗口分别启动 FastAPI 后端和 Vite 前端。

后端：

```bash
cd MMagent/backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

前端：

```bash
cd MMagent/frontend
npm install
npm run dev
```

打开前端地址：`http://127.0.0.1:5173`。

## 环境变量

将项目根目录下的 `.env.example` 复制为 `.env`。默认使用 mock 模式，不需要任何 API key。

前端 Vite 环境变量不在项目根目录，而是在 `frontend/.env`。如果你要覆盖 API 地址，请将 `frontend/.env.example` 复制为 `frontend/.env` 后再修改。

如需使用真实模型：

```env
LLM_PROVIDER=openai
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4o-mini
```

如需启用基于 MySQL 的会话持久化：

```env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=mmagent
MYSQL_CHARSET=utf8mb4
```

天气默认使用 Open-Meteo，本地演示不需要 key：

```env
WEATHER_PROVIDER=open_meteo
WEATHER_API_BASE_URL=https://api.open-meteo.com
WEATHER_GEOCODING_BASE_URL=https://geocoding-api.open-meteo.com
WEATHER_LANGUAGE=en
```

也支持 OpenWeather：

```env
WEATHER_PROVIDER=openweather
WEATHER_API_KEY=your_weather_key
WEATHER_API_BASE_URL=https://api.openweathermap.org/data/2.5/weather
```

网络查询默认使用 DuckDuckGo：

```env
WEB_SEARCH_BASE_URL=https://api.duckduckgo.com
```

## API 示例

健康检查：

```bash
curl http://127.0.0.1:8000/api/health
```

聊天接口：

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"demo-user\",\"message\":\"What's the weather and current time in Nanjing?\"}"
```

响应结构：

```json
{
  "session_id": "...",
  "final_answer": "...",
  "trace": [
    {
      "step": 1,
      "model_output": "{\"type\":\"tool_call\",...}",
      "tool_call": {
        "type": "tool_call",
        "tool_name": "get_weather",
        "arguments": {
          "city": "Nanjing"
        }
      },
      "tool_result": {
        "type": "tool_result",
        "tool_name": "get_weather",
        "status": "success"
      }
    }
  ],
  "messages": []
}
```

## 截图占位

运行应用后可补充截图：

- `docs/screenshots/chat-trace.png`
- `docs/screenshots/tools-panel.png`

## 简历描述参考

- 从零构建 JSON Tool Calling Agent Runtime，实现多步“推理-执行-观察”闭环。
- 基于 Pydantic 设计结构化协议，覆盖 tool call、tool result 和 final answer。
- 实现可插拔 Tool Registry，支持基于 schema 的工具发现与执行。
- 增加本地 Mock LLM adapter 便于演示，并预留 OpenAI 兼容 adapter 用于生产模型接入。
- 使用 React + TypeScript 构建 trace dashboard，可检查模型输出、JSON tool call、工具执行结果和最终回答。

## 后续扩展方向

- 通过 Server-Sent Events 或 WebSocket 增加流式响应。
- 使用 SQLite 或 Postgres 持久化会话。
- 增加认证，以及按用户隔离的 todo/document 数据。
- 增加多模态文件上传和图像理解工具。
- 可选扩展游戏 Agent 工具：背包查询、敌人位置查询、移动、攻击、拾取和规划策略。
- 为工具参数校验、runtime 循环和 adapter 解析增加测试套件。
