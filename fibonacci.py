"""
斐波那契数列计算器
斐波那契数列：0, 1, 1, 2, 3, 5, 8, 13, 21, 34, ...
每个数都是前两个数之和（除了第0项和第1项）
"""


def fibonacci(n):
    """
    计算第 n 个斐波那契数（从 0 开始计数）
    
    参数 n: 非负整数，表示要计算的项数
    返回值: 第 n 个斐波那契数
    
    示例：
        fibonacci(0) → 0
        fibonacci(1) → 1
        fibonacci(2) → 1  (0+1)
        fibonacci(3) → 2  (1+1)
        fibonacci(4) → 3  (1+2)
        fibonacci(5) → 5  (2+3)
    
    实现思路：用循环迭代，而不是递归
    好处：效率高，不会栈溢出
    """
    # 检查输入是否合法：n 不能是负数
    if n < 0:
        raise ValueError("n must be non-negative integer")
    
    # 第 0 项：直接返回 0
    if n == 0:
        return 0
    
    # 第 1 项：直接返回 1
    if n == 1:
        return 1
    
    # 从第 2 项开始，用循环计算
    # a 表示第 n-2 项，b 表示第 n-1 项
    a, b = 0, 1  # 初始：a = F(0), b = F(1)
    
    # range(2, n+1) 生成从 2 到 n 的整数序列
    # _ 表示"不关心这个变量的值"，只是一个占位符
    for _ in range(2, n + 1):
        # 关键步骤：更新 a 和 b
        # 新的 a = 旧的 b
        # 新的 b = 旧的 a + 旧的 b
        # 相当于同时推进了一步
        a, b = b, a + b
    
    # 循环结束后，b 就是第 n 项的值
    return b


# 如果直接运行这个文件（而不是被导入），执行测试代码
if __name__ == "__main__":
    # 打印前 10 个斐波那契数（F(0) 到 F(9)）
    print("前 10 个斐波那契数：")
    for i in range(10):
        print(f"F({i}) = {fibonacci(i)}")
