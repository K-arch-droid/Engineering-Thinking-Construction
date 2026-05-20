# 个人记账本 GUI 版实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有命令行记账本改造为 tkinter + ttkbootstrap 桌面 GUI 应用，保留原 CLI 版本不动。

**Architecture:** 在原有 config/models/storage/utils 之上新建 GUI 层（gui.py + ui_components.py + theme.py），GUI 层只负责界面渲染和事件分发，业务逻辑完全复用原有模块。

**Tech Stack:** Python 3.10+, ttkbootstrap (GUI 主题框架), tkinter (内置 GUI 库)

---

## 文件结构

```
├── config.py           # 不变
├── models.py           # 不变
├── storage.py          # 不变
├── utils.py            # 不变
├── main.py             # CLI 入口（保留）
├── gui.py              # GUI 入口（新建）
├── ui_components.py    # 可复用 UI 组件（新建）
├── theme.py            # 样式/字体配置（新建）
├── requirements.txt    # 更新
└── README.md           # 更新
```

---

### Task 1: 创建 theme.py — 样式配置中心

**Files:**
- Create: `theme.py`

集中管理所有视觉参数。后续调整 UI 风格只改这一个文件。

- [ ] **Step 1: 创建 theme.py**

```python
# -*- coding: utf-8 -*-
"""
theme.py - 样式配置中心

所有视觉参数集中在此文件。
修改这里的值即可全局换肤，无需改动其他模块。
"""

import ttkbootstrap as ttk

# ============================================================
# 字体配置
# ============================================================

FONT_FAMILY = "Microsoft YaHei"      # 字体族（可改为 SimHei/Consolas 等）
FONT_SIZE_TITLE = 18                  # 标题字号
FONT_SIZE_SUBTITLE = 14               # 副标题字号
FONT_SIZE_BODY = 12                   # 正文字号
FONT_SIZE_SMALL = 10                  # 辅助文字字号

# ============================================================
# 颜色配置
# ============================================================

COLOR_PRIMARY = "#2563EB"             # 主色调（按钮、高亮）
COLOR_SUCCESS = "#16A34A"             # 收入-绿色
COLOR_DANGER = "#DC2626"              # 支出-红色
COLOR_WARNING = "#F59E0B"             # 警告-黄色
COLOR_BG = "#F8FAFC"                  # 背景色
COLOR_TEXT = "#1E293B"                # 正文文字色
COLOR_TEXT_SECONDARY = "#64748B"      # 辅助文字色

# ============================================================
# ttkbootstrap 主题
# ============================================================

# 可选主题: cosmo, litera, flatly, journal, lumen, minty, pulse,
#           sandstone, united, yeti, morph, simple, cerculean,
#           darkly, superhero, solar, cyborg, vapor
THEME_NAME = "cosmo"

# ============================================================
# 窗口配置
# ============================================================

WINDOW_TITLE = "个人记账本 v1.0"
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 600
WINDOW_MIN_WIDTH = 700
WINDOW_MIN_HEIGHT = 500

# ============================================================
# 表格列配置
# ============================================================

TABLE_COLUMNS = {
    "id":       {"text": "编号", "width": 60,  "anchor": "center"},
    "date":     {"text": "日期", "width": 100, "anchor": "center"},
    "type":     {"text": "类型", "width": 60,  "anchor": "center"},
    "category": {"text": "分类", "width": 80,  "anchor": "center"},
    "amount":   {"text": "金额", "width": 100, "anchor": "e"},
    "note":     {"text": "备注", "width": 200, "anchor": "w"},
}


def get_font(size_key: str = "body", weight: str = "normal") -> tuple:
    """
    获取字体元组，供 tkinter 组件使用。

    参数:
        size_key: "title" / "subtitle" / "body" / "small"
        weight:   "normal" / "bold"

    返回:
        (字体族, 字号, 权重) 元组
    """
    size_map = {
        "title": FONT_SIZE_TITLE,
        "subtitle": FONT_SIZE_SUBTITLE,
        "body": FONT_SIZE_BODY,
        "small": FONT_SIZE_SMALL,
    }
    size = size_map.get(size_key, FONT_SIZE_BODY)
    return (FONT_FAMILY, size, weight)


def apply_theme(style: ttk.Style):
    """
    将本模块的配置注入 ttkbootstrap 的 Style 对象。
    在 gui.py 创建窗口时调用一次即可。
    """
    style.configure(".", font=get_font("body"))
    style.configure("TLabel", font=get_font("body"))
    style.configure("TButton", font=get_font("body"))
    style.configure("TEntry", font=get_font("body"))
    style.configure("Treeview", font=get_font("body"), rowheight=28)
    style.configure("Treeview.Heading", font=get_font("body", "bold"))
    style.configure("TNotebook.Tab", font=get_font("body"))
```

