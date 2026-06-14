"""
Agent 工具集
每个工具函数都返回一个元组 (结果文本, 是否成功)
相当于 AI 助手的"工具箱"，里面放着各种有用的工具 🔧
"""

import os                       # os 模块：文件路径、目录操作
import subprocess               # subprocess 模块：执行终端命令
import glob                     # glob 模块：文件搜索（支持通配符 * 和 **）


# ============================================================
# 工具注册表 - 给 AI 看的工具使用说明
# 格式是 OpenAI 的 function calling 标准格式
# AI 会阅读这些定义，了解它可以用什么工具、怎么用
# ============================================================

TOOL_DEFINITIONS = [
    # 工具 1：读取文件
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
                "required": ["path"],  # path 参数是必填的
            },
        },
    },
    # 工具 2：写入文件
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
                "required": ["path", "content"],  # 两个参数都必填
            },
        },
    },
    # 工具 3：执行命令
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
    # 工具 4：搜索文件
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
    # 工具 5：列出目录
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "列出指定目录下的文件和子目录。不传参数则列出当前工作目录",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "要列出的目录路径，默认为当前目录",
                    }
                },
                # 注意：path 参数不是必填的，不传就默认当前目录
            },
        },
    },
]


# ============================================================
# 工具实现（真正的功能代码）
# ============================================================

# 工作目录：所有相对路径都基于这个目录
# 默认是程序启动时的当前目录
WORK_DIR = os.getcwd()


def set_work_dir(path: str):
    """
    设置工作目录
    参数 path: 新的工作目录路径
    注意：用 global 关键字修改全局变量 WORK_DIR
    """
    global WORK_DIR
    WORK_DIR = os.path.abspath(path)  # os.path.abspath 把路径转为绝对路径


def _resolve_path(path: str) -> str:
    """
    将传入的路径解析为绝对路径
    
    参数 path: 用户传入的路径（可能是相对路径或绝对路径）
    返回值: 绝对路径字符串
    
    规则：
    - 如果已经是绝对路径（比如 C:\Users\xxx），直接返回
    - 如果是相对路径（比如 ./data/file.txt），拼上 WORK_DIR
    """
    if os.path.isabs(path):
        return path                     # 已经是绝对路径，直接返回
    return os.path.join(WORK_DIR, path)  # 相对路径，拼上工作目录


def read_file(path: str) -> tuple[str, bool]:
    """
    读取文件内容
    
    参数 path: 文件路径
    返回值: (文件内容 或 错误信息, 是否成功)
    
    限制：最多返回前 8000 个字符，防止内容太长超出 AI 的上下文窗口
    """
    full = _resolve_path(path)  # 解析成绝对路径
    
    try:
        # 打开文件，以只读模式 (r)，使用 UTF-8 编码
        # with 语句会自动关闭文件，不用手动 f.close()
        with open(full, "r", encoding="utf-8") as f:
            content = f.read()  # 读取全部内容
        
        # 如果内容太长，截断到 8000 字符
        if len(content) > 8000:
            content = content[:8000] + "\n... (内容已截断)"
        
        return content, True  # 成功！返回 (内容, True)
    
    except FileNotFoundError:
        # 文件没找到的错误
        return f"文件不存在: {path}", False
    
    except Exception as e:
        # 其他任何错误（比如权限不足、编码问题等）
        return f"读取失败: {e}", False


def write_file(path: str, content: str) -> tuple[str, bool]:
    """
    写入文件（会覆盖已有文件！）
    
    参数 path: 文件路径
    参数 content: 要写入的内容
    返回值: (操作结果信息, 是否成功)
    
    注意：如果文件所在的目录不存在，会自动创建目录
    """
    full = _resolve_path(path)  # 解析成绝对路径
    
    try:
        # 确保文件所在的目录存在，如果不存在就创建
        # os.path.dirname(full) 获取文件所在的目录路径
        # os.makedirs 创建目录，exist_ok=True 表示目录已存在也不报错
        os.makedirs(os.path.dirname(full), exist_ok=True)
        
        # 打开文件，以写入模式 (w)，使用 UTF-8 编码
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)  # 写入内容
        
        # 返回成功信息，包括写了多少字符
        return f"已写入: {path} ({len(content)} 字符)", True
    
    except Exception as e:
        return f"写入失败: {e}", False


