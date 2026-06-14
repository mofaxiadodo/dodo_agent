"""
Agent 核心循环
实现了完整的"思考→行动→观察→再思考"的 Agent 决策循环
简单来说：AI 先想想要不要用工具 → 用工具看结果 → 再决定下一步 → 直到给出最终答案
"""

import json                     # json 模块：处理 JSON 格式的数据
from openai import OpenAI       # OpenAI 库：用来调用大模型 API
from config import get_config, SYSTEM_PROMPT, MAX_TURNS, TEMPERATURE  # 从 config.py 导入配置
from tools import TOOL_DEFINITIONS, execute_tool  # 从 tools.py 导入工具定义和执行函数


class Agent:
    """
    LLM Agent - 通过工具调用循环完成用户任务
    
    可以理解为一个"智能助手对象"，它：
    1. 记住你和它的对话历史（messages）
    2. 能调用各种工具（读文件、写文件、执行命令等）
    3. 反复思考直到完成任务
    """

    def __init__(self):
        """
        构造方法（相当于 C 语言的初始化函数）
        当创建 Agent 对象时自动调用：agent = Agent()
        """
        # 读取配置文件，获取 API 地址、密钥、模型名称等信息
        cfg = get_config()

        # 创建一个 OpenAI 客户端，用来跟大模型 API 通信
        self.client = OpenAI(
            base_url=cfg["base_url"],   # API 地址（不同厂商地址不同）
            api_key=cfg["api_key"],     # API 密钥（相当于密码）
        )

        # 保存模型名称，比如 "deepseek-chat" 或 "gpt-4o"
        self.model = cfg["model"]

        # 消息列表：存储整个对话历史（包括用户说的、AI 说的、工具返回的）
        self.messages = []

    def reset(self):
        """重置对话上下文：清空所有消息，只保留系统提示词"""
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def _call_llm(self) -> dict:
        """
        调用大模型（LLM），返回 API 的响应消息
        
        注意：方法名前加下划线 _ 表示"内部方法"，不推荐外部直接调用
        相当于 C 语言里的 static 函数（仅本文件使用）
        """
        # 调用 OpenAI 兼容的 API，发送对话消息
        response = self.client.chat.completions.create(
            model=self.model,             # 使用的模型名称
            messages=self.messages,       # 对话历史（上下文）
            tools=TOOL_DEFINITIONS,       # 可用的工具列表（告诉 AI 它能用啥工具）
            temperature=TEMPERATURE,      # 温度参数（越高回答越随机，越低越确定）
        )
        # 返回 API 回复的第一条消息（AI 的回答）
        return response.choices[0].message

    def run(self, user_input: str) -> str:
        """
        执行一次用户请求，返回最终回复
        
        参数 user_input: 用户输入的文字（字符串）
        返回值: AI 的最终回复（字符串）
        
        核心流程（超级重要！）：
          1. 把用户说的话加入对话历史
          2. 调用 AI 模型，看它想怎么回答
          3. 如果 AI 想用工具 → 执行工具 → 把结果告诉 AI → 回到步骤 2
          4. 如果 AI 直接给文字回答 → 任务完成，返回文字
        
        这个循环叫做"ReAct 模式"（思考→行动→观察→再思考）
        """
        # 第一步：把用户的输入加到消息列表里
        self.messages.append({"role": "user", "content": user_input})

        # 开始循环：最多循环 MAX_TURNS 次（防止无限循环）
        for turn in range(MAX_TURNS):
            print(f"---第 {turn + 1} 轮---")  # 打印当前是第几轮

            # 调用 AI 模型，获取它的回应
            msg = self._call_llm()

            # ============================================================
            # 情况 A：AI 想调用工具
            # 如果 msg.tool_calls 不为空，说明 AI 决定使用某个工具
            # 比如 AI 说："我需要读取文件才能回答这个问题"
            # ============================================================
            if msg.tool_calls:
                # 遍历 AI 请求的所有工具调用（可能一次调用多个工具）
                for tool_call in msg.tool_calls:
                    # 获取工具名称，比如 "read_file"
                    tool_name = tool_call.function.name

                    # 获取工具参数（JSON 格式的字符串），解析成字典
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        # 如果解析失败（理论上不会发生），就用空字典
                        arguments = {}

                    # 打印：AI 要调用什么工具、传了什么参数
                    print(f"\n  [Agent] 调用工具: {tool_name}({arguments})")

                    # 执行工具！比如读取文件、执行命令等
                    result, success = execute_tool(tool_name, arguments)

                    # 打印工具执行结果（成功/失败，以及返回的内容）
                    status = "OK" if success else "FAIL"
                    print(f"  [Agent] 结果 [{status}]: {result[:200]}")

                    # 把 AI 的工具调用请求加入对话历史（让 AI 记得它调用了工具）
                    self.messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tool_call],
                    })

                    # 把工具的执行结果加入对话历史（让 AI 看到结果）
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })

                # 工具调用完后，继续循环，让 AI 看到工具结果后再次决策
                # （相当于"观察"阶段结束，进入下一轮"思考"）

            # ============================================================
            # 情况 B：AI 返回纯文本，任务完成
            # 如果 msg.tool_calls 为空，说明 AI 直接给出了文字回答
            # ============================================================
            else:
                # 获取 AI 的文字回复，如果为空就用 "(空回复)" 代替
                reply = msg.content or "(空回复)"

                # 把 AI 的回复加入对话历史
                self.messages.append({"role": "assistant", "content": reply})

                # 返回 AI 的回复，任务结束！
                return reply

        # 如果循环了 MAX_TURNS 次还没结束，强制终止并返回提示
        return "已达到最大循环轮数，任务可能未完成。"

    def chat(self):
        """交互式对话循环：用户一句一句跟 AI 聊天"""
        
        # 开始新对话前，先重置（清空历史，设置系统提示词）
        self.reset()

        # 打印欢迎界面
        print("=" * 60)
        print("  AI Agent 编程助手")
        print(f"  模型: {self.model}")
        print("  输入 /reset 重置对话 | /exit 退出")
        print("=" * 60)

        # 无限循环，直到用户输入 /exit 退出
        while True:
            try:
                # 等待用户输入，.strip() 去掉首尾空格
                user_input = input("\n你> ").strip()
            except (EOFError, KeyboardInterrupt):
                # 如果用户按了 Ctrl+C 或 Ctrl+D，友好地退出
                print("\n再见！")
                break

            # 如果用户什么都没输入（直接回车），跳过这次循环
            if not user_input:
                continue

            # 退出命令
            if user_input.lower() == "/exit":
                print("再见！")
                break

            # 重置命令：清空对话历史
            if user_input.lower() == "/reset":
                self.reset()
                print("对话已重置。")
                continue

            # 正常对话：打印思考中的提示，然后调用 run() 处理
            print(f"\n  [Agent] 思考中...")
            reply = self.run(user_input)
            print(f"\nAgent> {reply}")
