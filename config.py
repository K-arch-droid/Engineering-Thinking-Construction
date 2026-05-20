# -*- coding: utf-8 -*-
"""
config.py - 全局配置模块（数据流的起点：所有模块的"参数表"）

===================================================================
【工程思维】为什么需要单独的配置文件？
===================================================================
想象一下，如果日期格式 "%Y-%m-%d" 散落在 5 个文件里，
某天老板说要改成 "%Y/%m/%d"，你得满项目去找、去改，还可能漏掉。
把所有可配置的值集中到这里，改一处，全局生效。

这就是"单一数据源"（Single Source of Truth）原则。
===================================================================

本模块在整个数据流中的位置：
    config.py  →  提供常量给 models.py / storage.py / utils.py / gui.py
    （所有模块都从这里读取配置，但 config 不依赖任何其他模块）
"""

import os
import sys

# ============================================================
# 路径配置（兼容 PyInstaller 打包）
# ============================================================

# 【为什么要区分"开发时"和"打包后"的路径？】
#
# 开发时（直接运行 python gui.py）：
#   __file__ = "C:/项目/config.py"
#   数据文件和 .py 在同一个目录
#
# 打包后（运行 个人记账本.exe）：
#   __file__ 不存在了！（代码已被嵌入 exe 内部）
#   exe 在 "dist/个人记账本/" 目录
#   内部资源在 "dist/个人记账本/_internal/" 目录
#   用户数据（accounts.json）需要在 exe 旁边（可写）
#
# 所以需要两个路径函数：
#   get_base_path()     → 用户数据位置（exe 旁边，可写）
#   get_resource_path() → 内部资源位置（_internal/ 内，只读）


def get_base_path():
    """获取用户数据目录（可写位置）。

    【PyInstaller 的 frozen 机制】
    当程序被 PyInstaller 打包后，sys 模块会多出两个属性：
      - sys.frozen = True     （标记"我是打包后的程序"）
      - sys.executable = exe 文件的完整路径

    getattr(sys, 'frozen', False) 的意思是：
      如果 sys 有 frozen 属性，返回它的值（True）；
      如果没有（开发时），返回默认值 False。

    这样同一份代码，开发时和打包后都能正确找到路径。
    """
    if getattr(sys, 'frozen', False):
        # 打包后：exe 所在目录（用户数据放这里，可读可写）
        return os.path.dirname(sys.executable)
    # 开发时：源码所在目录
    return os.path.dirname(os.path.abspath(__file__))


def get_resource_path(relative_path=""):
    """获取内部资源路径（只读，如内置文档、图标）。

    【为什么资源文件在 _internal/ 目录？】
    PyInstaller --onedir 模式的目录结构：
      个人记账本/
        ├── 个人记账本.exe       ← sys.executable 指向这里
        ├── accounts.json        ← 用户数据（在 exe 旁边）
        └── _internal/           ← PyInstaller 的内部目录
            ├── assets/icon.ico  ← 内部资源在这里
            ├── docs/
            └── ...（Python 解释器 + 第三方库）

    所以内部资源的基目录 = exe 所在目录 + "/_internal"
    """
    if getattr(sys, 'frozen', False):
        # 打包后：内部资源在 _internal/ 子目录
        base = os.path.join(os.path.dirname(sys.executable), "_internal")
    else:
        # 开发时：资源和源码在同一目录
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path) if relative_path else base


# DATA_DIR = 用户数据目录（accounts.json 读写位置）
# 打包后指向 exe 旁边，开发时指向源码目录
DATA_DIR = get_base_path()

# DATA_FILE = accounts.json 的完整路径
# storage.py 会用这个路径读写记账数据
DATA_FILE = os.path.join(DATA_DIR, "accounts.json")

# ============================================================
# 收支类型常量
# ============================================================

# 【魔法字符串 vs 常量】
# 如果在代码里直接写 "income"，这叫"魔法字符串"——
# 拼错成 "incme" 不会报错，程序只是静默地判断为 False，bug 很难发现。
# 用常量 TYPE_INCOME 后，拼错会立即抛出 NameError，bug 无所遁形。
# IDE 也能自动补全常量名，提高编码效率。
TYPE_INCOME = "income"   # 收入
TYPE_EXPENSE = "expense" # 支出

# 合法类型列表 —— 校验时用 "if type not in VALID_TYPES" 来判断
# 新增类型（比如 "transfer" 转账）只需在这里加一行，校验逻辑自动覆盖
VALID_TYPES = [TYPE_INCOME, TYPE_EXPENSE]

# ============================================================
# 默认分类
# ============================================================

# 收入和支出使用不同的分类列表
# gui.py 中切换"收入/支出"单选按钮时，会根据这里切换下拉框的选项
# 新增分类只需在这里加一个字符串，UI 自动生效
INCOME_CATEGORIES = ["工资", "奖金", "理财", "兼职", "红包", "报销", "租金", "其他"]
EXPENSE_CATEGORIES = ["餐饮", "交通", "购物", "住房", "娱乐", "医疗", "教育", "通讯", "服饰", "日用", "社交", "其他"]

# ============================================================
# 显示格式配置
# ============================================================

# 日期格式 —— 全程序统一用这一种格式
# strftime = 把日期对象变成字符串（格式化输出）
# strptime = 把字符串解析成日期对象（解析输入）
# 这两个函数在 models.py 的 validate() 和 utils.py 的 get_today() 中都会用到
DATE_FORMAT = "%Y-%m-%d"

# 金额保留 2 位小数（和人民币的"分"对应）
AMOUNT_PRECISION = 2

# 表格列宽（用于对齐输出）
COLUMN_WIDTHS = {
    "id": 6,
    "date": 12,
    "type": 6,
    "category": 8,
    "amount": 12,
    "note": 20,
}
