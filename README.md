# 个人记账本 v1.6

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

---

## 版本历史

### v1.6（2026-05-20）

- **NSIS 安装包**：一键 `makensis installer.nsi` 生成 Windows 安装程序
- **安装向导**：MUI2 现代界面，支持自定义安装目录
- **桌面快捷方式**：安装时可选创建桌面快捷方式
- **开始菜单**：自动创建开始菜单文件夹和快捷方式
- **卸载程序**：完整卸载功能，清理文件、快捷方式和注册表
- **安装后操作**：询问删除安装包和立即打开程序
- **教学注释**：installer.nsi 添加完整的 NSIS 教学注释
- **学习文档**：文件分类指南新增安装包分类说明

### v1.5（2026-05-20）

- **文件分类指南**：一文看懂所有文件的作用和分类（8 大分类、初学者必读）
- **菜单栏入口完善**：新增"文件分类指南"和"exe 运行原理"菜单项
- **版本号统一更新**：所有文件同步更新至 v1.5
- **Git commit 规范化**：去掉版本号，每条 commit 标明内容作用

### v1.4（2026-05-20）

- **PyInstaller 打包系统**：一键 `python build.py` 生成独立 .exe
- **应用图标**：绿色背景 + ¥ 符号，四尺寸（16/32/48/256px）
- **Windows 版本信息**：右键 exe → 属性 → 详细信息 可查看
- **菜单栏帮助系统**：内置学习文档，点击菜单即可打开
- **路径兼容**：config.py 兼容 PyInstaller 打包后的路径解析
- **教学注释**：build.py / config.py / gui.py 添加打包和菜单栏教学注释
- **学习文档**：新增 exe运行原理.txt、文件分类指南.txt

### v1.3（2026-05-20）

- **主题预设系统**：深色模式、护眼模式、海洋蓝，运行时立即生效
- **设置页高级操作**：恢复系统设置 / 重置软件（二次确认）
- **分类频率排序**：常用分类自动排在最前面
- **分类扩充**：收入 6→8、支出 8→12
- **主题分组显示**：中文分组 + 分隔行防误选
- **Bug 修复**：主题切换后重启不生效的问题
- **学习文档**：新增 UI交互逻辑.txt

### v1.2（2026-05-20）

- **设置持久化**：字体、主题、字号保存到 settings.json
- **缓冲保存模式**：增删操作只改内存，关闭时统一写盘
- **撤回删除**：删除的记录压入 LIFO 栈，支持一键恢复
- **窗口关闭确认**：三选一（保存 / 不保存 / 取消）
- **右键删除菜单**：DataTable 支持右键上下文菜单

### v1.1（2026-05-19）

- **GUI 版本发布**：基于 tkinter + ttkbootstrap 的桌面记账界面
- **4 个标签页**：记一笔 / 收支流水 / 月度统计 / 设置
- **可复用组件**：FormRow / DataTable / StatsCard
- **样式配置中心**：theme.py 集中管理字体、颜色、主题
- **设计文档**：新建 docs/ 目录

### v1.0（2026-05-18）

- **CLI 版本发布**：命令行交互式记账
- **核心模块**：config.py / models.py / storage.py / utils.py
- **数据持久化**：JSON 格式 + 原子写入 + 备份
- **数据模型**：@dataclass + 校验逻辑
