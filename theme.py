# -*- coding: utf-8 -*-
"""
theme.py - 样式配置中心

所有视觉参数集中在此文件。
修改这里的值即可全局换肤，无需改动其他模块。
"""

import json
import os

import tkinter as tk
import ttkbootstrap as ttk

# 从 config 导入数据目录（用于定位 settings.json）
from config import DATA_DIR

# ============================================================
# 字体配置
# ============================================================

FONT_FAMILY = "Microsoft YaHei"      # 字体族（可改为 SimHei/Consolas 等）
FONT_SIZE_TITLE = 18                  # 标题字号
FONT_SIZE_SUBTITLE = 14               # 副标题字号
FONT_SIZE_BODY = 12                   # 正文字号（用户可在设置页调整）
FONT_SIZE_SMALL = 10                  # 辅助文字字号

# 字号映射（模块级变量，load_settings() 会根据用户设置动态更新）
FONT_SIZE_MAP = {
    "title": FONT_SIZE_TITLE,
    "subtitle": FONT_SIZE_SUBTITLE,
    "body": FONT_SIZE_BODY,
    "small": FONT_SIZE_SMALL,
}

# ============================================================
# 颜色配置（供 gui.py 等模块直接引用）
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

# 主题中文分组映射：{组名: [(中文名, 英文主题名), ...]}
# gui.py 的设置页下拉框会用到这个映射，按组显示中文主题名
THEME_GROUPS = {
    "红色系": [("玫瑰", "cosmo"), ("砂岩", "sandstone"), ("联合", "united")],
    "蓝绿色系": [("清新", "litera"), ("扁平", "flatly"), ("雪杉", "cerculean"), ("雪人", "yeti")],
    "紫色系": [("脉搏", "pulse"), ("薄荷", "minty"), ("流明", "lumen")],
    "暗色系": [("暗黑", "darkly"), ("超级英雄", "superhero"), ("太阳", "solar"), ("机械", "cyborg"), ("蒸汽", "vapor")],
    "简约/质感": [("日志", "journal"), ("极简", "simple"), ("拟态", "morph")],
}

# 从 THEME_GROUPS 构建中文名→英文名的反向映射（供 gui.py 解析选中值）
THEME_NAME_MAP = {}
for _group in THEME_GROUPS.values():
    for _cn, _en in _group:
        THEME_NAME_MAP[f"{_cn}({_en})"] = _en

# ============================================================
# 主题预设（真正改变界面颜色的方案）
# ============================================================
# ttkbootstrap 的主题之间差异很小（都是浅色系），
# 这里的预设会额外注入颜色配置，让主题切换有明显的视觉差异。

THEME_PRESETS = {
    "深色模式": {
        "base_theme": "darkly",       # ttkbootstrap 基础主题
        "bg": "#1a1a2e",              # 主背景（深蓝黑）
        "fg": "#e0e0e0",              # 主文字（浅灰）
        "field_bg": "#16213e",        # 输入框背景（深蓝）
        "select_bg": "#0f3460",       # 选中背景
        "accent": "#e94560",          # 强调色（红色）
    },
    "护眼模式": {
        "base_theme": "cosmo",
        "bg": "#f5f0e1",              # 主背景（米黄）
        "fg": "#3d3229",              # 主文字（深棕）
        "field_bg": "#ede5d0",        # 输入框背景（浅米）
        "select_bg": "#c9b98a",       # 选中背景
        "accent": "#6b8e23",          # 强调色（橄榄绿）
    },
    "海洋蓝": {
        "base_theme": "cerculean",
        "bg": "#e8f4f8",              # 主背景（浅蓝）
        "fg": "#1b3a4b",              # 主文字（深蓝）
        "field_bg": "#d4eef6",        # 输入框背景
        "select_bg": "#7ec8e3",       # 选中背景
        "accent": "#0077b6",          # 强调色
    },
}

# 预设名列表（供 gui.py 的下拉框使用）
PRESET_NAMES = list(THEME_PRESETS.keys())


def apply_preset(preset_name: str, style: ttk.Style):
    """
    应用主题预设 —— 在 ttkbootstrap 主题之上叠加自定义颜色。

    【为什么要单独做预设？】
    ttkbootstrap 的 18 个主题都是"浅色系"，彼此差异很小。
    预设通过注入自定义颜色，让深色模式、护眼模式等真正有视觉差异。

    参数:
        preset_name: 预设名（"深色模式" / "护眼模式" / "海洋蓝"）
        style:       ttkbootstrap 的 Style 对象
    """
    if preset_name not in THEME_PRESETS:
        return

    preset = THEME_PRESETS[preset_name]
    bg = preset["bg"]
    fg = preset["fg"]
    field_bg = preset["field_bg"]
    select_bg = preset["select_bg"]

    # ---- 第一步：配置 ttkbootstrap 样式 ----
    # TLabel / TButton / TEntry 等 ttk 组件的文字颜色
    style.configure("TLabel", foreground=fg, background=bg)
    style.configure("TButton", foreground=fg)
    style.configure("TEntry", fieldbackground=field_bg, foreground=fg)
    style.configure("TCombobox", fieldbackground=field_bg, foreground=fg)
    style.configure("TFrame", background=bg)
    style.configure("TLabelframe", background=bg, foreground=fg)
    style.configure("TLabelframe.Label", background=bg, foreground=fg)
    style.configure("TNotebook", background=bg)
    style.configure("TNotebook.Tab", background=field_bg, foreground=fg)
    style.configure("Treeview", background=field_bg, foreground=fg, fieldbackground=field_bg)
    style.configure("Treeview.Heading", background=select_bg, foreground=fg)
    style.configure("TScale", background=bg)
    style.configure("TRadiobutton", background=bg, foreground=fg)
    style.configure("TCheckbutton", background=bg, foreground=fg)

    # ---- 第二步：更新 tk 原生组件 ----
    # tkinter 的 Menu / Text 等组件不受 ttkbootstrap 控制，需要单独设置
    # 这部分在 gui.py 的 _apply_preset_to_widgets() 中通过遍历窗口控件完成