def run_command(command: str) -> tuple[str, bool]:
    """
    在终端中执行一条命令
    
    参数 command: 要执行的 PowerShell 命令
    返回值: (命令输出 或 错误信息, 是否成功)
    
    注意：
    - 在 Windows 环境下运行，使用 PowerShell
    - 超时时间 60 秒，防止命令卡死
    - 输出限制 4000 字符
    """
    try:
        # subprocess.run 用来运行外部命令
        # 相当于在终端里输入命令
        result = subprocess.run(
            ["powershell", "-Command", command],  # 用 PowerShell 执行
            capture_output=True,   # 捕获输出（不打印到屏幕）
            text=True,             # 以文本形式返回（而不是字节）
            cwd=WORK_DIR,          # 在工作目录下执行
            timeout=60,            # 超时时间 60 秒
            shell=False,           # 不通过系统 shell 执行（更安全）
        )
        
        # 收集标准输出
        output = result.stdout.strip()
        
        # 如果有错误输出，也加上
        if result.stderr.strip():
            output += "\n[stderr]\n" + result.stderr.strip()
        
        # 如果完全没有输出，给个提示
        if not output:
            output = "(无输出)"
        
        # 限制输出长度，避免太长
        if len(output) > 4000:
            output = output[:4000] + "\n... (输出已截断)"
        
        # result.returncode 是命令的返回值，0 表示成功
        return output, result.returncode == 0
    
    except subprocess.TimeoutExpired:
        # 命令执行超过 60 秒
        return "命令执行超时 (60s)", False
    
    except Exception as e:
        return f"执行失败: {e}", False


def search_files(pattern: str) -> tuple[str, bool]:
    """
    按 glob 模式搜索文件
    
    参数 pattern: 文件匹配模式
        例如: "*.py" 匹配所有 Python 文件
              "**/*.txt" 匹配所有子目录中的 txt 文件
    返回值: (匹配的文件列表 或 提示信息, 是否成功)
    
    限制：最多显示前 50 个匹配结果
    """
    try:
        # glob.glob 搜索匹配的文件
        # root_dir=WORK_DIR 表示在工作目录下搜索
        # recursive=True 表示递归搜索子目录（支持 ** 通配符）
        matches = glob.glob(pattern, root_dir=WORK_DIR, recursive=True)
        
        # 如果没有匹配的文件
        if not matches:
            return f"未找到匹配 '{pattern}' 的文件", True
        
        # 把匹配的文件名用换行符拼起来，最多 50 个
        result = "\n".join(f"  {m}" for m in sorted(matches)[:50])
        
        # 如果超过 50 个，提示还有更多
        if len(matches) > 50:
            result += f"\n  ... (还有 {len(matches) - 50} 个文件)"
        
        return result, True
    
    except Exception as e:
        return f"搜索失败: {e}", False


def list_dir(path: str = ".") -> tuple[str, bool]:
    """
    列出指定目录下的文件和子目录
    
    参数 path: 要列出的目录路径，默认为 "."（当前目录）
    返回值: (目录内容列表 或 错误信息, 是否成功)
    
    显示格式：
    - 文件名后面带 "/" 的表示是目录
    - 按字母顺序排序
    """
    full = _resolve_path(path)  # 解析成绝对路径
    
    try:
        # os.listdir 列出目录下的所有文件和子目录名
        items = os.listdir(full)
        
        # 如果是空目录
        if not items:
            return f"目录 '{path}' 是空的", True
        
        # 遍历所有项目，判断是文件还是目录
        lines = []
        for name in sorted(items):  # 按字母排序
            item_path = os.path.join(full, name)
            # 如果是目录，在名字后面加 "/"
            tag = "/" if os.path.isdir(item_path) else ""
            lines.append(f"  {name}{tag}")
        
        # 用换行符拼成字符串返回
        return "\n".join(lines), True
    
    except FileNotFoundError:
        return f"目录不存在: {path}", False
    
    except Exception as e:
        return f"列出失败: {e}", False


# ============================================================
# 工具分发系统
# 把工具名称（字符串）和对应的函数关联起来
# ============================================================

# 工具分发字典：工具名 → 对应的函数
TOOL_DISPATCH = {
    "read_file": read_file,       # "read_file" 对应 read_file() 函数
    "write_file": write_file,     # "write_file" 对应 write_file() 函数
    "run_command": run_command,   # "run_command" 对应 run_command() 函数
    "search_files": search_files, # "search_files" 对应 search_files() 函数
    "list_dir": list_dir,         # "list_dir" 对应 list_dir() 函数
}


def execute_tool(tool_name: str, arguments: dict) -> tuple[str, bool]:
    """
    根据工具名和参数执行对应的工具函数
    
    参数 tool_name: 工具名称（字符串），比如 "read_file"
    参数 arguments: 工具参数（字典），比如 {"path": "test.txt"}
    返回值: (执行结果, 是否成功)
    
    这个函数是"工具调用的总入口"，
    agent.py 里调用工具时，实际调用的是这个函数
    """
    # 从分发字典中查找工具名对应的函数
    func = TOOL_DISPATCH.get(tool_name)
    
    # 如果没找到这个工具名
    if func is None:
        return f"未知工具: {tool_name}", False
    
    try:
        # 执行工具函数，把 arguments 字典作为关键字参数传入
        # **arguments 表示把字典展开成关键字参数
        # 比如 {"path": "test.txt"} → func(path="test.txt")
        return func(**arguments)
    
    except TypeError as e:
        # 参数类型错误（比如传了不存在的参数名）
        return f"参数错误: {e}", False
