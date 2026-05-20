# -*- coding: utf-8 -*-
"""
ui_components.py - 可复用 UI 组件

将常用的界面元素封装为独立组件，供 gui.py 中的各标签页复用。
每个组件都是一个 ttk.Frame 的子类，可以像积木一样拼装。
"""

import tkinter as tk
from tkinter import messagebox, Menu
import ttkbootstrap as ttk

from config import TYPE_INCOME
from utils import format_amount
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
            self.widget = ttk.Combobox(self, state=kwargs.pop("state", "readonly"), **kwargs)
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

    def __init__(self, parent, columns: dict, delete_callback=None, **kwargs):
        """
        参数:
            parent:          父容器
            columns:         列定义字典，格式见 theme.TABLE_COLUMNS
            delete_callback: 右键删除回调函数，接收 entry_id (int)；
                             为 None 时不启用右键菜单
        """
        super().__init__(parent, **kwargs)

        self.columns_def = columns
        self._delete_callback = delete_callback
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

        # 右键删除菜单（仅在传入 delete_callback 时启用）
        if self._delete_callback is not None:
            self.tree.bind("<Button-3>", self._show_context_menu)

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

    def _show_context_menu(self, event):
        """
        右键点击表格行时弹出上下文菜单。

        【流程】
        ① 识别鼠标位置对应的行
        ② 若该行有数据，弹出菜单，菜单项"删除此记录"触发 delete_callback
        """
        # 识别鼠标位置对应的行
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return  # 点在空白区域，不弹菜单

        # 选中该行（视觉反馈）
        self.tree.selection_set(row_id)

        # 构建右键菜单
        menu = Menu(self.tree, tearoff=0)
        menu.add_command(
            label="删除此记录",
            command=lambda: self._on_context_delete(row_id),
        )
        # 在鼠标位置弹出菜单
        menu.post(event.x_root, event.y_root)

    def _on_context_delete(self, tree_item_id):
        """右键菜单"删除此记录"的回调，将 tree_item_id 转换为账单 entry_id 后调用回调"""
        entry_id = self._id_map.get(tree_item_id)
        if entry_id is not None and self._delete_callback is not None:
            self._delete_callback(entry_id)


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
        """更新数值显示。不传 color 时恢复默认前景色。"""
        self.value_label.config(text=value)
        if color:
            self.value_label.config(foreground=color)
        else:
            self.value_label.config(foreground="")


def show_confirm(title: str, message: str) -> bool:
    """弹出确认对话框，返回用户是否确认"""
    return messagebox.askyesno(title, message)


def show_info(title: str, message: str):
    """弹出信息提示框"""
    messagebox.showinfo(title, message)


def show_error(title: str, message: str):
    """弹出错误提示框"""
    messagebox.showerror(title, message)
