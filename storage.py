# -*- coding: utf-8 -*-
"""
storage.py - 数据持久化模块（数据流的第三层：数据进出磁盘的唯一通道）

===================================================================
【数据流位置】
    config.py（路径常量）
        ↓
    models.py（数据结构）
        ↓
    storage.py（读写磁盘）  ← 你在这里
        ↓
    accounts.json（磁盘上的 JSON 文件）
===================================================================

【工程思维】为什么要把磁盘操作单独抽成一个模块？
===================================================================
1. 【解耦】gui.py / main.py 不需要知道数据存在 JSON 还是 SQLite 还是云端。
   它们只管调 storage.load_all() 和 storage.save_all()。
   将来要换数据库？只改这一个文件，界面层完全不受影响。

2. 【数据安全】集中管理读写，可以统一加备份、加锁、加校验。
   如果每个地方都自己 open() 文件，很容易出现"写到一半崩溃，数据全丢"。

3. 【可测试】测试时可以注入临时文件路径，不影响真实数据。
===================================================================
"""

import json
import os
import shutil
from datetime import datetime
from typing import Optional

# 从 config 导入路径常量，从 models 导入数据模型
# 依赖方向：storage → config + models（单向依赖，不反向）
from config import DATA_FILE, DATE_FORMAT
from models import BillEntry