- [ ] **Step 2: 验证导入无报错**

Run: `cd C:/Users/Administrator/Documents/test_2_CC_2026_5_15 && python -c "import theme; print('theme.py OK')"`
Expected: `theme.py OK`

- [ ] **Step 3: Commit**

```bash
git add theme.py
git commit -m "feat: add theme.py style configuration center"
```

---

### Task 2: 创建 ui_components.py — 可复用 UI 组件

**Files:**
- Create: `ui_components.py`

封装可复用的 UI 组件：表单行、数据表格、统计卡片、确认对话框。

- [ ] **Step 1: 创建 ui_components.py**

```python
# -*- coding: utf-8 -*-
"""
ui_components.py - 可复用 UI 组件

将常用的界面元素封装为独立组件，供 gui.py 中的各标签页复用。
每个组件都是一个 ttk.Frame 的子类，可以像积木一样拼装。
"""

import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from config import TYPE_INCOME, TYPE_EXPENSE, INCOME_CATEGORIES, EXPENSE_CATEGORIES
from utils import validate_amount, get_today, format_amount
from theme import get_font, COLOR_SUCCESS, COLOR_DANGER


class FormRow(ttk.Frame):
    """
    表单行组件：标签 + 输入控件，自动对齐。

    用法:
        row = FormRow(parent, label="金额:")
        row.get_value()  # 获取输入值
    """

    def __init__(self, parent, label: str, widget_type: str = "entry", **kwargs):
        """
        参数:
            parent:     父容器
            label:      标签文字
            widget_type: 控件类型 "entry" / "combobox" / "spinbox"
            **kwargs:    传递给具体控件的参数
        """
        super().__init__(parent)

        # 标签
        self.label = ttk.Label(self, text=label, width=10, anchor="e")
        self.label.pack(side="left", padx=(0, 8))

        # 输入控件
        if widget_type == "entry":
            self.widget = ttk.Entry(self, **kwargs)
        elif widget_type == "combobox":
            self.widget = ttk.Combobox(self, state="readonly", **kwargs)
        elif widget_type == "spinbox":
            self.widget = ttk.Spinbox(self, **kwargs)
        else:
            self.widget = ttk.Entry(self, **kwargs)

        self.widget.pack(side="left", fill="x", expand=True)

    def get_value(self) -> str:
        """获取控件当前值"""
        if isinstance(self.widget, ttk.Combobox):
            return self.widget.get()
        return self.widget.get().strip()

    def set_value(self, value: str):
        """设置控件值"""
        if isinstance(self.widget, ttk.Combobox):
            self.widget.set(value)
        else:
            self.widget.delete(0, "end")
            self.widget.insert(0, value)

    def clear(self):
        """清空控件"""
        if isinstance(self.widget, ttk.Combobox):
            self.widget.set("")
        else:
            self.widget.delete(0, "end")


class DataTable(ttk.Frame):
    """
    数据表格组件：基于 Treeview，支持表头定义、数据加载、行选择。

    用法:
        table = DataTable(parent, columns=theme.TABLE_COLUMNS)
        table.load_data(entries)  # entries 为 BillEntry 列表
        selected = table.get_selected_id()  # 获取选中行的 ID
    """

    def __init__(self, parent, columns: dict, **kwargs):
        """
        参数:
            parent:  父容器
            columns: 列定义字典，格式见 theme.TABLE_COLUMNS
        """
        super().__init__(parent, **kwargs)

        self.columns_def = columns
        col_ids = list(columns.keys())

        # 创建 Treeview + 滚动条
        scrollbar = ttk.Scrollbar(self, orient="vertical")
        self.tree = ttk.Treeview(
            self,
            columns=col_ids,
            show="headings",
            height=15,
            yscrollcommand=scrollbar.set,
        )
        scrollbar.config(command=self.tree.yview)

        # 配置列
        for col_id, cfg in columns.items():
            self.tree.heading(col_id, text=cfg["text"])
            self.tree.column(col_id, width=cfg["width"], anchor=cfg["anchor"])

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 存储 ID 到行的映射
        self._id_map: dict[str, int] = {}

    def load_data(self, entries):
        """
        加载 BillEntry 列表到表格。

        参数:
            entries: BillEntry 对象列表
        """
        # 清空现有数据
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._id_map.clear()

        # 插入新数据
        for entry in entries:
            type_display = "收入" if entry.type == TYPE_INCOME else "支出"
            sign = "+" if entry.type == TYPE_INCOME else "-"
            amount_display = f"{sign}{format_amount(entry.amount)}"

            values = (
                entry.id,
                entry.date,
                type_display,
                entry.category,
                amount_display,
                entry.note,
            )

            # 根据类型设置行标签（用于颜色区分）
            tag = "income" if entry.type == TYPE_INCOME else "expense"
            item_id = self.tree.insert("", "end", values=values, tags=(tag,))
            self._id_map[item_id] = entry.id

        # 配置行颜色
        self.tree.tag_configure("income", foreground=COLOR_SUCCESS)
        self.tree.tag_configure("expense", foreground=COLOR_DANGER)

    def get_selected_id(self) -> int | None:
        """
        获取当前选中行的账单 ID。

        返回:
            账单 ID（int），未选中返回 None
        """
        selection = self.tree.selection()
        if not selection:
            return None
        item_id = selection[0]
        return self._id_map.get(item_id)

    def clear(self):
        """清空表格"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._id_map.clear()


class StatsCard(ttk.Frame):
    """
    统计卡片组件：显示一个指标（标题 + 数值）。

    用法:
        card = StatsCard(parent, title="收入合计", value="+10000.00")
        card.update_value("+20000.00")
    """

    def __init__(self, parent, title: str, value: str = "0.00", **kwargs):
        super().__init__(parent, padding=10, **kwargs)

        self.title_label = ttk.Label(
            self, text=title, font=get_font("small"), bootstyle="secondary"
        )
        self.title_label.pack(anchor="w")

        self.value_label = ttk.Label(
            self, text=value, font=get_font("subtitle", "bold")
        )
        self.value_label.pack(anchor="w", pady=(4, 0))

    def update_value(self, value: str, color: str = None):
        """更新数值显示"""
        self.value_label.config(text=value)
        if color:
            self.value_label.config(foreground=color)


def show_confirm(title: str, message: str) -> bool:
    """弹出确认对话框，返回用户是否确认"""
    return messagebox.askyesno(title, message)


def show_info(title: str, message: str):
    """弹出信息提示框"""
    messagebox.showinfo(title, message)


def show_error(title: str, message: str):
    """弹出错误提示框"""
    messagebox.showerror(title, message)
```

