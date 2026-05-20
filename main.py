# -*- coding: utf-8 -*-
"""
main.py - 程序入口与主交互逻辑

本模块是整个程序的"大脑"——负责：
1. 显示菜单、读取用户输入
2. 协调其他模块完成业务操作
3. 控制程序的主循环

它不直接读写文件（交给 storage），
不直接校验数据（交给 models 和 utils），
只负责"流程编排"——这叫"控制器层"（Controller）。
"""

import sys
from datetime import datetime

from config import (
    TYPE_INCOME, TYPE_EXPENSE, VALID_TYPES,
    INCOME_CATEGORIES, EXPENSE_CATEGORIES, DATE_FORMAT,
)
from models import BillEntry
from storage import Storage
from utils import (
    get_today, validate_amount, safe_input, confirm,
    format_amount, get_current_month_range, parse_date,
)


# ============================================================
# 初始化
# ============================================================

# 创建存储管理器实例（全局唯一，整个程序共享同一个实例）
storage = Storage()


# ============================================================
# 菜单与界面
# ============================================================

def show_banner():
    """显示程序标题"""
    print()
    print("=" * 50)
    print("      个人记账本 v1.6")
    print("      命令行收支管理工具")
    print("=" * 50)
    print()


def show_menu():
    """显示主菜单"""
    print("-" * 40)
    print("  1. 记一笔收入")
    print("  2. 记一笔支出")
    print("  3. 查看所有流水")
    print("  4. 查看本月统计")
    print("  5. 按月份查询")
    print("  6. 删除一条记录")
    print("  7. 导出账单")
    print("  0. 退出")
    print("-" * 40)


# ============================================================
# 核心业务功能
# ============================================================

def add_entry(entry_type: str):
    """
    添加一条收支记录。

    参数:
        entry_type: "income" 或 "expense"

    流程：
        1. 选择分类
        2. 输入金额（带校验）
        3. 输入备注（可选）
        4. 确认保存
    """
    type_name = "收入" if entry_type == TYPE_INCOME else "支出"
    print(f"\n--- 记一笔{type_name} ---")

    # 第一步：选择分类
    categories = INCOME_CATEGORIES if entry_type == TYPE_INCOME else EXPENSE_CATEGORIES
    print(f"可选分类：")
    for i, cat in enumerate(categories, 1):
        print(f"  {i}. {cat}")

    cat_choice = safe_input("请选择分类编号（直接回车选'其他'）: ", str(len(categories)))
    try:
        cat_index = int(cat_choice) - 1
        if not (0 <= cat_index < len(categories)):
            print("[错误] 无效的分类编号")
            return
    except ValueError:
        print("[错误] 请输入数字")
        return

    category = categories[cat_index]

    # 第二步：输入金额
    amount_str = safe_input("请输入金额（元）: ")
    if not amount_str:
        print("[提示] 已取消")
        return

    ok, amount = validate_amount(amount_str)
    if not ok:
        print(f"[错误] 金额格式不正确，应为正数且最多两位小数，输入为 '{amount_str}'")
        return

    # 第三步：输入备注（可选）
    note = safe_input("备注（可选，直接回车跳过）: ")

    # 第四步：确认保存
    print(f"\n  日期: {get_today()}")
    print(f"  类型: {type_name}")
    print(f"  分类: {category}")
    print(f"  金额: {format_amount(amount)} 元")
    print(f"  备注: {note or '(无)'}")

    if not confirm("确认保存？"):
        print("[提示] 已取消")
        return

    # 构建对象并保存
    entries = storage.load_all()
    new_id = storage.get_next_id(entries)

    entry = BillEntry(
        id=new_id,
        date=get_today(),
        type=entry_type,
        category=category,
        amount=amount,
        note=note,
    )

    # 校验（理论上不应该失败，因为上面已经逐步校验过了，但防御性编程要求再验一次）
    valid, msg = entry.validate()
    if not valid:
        print(f"[错误] 数据校验失败: {msg}")
        return

    entries.append(entry)

    if storage.save_all(entries):
        print(f"[成功] 已记录！编号: {new_id}")
    else:
        print("[错误] 保存失败，请检查磁盘空间或文件权限")


def list_entries():
    """
    查看所有流水记录。

    从文件加载全部数据，格式化输出。
    如果数据量很大，可以加分页——这里为了简洁只做全量展示。
    """
    print("\n--- 全部流水 ---")

    entries = storage.load_all()
    if not entries:
        print("（暂无记录）")
        return

    # 打印表头
    print(f"{'编号':>6}  {'日期':<12}  {'类型':<6}  {'分类':<8}  {'金额':>12}  {'备注'}")
    print("-" * 70)

    total_income = 0.0
    total_expense = 0.0

    for entry in entries:
        print(entry.format_display())
        if entry.type == TYPE_INCOME:
            total_income += entry.amount
        else:
            total_expense += entry.amount

    # 打印汇总
    print("-" * 70)
    print(f"  收入合计: +{format_amount(total_income)}")
    print(f"  支出合计: -{format_amount(total_expense)}")
    balance = total_income - total_expense
    sign = "+" if balance >= 0 else ""
    print(f"  结余:     {sign}{format_amount(balance)}")
    print(f"  共 {len(entries)} 条记录")