def apply_preset_to_root(root, preset_name: str):
    """
    将预设颜色应用到窗口中的所有 tk 原生组件（递归遍历）。

    【为什么需要这个函数？】
    ttkbootstrap 的 style.configure() 只影响 ttk 组件。
    tkinter 的原生组件（如 Menu、Text、Listbox）需要用 config() 单独设置。
    这个函数递归遍历窗口中的所有组件，给 tk 原生组件上色。

    参数:
        root:        主窗口（tkinter.Tk 或 ttk.Window）
        preset_name: 预设名
    """
    if preset_name not in THEME_PRESETS:
        return

    preset = THEME_PRESETS[preset_name]
    bg = preset["bg"]
    fg = preset["fg"]

    # 递归遍历所有子组件
    def _apply(widget):
        try:
            # 尝试设置背景色（大多数 tk 组件都支持）
            widget.configure(background=bg)
        except tk.TclError:
            pass
        try:
            # 尝试设置前景色
            widget.configure(foreground=fg)
        except tk.TclError:
            pass
        try:
            # Entry / Spinbox 的特殊属性
            widget.configure(insertbackground=fg)  # 光标颜色
        except tk.TclError:
            pass

        # 递归处理子组件
        for child in widget.winfo_children():
            _apply(child)

    _apply(root)

# ============================================================
# 设置持久化（settings.json）
# ============================================================

# 设置文件路径：与 accounts.json 同目录
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

# 默认设置（首次运行或 settings.json 不存在时使用）
DEFAULT_SETTINGS = {
    "theme": "cosmo",
    "font_family": "Microsoft YaHei",
    "font_size_body": 12,
}

# ============================================================
# 窗口配置
# ============================================================

WINDOW_TITLE = "个人记账本 v1.6"
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 600
WINDOW_MIN_WIDTH = 700
WINDOW_MIN_HEIGHT = 500

# ============================================================
# 表格配置
# ============================================================

TABLE_ROW_HEIGHT = 28                 # 表格行高

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


def get_font(size_key: str = "body", weight: str = "normal") -> tuple[str, int, str]:
    """
    获取字体元组，供 tkinter 组件使用。

    参数:
        size_key: "title" / "subtitle" / "body" / "small"
        weight:   "normal" / "bold"

    返回:
        (字体族, 字号, 权重) 元组
    """
    if size_key not in FONT_SIZE_MAP:
        raise ValueError(f"未知的 size_key: '{size_key}'，可选: {list(FONT_SIZE_MAP.keys())}")
    size = FONT_SIZE_MAP[size_key]
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
    style.configure("Treeview", font=get_font("body"), rowheight=TABLE_ROW_HEIGHT)
    style.configure("Treeview.Heading", font=get_font("body", "bold"))
    style.configure("TNotebook.Tab", font=get_font("body"))


def load_settings() -> dict:
    """
    从 settings.json 加载用户设置，更新模块级变量。

    【数据流】
    settings.json（磁盘）
        → json.load() 读取为字典
        → 更新 FONT_FAMILY / FONT_SIZE_BODY / THEME_NAME
        → 重建 FONT_SIZE_MAP
        → 返回设置字典

    【异常处理】
    文件不存在 → 使用 DEFAULT_SETTINGS（首次运行）
    JSON 损坏 → 使用 DEFAULT_SETTINGS，打印警告
    缺少字段 → 用 DEFAULT_SETTINGS 补全
    """
    global FONT_FAMILY, FONT_SIZE_BODY, FONT_SIZE_MAP, THEME_NAME

    settings = dict(DEFAULT_SETTINGS)  # 以默认值为基底

    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            # 用保存的值覆盖默认值（缺少的字段保留默认值）
            for key in DEFAULT_SETTINGS:
                if key in saved:
                    settings[key] = saved[key]
        except (json.JSONDecodeError, IOError) as e:
            print(f"[警告] 读取设置文件失败，使用默认设置: {e}")

    # 更新模块级变量，使 get_font() / apply_theme() 反映最新设置
    FONT_FAMILY = settings["font_family"]
    FONT_SIZE_BODY = settings["font_size_body"]
    THEME_NAME = settings["theme"]

    # 根据新的 body 字号重建字号映射（保持各档位的相对比例）
    FONT_SIZE_MAP["body"] = FONT_SIZE_BODY
    FONT_SIZE_MAP["title"] = FONT_SIZE_BODY + 6
    FONT_SIZE_MAP["subtitle"] = FONT_SIZE_BODY + 2
    FONT_SIZE_MAP["small"] = FONT_SIZE_BODY - 2

    return settings


def save_settings(settings: dict):
    """
    将用户设置保存到 settings.json（原子写入，与 storage.py 同策略）。

    【为什么用原子写入？】
    与 accounts.json 的保存策略一致：先写 .tmp，再 os.replace()。
    防止写到一半崩溃导致设置文件损坏。
    """
    temp_path = SETTINGS_FILE + ".tmp"
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        if os.path.exists(SETTINGS_FILE):
            os.replace(temp_path, SETTINGS_FILE)
        else:
            os.rename(temp_path, SETTINGS_FILE)
    except (IOError, OSError) as e:
        print(f"[错误] 保存设置失败: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