- [ ] **Step 2: 验证导入无报错**

Run: `cd C:/Users/Administrator/Documents/test_2_CC_2026_5_15 && python -c "import ui_components; print('ui_components.py OK')"`
Expected: `ui_components.py OK`

- [ ] **Step 3: Commit**

```bash
git add ui_components.py
git commit -m "feat: add ui_components.py reusable UI components"
```

---

### Task 3: 创建 gui.py — GUI 主入口（含全部 4 个标签页）

**Files:**
- Create: `gui.py`

主窗口 + 4 个标签页（记一笔 / 收支流水 / 月度统计 / 设置）。

- [ ] **Step 1: 创建 gui.py**

```python
# -*- coding: utf-8 -*-
"""
gui.py - GUI 主入口

程序的图形界面入口。
负责创建主窗口、加载标签页、协调 UI 事件与业务逻辑。

启动方式: python gui.py
"""

import tkinter as tk
from datetime import datetime
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from config import (
    TYPE_INCOME, TYPE_EXPENSE,
    INCOME_CATEGORIES, EXPENSE_CATEGORIES,
)
from models import BillEntry
from storage import Storage
from utils import (
    get_today, validate_amount, format_amount,
    get_current_month_range, get_month_range,
)
from theme import (
    THEME_NAME, WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT,
    WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT, TABLE_COLUMNS,
    get_font, apply_theme,
    COLOR_SUCCESS, COLOR_DANGER, COLOR_PRIMARY,
)
from ui_components import (
    FormRow, DataTable, StatsCard,
    show_confirm, show_info, show_error,
)


class AccountApp:
    """
    记账本 GUI 应用主类。

    职责：
        1. 创建和配置主窗口
        2. 管理标签页切换
        3. 协调 UI 事件与 Storage/Models 的交互
    """

    def __init__(self):
        # 创建主窗口（使用 ttkbootstrap 主题）
        self.root = ttk.Window(
            title=WINDOW_TITLE,
            themename=THEME_NAME,
            size=(WINDOW_WIDTH, WINDOW_HEIGHT),
            minsize=(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT),
        )

        # 居中显示
        self.root.place_window_center()

        # 注入全局样式
        style = ttk.Style()
        apply_theme(style)

        # 存储管理器
        self.storage = Storage()

        # 构建界面
        self._build_ui()

    def _build_ui(self):
        """构建主界面：标签页容器 + 4 个标签页"""
        # 标签页容器
        self.notebook = ttk.Notebook(self.root, bootstyle="primary")
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # 创建 4 个标签页
        self._build_add_tab()
        self._build_list_tab()
        self._build_stats_tab()
        self._build_settings_tab()

    # ==============================================================
    # 标签页 1：记一笔
    # ==============================================================

    def _build_add_tab(self):
        """构建"记一笔"标签页"""
        tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(tab, text="  记一笔  ")

        # 标题
        ttk.Label(tab, text="记录一笔收支", font=get_font("title", "bold")).pack(
            anchor="w", pady=(0, 20)
        )

        # 日期
        self.add_date = FormRow(tab, label="日期:")
        self.add_date.set_value(get_today())
        self.add_date.pack(fill="x", pady=5)

        # 收支类型（单选按钮）
        type_frame = ttk.Frame(tab)
        type_frame.pack(fill="x", pady=5)
        ttk.Label(type_frame, text="类型:", width=10, anchor="e").pack(side="left", padx=(0, 8))
        self.add_type = tk.StringVar(value=TYPE_EXPENSE)
        ttk.Radiobutton(
            type_frame, text="支出", variable=self.add_type,
            value=TYPE_EXPENSE, command=self._on_type_change
        ).pack(side="left", padx=(0, 16))
        ttk.Radiobutton(
            type_frame, text="收入", variable=self.add_type,
            value=TYPE_INCOME, command=self._on_type_change
        ).pack(side="left")

        # 分类下拉
        self.add_category = FormRow(tab, label="分类:", widget_type="combobox")
        self.add_category.pack(fill="x", pady=5)
        self._on_type_change()  # 初始化分类列表

        # 金额
        self.add_amount = FormRow(tab, label="金额（元）:")
        self.add_amount.pack(fill="x", pady=5)

        # 备注
        self.add_note = FormRow(tab, label="备注:")
        self.add_note.pack(fill="x", pady=5)

        # 保存按钮
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill="x", pady=(20, 0))
        ttk.Button(
            btn_frame, text="保存", bootstyle="success",
            command=self._on_save_entry, width=12
        ).pack(side="left", padx=(78, 0))

    def _on_type_change(self):
        """收支类型切换时，更新分类下拉选项"""
        entry_type = self.add_type.get()
        categories = INCOME_CATEGORIES if entry_type == TYPE_INCOME else EXPENSE_CATEGORIES
        self.add_category.widget["values"] = categories
        self.add_category.set_value(categories[0])

    def _on_save_entry(self):
        """保存一条收支记录"""
        # 获取表单值
        date_str = self.add_date.get_value()
        entry_type = self.add_type.get()
        category = self.add_category.get_value()
        amount_str = self.add_amount.get_value()
        note = self.add_note.get_value()

        # 校验金额
        ok, amount = validate_amount(amount_str)
        if not ok:
            show_error("输入错误", f"金额格式不正确：'{amount_str}'\n请输入正数，最多两位小数。")
            return

        # 构建对象
        entries = self.storage.load_all()
        new_id = self.storage.get_next_id(entries)

        entry = BillEntry(
            id=new_id, date=date_str, type=entry_type,
            category=category, amount=amount, note=note,
        )

        # 校验
        valid, msg = entry.validate()
        if not valid:
            show_error("数据错误", msg)
            return

        # 保存
        entries.append(entry)
        if self.storage.save_all(entries):
            show_info("成功", f"已记录！编号: {new_id}")
            self._clear_add_form()
            self._refresh_list()  # 刷新流水表格
        else:
            show_error("错误", "保存失败，请检查磁盘空间或文件权限。")

    def _clear_add_form(self):
        """清空记账表单"""
        self.add_date.set_value(get_today())
        self.add_type.set(TYPE_EXPENSE)
        self._on_type_change()
        self.add_amount.clear()
        self.add_note.clear()

    # ==============================================================
    # 标签页 2：收支流水
    # ==============================================================

    def _build_list_tab(self):
        """构建"收支流水"标签页"""
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="  收支流水  ")

        # 顶部统计栏
        stats_frame = ttk.Frame(tab)
        stats_frame.pack(fill="x", pady=(0, 10))

        self.list_income_card = StatsCard(stats_frame, title="收入合计", value="+0.00")
        self.list_income_card.pack(side="left", padx=(0, 10))

        self.list_expense_card = StatsCard(stats_frame, title="支出合计", value="-0.00")
        self.list_expense_card.pack(side="left", padx=(0, 10))

        self.list_balance_card = StatsCard(stats_frame, title="结余", value="0.00")
        self.list_balance_card.pack(side="left")

        # 刷新按钮
        ttk.Button(
            stats_frame, text="刷新", bootstyle="info-outline",
            command=self._refresh_list
        ).pack(side="right")

        # 数据表格
        self.list_table = DataTable(tab, columns=TABLE_COLUMNS)
        self.list_table.pack(fill="both", expand=True)

        # 底部操作栏
        action_frame = ttk.Frame(tab)
        action_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(
            action_frame, text="删除选中记录", bootstyle="danger-outline",
            command=self._on_delete_entry
        ).pack(side="left")

        self.list_count_label = ttk.Label(action_frame, text="共 0 条记录", font=get_font("small"))
        self.list_count_label.pack(side="right")

    def _refresh_list(self):
        """刷新流水表格数据"""
        entries = self.storage.load_all()
        self.list_table.load_data(entries)

        # 计算统计
        total_income = sum(e.amount for e in entries if e.type == TYPE_INCOME)
        total_expense = sum(e.amount for e in entries if e.type == TYPE_EXPENSE)
        balance = total_income - total_expense

        self.list_income_card.update_value(f"+{format_amount(total_income)}", COLOR_SUCCESS)
        self.list_expense_card.update_value(f"-{format_amount(total_expense)}", COLOR_DANGER)
        balance_color = COLOR_SUCCESS if balance >= 0 else COLOR_DANGER
        balance_sign = "+" if balance >= 0 else ""
        self.list_balance_card.update_value(f"{balance_sign}{format_amount(balance)}", balance_color)
        self.list_count_label.config(text=f"共 {len(entries)} 条记录")

    def _on_delete_entry(self):
        """删除选中的记录"""
        entry_id = self.list_table.get_selected_id()
        if entry_id is None:
            show_info("提示", "请先选中要删除的记录。")
            return

        if not show_confirm("确认删除", f"确定要删除编号 {entry_id} 的记录吗？\n删除前会自动备份。"):
            return

        # 备份
        self.storage.backup()

        # 删除
        entries = self.storage.load_all()
        entries = [e for e in entries if e.id != entry_id]

        if self.storage.save_all(entries):
            show_info("成功", f"已删除编号 {entry_id} 的记录。")
            self._refresh_list()
        else:
            show_error("错误", "删除失败，请从备份恢复。")

    # ==============================================================
    # 标签页 3：月度统计
    # ==============================================================

    def _build_stats_tab(self):
        """构建"月度统计"标签页"""
        tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(tab, text="  月度统计  ")

        # 标题
        ttk.Label(tab, text="月度收支统计", font=get_font("title", "bold")).pack(
            anchor="w", pady=(0, 16)
        )

        # 年月选择器
        selector_frame = ttk.Frame(tab)
        selector_frame.pack(fill="x", pady=(0, 16))

        ttk.Label(selector_frame, text="年份:", font=get_font("body")).pack(side="left")
        current_year = datetime.now().year
        self.stats_year = ttk.Combobox(
            selector_frame, state="readonly", width=6,
            values=[str(y) for y in range(current_year - 5, current_year + 2)]
        )
        self.stats_year.set(str(current_year))
        self.stats_year.pack(side="left", padx=(4, 16))

        ttk.Label(selector_frame, text="月份:", font=get_font("body")).pack(side="left")
        self.stats_month = ttk.Combobox(
            selector_frame, state="readonly", width=4,
            values=[str(m) for m in range(1, 13)]
        )
        self.stats_month.set(str(datetime.now().month))
        self.stats_month.pack(side="left", padx=(4, 16))

        ttk.Button(
            selector_frame, text="查询", bootstyle="primary",
            command=self._on_query_stats
        ).pack(side="left")

        # 统计卡片
        stats_cards_frame = ttk.Frame(tab)
        stats_cards_frame.pack(fill="x", pady=(0, 16))

        self.stats_income_card = StatsCard(stats_cards_frame, title="收入合计", value="+0.00")
        self.stats_income_card.pack(side="left", padx=(0, 10))

        self.stats_expense_card = StatsCard(stats_cards_frame, title="支出合计", value="-0.00")
        self.stats_expense_card.pack(side="left", padx=(0, 10))

        self.stats_balance_card = StatsCard(stats_cards_frame, title="月度结余", value="0.00")
        self.stats_balance_card.pack(side="left")

        # 分类汇总表格
        self.stats_table = DataTable(tab, columns={
            "category": {"text": "分类", "width": 120, "anchor": "center"},
            "count":    {"text": "笔数", "width": 80,  "anchor": "center"},
            "amount":   {"text": "金额", "width": 120, "anchor": "e"},
        })
        self.stats_table.pack(fill="both", expand=True)

    def _on_query_stats(self):
        """查询指定月份的统计数据"""
        try:
            year = int(self.stats_year.get())
            month = int(self.stats_month.get())
        except ValueError:
            show_error("错误", "请选择有效的年月。")
            return

        start, end = get_month_range(year, month)
        entries = self.storage.load_all()
        month_entries = [e for e in entries if start <= e.date <= end]

        if not month_entries:
            self.stats_table.clear()
            self.stats_income_card.update_value("+0.00")
            self.stats_expense_card.update_value("-0.00")
            self.stats_balance_card.update_value("0.00")
            show_info("提示", f"{year}年{month}月暂无记录。")
            return

        # 按分类汇总
        income_by_cat: dict[str, tuple[int, float]] = {}
        expense_by_cat: dict[str, tuple[int, float]] = {}

        for entry in month_entries:
            if entry.type == TYPE_INCOME:
                count, amt = income_by_cat.get(entry.category, (0, 0.0))
                income_by_cat[entry.category] = (count + 1, amt + entry.amount)
            else:
                count, amt = expense_by_cat.get(entry.category, (0, 0.0))
                expense_by_cat[entry.category] = (count + 1, amt + entry.amount)

        total_income = sum(amt for _, amt in income_by_cat.values())
        total_expense = sum(amt for _, amt in expense_by_cat.values())
        balance = total_income - total_expense

        # 更新统计卡片
        self.stats_income_card.update_value(f"+{format_amount(total_income)}", COLOR_SUCCESS)
        self.stats_expense_card.update_value(f"-{format_amount(total_expense)}", COLOR_DANGER)
        balance_color = COLOR_SUCCESS if balance >= 0 else COLOR_DANGER
        balance_sign = "+" if balance >= 0 else ""
        self.stats_balance_card.update_value(f"{balance_sign}{format_amount(balance)}", balance_color)

        # 构建表格数据（使用简单对象模拟 BillEntry 的 display 接口）
        class StatsRow:
            def __init__(self, cat, count, amt, entry_type):
                self.id = 0
                self.date = f"{'收入' if entry_type == TYPE_INCOME else '支出'}"
                self.type = entry_type
                self.category = cat
                self.amount = amt
                self.note = f"{count} 笔"

        rows = []
        for cat, (count, amt) in sorted(income_by_cat.items(), key=lambda x: -x[1][1]):
            rows.append(StatsRow(cat, count, amt, TYPE_INCOME))
        for cat, (count, amt) in sorted(expense_by_cat.items(), key=lambda x: -x[1][1]):
            rows.append(StatsRow(cat, count, amt, TYPE_EXPENSE))

        self.stats_table.load_data(rows)

    # ==============================================================
    # 标签页 4：设置
    # ==============================================================

    def _build_settings_tab(self):
        """构建"设置"标签页"""
        tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(tab, text="  设置  ")

        # 标题
        ttk.Label(tab, text="界面设置", font=get_font("title", "bold")).pack(
            anchor="w", pady=(0, 20)
        )

        # 主题选择
        theme_frame = ttk.Frame(tab)
        theme_frame.pack(fill="x", pady=5)
        ttk.Label(theme_frame, text="主题:", width=10, anchor="e").pack(side="left", padx=(0, 8))

        available_themes = [
            "cosmo", "litera", "flatly", "journal", "lumen", "minty",
            "pulse", "sandstone", "united", "yeti", "morph", "simple",
            "cerculean", "darkly", "superhero", "solar", "cyborg", "vapor",
        ]
        self.settings_theme = ttk.Combobox(
            theme_frame, state="readonly", values=available_themes, width=15
        )
        self.settings_theme.set(THEME_NAME)
        self.settings_theme.pack(side="left")

        # 字体族
        font_frame = ttk.Frame(tab)
        font_frame.pack(fill="x", pady=5)
        ttk.Label(font_frame, text="字体:", width=10, anchor="e").pack(side="left", padx=(0, 8))

        import tkinter.font as tkfont
        available_fonts = sorted(set(tkfont.families()))
        self.settings_font = ttk.Combobox(
            font_frame, state="readonly", values=available_fonts, width=20
        )
        self.settings_font.set(get_font("body")[0])
        self.settings_font.pack(side="left")

        # 字号
        size_frame = ttk.Frame(tab)
        size_frame.pack(fill="x", pady=5)
        ttk.Label(size_frame, text="字号:", width=10, anchor="e").pack(side="left", padx=(0, 8))

        self.settings_font_size = ttk.Scale(
            size_frame, from_=10, to=24, value=get_font("body")[1],
            bootstyle="info"
        )
        self.settings_font_size.pack(side="left", fill="x", expand=True)

        self.size_label = ttk.Label(size_frame, text=str(int(get_font("body")[1])), width=4)
        self.size_label.pack(side="left", padx=(8, 0))
        self.settings_font_size.configure(command=lambda v: self.size_label.config(text=str(int(float(v)))))

        # 预览区域
        preview_frame = ttk.Labelframe(tab, text="预览", padding=16)
        preview_frame.pack(fill="x", pady=(20, 0))

        self.preview_label = ttk.Label(
            preview_frame,
            text="这是预览文字 - AaBbCc 123 收入 支出 餐饮 工资",
            font=get_font("body"),
        )
        self.preview_label.pack(anchor="w")

        # 应用按钮
        ttk.Button(
            tab, text="应用设置", bootstyle="primary",
            command=self._on_apply_settings
        ).pack(anchor="w", pady=(20, 0))

    def _on_apply_settings(self):
        """应用界面设置"""
        import tkinter.font as tkfont

        new_theme = self.settings_theme.get()
        new_font_family = self.settings_font.get()
        new_font_size = int(float(self.settings_font_size.get()))

        # 更新预览
        self.preview_label.config(font=(new_font_family, new_font_size))

        # 提示用户需要重启
        show_info(
            "设置已应用",
            f"字体: {new_font_family}\n字号: {new_font_size}\n"
            f"主题切换需要重启程序才能完全生效。\n"
            f"字体和字号变更已立即应用到预览区。"
        )

    # ==============================================================
    # 启动
    # ==============================================================

    def run(self):
        """启动应用主循环"""
        # 初始加载流水数据
        self._refresh_list()
        self.root.mainloop()


def main():
    """程序入口"""
    app = AccountApp()
    app.run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 验证 GUI 可启动**

Run: `cd C:/Users/Administrator/Documents/test_2_CC_2026_5_15 && python -c "from gui import AccountApp; print('gui.py import OK')"`
Expected: `gui.py import OK`

- [ ] **Step 3: Commit**

```bash
git add gui.py
git commit -m "feat: add gui.py main GUI entry with 4 tabs"
```

---

### Task 4: 更新 requirements.txt 和 README.md

**Files:**
- Modify: `requirements.txt`
- Modify: `README.md`

- [ ] **Step 1: 更新 requirements.txt**

将内容替换为：

```
# 个人记账本 - 依赖清单
#
# Python 3.10+ 标准库 + ttkbootstrap GUI 主题框架