def show_monthly_stats():
    """查看当前月份的收支统计"""
    print("\n--- 本月统计 ---")

    start, end, year, month = get_current_month_range()
    entries = storage.load_all()

    # 筛选本月数据
    month_entries = [e for e in entries if start <= e.date <= end]

    if not month_entries:
        print(f"  {year}年{month}月暂无记录")
        return

    # 按分类汇总
    income_by_cat: dict[str, float] = {}
    expense_by_cat: dict[str, float] = {}

    for entry in month_entries:
        if entry.type == TYPE_INCOME:
            income_by_cat[entry.category] = income_by_cat.get(entry.category, 0) + entry.amount
        else:
            expense_by_cat[entry.category] = expense_by_cat.get(entry.category, 0) + entry.amount

    total_income = sum(income_by_cat.values())
    total_expense = sum(expense_by_cat.values())

    print(f"\n  {year}年{month}月 ({start} ~ {end})")
    print()

    # 收入明细
    if income_by_cat:
        print("  【收入】")
        for cat, amount in sorted(income_by_cat.items(), key=lambda x: -x[1]):
            print(f"    {cat:<8} +{format_amount(amount)}")

    # 支出明细
    if expense_by_cat:
        print("  【支出】")
        for cat, amount in sorted(expense_by_cat.items(), key=lambda x: -x[1]):
            print(f"    {cat:<8} -{format_amount(amount)}")

    # 汇总
    print()
    print(f"  收入合计: +{format_amount(total_income)}")
    print(f"  支出合计: -{format_amount(total_expense)}")
    balance = total_income - total_expense
    sign = "+" if balance >= 0 else ""
    print(f"  本月结余: {sign}{format_amount(balance)}")


def query_by_month():
    """按指定月份查询统计"""
    print("\n--- 按月份查询 ---")

    date_str = safe_input("请输入年月（格式: 2026-05 或 202605）: ")
    if not date_str:
        print("[提示] 已取消")
        return

    # 支持两种格式
    date_str = date_str.replace("/", "-").replace(".", "-")

    try:
        if len(date_str) == 6 and date_str.isdigit():
            # 202605 格式
            year = int(date_str[:4])
            month = int(date_str[4:])
        elif len(date_str) == 7 and "-" in date_str:
            # 2026-05 格式
            parts = date_str.split("-")
            year = int(parts[0])
            month = int(parts[1])
        else:
            print("[错误] 格式不正确，请输入如 2026-05 或 202605")
            return
    except (ValueError, IndexError):
        print("[错误] 无法解析日期")
        return

    if not (1 <= month <= 12):
        print("[错误] 月份必须在 1-12 之间")
        return

    # 复用月份统计逻辑
    from utils import get_month_range
    start, end = get_month_range(year, month)
    entries = storage.load_all()
    month_entries = [e for e in entries if start <= e.date <= end]

    if not month_entries:
        print(f"  {year}年{month}月暂无记录")
        return

    # 和 show_monthly_stats 类似的统计逻辑
    income_by_cat: dict[str, float] = {}
    expense_by_cat: dict[str, float] = {}

    for entry in month_entries:
        if entry.type == TYPE_INCOME:
            income_by_cat[entry.category] = income_by_cat.get(entry.category, 0) + entry.amount
        else:
            expense_by_cat[entry.category] = expense_by_cat.get(entry.category, 0) + entry.amount

    total_income = sum(income_by_cat.values())
    total_expense = sum(expense_by_cat.values())

    print(f"\n  {year}年{month}月 ({start} ~ {end})")
    print()

    if income_by_cat:
        print("  【收入】")
        for cat, amount in sorted(income_by_cat.items(), key=lambda x: -x[1]):
            print(f"    {cat:<8} +{format_amount(amount)}")

    if expense_by_cat:
        print("  【支出】")
        for cat, amount in sorted(expense_by_cat.items(), key=lambda x: -x[1]):
            print(f"    {cat:<8} -{format_amount(amount)}")

    print()
    print(f"  收入合计: +{format_amount(total_income)}")
    print(f"  支出合计: -{format_amount(total_expense)}")
    balance = total_income - total_expense
    sign = "+" if balance >= 0 else ""
    print(f"  本月结余: {sign}{format_amount(balance)}")
    print(f"  共 {len(month_entries)} 条记录")


