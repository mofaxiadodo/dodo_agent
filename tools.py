"""
Agent 工具集
每个工具函数返回 (结果文本, 是否成功) 的元组
"""

import os
import subprocess
import glob


# ============================================================
# 工具注册表 - 给 LLM 看的工具定义（OpenAI function calling 格式）
# ============================================================

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取指定文件的内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件路径（相对于工作目录或绝对路径）",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "写入内容到指定文件，会覆盖已有文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件路径",
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入的内容",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "在工作目录中执行一条终端命令，返回命令输出",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的命令（注意是 Windows 环境的 PowerShell）",
                    }
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "在工作目录中按 glob 模式搜索文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "文件匹配模式，如 *.py, **/*.js",
                    }
                },
                "required": ["pattern"],
            },
        },
    },
]


# ============================================================
# 工具实现
# ============================================================

WORK_DIR = os.getcwd()


def set_work_dir(path: str):
    """设置工作目录"""
    global WORK_DIR
    WORK_DIR = os.path.abspath(path)


def _resolve_path(path: str) -> str:
    """将相对路径转为工作目录下的绝对路径"""
    if os.path.isabs(path):
        return path
    return os.path.join(WORK_DIR, path)


def read_file(path: str) -> tuple[str, bool]:
    """读取文件"""
    full = _resolve_path(path)
    try:
        with open(full, "r", encoding="utf-8") as f:
            content = f.read()
        # 限制返回长度，避免超出 token 上下文
        if len(content) > 8000:
            content = content[:8000] + "\n... (内容已截断)"
        return content, True
    except FileNotFoundError:
        return f"文件不存在: {path}", False
    except Exception as e:
        return f"读取失败: {e}", False


def write_file(path: str, content: str) -> tuple[str, bool]:
    """写入文件"""
    full = _resolve_path(path)
    try:
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
        return f"已写入: {path} ({len(content)} 字符)", True
    except Exception as e:
        return f"写入失败: {e}", False


def run_command(command: str) -> tuple[str, bool]:
    """执行终端命令"""
    try:
        result = subprocess.run(
            ["powershell", "-Command", command],
            capture_output=True,
            text=True,
            cwd=WORK_DIR,
            timeout=60,
            shell=False,
        )
        output = result.stdout.strip()
        if result.stderr.strip():
            output += "\n[stderr]\n" + result.stderr.strip()
        if not output:
            output = "(无输出)"
        # 限制长度
        if len(output) > 4000:
            output = output[:4000] + "\n... (输出已截断)"
        return output, result.returncode == 0
    except subprocess.TimeoutExpired:
        return "命令执行超时 (60s)", False
    except Exception as e:
        return f"执行失败: {e}", False


def search_files(pattern: str) -> tuple[str, bool]:
    """搜索文件"""
    try:
        matches = glob.glob(pattern, root_dir=WORK_DIR, recursive=True)
        if not matches:
            return f"未找到匹配 '{pattern}' 的文件", True
        result = "\n".join(f"  {m}" for m in sorted(matches)[:50])
        if len(matches) > 50:
            result += f"\n  ... (还有 {len(matches) - 50} 个文件)"
        return result, True
    except Exception as e:
        return f"搜索失败: {e}", False


# 工具分发字典
TOOL_DISPATCH = {
    "read_file": read_file,
    "write_file": write_file,
    "run_command": run_command,
    "search_files": search_files,
}


def execute_tool(tool_name: str, arguments: dict) -> tuple[str, bool]:
    """根据工具名和参数执行工具"""
    func = TOOL_DISPATCH.get(tool_name)
    if func is None:
        return f"未知工具: {tool_name}", False
    try:
        return func(**arguments)
    except TypeError as e:
        return f"参数错误: {e}", False