python>=3.10
ttkbootstrap>=1.10
```

- [ ] **Step 2: 更新 README.md**

将内容替换为：

```markdown
# 个人记账本 v1.0

桌面 GUI 收支管理工具，基于 tkinter + ttkbootstrap。

## 运行方式

```bash
# 安装依赖
pip install ttkbootstrap

# 启动 GUI 版本
python gui.py

# 启动 CLI 版本（保留）
python main.py
```

要求 Python 3.10+。

## 功能

- 记录收入 / 支出
- 查看全部流水（带颜色区分）
- 月度分类统计
- 删除记录（带自动备份）
- 主题与字体定制

## 工程结构

```
├── main.py           # CLI 入口（保留）
├── gui.py            # GUI 入口（主程序）
├── ui_components.py  # 可复用 UI 组件
├── theme.py          # 样式/字体配置（调 UI 改这里）
├── config.py         # 全局配置、常量
├── models.py         # 数据模型
├── storage.py        # 数据持久化
├── utils.py          # 工具函数
├── accounts.json     # 数据文件（自动生成）
├── requirements.txt  # 依赖清单
└── README.md         # 本文件
```

## UI 定制

修改 `theme.py` 可调整：
- 字体族、字号
- 颜色方案
- ttkbootstrap 主题
- 窗口尺寸

