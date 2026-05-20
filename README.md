# 个人记账本 v1.5

一个用 Python 构建的桌面记账应用，基于 tkinter + ttkbootstrap，采用分层解耦的工程架构。项目从 v1.0 到 v1.5 逐步迭代，完整展示了软件从"能用"到"好用"再到"能打包分发"的演进过程。

## 核心功能

- **缓冲保存模式**：增删操作只修改内存工作副本，关闭时统一确认（保存 / 不保存 / 取消），避免数据丢失
- **撤回删除**：删除的记录压入 LIFO 栈，支持一键恢复
- **主题预设系统**：深色模式、护眼模式、海洋蓝，运行时立即生效
- **分类频率排序**：常用分类自动排在最前面，提高记账效率
- **设置持久化**：字体、主题、字号保存到 settings.json，下次启动自动加载
- **月度统计**：按月筛选 + 分类聚合，收入/支出/结余一目了然
- **PyInstaller 打包**：一键打包成独立 .exe，无需安装 Python 即可运行
- **菜单栏帮助系统**：内置学习文档，点击菜单即可打开

## 运行方式

### 方式一：直接运行源码

```bash
pip install ttkbootstrap Pillow
python gui.py      # GUI 版本
python main.py     # CLI 版本
```

要求 Python 3.10+。

### 方式二：打包成 .exe

```bash
pip install pyinstaller ttkbootstrap Pillow
python build.py
```

打包产物在 `dist/个人记账本/` 目录下，双击 `个人记账本.exe` 即可运行。

## 工程架构（7 层分层设计）

```
build.py        打包层    源码 → .exe 的桥梁
gui.py          界面层    用户操作的起点和终点
ui_components   组件层    FormRow / DataTable / StatsCard
theme.py        样式层    主题预设 + 设置持久化
storage.py      持久化层  原子写入，断电不丢数据
models.py       模型层    @dataclass + 校验逻辑
config.py       配置层    一处改，全局生效（兼容 PyInstaller）
```

## 工程结构

```
├── main.py           # CLI 入口（保留）
├── gui.py            # GUI 入口（主程序）
├── build.py          # PyInstaller 打包脚本
├── version_info.txt  # Windows exe 版本元数据
├── assets/
│   └── icon.ico      # 应用图标（16/32/48/256px）
├── ui_components.py  # 可复用 UI 组件（FormRow、DataTable、StatsCard）
├── theme.py          # 样式/字体/主题配置 + 设置持久化
├── config.py         # 全局配置、常量（兼容 PyInstaller 路径）
├── models.py         # 数据模型 + 校验
├── storage.py        # 数据持久化（原子写入）
├── utils.py          # 工具函数（纯函数）
├── accounts.json     # 数据文件（自动生成）
├── settings.json     # 用户设置（自动生成）
├── requirements.txt  # 依赖清单
├── README.md         # 本文件
├── 更新日志.txt       # 版本更新记录
├── UI交互逻辑.txt     # 从用户视角详解每个按钮的代码流（Python 学习版）
├── code阅读目录.txt   # 按数据流顺序的代码阅读指引
├── exe运行原理.txt    # 从双击 exe 到运行的完整原理详解
└── 文件分类指南.txt   # 一文看懂所有文件的作用和分类（初学者必读）
```

## 模块职责

| 模块 | 作用 | 关键词 |
|------|------|--------|
| `gui.py` | GUI 入口、标签页、事件协调 | 控制器、缓冲保存、撤回栈 |
| `ui_components.py` | 可复用 UI 组件 | FormRow、DataTable、StatsCard |
| `theme.py` | 样式/字体/主题/预设配置 | 换肤、THEME_PRESETS、设置持久化 |
| `config.py` | 全局业务配置 | 配置集中、分类列表 |
| `models.py` | 数据结构和校验 | @dataclass、validate |
| `storage.py` | 文件读写 | 持久化、原子写入 |
| `utils.py` | 通用工具函数 | 复用、纯函数 |

## 数据流

```
记账数据流：
用户操作 GUI → gui.py（事件处理）
             → models.py（校验）
             → 内存工作副本 _entries（缓冲保存）
             → storage.py（关闭时写盘）
             → accounts.json（持久化存储）

设置数据流：
用户在设置页调整 → gui.py（应用设置）
                 → theme.py（更新模块变量）
                 → settings.json（持久化存储）
```

## 学习资源

- **代码注释**：每个函数都有详细的中文注释，解释"为什么这样做"
- **UI交互逻辑.txt**：从用户视角逐一详解每个按钮背后的完整代码流
- **code阅读目录.txt**：按数据流顺序的代码阅读指引，循序渐进
- **exe运行原理.txt**：从双击 exe 到运行的完整原理详解，理解打包后的程序怎么工作
- **文件分类指南.txt**：一文看懂所有文件的作用和分类，初学者必读
- **更新日志.txt**：语义化版本记录，了解每个版本的变更
- **build.py**：PyInstaller 打包脚本，含完整的打包原理教学注释
