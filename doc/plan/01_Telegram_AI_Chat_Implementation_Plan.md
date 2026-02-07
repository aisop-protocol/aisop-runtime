# 01. Telegram AI 聊天程序实施方案与架构设计

本文档详细描述了构建一个基于 Python 的 Telegram 聊天机器人，集成 AI 大模型，并最终作为 AISOP 协议执行环境的实施计划。

## 1. 项目目标

构建一个轻量级、可扩展的 Telegram Bot，具备以下核心能力：
1.  **基础连接**：能够通过 Telegram API 收发消息。
2.  **AI 集成**：能够将用户消息转发给 LLM（如 Gemini/OpenAI），并将回复返回给用户。
3.  **AISOP 准备**：架构设计需预留 AISOP 协议执行层，未来让 AI 通过 AISOP 协议控制 Bot 的行为。

## 2. 技术栈选择

-   **编程语言**: Python 3.10+
-   **Telegram 框架**: `python-telegram-bot` (异步、功能丰富)
-   **AI SDK**: `google-generativeai` (Gemini) 或 `openai`
-   **配置管理**: `python-dotenv`
-   **运行环境**: 本地开发 / 简单的云服务器

## 3. 系统架构

```mermaid
graph TD
    User[用户 (Telegram App)] <-->|消息| TG_Server[Telegram 服务器]
    TG_Server <-->|Webhook/Polling| Bot[Telegram Bot (Python)]
    
    subgraph "AISOP Test System"
        Bot -->|获取更新| Handler[消息处理器]
        Handler -->|调用| AI_Service[AI 服务接口]
        AI_Service <-->|API| LLM[大语言模型 (Gemini/GPT)]
        
        Handler -.->|未来集成| AISOP_Runtime[AISOP 执行引擎]
        AISOP_Runtime -.->|控制| Bot
    end
```

## 4. 目录结构规划

```
D:\vscode\openmind\aisoptest\
├── doc\
│   └── plan\
│       └── 01_Telegram_AI_Architecture.md  (本文档)
├── src\
│   ├── bot.py              # Telegram Bot 初始化与运行逻辑
│   ├── config.py           # 配置加载 (.env)
│   └── llm_client.py       # AI 模型调用封装
├── .env                    # 敏感配置 (Token, API Key)
├── main.py                 # 程序入口
└── requirements.txt        # 依赖列表
```

## 5. 实施步骤

### 阶段一：基础搭建与连通性验证 (Foundation)
- [ ] **1.1 环境初始化**
    - 创建项目目录结构
    - 创建虚拟环境并安装 `python-telegram-bot`, `python-dotenv`
- [ ] **1.2 申请资源**
    - 申请 Telegram Bot Token (通过 @BotFather)
    - 准备 AI API Key
- [ ] **1.3 编写 Hello World Bot**
    - 实现最简单的 `/start` 响应，验证 Bot 可运行。

### 阶段二：AI 能力集成 (Intelligence)
- [ ] **2.1 封装 LLM 客户端**
    - 编写 `llm_client.py`，实现 `chat(user_input) -> response` 函数。
    - 支持流式输出（可选）或完整响应。
- [ ] **2.2 连接 Bot 与 AI**
    - 修改消息处理器，将用户文本发送给 LLM 客户端。
    - 将 LLM 的回复发送回 Telegram 用户。
- [ ] **2.3 维护会话上下文 (简单版)**
    - 在内存中保存简单的历史对话列表，实现多轮对话体验。

### 阶段三：AISOP 运行时集成 (Evolution)
- [ ] **3.1 引入 AISOP SDK**
    - 将 `aisop` 库集成到项目中。
- [ ] **3.2 定义 Chat Protocol**
    - 编写一个 `.aisop.json` 协议，定义 "接收消息 -> 分析意图 -> 生成回复" 的流程。
- [ ] **3.3 替换硬编码逻辑**
    - 使用 AISOP 引擎来驱动消息处理流程，替代阶段二中的 Python 硬编码逻辑。

## 6. 关键代码示例预演

### `main.py` (入口)
```python
import asyncio
from src.bot import run_bot

if __name__ == "__main__":
    asyncio.run(run_bot())
```

### `src/llm_client.py` (AI 接口)
```python
# 伪代码
class AIClient:
    def __init__(self, api_key):
        self.model = ... # 初始化模型
        
    async def get_response(self, message: str) -> str:
        # 调用 LLM API
        return "AI 的回复"
```

## 7. 风险与对策
- **网络问题**: Telegram API 国内访问可能受限，需配置代理。
- **Token 限制**: LLM 上下文长度限制，需实现简单的滑动窗口机制。