class Storage:
    """
    账单数据存储管理器 —— 整个程序中唯一与磁盘对话的"门卫"

    【核心职责】
        - load_all()    → 从 JSON 文件读取所有账单，返回对象列表
        - save_all()    → 把对象列表写回 JSON 文件（原子写入，防崩溃）
        - get_next_id() → 分配自增编号
        - backup()      → 删除前自动备份

    【设计选择：为什么用 JSON 而不是 CSV / SQLite？】
        - JSON 可读性强：用记事本打开 accounts.json 就能直接看数据
        - Python 内置 json 库：零外部依赖
        - 结构化存储：天然支持 key-value 映射
        - 对于几千条以内的小数据量，性能完全够用
        - 将来换 SQLite？只改这个文件，其他模块不用动
    """

    def __init__(self, file_path: Optional[str] = None):
        """
        初始化存储管理器。

        参数:
            file_path: 数据文件路径，默认使用 config.py 中的 DATA_FILE
                       测试时可以传入临时路径，不影响真实数据
        """
        self.file_path = file_path or DATA_FILE
        # 防御性初始化：程序启动时确保数据文件存在
        # 如果不存在，自动创建一个空的 JSON 文件
        self._ensure_file()

    # ----------------------------------------------------------
    # 公开接口
    # ----------------------------------------------------------

    def load_all(self) -> list[BillEntry]:
        """
        从 JSON 文件加载所有账单条目，返回 BillEntry 对象列表。

        【数据流】
        accounts.json（磁盘）
            → json.load() 读取为 list[dict]
            → 逐条调 BillEntry.from_dict() 转为对象
            → 返回 list[BillEntry]

        【异常处理策略 —— 三级防御】
        1. 文件不存在 → 返回空列表（首次运行时正常情况）
        2. JSON 格式损坏 → 打印警告，返回空列表（给用户提示）
        3. 单条记录损坏 → 跳过该条，继续加载其他的（尽量保全数据）

        【为什么不让异常直接抛出？】
        因为调用者（gui.py）拿到异常也不知道怎么处理——
        总不能因为一条数据坏了就让整个程序崩溃吧。
        所以在这里"消化"异常，尽量返回有用的数据。
        """
        # 第一步：读取 JSON 文件
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            return []  # 文件不存在 → 空列表（不是错误）
        except json.JSONDecodeError as e:
            print(f"[警告] 数据文件格式损坏: {e}")
            print("[提示] 已返回空数据，建议检查数据文件或从备份恢复。")
            return []  # JSON 格式坏了 → 空列表

        # 第二步：把字典列表转成 BillEntry 对象列表
        entries = []
        for item in data:
            try:
                entry = BillEntry.from_dict(item)  # 字典 → 对象
                entries.append(entry)
            except Exception as e:
                # 单条记录有问题 → 跳过，不影响其他记录
                print(f"[警告] 跳过一条损坏记录: {item}，原因: {e}")

        return entries

    def save_all(self, entries: list[BillEntry]) -> bool:
        """
        把所有账单条目保存到 JSON 文件。

        【数据流】
        list[BillEntry]（内存中的对象列表）
            → 逐条调 entry.to_dict() 转为字典
            → json.dump() 写入磁盘

        返回值：
            True  → 保存成功
            False → 保存失败

        【核心安全策略：原子写入】
        想象这个场景：写到一半，突然断电了。
        如果直接写原文件，accounts.json 就会变成半截的乱码，数据全丢。

        原子写入的做法：
        1. 先写到 accounts.json.tmp（临时文件）
        2. 写成功后，用 os.replace() 把 tmp 替换掉原文件
        3. os.replace() 是操作系统级别的"原子操作"——
           要么完全替换成功，要么完全不替换，不存在"替换到一半"的状态

        这样即使在第 2 步断电，原文件 accounts.json 仍然完好无损。
        """
        # 第一步：对象列表 → 字典列表
        data = [entry.to_dict() for entry in entries]

        # 第二步：写入临时文件（accounts.json.tmp）
        temp_path = self.file_path + ".tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                # ensure_ascii=False → 中文直接显示，不转义成 \uXXXX
                # indent=2 → 格式化缩进，用记事本打开也能看清楚
                json.dump(data, f, ensure_ascii=False, indent=2)
        except (IOError, OSError) as e:
            print(f"[错误] 写入临时文件失败: {e}")
            return False

        # 第三步：原子替换（tmp → 原文件）
        try:
            # os.replace() = 操作系统级别的原子替换
            # Windows 下 os.replace() 能覆盖已存在的文件
            if os.path.exists(self.file_path):
                os.replace(temp_path, self.file_path)
            else:
                os.rename(temp_path, self.file_path)
        except (IOError, OSError) as e:
            print(f"[错误] 替换数据文件失败: {e}")
            # 替换失败 → 清理临时文件，避免残留垃圾
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False

        return True

    def get_next_id(self, entries: list[BillEntry]) -> int:
        """
        计算下一个自增编号。

        策略：找到当前所有记录中最大的 ID，加 1。
        如果列表为空（没有任何记录），从 1 开始。

        gui.py 在保存新记录前会调用这个方法，拿到新编号后赋给 BillEntry.id。
        """
        if not entries:
            return 1
        return max(entry.id for entry in entries) + 1

    def backup(self) -> Optional[str]:
        """
        备份当前数据文件（gui.py 删除记录前会自动调用）。

        返回值：
            成功 → 备份文件的路径（如 accounts.json.bak.20260515_143022）
            失败 → None

        【备份命名规则】
        原文件名 + ".bak." + 时间戳
        带时间戳的好处：如果删错了，可以按时间找到删之前的备份来恢复。
        """
        if not os.path.exists(self.file_path):
            return None

        # 生成带时间戳的备份文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.file_path}.bak.{timestamp}"

        try:
            # shutil.copy2 = 复制文件并保留元数据（创建时间等）
            shutil.copy2(self.file_path, backup_path)
            return backup_path
        except (IOError, OSError) as e:
            print(f"[错误] 备份失败: {e}")
            return None

    # ----------------------------------------------------------
    # 内部方法
    # ----------------------------------------------------------

    def _ensure_file(self):
        """
        【防御性初始化】确保数据文件存在。

        程序启动时（__init__ 中）调用。
        如果 accounts.json 不存在，自动创建一个包含空列表 [] 的文件。
        这样后续的 load_all() 就不会因为 FileNotFoundError 而失败。

        为什么叫"防御性"？因为不管用户是第一次运行还是文件被误删，
        程序都能自动恢复到一个可用的状态，而不是崩溃。
        """
        if not os.path.exists(self.file_path):
            try:
                # 先确保目录存在（如果目录也不存在，先创建目录）
                dir_path = os.path.dirname(self.file_path)
                if dir_path and not os.path.exists(dir_path):
                    os.makedirs(dir_path)

                # 创建空的 JSON 文件：[]
                with open(self.file_path, "w", encoding="utf-8") as f:
                    json.dump([], f)
            except (IOError, OSError) as e:
                print(f"[警告] 无法创建数据文件: {e}")
