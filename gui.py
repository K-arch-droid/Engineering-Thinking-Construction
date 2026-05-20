# -*- coding: utf-8 -*-
"""
gui.py - GUI 主入口（数据流的起点：用户操作从这里开始）

===================================================================
【数据流全景 —— 以"记一笔"为例】
===================================================================

    用户在界面填写日期、类型、分类、金额、备注
        ↓
    点击"保存"按钮
        ↓
    gui.py::_on_save_entry()          ← 数据流从这里启动
        ↓ ① 从界面控件取值（字符串）
        ↓ ② 调 utils.validate_amount() 校验金额格式
        ↓ ③ 调 storage.load_all() 从磁盘加载现有数据
        ↓ ④ 构造 BillEntry 对象（models.py）
        ↓ ⑤ 调 entry.validate() 校验业务规则
        ↓ ⑥ 把新记录追加到列表
        ↓ ⑦ 调 storage.save_all() 写回磁盘
        ↓
    accounts.json 文件更新完成
        ↓
    刷新界面显示

===================================================================
【工程思维：gui.py 是"薄控制器"】
===================================================================
gui.py 不做任何业务计算（金额求和、分类统计除外，这些是展示逻辑）。
它只负责：
    - 把用户输入传给模型层
    - 把结果显示到界面
    - 协调各模块的调用顺序

这叫"薄控制器"——界面层越薄，程序越容易维护和测试。
如果把业务逻辑写在 gui.py 里，将来要加 Web 版本就得重写一遍。
===================================================================

启动方式: python gui.py
"""

# ============================================================
# 导入依赖 —— 体现了模块之间的依赖关系
# ============================================================

import tkinter as tk                    # Python 内置的 GUI 库
import tkinter.font as tkfont           # 字体管理
from tkinter import messagebox          # 弹窗对话框（关闭确认等）
from datetime import datetime
import os
import subprocess
import sys
import ttkbootstrap as ttk              # tkinter 的美化主题库（第三方）

# 从 config 导入常量（配置层）
from config import (
    TYPE_INCOME, TYPE_EXPENSE,
    INCOME_CATEGORIES, EXPENSE_CATEGORIES,
    get_resource_path,
)
# 从 models 导入数据模型（模型层）
from models import BillEntry
# 从 storage 导入存储管理器（持久化层）
from storage import Storage
# 从 utils 导入工具函数（工具层）
from utils import (
    get_today, validate_amount, format_amount,
    get_month_range,
)
# 从 theme 导入样式配置（样式层）
import theme
from theme import (
    THEME_NAME, WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT,
    WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT, TABLE_COLUMNS,
    THEME_GROUPS, THEME_NAME_MAP, THEME_PRESETS, PRESET_NAMES,
    get_font, apply_theme, apply_preset, apply_preset_to_root,
    load_settings, save_settings,
    COLOR_SUCCESS, COLOR_DANGER, COLOR_PRIMARY,
)
# 从 ui_components 导入可复用 UI 组件（组件层）
from ui_components import (
    FormRow, DataTable, StatsCard,
    show_confirm, show_info, show_error,
)


class _StatsRow:
    """
    月度统计表格的行数据适配器。

    【为什么需要这个类？】
    月度统计表格复用了 DataTable 组件，但 DataTable 期望的数据格式是
    有 id、date、type、category、amount、note 字段的对象。
    统计数据（分类、笔数、金额）不是 BillEntry，所以需要一个"适配器"
    把统计数据包装成 DataTable 能识别的格式。

    这就是"适配器模式"——让两个接口不匹配的模块能够协作。
    """
    def __init__(self, cat: str, count: int, amt: float, entry_type: str):
        self.id = 0
        self.date = "收入" if entry_type == TYPE_INCOME else "支出"
        self.type = entry_type
        self.category = cat
        self.amount = amt
        self.note = f"{count} 笔"


