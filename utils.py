# -*- coding: utf-8 -*-
"""
utils.py - 工具函数模块（数据流中的"辅助工具箱"）

===================================================================
【数据流位置】
    config.py（常量）
        ↓
    utils.py（纯函数工具）  ← 你在这里
        ↓
    gui.py / main.py / models.py 都可能调用这里的函数
===================================================================

【工程思维】为什么要单独抽一个工具模块？
===================================================================
1. 【复用】"校验金额"这个逻辑，gui.py 要用，main.py 也要用。
   写一次，到处调用，不用重复写。

2. 【可测试】这里的函数都是"纯函数"——
   输入确定，输出就确定，没有副作用（不读写文件、不改全局变量）。
   纯函数是最容易写单元测试的代码形态。

3. 【主文件瘦身】gui.py 只关心"界面怎么显示"，
   不需要关心"怎么校验日期格式"这种细节。
===================================================================
"""

import re
from datetime import datetime, timedelta

from config import DATE_FORMAT, AMOUNT_PRECISION


# ============================================================
# 日期工具 —— gui.py 和 main.py 都会用到
# ============================================================

def get_today() -> str:
    """
    返回今天的日期字符串，格式 "YYYY-MM-DD"。
    gui.py 的"记一笔"表单会用它作为日期的默认值。
    """
    return datetime.now().strftime(DATE_FORMAT)


def parse_date(date_str: str) -> datetime | None:
    """
    安全地把日期字符串解析成 datetime 对象。

    【防御性编程】解析失败返回 None，而不是抛异常。
    调用者拿到 None 后可以给用户友好提示，而不是让程序崩溃。
    """
    try:
        return datetime.strptime(date_str, DATE_FORMAT)
    except (ValueError, TypeError):
        return None


def get_month_range(year: int, month: int) -> tuple[str, str]:
    """
    获取指定月份的起止日期字符串。
    gui.py 的"月度统计"功能会调用它来筛选某月的数据。

    返回: (月初日期, 月末日期)，格式均为 "YYYY-MM-DD"

    【实现技巧】
    月末 = 下个月1号 - 1天
    比如 2026年2月的月末 = 2026年3月1日 - 1天 = 2026年2月28日
    这样就不用手动判断闰年、大月小月了，优雅且不出错。
    """
    first_day = datetime(year, month, 1)

    # 特殊情况：12月的下个月是明年1月
    if month == 12:
        next_month_first = datetime(year + 1, 1, 1)
    else:
        next_month_first = datetime(year, month + 1, 1)

    last_day = next_month_first - timedelta(days=1)

    return first_day.strftime(DATE_FORMAT), last_day.strftime(DATE_FORMAT)


def get_current_month_range() -> tuple[str, str, int, int]:
    """
    获取当前月份的起止日期及年月。
    返回: (月初日期, 月末日期, 年, 月)
    """
    now = datetime.now()
    start, end = get_month_range(now.year, now.month)
    return start, end, now.year, now.month


# ============================================================
# 金额工具 —— gui.py 的 _on_save_entry() 会调用
# ============================================================

def validate_amount(amount_str: str) -> tuple[bool, float]:
    """
    校验并转换金额字符串（用户在界面输入的是字符串，需要转成数字）。

    返回值:
        (True, 金额数值)   → 合法，可以使用
        (False, 0.0)       → 不合法，需要提示用户

    校验规则（三道关卡）：
        1. 格式正确：必须是数字，最多两位小数（用正则匹配）
        2. 类型正确：能转成 float
        3. 值正确：必须大于 0（不能记一笔 0 元或负数的账）

    【为什么用正则而不是直接 float()？】
    因为 float("1.234") 不会报错，但金额不应该有 3 位小数。
    正则表达式确保"数字格式正确 + 最多两位小数"。
    """
    # 去除首尾空格（用户可能输入了 " 100 "）
    amount_str = amount_str.strip()

    # 第一关：正则校验格式
    if not re.match(r"^\d+(\.\d{1,2})?$", amount_str):
        return False, 0.0

    # 第二关：转成浮点数
    try:
        amount = float(amount_str)
    except ValueError:
        return False, 0.0

    # 第三关：必须是正数
    if amount <= 0:
        return False, 0.0

    # 三关都过了，四舍五入到指定位数后返回
    amount = round(amount, AMOUNT_PRECISION)
    return True, amount


# ============================================================
# 输入工具 —— CLI 版本 (main.py) 使用，GUI 版本不需要
# ============================================================

def safe_input(prompt: str, default: str = "") -> str:
    """
    安全的输入读取，处理 Ctrl+C / Ctrl+D 等中断信号。

    【工程思维】用户随时可能按 Ctrl+C 中断程序。
    如果不捕获这个信号，程序会抛出丑陋的 KeyboardInterrupt traceback。
    捕获后优雅地返回空字符串，用户体验更好。
    """
    try:
        value = input(prompt).strip()
        return value if value else default
    except (KeyboardInterrupt, EOFError):
        print()  # 换行，保持输出美观
        return ""


def confirm(prompt: str) -> bool:
    """
    读取用户确认（y/n），用于删除等危险操作前的二次确认。
    gui.py 中用 show_confirm() 弹窗代替，但 CLI 版本用这个。
    """
    answer = safe_input(f"{prompt} (y/n): ", "n")
    return answer.lower() in ("y", "yes", "是")


def format_amount(amount: float) -> str:
    """
    格式化金额为带两位小数的字符串。
    gui.py 的统计卡片显示金额时会调用它。
    """
    return f"{amount:.{AMOUNT_PRECISION}f}"
