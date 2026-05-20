# -*- coding: utf-8 -*-
"""
build.py - PyInstaller 打包脚本（将 Python 程序变成独立 .exe）

===================================================================
【什么是打包？为什么要打包？】
===================================================================

你的 Python 程序需要 Python 解释器 + 一堆第三方库才能运行。
如果把程序发给朋友，朋友的电脑上没装 Python，程序就跑不起来。

"打包"就是把你的代码 + Python 解释器 + 第三方库 + 资源文件
全部塞进一个文件夹（或一个 .exe），让别人的电脑上不需要装
任何东西就能直接双击运行。

===================================================================
【PyInstaller 是什么？】
===================================================================

PyInstaller 是 Python 最常用的打包工具。它会：
  1. 分析你的代码，找出所有 import 的模块
  2. 把 Python 解释器 + 这些模块 + 你的代码打包到一起
  3. 生成一个 .exe 可执行文件

两种打包模式：
  --onedir（文件夹模式）：生成一个文件夹，里面有 .exe + 一堆依赖文件
  --onefile（单文件模式）：生成一个单独的 .exe（启动稍慢，因为要先解压）

本项目使用 --onedir，因为需要在 exe 旁边放用户数据文件（accounts.json）。

===================================================================
【打包后的目录结构】
===================================================================

  dist/个人记账本/
      ├── 个人记账本.exe      ← 双击运行的主程序
      ├── accounts.json       ← 用户数据（可写）
      └── _internal/          ← 内部资源（只读）
          ├── assets/
          │   └── icon.ico    ← 应用图标
          ├── docs/           ← 学习文档
          ├── code阅读目录.txt
          ├── UI交互逻辑.txt
          ├── 更新日志.txt
          ├── README.md
          └── ...             ← Python 解释器 + 第三方库

===================================================================
【使用方式】
===================================================================

  python build.py

打包完成后，输出目录在 dist/个人记账本/

===================================================================
"""

import PyInstaller.__main__  # PyInstaller 的编程接口（而非命令行）
import os
import shutil


# ============================================================
# 项目路径配置
# ============================================================

# os.path.dirname(os.path.abspath(__file__))
#   __file__ = 当前脚本文件的路径（build.py）
#   os.path.abspath() = 转为绝对路径
#   os.path.dirname() = 去掉文件名，只留目录
#   结果：build.py 所在的目录（即项目根目录）
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# dist = PyInstaller 的默认输出目录
DIST_DIR = os.path.join(PROJECT_DIR, "dist")

# 生成的 exe 文件名（不含 .exe 后缀）
APP_NAME = "个人记账本"


# ============================================================
# 需要打包进去的数据文件（--add-data）
# ============================================================

# PyInstaller 默认只打包 .py 文件。图片、文档、JSON 等"数据文件"
# 需要用 --add-data 手动指定。
#
# 格式：(源文件路径, 打包后的目标目录)
#   源文件路径 = 相对于项目根目录的路径
#   目标目录   = 打包后放在 _internal/ 下的哪个位置
#
# 例如：("assets/icon.ico", "assets")
#   → 把 assets/icon.ico 打包到 _internal/assets/icon.ico
#
# 例如：("code阅读目录.txt", ".")
#   → 把 code阅读目录.txt 打包到 _internal/ 根目录（"." 表示当前目录）

DATAS = [
    ("assets/icon.ico", "assets"),   # 应用图标
    ("code阅读目录.txt", "."),       # 学习文档
    ("UI交互逻辑.txt", "."),         # 学习文档
    ("exe运行原理.txt", "."),        # 学习文档
    ("文件分类指南.txt", "."),       # 学习文档
    ("更新日志.txt", "."),           # 学习文档
    ("README.md", "."),              # 项目说明
    ("docs", "docs"),                # docs/ 整个目录
]


# ============================================================
# 构建 PyInstaller 参数列表
# ============================================================

# PyInstaller 的每个命令行参数都可以用列表元素表示：
#   命令行：pyinstaller --name=个人记账本 --noconsole gui.py
#   等价于：["gui.py", "--name=个人记账本", "--noconsole"]
#
# 这里用编程方式构建参数列表，好处是：
#   1. 可以用变量和循环（比如动态添加 --add-data）
#   2. 可以用条件判断（比如检测文件是否存在）
#   3. 跨平台（自动处理路径分隔符）