class AccountApp:
    """
    记账本 GUI 应用主类 —— 整个程序的"总指挥"。

    【职责】
        1. 创建和配置主窗口
        2. 管理 4 个标签页（记一笔、收支流水、月度统计、设置）
        3. 协调 UI 事件与 Storage / Models 的交互

    【设计模式：MVC 的简化版】
    - Model（模型）= models.py + storage.py（数据和持久化）
    - View（视图）= ui_components.py + theme.py（界面组件和样式）
    - Controller（控制器）= AccountApp 类（事件处理和流程协调）

    AccountApp 不做业务计算，只负责"把用户操作翻译成对模型层的调用"。
    """

    def __init__(self):
        # ---- 第一步：加载用户设置 ----
        # 从 settings.json 读取字体、主题等配置，更新 theme.py 模块变量
        self._settings = load_settings()

        # ---- 第二步：创建主窗口 ----
        # ttkbootstrap 的 Window 类是 tkinter.Tk 的美化版
        self.root = ttk.Window(
            title=WINDOW_TITLE,           # 窗口标题（来自 theme.py）
            themename=THEME_NAME,         # 主题名（来自 theme.py，已加载用户设置）
            size=(WINDOW_WIDTH, WINDOW_HEIGHT),           # 初始尺寸
            minsize=(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT), # 最小尺寸
        )

        # 窗口居中显示
        self.root.place_window_center()

        # ---- 第三步：注入全局样式 ----
        self.style = ttk.Style()
        apply_theme(self.style)  # 把 theme.py 中定义的颜色、字体应用到全局

        # 如果上次保存了预设，启动时立即应用（让深色/护眼模式立即生效）
        saved_preset = self._settings.get("preset", "")
        if saved_preset and saved_preset in THEME_PRESETS:
            apply_preset(saved_preset, self.style)

        # ---- 第四步：创建存储管理器 ----
        # 这一行会自动确保 accounts.json 存在（Storage.__init__ 中调用 _ensure_file）
        self.storage = Storage()

        # ---- 第五步：初始化缓冲数据 ----
        # 内存工作副本：所有增删操作只修改此列表，关闭时统一写盘
        self._entries: list[BillEntry] = []
        # 撤回栈：保存本次运行期间被删除的记录，支持撤回操作
        self._undo_stack: list[BillEntry] = []
        # 标记是否有未保存的改动（用于关闭时弹出保存确认）
        self._has_changes = False

        # ---- 第六步：构建界面 ----
        self._build_ui()

        # ---- 第七步：注册窗口关闭事件 ----
        # 拦截窗口关闭按钮，弹出保存确认对话框
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        """
        构建主界面：菜单栏 + 标签页容器 + 4 个标签页。

        【界面结构】
        主窗口 (root)
            ├── 菜单栏 (menubar)
            │   └── 帮助 → 打开文档 / 关于
            └── 标签页容器 (notebook)
                ├── 标签页1：记一笔    → _build_add_tab()
                ├── 标签页2：收支流水  → _build_list_tab()
                ├── 标签页3：月度统计  → _build_stats_tab()
                └── 标签页4：设置      → _build_settings_tab()
        """
        # ---- 菜单栏 ----
        self._build_menubar()

        # ttk.Notebook = 标签页容器（类似浏览器的多标签）
        self.notebook = ttk.Notebook(self.root, bootstyle="primary")
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # 依次构建 4 个标签页
        self._build_add_tab()      # 记一笔
        self._build_list_tab()     # 收支流水
        self._build_stats_tab()    # 月度统计
        self._build_settings_tab() # 设置

    def _build_menubar(self):
        """
        构建菜单栏：帮助 → 打开学习文档 / 关于。

        【tkinter 菜单系统的结构】
        菜单栏的层级关系：
            Menu (菜单栏)             ← 水平的那一行
              └── Menu (下拉菜单)     ← 点击后弹出的垂直列表
                    ├── add_command   ← 可点击的菜单项
                    ├── add_separator ← 分隔线
                    └── add_command

        Menu(menubar, tearoff=0) 的 tearoff=0 表示：
          禁用"撕下"功能（tearoff 是 tkinter 的古老特性，
          允许用户把菜单"撕下来"变成独立窗口，现代程序都不用它）。

        add_cascade(label="帮助", menu=help_menu) 的意思是：
          在菜单栏上添加一个"帮助"按钮，点击后展开 help_menu 子菜单。
        """
        # 创建顶级菜单栏（水平的那一行）
        menubar = tk.Menu(self.root)

        # ---- 帮助菜单（下拉菜单）----
        help_menu = tk.Menu(menubar, tearoff=0)

        # add_command：添加可点击的菜单项
        #   label   = 显示文字
        #   command = 点击时调用的函数（回调函数）
        #   ⚠️ 注意：command=self._open_file("xxx") 是错误写法！
        #      这样会立即执行函数，把返回值赋给 command。
        #      正确写法是传函数引用：command=self._open_doc_code_guide
        help_menu.add_command(label="📖 文件分类指南", command=self._open_doc_file_guide)
        help_menu.add_command(label="📖 代码阅读目录", command=self._open_doc_code_guide)
        help_menu.add_command(label="📖 UI 交互逻辑", command=self._open_doc_ui_logic)
        help_menu.add_command(label="📖 exe 运行原理", command=self._open_doc_exe_principle)
        help_menu.add_command(label="📖 更新日志", command=self._open_doc_changelog)
        help_menu.add_command(label="📖 README", command=self._open_doc_readme)

        # add_separator：在菜单中添加一条分隔线（视觉分组）
        help_menu.add_separator()

        help_menu.add_command(label="📂 打开学习资料目录", command=self._open_docs_folder)

        help_menu.add_separator()
        help_menu.add_command(label="关于", command=self._show_about)

        # add_cascade：把 help_menu 作为"帮助"的子菜单挂到菜单栏上
        menubar.add_cascade(label="帮助", menu=help_menu)

        # root.config(menu=menubar)：把菜单栏绑定到主窗口
        self.root.config(menu=menubar)

    def _open_file(self, relative_path):
        """
        用系统默认程序打开指定文件。

        【跨平台打开文件的三种方式】
        不同操作系统打开文件的命令不同：
          Windows : os.startfile(filepath)       —— 内置函数，最简单
          macOS   : subprocess(["open", filepath]) —— shell 命令 "open"
          Linux   : subprocess(["xdg-open", filepath]) —— FreeDesktop 标准

        sys.platform 的值：
          "win32"  = Windows
          "darwin" = macOS
          "linux"  = Linux

        get_resource_path() 会把相对路径转为打包后的绝对路径：
          开发时："code阅读目录.txt" → "C:/项目/code阅读目录.txt"
          打包后："code阅读目录.txt" → "dist/个人记账本/_internal/code阅读目录.txt"
        """
        filepath = get_resource_path(relative_path)
        if not os.path.exists(filepath):
            show_error("文件不存在", f"找不到文件：\n{filepath}")
            return
        try:
            if sys.platform == "win32":
                os.startfile(filepath)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", filepath])
            else:
                subprocess.Popen(["xdg-open", filepath])
        except Exception as e:
            show_error("打开失败", f"无法打开文件：\n{e}")

    # ---- 以下函数是菜单项的回调 ----
    # 为什么每个菜单项单独一个函数，而不是直接 lambda？
    # 因为 add_command 的 command 参数只能传"无参数的可调用对象"。
    # 如果用 lambda：command=lambda: self._open_file("xxx")
    # 这样写也行，但单独的函数更清晰，也方便调试（堆栈里能看到函数名）。

    def _open_doc_file_guide(self):
        """菜单项回调：打开"文件分类指南.txt"。"""
        self._open_file("文件分类指南.txt")

    def _open_doc_code_guide(self):
        """菜单项回调：打开"代码阅读目录.txt"。"""
        self._open_file("code阅读目录.txt")

    def _open_doc_exe_principle(self):
        """菜单项回调：打开"exe运行原理.txt"。"""
        self._open_file("exe运行原理.txt")

    def _open_doc_ui_logic(self):
        """菜单项回调：打开"UI交互逻辑.txt"。"""
        self._open_file("UI交互逻辑.txt")

    def _open_doc_changelog(self):
        """菜单项回调：打开"更新日志.txt"。"""
        self._open_file("更新日志.txt")

    def _open_doc_readme(self):
        """菜单项回调：打开"README.md"。"""
        self._open_file("README.md")

    def _open_docs_folder(self):
        """用资源管理器打开 docs/ 学习资料目录。

        【os.startfile() vs subprocess.Popen()】
        打开文件用 os.startfile()（Windows 内置）。
        打开目录也用 os.startfile()——它会调用资源管理器。
        subprocess.Popen() 是更通用的方式，但需要知道系统命令。
        """
        folder = get_resource_path("docs")
        if not os.path.isdir(folder):
            show_error("目录不存在", f"找不到目录：\n{folder}")
            return
        try:
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            show_error("打开失败", f"无法打开目录：\n{e}")

    def _show_about(self):
        """弹窗显示关于信息。"""
        messagebox.showinfo(
            "关于",
            "个人记账本 v1.6\n\n"
            "一个基于 Python + tkinter 的收支管理工具\n\n"
            "功能特色：\n"
            "  · 记账 / 流水 / 统计 / 主题设置\n"
            "  · 缓冲保存，关闭时统一写盘\n"
            "  · 多主题预设（护眼 / 深色 / 默认）\n\n"
            "技术栈：Python 3.10+ / ttkbootstrap",
        )

    # ==============================================================
    # 标签页 1：记一笔 —— 数据流的起点
    # ==============================================================

    def _build_add_tab(self):
        """
        构建"记一笔"标签页。

        【界面上有这些输入控件】
        - 日期（文本框，默认今天）
        - 类型（单选按钮：收入 / 支出）
        - 分类（下拉框，选项随类型切换）
        - 金额（文本框）
        - 备注（文本框）
        - 保存按钮（点击后触发 _on_save_entry）
        """
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
        """
        收支类型切换时，更新分类下拉选项（按使用频率排序）。

        【排序逻辑】
        统计 self._entries 中各分类的使用次数，按频率降序排列。
        "其他"始终排在最后（兜底选项不应出现在最前面）。
        """
        entry_type = self.add_type.get()
        default_cats = INCOME_CATEGORIES if entry_type == TYPE_INCOME else EXPENSE_CATEGORIES

        # 统计当前工作副本中各分类的使用次数
        freq: dict[str, int] = {}
        for e in self._entries:
            if e.type == entry_type:
                freq[e.category] = freq.get(e.category, 0) + 1

        # 按频率降序排列，"其他"始终排在最后
        sorted_cats = sorted(
            default_cats,
            key=lambda c: (c == "其他", -freq.get(c, 0)),
        )

        self.add_category.widget["values"] = sorted_cats
        self.add_category.set_value(sorted_cats[0])

    def _on_save_entry(self):
        """
        保存一条收支记录 —— 这是整个程序最核心的数据流方法。

        【完整数据流，每一步都有注释】
        用户点击"保存" → 取值 → 校验 → 构造对象 → 追加到内存工作副本 → 刷新界面

        【缓冲保存模式】
        新记录只追加到 self._entries（内存工作副本），不立即写盘。
        用户关闭程序时会弹出确认对话框，选择"保存"才写入磁盘。
        """
        # ---- 第一步：从界面控件取值（都是字符串） ----
        date_str = self.add_date.get_value()    # 日期文本框
        entry_type = self.add_type.get()         # "income" 或 "expense"
        category = self.add_category.get_value() # 下拉框选中的分类
        amount_str = self.add_amount.get_value() # 金额文本框（字符串）
        note = self.add_note.get_value()         # 备注文本框

        # ---- 第二步：校验金额格式（调 utils.py 的纯函数） ----
        # validate_amount 会检查：是不是数字？> 0？最多两位小数？
        ok, amount = validate_amount(amount_str)
        if not ok:
            show_error("输入错误", f"金额格式不正确：'{amount_str}'\n请输入正数，最多两位小数。")
            return  # 校验失败，提前返回，不往下走

        # ---- 第三步：从内存工作副本计算新编号 ----
        new_id = self.storage.get_next_id(self._entries)

        # ---- 第四步：构造 BillEntry 对象（调 models.py） ----
        entry = BillEntry(
            id=new_id, date=date_str, type=entry_type,
            category=category, amount=amount, note=note,
        )

        # ---- 第五步：校验业务规则（调 models.py 的 validate） ----
        # 检查：日期格式对不对？类型合不合法？金额是不是正数？分类空不空？
        valid, msg = entry.validate()
        if not valid:
            show_error("数据错误", msg)
            return  # 校验失败，提前返回

        # ---- 第六步：追加到内存工作副本（不写盘，关闭时统一保存） ----
        self._entries.append(entry)
        self._has_changes = True  # 标记有未保存的改动
        show_info("成功", f"已记录！编号: {new_id}")
        self._clear_add_form()   # 清空表单，方便记下一笔
        self._refresh_list()     # 刷新"收支流水"标签页的表格

    def _clear_add_form(self):
        """
        清空记账表单，恢复到初始状态。
        保存成功后调用，方便用户立即记下一笔账。
        """
        self.add_date.set_value(get_today())  # 日期重置为今天
        self.add_type.set(TYPE_EXPENSE)       # 类型重置为"支出"
        self._on_type_change()                # 分类列表跟着切换
        self.add_amount.clear()               # 清空金额
        self.add_note.clear()                 # 清空备注

    # ==============================================================
    # 标签页 2：收支流水 —— 展示所有记录 + 删除功能
    # ==============================================================

    def _build_list_tab(self):
        """
        构建"收支流水"标签页。

        【界面结构】
        顶部：三个统计卡片（收入合计、支出合计、结余）
        中部：数据表格（显示所有账单记录）
        底部：删除按钮 + 记录计数
        """
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

        # 数据表格（传入 delete_callback 启用右键删除菜单）
        self.list_table = DataTable(
            tab, columns=TABLE_COLUMNS,
            delete_callback=self._on_delete_entry,
        )
        self.list_table.pack(fill="both", expand=True)

        # 底部操作栏
        action_frame = ttk.Frame(tab)
        action_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(
            action_frame, text="删除选中记录", bootstyle="danger-outline",
            command=self._on_delete_entry
        ).pack(side="left")

        # 撤回删除按钮（初始禁用，有删除记录时启用）
        self.undo_btn = ttk.Button(
            action_frame, text="撤回删除", bootstyle="warning-outline",
            command=self._on_undo_delete, state="disabled",
        )
        self.undo_btn.pack(side="left", padx=(10, 0))

        self.list_count_label = ttk.Label(action_frame, text="共 0 条记录", font=get_font("small"))
        self.list_count_label.pack(side="right")

    def _refresh_list(self):
        """
        刷新流水表格数据 —— 从内存工作副本读取并更新界面。

        【调用时机】
        - 程序启动时（run() 中调用）
        - 保存新记录后（_on_save_entry 中调用）
        - 删除记录后（_on_delete_entry 中调用）
        - 撤回删除后（_on_undo_delete 中调用）
        - 用户点击"刷新"按钮

        【数据流】
        self._entries（内存工作副本）
            → load_data() 填充表格
            → 计算收入/支出/结余 → 更新统计卡片
        """
        # 从内存工作副本读取（不从磁盘加载，避免覆盖未保存的改动）
        entries = self._entries

        # 把数据填充到表格组件
        self.list_table.load_data(entries)

        # 计算统计数据（列表推导式，一行搞定）
        total_income = sum(e.amount for e in entries if e.type == TYPE_INCOME)
        total_expense = sum(e.amount for e in entries if e.type == TYPE_EXPENSE)
        balance = total_income - total_expense

        # 更新顶部的三个统计卡片
        self.list_income_card.update_value(f"+{format_amount(total_income)}", COLOR_SUCCESS)
        self.list_expense_card.update_value(f"-{format_amount(total_expense)}", COLOR_DANGER)
        balance_color = COLOR_SUCCESS if balance >= 0 else COLOR_DANGER
        balance_sign = "+" if balance >= 0 else ""
        self.list_balance_card.update_value(f"{balance_sign}{format_amount(balance)}", balance_color)
        self.list_count_label.config(text=f"共 {len(entries)} 条记录")

    def _on_delete_entry(self, entry_id: int = None):
        """
        删除一条记录 —— 从内存工作副本中移除，压入撤回栈。

        【缓冲删除模式】
        不立即写盘，仅修改内存工作副本 self._entries。
        被删记录压入 self._undo_stack，用户可通过"撤回删除"按钮恢复。
        用户关闭程序时弹出确认对话框，选择"保存"才将删除结果写入磁盘。

        参数:
            entry_id: 要删除的记录编号；为 None 时从表格选中行获取
        """
        # ① 确定要删除的记录编号（支持右键菜单传入和按钮选中两种方式）
        if entry_id is None:
            entry_id = self.list_table.get_selected_id()
        if entry_id is None:
            show_info("提示", "请先选中要删除的记录。")
            return

        # ② 二次确认（防误删）
        if not show_confirm("确认删除", f"确定要删除编号 {entry_id} 的记录吗？\n可通过「撤回删除」按钮恢复。"):
            return

        # ③ 从内存工作副本中找到并移除目标记录，压入撤回栈
        deleted_entry = None
        remaining = []
        for e in self._entries:
            if e.id == entry_id:
                deleted_entry = e
            else:
                remaining.append(e)

        if deleted_entry is None:
            show_info("提示", f"未找到编号 {entry_id} 的记录。")
            return

        # ④ 更新工作副本和撤回栈
        self._entries = remaining
        self._undo_stack.append(deleted_entry)
        self._has_changes = True  # 标记有未保存的改动

        show_info("成功", f"已删除编号 {entry_id} 的记录。可通过「撤回删除」恢复。")
        self._refresh_list()          # ⑤ 刷新界面
        self._update_undo_button_state()  # ⑥ 更新撤回按钮状态

    def _on_undo_delete(self):
        """
        撤回最近一次删除操作 —— 从撤回栈弹出记录，恢复到内存工作副本。

        【数据流】
        self._undo_stack.pop() → 取出最近删除的记录
            → 追加到 self._entries
            → 刷新界面
            → 更新撤回按钮状态
        """
        if not self._undo_stack:
            show_info("提示", "没有可撤回的删除记录。")
            return

        # 从撤回栈弹出最近删除的记录
        entry = self._undo_stack.pop()
        # 恢复到内存工作副本
        self._entries.append(entry)
        self._has_changes = True

        show_info("撤回成功", f"已恢复编号 {entry.id} 的记录：{entry.category} {entry.amount:.2f} 元")
        self._refresh_list()
        self._update_undo_button_state()

    def _update_undo_button_state(self):
        """
        根据撤回栈是否为空，启用或禁用"撤回删除"按钮。

        【调用时机】
        - 删除记录后（_on_delete_entry）
        - 撤回删除后（_on_undo_delete）
        """
        if self._undo_stack:
            self.undo_btn.config(state="normal")
        else:
            self.undo_btn.config(state="disabled")

    def _on_close(self):
        """
        窗口关闭事件处理 —— 若有未保存的改动，弹出确认对话框。

        【三种选择】
        - 保存：将内存工作副本写入磁盘后关闭
        - 不保存：丢弃本次运行的所有改动，直接关闭
        - 取消：不关闭窗口，返回程序继续操作
        """
        if not self._has_changes:
            # 没有未保存的改动，直接关闭
            self.root.destroy()
            return

        # 有未保存的改动，弹出三选一对话框
        result = messagebox.askyesnocancel(
            "保存确认",
            "本次运行有未保存的记录改动，是否保存？\n\n"
            "「是」保存并关闭\n「否」不保存直接关闭\n「取消」返回程序",
        )

        if result is True:
            # 用户选择"保存" → 写盘后关闭
            if self.storage.save_all(self._entries):
                self.root.destroy()
            else:
                show_error("错误", "保存失败，请检查磁盘空间或文件权限。")
        elif result is False:
            # 用户选择"不保存" → 丢弃改动，直接关闭
            self.root.destroy()
        # result is None → 用户选择"取消" → 不做任何操作，返回程序

    # ==============================================================
    # 标签页 3：月度统计 —— 按月筛选 + 分类汇总
    # ==============================================================

    def _build_stats_tab(self):
        """
        构建"月度统计"标签页。

        【界面结构】
        顶部：年月选择器（下拉框 + 查询按钮）
        中部：三个统计卡片（收入合计、支出合计、月度结余）
        底部：分类汇总表格（每个分类的笔数和金额）
        """
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
        """
        查询指定月份的统计数据 —— 数据流：磁盘 → 过滤 → 聚合 → 显示。

        【数据流】
        storage.load_all() → 全部记录
            → get_month_range() 算出月初/月末日期
            → 用字符串比较筛选出本月记录（利用 "YYYY-MM-DD" 格式的字典序）
            → 按分类聚合（求和 + 计数）
            → 更新统计卡片和表格
        """
        # 获取用户选择的年月
        try:
            year = int(self.stats_year.get())
            month = int(self.stats_month.get())
        except ValueError:
            show_error("错误", "请选择有效的年月。")
            return

        # 算出该月的起止日期（调 utils.py）
        start, end = get_month_range(year, month)
        # 从内存工作副本读取（与收支流水标签页保持一致）
        entries = self._entries
        # 筛选本月的记录（字符串比较，因为日期格式是 "YYYY-MM-DD"，天然支持字典序比较）
        month_entries = [e for e in entries if start <= e.date <= end]

        if not month_entries:
            self.stats_table.clear()
            self.stats_income_card.update_value("+0.00")
            self.stats_expense_card.update_value("-0.00")
            self.stats_balance_card.update_value("0.00")
            show_info("提示", f"{year}年{month}月暂无记录。")
            return

        # ---- 按分类聚合：把本月记录按"收入分类"和"支出分类"分别汇总 ----
        # 字典结构：{分类名: (笔数, 金额合计)}
        income_by_cat: dict[str, tuple[int, float]] = {}
        expense_by_cat: dict[str, tuple[int, float]] = {}

        for entry in month_entries:
            if entry.type == TYPE_INCOME:
                # 收入归入收入分类字典
                count, amt = income_by_cat.get(entry.category, (0, 0.0))
                income_by_cat[entry.category] = (count + 1, amt + entry.amount)
            else:
                # 支出归入支出分类字典
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

        # 构建表格数据
        rows = []
        for cat, (count, amt) in sorted(income_by_cat.items(), key=lambda x: -x[1][1]):
            rows.append(_StatsRow(cat, count, amt, TYPE_INCOME))
        for cat, (count, amt) in sorted(expense_by_cat.items(), key=lambda x: -x[1][1]):
            rows.append(_StatsRow(cat, count, amt, TYPE_EXPENSE))

        self.stats_table.load_data(rows)

    # ==============================================================
    # 标签页 4：设置
    # ==============================================================

    def _build_settings_tab(self):
        """
        构建"设置"标签页。

        【界面结构】
        主题选择（下拉框）→ 需重启生效
        字体选择（下拉框）→ 立即生效
        字号调整（滑块）  → 立即生效
        预览区域          → 实时反映当前选择
        应用按钮          → 保存设置到磁盘 + 更新全局样式
        """
        tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(tab, text="  设置  ")

        # 标题
        ttk.Label(tab, text="界面设置", font=get_font("title", "bold")).pack(
            anchor="w", pady=(0, 20)
        )

        # 主题选择（预设 + 中文分组显示）
        theme_frame = ttk.Frame(tab)
        theme_frame.pack(fill="x", pady=5)
        ttk.Label(theme_frame, text="主题:", width=10, anchor="e").pack(side="left", padx=(0, 8))

        # 构建带分组标题的主题列表（分隔行用 "── 组名 ──" 格式，不可选中）
        self._theme_display_list = []
        self._theme_value_map = {}    # 显示名 → 英文主题名
        self._preset_value_map = {}   # 显示名 → 预设名

        # 第一组：主题预设（深色/护眼等，有明显的颜色差异）
        separator = "── 主题预设 ──"
        self._theme_display_list.append(separator)
        for preset_name in PRESET_NAMES:
            display = f"  {preset_name}"
            self._theme_display_list.append(display)
            self._preset_value_map[display] = preset_name

        # 第二组起：ttkbootstrap 主题（按颜色系分组）
        for group_name, themes in THEME_GROUPS.items():
            separator = f"── {group_name} ──"
            self._theme_display_list.append(separator)
            for cn_name, en_name in themes:
                display = f"  {cn_name}({en_name})"
                self._theme_display_list.append(display)
                self._theme_value_map[display] = en_name

        self.settings_theme = ttk.Combobox(
            theme_frame, state="readonly", values=self._theme_display_list, width=20
        )
        # 根据当前设置的主题找到对应的中文显示名
        current_theme = self._settings["theme"]
        current_preset = self._settings.get("preset", "")
        if current_preset:
            # 当前是预设模式，找到预设的显示名
            for display, name in self._preset_value_map.items():
                if name == current_preset:
                    self.settings_theme.set(display)
                    break
        else:
            # 当前是普通主题模式
            for display, en in self._theme_value_map.items():
                if en == current_theme:
                    self.settings_theme.set(display)
                    break
        self.settings_theme.pack(side="left")
        # 选择分隔行时自动跳回上一个有效选项
        self.settings_theme.bind("<<ComboboxSelected>>", self._on_theme_select)

        # 字体族
        font_frame = ttk.Frame(tab)
        font_frame.pack(fill="x", pady=5)
        ttk.Label(font_frame, text="字体:", width=10, anchor="e").pack(side="left", padx=(0, 8))

        available_fonts = sorted(set(tkfont.families()))
        self.settings_font = ttk.Combobox(
            font_frame, state="readonly", values=available_fonts, width=20
        )
        self.settings_font.set(self._settings["font_family"])  # 从已加载的设置中读取
        self.settings_font.pack(side="left")

        # 字号
        size_frame = ttk.Frame(tab)
        size_frame.pack(fill="x", pady=5)
        ttk.Label(size_frame, text="字号:", width=10, anchor="e").pack(side="left", padx=(0, 8))

        self.settings_font_size = ttk.Scale(
            size_frame, from_=10, to=24,
            value=self._settings["font_size_body"],  # 从已加载的设置中读取
            bootstyle="info",
        )
        self.settings_font_size.pack(side="left", fill="x", expand=True)

        self.size_label = ttk.Label(
            size_frame, text=str(int(self._settings["font_size_body"])), width=4
        )
        self.size_label.pack(side="left", padx=(8, 0))
        self.settings_font_size.configure(
            command=lambda v: self.size_label.config(text=str(int(float(v))))
        )

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

        # 危险操作区（恢复默认设置 / 重置软件）
        danger_frame = ttk.Labelframe(tab, text="高级操作", padding=16)
        danger_frame.pack(fill="x", pady=(20, 0))

        ttk.Button(
            danger_frame, text="恢复系统设置", bootstyle="warning-outline",
            command=self._on_restore_settings
        ).pack(side="left", padx=(0, 10))

        ttk.Button(
            danger_frame, text="重置软件", bootstyle="danger-outline",
            command=self._on_reset_software
        ).pack(side="left")

        ttk.Label(
            danger_frame, text="恢复系统设置：重置字体/主题为默认值\n重置软件：删除所有数据并初始化",
            font=get_font("small"), bootstyle="secondary",
        ).pack(side="left", padx=(16, 0))

    def _on_apply_settings(self):
        """
        应用界面设置 —— 更新全局样式 + 持久化到磁盘。

        【数据流】
        从界面控件取值
            → 判断是预设还是普通主题
            → 更新 theme.py 模块变量
            → 调用 apply_theme() + apply_preset() 更新全局样式
            → 调用 save_settings() 写入 settings.json
            → 更新预览标签

        【两种模式】
        预设模式：深色/护眼/海洋蓝，立即生效（自定义颜色注入）
        普通主题：ttkbootstrap 原生主题，下次启动生效
        """
        # 从下拉框解析选中值
        theme_display = self.settings_theme.get()
        new_font_family = self.settings_font.get()
        new_font_size = int(float(self.settings_font_size.get()))

        # 判断选中的是预设还是普通主题
        is_preset = theme_display in self._preset_value_map
        if is_preset:
            preset_name = self._preset_value_map[theme_display]
            new_theme = THEME_PRESETS[preset_name]["base_theme"]
        else:
            preset_name = ""
            new_theme = self._theme_value_map.get(theme_display, "cosmo")

        # ---- 第一步：更新 theme.py 模块变量 ----
        theme.FONT_FAMILY = new_font_family
        theme.FONT_SIZE_BODY = new_font_size
        theme.FONT_SIZE_MAP["body"] = new_font_size
        theme.FONT_SIZE_MAP["title"] = new_font_size + 6
        theme.FONT_SIZE_MAP["subtitle"] = new_font_size + 2
        theme.FONT_SIZE_MAP["small"] = new_font_size - 2
        theme.THEME_NAME = new_theme

        # ---- 第二步：更新全局样式 ----
        apply_theme(self.style)
        self.style.configure("Treeview", rowheight=new_font_size + 14)

        # 如果是预设，立即应用自定义颜色（立即生效）
        if is_preset:
            apply_preset(preset_name, self.style)
            apply_preset_to_root(self.root, preset_name)

        # ---- 第三步：持久化设置到磁盘 ----
        self._settings = {
            "theme": new_theme,
            "preset": preset_name,
            "font_family": new_font_family,
            "font_size_body": new_font_size,
        }
        save_settings(self._settings)

        # ---- 第四步：更新预览标签 ----
        self.preview_label.config(font=(new_font_family, new_font_size))

        # ---- 第五步：提示用户 ----
        if is_preset:
            show_info(
                "设置已保存",
                f"预设: {preset_name}\n字体: {new_font_family}\n字号: {new_font_size}\n\n"
                f"预设已立即生效。"
            )
        else:
            show_info(
                "设置已保存",
                f"主题: {new_theme}\n字体: {new_font_family}\n字号: {new_font_size}\n\n"
                f"字体和字号已立即生效。\n"
                f"主题切换将在下次启动程序时生效。"
            )

    def _on_theme_select(self, event=None):
        """
        主题下拉框选择事件 —— 若选中分隔行则自动跳回上一个有效选项。

        【为什么需要这个方法？】
        下拉框中的 "── 红色系 ──" 等分隔行不是真正的主题选项，
        用户误点时应自动忽略，保持选中上一个有效主题。
        """
        current = self.settings_theme.get()
        # 分隔行以 "──" 开头，不是有效选项
        if current.startswith("──"):
            # 找到上一个有效选项（预设或普通主题）
            for display in reversed(self._theme_display_list):
                if display in self._theme_value_map or display in self._preset_value_map:
                    self.settings_theme.set(display)
                    break

    def _on_restore_settings(self):
        """
        恢复系统设置 —— 将字体、主题等重置为默认值，不删除记账数据。

        【数据流】
        用户确认 → 用 DEFAULT_SETTINGS 覆盖 self._settings
            → 更新 theme.py 模块变量
            → 保存到 settings.json
            → 更新界面控件显示
            → 提示重启
        """
        if not show_confirm(
            "恢复系统设置",
            "将恢复字体、主题等设置为默认值。\n记账数据不会被删除。\n\n确定继续吗？"
        ):
            return

        # 用默认值覆盖当前设置（清除预设字段）
        from theme import DEFAULT_SETTINGS
        self._settings = dict(DEFAULT_SETTINGS)
        self._settings["preset"] = ""  # 清除预设

        # 更新 theme.py 模块变量
        theme.FONT_FAMILY = self._settings["font_family"]
        theme.FONT_SIZE_BODY = self._settings["font_size_body"]
        theme.FONT_SIZE_MAP["body"] = self._settings["font_size_body"]
        theme.FONT_SIZE_MAP["title"] = self._settings["font_size_body"] + 6
        theme.FONT_SIZE_MAP["subtitle"] = self._settings["font_size_body"] + 2
        theme.FONT_SIZE_MAP["small"] = self._settings["font_size_body"] - 2
        theme.THEME_NAME = self._settings["theme"]

        # 持久化到磁盘
        save_settings(self._settings)

        # 更新界面控件显示（反向查找主题的中文显示名）
        default_theme = self._settings["theme"]
        for display, en in self._theme_value_map.items():
            if en == default_theme:
                self.settings_theme.set(display)
                break
        self.settings_font.set(self._settings["font_family"])
        self.settings_font_size.set(self._settings["font_size_body"])
        self.size_label.config(text=str(self._settings["font_size_body"]))

        show_info(
            "已恢复默认设置",
            "字体、主题等设置已恢复为默认值。\n请重启程序使主题生效。"
        )

    def _on_reset_software(self):
        """
        重置软件 —— 删除所有记账数据和设置文件，初始化软件。

        【危险操作】
        此操作不可撤销！会删除：
        - accounts.json（所有记账数据）
        - settings.json（用户设置）

        【安全措施】
        两次确认弹窗，防止误操作。
        """
        if not show_confirm(
            "⚠ 重置软件",
            "此操作将删除所有记账数据和设置！\n"
            "此操作不可撤销！\n\n"
            "确定要继续吗？"
        ):
            return

        # 二次确认
        if not show_confirm(
            "⚠ 最终确认",
            "真的要删除所有数据吗？\n\n"
            "点击「是」将立即删除所有数据并关闭程序。"
        ):
            return

        # 删除数据文件
        import os
        data_file = self.storage.file_path
        settings_file = theme.SETTINGS_FILE

        if os.path.exists(data_file):
            os.remove(data_file)
        if os.path.exists(settings_file):
            os.remove(settings_file)

        # 清空内存状态
        self._entries = []
        self._undo_stack = []
        self._has_changes = False

        show_info("重置完成", "所有数据已删除。程序将关闭，请重新启动。")
        self.root.destroy()

    # ==============================================================
    # 启动 —— 程序的入口
    # ==============================================================

    def run(self):
        """
        启动应用主循环。

        【启动流程】
        ① storage.load_all() → 从磁盘加载数据到内存工作副本
        ② _refresh_list() → 从工作副本填充流水表格
        ③ root.mainloop() → 进入 tkinter 事件循环（等待用户操作）

        mainloop() 会让程序一直运行，直到用户关闭窗口。
        它不断地监听用户的鼠标点击、键盘输入等事件，
        然后调用对应的回调函数（比如 _on_save_entry）。
        """
        self._entries = self.storage.load_all()  # ① 从磁盘加载到内存工作副本
        self._refresh_list()                      # ② 从工作副本刷新界面

        # ③ 如果有保存的预设，应用颜色到所有 tk 原生组件
        saved_preset = self._settings.get("preset", "")
        if saved_preset and saved_preset in THEME_PRESETS:
            apply_preset_to_root(self.root, saved_preset)

        self.root.mainloop()                      # ④ 进入事件循环


def main():
    """
    程序入口 —— python gui.py 会从这里开始执行。

    【启动链】
    python gui.py
        → __name__ == "__main__" 成立
        → 调 main()
        → 创建 AccountApp()（构建窗口 + 加载数据）
        → 调 app.run()（进入事件循环）
    """
    app = AccountApp()
    app.run()


# Python 的入口约定：当这个文件被直接运行时（而不是被 import 时），
# __name__ 的值是 "__main__"，此时才执行 main()。
# 如果其他文件 import gui.py，main() 不会被执行。
if __name__ == "__main__":
    main()