或在程序内"设置"标签页实时调整。
```

- [ ] **Step 3: Commit**

```bash
git add requirements.txt README.md
git commit -m "docs: update requirements and README for GUI version"
```

---

### Task 5: 安装依赖并验证完整运行

**Files:**
- None (verification only)

- [ ] **Step 1: 安装 ttkbootstrap**

Run: `pip install ttkbootstrap`
Expected: Successfully installed ttkbootstrap

- [ ] **Step 2: 验证所有模块导入**

Run: `cd C:/Users/Administrator/Documents/test_2_CC_2026_5_15 && python -c "import config; import models; import utils; import storage; import theme; import ui_components; from gui import AccountApp; print('All modules OK')"`
Expected: `All modules OK`

- [ ] **Step 3: 启动 GUI 并手动验证**

Run: `cd C:/Users/Administrator/Documents/test_2_CC_2026_5_15 && python gui.py`

手动验证清单：
- [ ] 窗口正常显示，4 个标签页可见
- [ ] 记一笔：切换收入/支出，分类下拉自动更新，保存一条记录成功
- [ ] 收支流水：表格显示记录，收入绿色/支出红色，统计数字正确
- [ ] 月度统计：查询当月数据，分类汇总正确
- [ ] 设置：主题下拉、字体选择、字号滑块可用
- [ ] 关闭窗口程序正常退出

- [ ] **Step 4: Commit (if any fixes needed)**

```bash
git add -A
git commit -m "fix: GUI verification fixes"
```