args = [
    # ---- 入口文件 ----
    # PyInstaller 需要知道从哪个 .py 文件开始执行
    # 就像 python gui.py 一样，这里指定 gui.py 为入口
    os.path.join(PROJECT_DIR, "gui.py"),

    # ---- 输出文件名 ----
    f"--name={APP_NAME}",

    # ---- 不显示控制台窗口 ----
    # GUI 程序不需要黑色的命令行窗口
    # 如果是 CLI 程序（如 main.py），应该用 --console
    "--noconsole",

    # ---- 打包模式：文件夹模式 ----
    # --onedir：生成文件夹，exe 和依赖文件分开存放
    # --onefile：生成单个 exe（启动慢，因为要先解压到临时目录）
    # 我们选 --onedir，因为 accounts.json 需要放在 exe 旁边（可写）
    "--onedir",

    # ---- 应用图标 ----
    # 这个图标会显示在 exe 文件的图标上（资源管理器中看到的图标）
    # 注意：这和窗口标题栏图标是两回事（标题栏图标要代码设置）
    f"--icon={os.path.join(PROJECT_DIR, 'assets', 'icon.ico')}",

    # ---- Windows 版本信息 ----
    # version_info.txt 包含产品名、版本号、公司名等元数据
    # 会嵌入到 exe 文件中（右键 → 属性 → 详细信息 可以看到）
    f"--version-file={os.path.join(PROJECT_DIR, 'version_info.txt')}",

    # ---- 隐藏导入（hidden import）----
    # PyInstaller 分析代码时，有些模块它发现不了：
    #   - ttkbootstrap 的主题文件（运行时动态加载）
    #   - PIL 的 tkinter 支持（PIL._tkinter_finder）
    # 这些需要手动告诉 PyInstaller："别忘了把这些也打包进去"
    "--hidden-import=ttkbootstrap",
    "--hidden-import=PIL",
    "--hidden-import=PIL._tkinter_finder",

    # ---- 收集 ttkbootstrap 全部资源 ----
    # ttkbootstrap 的主题文件（.json）不在 Python 模块搜索路径中，
    # --collect-all 会把整个包的所有文件（包括数据文件）都收集起来
    "--collect-all=ttkbootstrap",

    # ---- 覆盖已有输出 ----
    # 如果 dist/ 目录已存在，不询问直接覆盖
    "--noconfirm",

    # ---- 清理临时文件 ----
    # 打包过程中会生成很多临时文件，--clean 在打包前先清理
    "--clean",
]


# ============================================================
# 动态添加数据文件（--add-data）
# ============================================================

# 遍历 DATAS 列表，为每个数据文件生成 --add-data 参数
for src, dst in DATAS:
    src_path = os.path.join(PROJECT_DIR, src)

    if os.path.exists(src_path):
        # ---- 路径分隔符的坑 ----
        # --add-data 的格式是 "源路径:目标目录"（Linux/Mac 用 :）
        # 但在 Windows 上必须用分号 ";" 而不是冒号 ":"
        # os.name == "nt" 表示 Windows 系统
        sep = ";" if os.name == "nt" else ":"
        args.append(f"--add-data={src_path}{sep}{dst}")
    else:
        # 文件不存在时打印警告（不会中断打包）
        print(f"[WARN] 跳过不存在的文件: {src_path}")


# ============================================================
# 执行打包
# ============================================================

print("=" * 50)
print(f"  开始打包: {APP_NAME}")
print("=" * 50)
print()

# PyInstaller.__main__.run(args)
#   这是 PyInstaller 的编程接口，等价于在命令行执行：
#   pyinstaller gui.py --name=个人记账本 --noconsole ...
#   参数以列表形式传入，每个元素对应一个命令行参数
PyInstaller.__main__.run(args)


# ============================================================
# 打包后处理：复制用户数据模板
# ============================================================

# PyInstaller 打包后的 _internal/ 目录是只读的（会被冻结）。
# 但 accounts.json 是用户数据，需要放在 exe 旁边（可写位置）。
# 所以打包完成后，手动把 accounts.json 复制到 dist 根目录。

dist_app_dir = os.path.join(DIST_DIR, APP_NAME)
template = os.path.join(PROJECT_DIR, "accounts.json")

if os.path.exists(template) and os.path.isdir(dist_app_dir):
    shutil.copy2(template, os.path.join(dist_app_dir, "accounts.json"))
    print(f"\n已复制 accounts.json 到 {dist_app_dir}")


print()
print("=" * 50)
print(f"  打包完成！输出目录: {dist_app_dir}")
print(f"  可执行文件: {os.path.join(dist_app_dir, APP_NAME + '.exe')}")
print("=" * 50)
