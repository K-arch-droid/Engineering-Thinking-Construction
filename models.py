# -*- coding: utf-8 -*-
"""
models.py - 数据模型模块（数据流的第二层：定义"数据长什么样"）

===================================================================
【数据流位置】
    config.py（常量）
        ↓
    models.py（数据结构 + 校验）  ← 你在这里
        ↓
    storage.py（读写磁盘）
        ↓
    gui.py / main.py（界面层调用上面两层）
===================================================================

【工程思维】为什么需要模型层？
===================================================================
想象没有模型层的情况：gui.py 里直接用字典 {"id":1, "amount":100, ...}
- 字典的 key 拼错了不会报错（比如 "amout" 少了个 n）
- 校验逻辑散落在界面代码里，CLI 版本要重写一遍
- 没有自动补全，每次访问数据都要查字段名

用 @dataclass 定义模型后：
- 字段名拼错 → 立即报 AttributeError
- 校验逻辑写在模型里 → CLI 和 GUI 共用一套
- IDE 能自动补全字段名
===================================================================
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

# 从 config 导入常量（models 依赖 config，但 config 不依赖 models）
from config import TYPE_INCOME, TYPE_EXPENSE, VALID_TYPES, DATE_FORMAT


@dataclass
class BillEntry:
    """
    账单条目数据模型 —— 一条收支记录的"骨架"

    【@dataclass 是什么？】
    Python 3.7+ 的语法糖。加了这个装饰器后，Python 自动生成：
    - __init__()    → 不用手写构造函数
    - __repr__()    → 打印对象时显示可读内容
    - __eq__()      → 两个对象可以比较是否相等
    让你专注于"定义字段"，不用写一堆样板代码。

    【字段说明】
        id:         唯一编号（自增整数，由 storage.py 的 get_next_id() 分配）
        date:       交易日期，字符串格式 "YYYY-MM-DD"（来自 config.DATE_FORMAT）
        type:       收支类型，只能是 config.TYPE_INCOME 或 config.TYPE_EXPENSE
        category:   分类标签，如 "餐饮"、"工资"（来自 config 中的分类列表）
        amount:     金额（正数，单位：元，保留 2 位小数）
        note:       备注信息（可选，默认空字符串）
    """

    id: int = 0
    date: str = ""
    type: str = ""
    category: str = ""
    amount: float = 0.0
    note: str = ""

    def __post_init__(self):
        """
        【__post_init__ 是什么？】
        @dataclass 的特殊钩子：在 __init__() 执行完毕后自动调用。
        适合做"默认值填充"和"数据清洗"。

        这里做的事：如果用户没有传入日期（date 为空字符串），
        自动用今天的日期填充。这样用户记账时可以不填日期，体验更友好。
        """
        if not self.date:
            self.date = datetime.now().strftime(DATE_FORMAT)

    # ----------------------------------------------------------
    # 校验方法 —— 数据流中的"质量检查站"
    # ----------------------------------------------------------

    def validate(self) -> tuple[bool, str]:
        """
        校验账单条目的合法性。

        返回值：
            (True, "")           → 校验通过，数据可以保存
            (False, "错误信息")   → 校验失败，附带人可读的原因

        【工程思维：校验为什么放在模型层？】
        试想如果校验写在 gui.py 里：
        - CLI 版本 (main.py) 要重写一遍校验 → 代码重复
        - 两个版本的校验规则可能不一致 → 数据质量不可控
        - 以后加 Web 接口，又要写第三遍

        放在模型层后，无论从哪里创建账单（GUI、CLI、Web、API），
        都调同一个 validate()，规则统一，改一处全局生效。
        """
        # 1. 校验日期格式 —— 必须是合法的 YYYY-MM-DD
        try:
            datetime.strptime(self.date, DATE_FORMAT)
        except ValueError:
            return False, f"日期格式错误，应为 {DATE_FORMAT}，实际为 '{self.date}'"

        # 2. 校验收支类型 —— 必须是 config 中定义的合法类型
        if self.type not in VALID_TYPES:
            return False, f"收支类型错误，应为 {VALID_TYPES} 之一，实际为 '{self.type}'"

        # 3. 校验金额 —— 必须是正数
        if self.amount <= 0:
            return False, f"金额必须为正数，实际为 {self.amount}"

        # 4. 校验分类 —— 不能为空白
        if not self.category.strip():
            return False, "分类不能为空"

        # 全部通过
        return True, ""

    # ----------------------------------------------------------
    # 序列化方法 —— 对象 ←→ 字典 ←→ JSON 文件
    # ----------------------------------------------------------

    def to_dict(self) -> dict:
        """
        把对象转成字典 → 交给 storage.py 写入 JSON 文件

        dataclass 自带的 asdict() 会递归转换所有字段为普通 Python 类型。
        转换后: BillEntry(id=1, amount=100.0) → {"id":1, "amount":100.0}
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "BillEntry":
        """
        从字典重建对象 ← storage.py 从 JSON 文件加载后调用

        【@classmethod 是什么？】
        普通方法的第一个参数是 self（对象实例），
        classmethod 的第一个参数是 cls（类本身）。
        这里用 classmethod 因为它是"工厂方法"——
        不是操作已有对象，而是根据数据创建新对象。

        【为什么用 .get() 而不是 data["id"]？】
        防御性编程：如果 JSON 文件中某条记录缺少 "id" 字段，
        data["id"] 会抛 KeyError 导致程序崩溃，
        data.get("id", 0) 会返回默认值 0，程序继续运行。

        【为什么 amount 要 float() 转换？】
        JSON 中的数字加载后可能是 int 或 float，
        统一转成 float 保证类型一致性。
        """
        return cls(
            id=data.get("id", 0),
            date=data.get("date", ""),
            type=data.get("type", ""),
            category=data.get("category", ""),
            amount=float(data.get("amount", 0)),
            note=data.get("note", ""),
        )

    # ----------------------------------------------------------
    # 显示方法
    # ----------------------------------------------------------

    def format_display(self) -> str:
        """
        格式化为人类可读的单行文本，用于列表展示。
        收入显示 +，支出显示 -，一目了然。
        """
        sign = "+" if self.type == TYPE_INCOME else "-"
        return (
            f"[{self.id:>4}] {self.date}  "
            f"{'收入' if self.type == TYPE_INCOME else '支出'}  "
            f"{self.category:<6}  "
            f"{sign}{self.amount:>10.2f}  "
            f"{self.note}"
        )