def delete_entry():
    """
    删除一条记录。

    安全策略：
        1. 先展示列表让用户看到编号
        2. 输入编号后二次确认
        3. 删除前自动备份
    """
    print("\n--- 删除记录 ---")

    entries = storage.load_all()
    if not entries:
        print("（暂无记录）")
        return

    # 展示列表
    print(f"{'编号':>6}  {'日期':<12}  {'类型':<6}  {'分类':<8}  {'金额':>12}  {'备注'}")
    print("-" * 70)
    for entry in entries:
        print(entry.format_display())
    print("-" * 70)

    # 输入编号
    id_str = safe_input("请输入要删除的编号: ")
    if not id_str:
        print("[提示] 已取消")
        return

    try:
        target_id = int(id_str)
    except ValueError:
        print("[错误] 请输入数字编号")
        return

    # 查找目标
    target = None
    for entry in entries:
        if entry.id == target_id:
            target = entry
            break

    if target is None:
        print(f"[错误] 编号 {target_id} 不存在")
        return

    # 二次确认
    print(f"\n即将删除: {target.format_display()}")
    if not confirm("确认删除？此操作不可恢复"):
        print("[提示] 已取消")
        return

    # 先备份
    backup_path = storage.backup()
    if backup_path:
        print(f"[提示] 已自动备份到: {backup_path}")

    # 执行删除
    entries = [e for e in entries if e.id != target_id]

    if storage.save_all(entries):
        print(f"[成功] 已删除编号 {target_id} 的记录")
    else:
        print("[错误] 删除失败，请从备份恢复")


def export_bill():
    """
    导出账单为文本文件。

    生成一个可读性好的 .txt 文件，方便分享或打印。
    """
    print("\n--- 导出账单 ---")

    entries = storage.load_all()
    if not entries:
        print("（暂无记录，无需导出）")
        return

    # 生成导出文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_path = f"账单导出_{timestamp}.txt"

    try:
        with open(export_path, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("          个人账单\n")
            f.write(f"          导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")

            # 写入表头
            f.write(f"{'编号':>6}  {'日期':<12}  {'类型':<6}  {'分类':<8}  {'金额':>12}  {'备注'}\n")
            f.write("-" * 70 + "\n")

            total_income = 0.0
            total_expense = 0.0

            for entry in entries:
                sign = "+" if entry.type == TYPE_INCOME else "-"
                type_name = "收入" if entry.type == TYPE_INCOME else "支出"
                f.write(
                    f"[{entry.id:>4}] {entry.date}  "
                    f"{type_name}  {entry.category:<6}  "
                    f"{sign}{entry.amount:>10.2f}  "
                    f"{entry.note}\n"
                )
                if entry.type == TYPE_INCOME:
                    total_income += entry.amount
                else:
                    total_expense += entry.amount

            f.write("-" * 70 + "\n")
            f.write(f"  收入合计: +{format_amount(total_income)}\n")
            f.write(f"  支出合计: -{format_amount(total_expense)}\n")
            balance = total_income - total_expense
            sign = "+" if balance >= 0 else ""
            f.write(f"  结余:     {sign}{format_amount(balance)}\n")
            f.write(f"\n  共 {len(entries)} 条记录\n")

        print(f"[成功] 账单已导出到: {export_path}")

    except (IOError, OSError) as e:
        print(f"[错误] 导出失败: {e}")


# ============================================================
# 主循环
# ============================================================

def main():
    """
    程序主入口。

    主循环的设计模式：
        1. 显示菜单
        2. 读取用户选择
        3. 分发到对应功能
        4. 循环直到用户选择退出

    这是最经典的"命令分发器"（Command Dispatcher）模式。
    """
    show_banner()

    # 功能分发表：数字 -> 函数
    # 用字典代替 if-elif 链，更易扩展（新增功能只需加一行）
    actions = {
        "1": lambda: add_entry(TYPE_INCOME),
        "2": lambda: add_entry(TYPE_EXPENSE),
        "3": list_entries,
        "4": show_monthly_stats,
        "5": query_by_month,
        "6": delete_entry,
        "7": export_bill,
    }

    while True:
        show_menu()
        choice = safe_input("请选择功能 (0-7): ")

        if choice == "0":
            if confirm("确认退出？"):
                print("再见！")
                break
            continue

        action = actions.get(choice)
        if action:
            action()
        else:
            print("[提示] 无效选择，请输入 0-7")

        # 每次操作后空一行，保持输出整洁
        print()


# ============================================================
# 程序入口
# ============================================================

if __name__ == "__main__":
    """
    Python 的标准入口写法。

    if __name__ == "__main__" 的含义：
        当这个文件被直接运行时，__name__ 的值是 "__main__"
        当这个文件被其他模块 import 时，__name__ 的值是 "main"

    这样设计的好处：
        - 直接运行：执行 main()
        - 被 import：不自动执行，只暴露函数供调用

    这是 Python 工程中最基本的规范之一。
    """
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序被中断，再见！")
        sys.exit(0)
