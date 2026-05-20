; ============================================================
; installer.nsi - NSIS 安装包脚本（个人记账本 v1.6）
; ============================================================
;
; 【什么是 NSIS？】
; NSIS（Nullsoft Scriptable Install System）是一个免费的
; Windows 安装包制作工具。它用脚本语言描述安装过程，
; 然后编译成一个 .exe 安装程序。
;
; 你平时下载软件时双击的 "setup.exe"，很多就是 NSIS 做的。
;
; 【NSIS 脚本的基本结构】
; NSIS 脚本由"区段"（Section）和"函数"（Function）组成：
;   Section    = 安装时执行的操作（复制文件、创建快捷方式等）
;   Function   = 可复用的代码块（回调函数、工具函数）
;
; 【NSIS 的回调函数】
; NSIS 有一些预定义的函数名，在特定时机自动调用：
;   .onInit           = 安装程序启动时（显示欢迎界面前）
;   .onInstSuccess    = 安装成功后
;   un.onInit         = 卸载程序启动时
;
; 【编译方式】
;   makensis installer.nsi
; 编译后会生成 "个人记账本_安装程序.exe"
;
; ============================================================


; ============================================================
; 基本信息（安装程序的"身份证"）
; ============================================================

; 名称和版本 —— 显示在安装程序的标题栏和界面中
!define APP_NAME "个人记账本"
!define APP_VERSION "1.6"
!define APP_PUBLISHER "Personal Project"
!define APP_EXE "个人记账本.exe"

; 安装程序的输出文件名（编译后生成的 .exe）
OutFile "个人记账本_安装程序.exe"

; 默认安装目录
; $PROGRAMFILES = C:\Program Files（64位程序）
; $PROGRAMFILES32 = C:\Program Files (x86)（32位程序）
; NSIS 生成的安装程序默认是 32 位的，所以用 $PROGRAMFILES32
; 用户可以在安装界面中修改这个路径
InstallDir "$PROGRAMFILES32\${APP_NAME}"

; 注册表键 —— 记录安装路径
; 下次运行安装程序时，会自动读取上次的安装路径
InstallDirRegKey HKLM "Software\${APP_NAME}" "InstallDir"

; 请求管理员权限（安装到 Program Files 需要）
RequestExecutionLevel admin

; 压缩算法（减少安装包体积）
SetCompressor /SOLID lzma


; ============================================================
; 界面设置
; ============================================================

; 使用现代 UI（Modern UI 2.0）
; MUI2.nsh 提供了美观的向导式安装界面
!include "MUI2.nsh"

; 安装程序图标（显示在安装包的 .exe 图标上）
!define MUI_ICON "assets\icon.ico"
!define MUI_UNICON "assets\icon.ico"

; 安装界面的页面顺序
; MUI_PAGE_WELCOME     = 欢迎页面（"欢迎安装 xxx"）
; MUI_PAGE_DIRECTORY   = 选择安装目录（用户可以修改路径）
; MUI_PAGE_INSTFILES   = 安装进度（复制文件的进度条）
; MUI_PAGE_FINISH      = 完成页面（"安装完成" + 可选"立即运行"）
!define MUI_PAGE_CUSTOMFUNCTION_SHOW WelcomeShowCallback
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; 卸载界面的页面顺序
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; 语言设置（简体中文）
!insertmacro MUI_LANGUAGE "SimpChinese"


; ============================================================
; 版本信息（嵌入到安装程序的 .exe 中）
; ============================================================
; 右键安装程序 → 属性 → 详细信息，可以看到这些信息

VIProductVersion "1.6.0.0"
VIAddVersionKey "ProductName" "${APP_NAME}"
VIAddVersionKey "ProductVersion" "${APP_VERSION}"
VIAddVersionKey "FileDescription" "${APP_NAME} 安装程序"
VIAddVersionKey "LegalCopyright" "Copyright (C) 2026"
VIAddVersionKey "FileVersion" "${APP_VERSION}.0.0"


; ============================================================
; 安装区段 —— 实际执行的安装操作
; ============================================================
; Section 是 NSIS 的核心概念：
;   每个 Section 代表安装过程中的一个"步骤"。
;   安装程序会按顺序执行所有 Section。
;   Section 里的代码就是"复制文件、创建快捷方式"等操作。

Section "安装主程序" SecMain

    ; ---- 设置输出目录（文件复制到哪里）----
    ; $INSTDIR = 用户选择的安装目录（默认 C:\Program Files (x86)\个人记账本）
    ; SetOutPath 设置"当前目标目录"，后续的 File 命令会把文件复制到这里
    SetOutPath "$INSTDIR"

    ; ---- 复制打包好的程序文件 ----
    ; /r 表示递归复制目录下的所有文件和子目录
    ; dist\个人记账本\*.* = PyInstaller 打包输出的整个目录
    ; 这会把 exe、_internal、accounts.json 等全部复制到安装目录
    File /r "dist\个人记账本\*.*"

    ; ---- 创建卸载程序 ----
    ; WriteUninstaller 会在安装目录中生成 "uninstall.exe"
    ; 用户可以通过它来卸载程序
    WriteUninstaller "$INSTDIR\uninstall.exe"

    ; ---- 写入注册表（记录安装信息）----
    ; Windows 的"添加/删除程序"列表从注册表读取信息
    ; 这些注册表键让我们的程序出现在那个列表中

    ; 卸载程序的路径
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
        "UninstallString" '"$INSTDIR\uninstall.exe"'

    ; 显示名称
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
        "DisplayName" "${APP_NAME}"

    ; 版本号
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
        "DisplayVersion" "${APP_VERSION}"

    ; 发布者
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
        "Publisher" "${APP_PUBLISHER}"

    ; 安装路径
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
        "InstallLocation" "$INSTDIR"

    ; 安装路径（供下次安装时读取）
    WriteRegStr HKLM "Software\${APP_NAME}" "InstallDir" "$INSTDIR"

SectionEnd


; ============================================================
; 桌面快捷方式区段
; ============================================================
; 这个 Section 的名称前面有一个 "o"，表示 Optional（可选）
; 用户可以在安装界面中勾选/取消这个选项

Section /o "创建桌面快捷方式" SecDesktop

    ; CreateShortcut：创建快捷方式
    ;   参数1：快捷方式文件路径（放在桌面）
    ;   参数2：目标程序路径
    ;   参数3：工作目录
    ;   参数4：图标路径
    ;   参数5：提示文字（鼠标悬停时显示）
    CreateShortcut "$DESKTOP\${APP_NAME}.lnk" \
        "$INSTDIR\${APP_EXE}" \
        "$INSTDIR" \
        "$INSTDIR\assets\icon.ico" \
        0 \
        SW_SHOWNORMAL \
        "" \
        "打开${APP_NAME}"

SectionEnd


; ============================================================
; 开始菜单快捷方式区段
; ============================================================

Section "创建开始菜单快捷方式" SecStartMenu

    ; 创建开始菜单文件夹
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"

    ; 创建开始菜单快捷方式
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" \
        "$INSTDIR\${APP_EXE}" \
        "$INSTDIR" \
        "$INSTDIR\assets\icon.ico" \
        0

    ; 创建卸载快捷方式
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\卸载${APP_NAME}.lnk" \
        "$INSTDIR\uninstall.exe"

SectionEnd


; ============================================================
; 回调函数 —— 安装过程中的"钩子"
; ============================================================

Function WelcomeShowCallback
    ; 欢迎页面显示时的回调
    ; 可以在这里修改界面文字等
    ; 当前为空，保留占位
FunctionEnd


; ============================================================
; .onInit —— 安装程序启动时执行
; ============================================================
; 这个函数在用户双击安装程序后立即执行，
; 在显示任何界面之前。
; 可以用来做初始化检查（比如检测是否已安装）。

Function .onInit

    ; 检查是否已经安装过
    ; 如果注册表中有安装路径，说明已安装
    ReadRegStr $0 HKLM "Software\${APP_NAME}" "InstallDir"
    ${If} $0 != ""
        ; 已安装，询问是否覆盖安装
        MessageBox MB_YESNO|MB_ICONQUESTION \
            "检测到 ${APP_NAME} 已安装在 $0$\n$\n是否覆盖安装？" \
            IDYES ContinueInstall
        ; 用户选择"否"，退出安装程序
        Abort
        ContinueInstall:
    ${EndIf}

FunctionEnd


; ============================================================
; .onInstSuccess —— 安装成功后执行
; ============================================================
; 这个函数在所有文件复制完成后执行。
; 我们用它来实现"安装完成后删除安装包"和"打开软件"的功能。
;
; NSIS 的全局变量 $EXEFILE 是安装程序自身的文件名。
; $CMDLINE 是命令行参数。
;
; 注意：删除安装包需要安装程序在运行结束后才能删除自己，
; 所以我们用 cmd /c 的方式延迟删除。

Function .onInstSuccess

    ; ---- 询问是否删除安装包 ----
    MessageBox MB_YESNO|MB_ICONQUESTION \
        "安装完成！$\n$\n是否删除安装程序？" \
        IDYES DeleteInstaller IDNO SkipDelete

    DeleteInstaller:
        ; 使用 cmd /c ping 延迟 2 秒后删除安装程序
        ; 为什么需要延迟？因为安装程序还在运行，不能立即删除自己
        ; ping 127.0.0.1 -n 3 > nul = 等待约 2 秒
        ; del "%~f0" = 删除自身（%~f0 = 当前脚本的完整路径）
        Exec 'cmd /c ping 127.0.0.1 -n 3 > nul & del "$EXEPATH"'
    SkipDelete:

    ; ---- 询问是否打开软件 ----
    MessageBox MB_YESNO|MB_ICONQUESTION \
        "是否立即打开 ${APP_NAME}？" \
        IDYES LaunchApp IDNO SkipLaunch

    LaunchApp:
        Exec '"$INSTDIR\${APP_EXE}"'
    SkipLaunch:

FunctionEnd


; ============================================================
; 卸载区段 —— 卸载时执行的操作
; ============================================================
; 当用户通过"添加/删除程序"或运行 uninstall.exe 卸载时，
; 这个 Section 会被执行。

Section "Uninstall"

    ; ---- 删除安装目录中的所有文件 ----
    ; RMDir /r = 递归删除目录及其所有内容
    RMDir /r "$INSTDIR"

    ; ---- 删除桌面快捷方式 ----
    Delete "$DESKTOP\${APP_NAME}.lnk"

    ; ---- 删除开始菜单快捷方式 ----
    RMDir /r "$SMPROGRAMS\${APP_NAME}"

    ; ---- 删除注册表键 ----
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
    DeleteRegKey HKLM "Software\${APP_NAME}"

SectionEnd


; ============================================================
; 卸载回调函数
; ============================================================

Function un.onInit
    ; 卸载程序启动时的回调
    ; 可以在这里添加确认对话框等
    MessageBox MB_YESNO|MB_ICONQUESTION \
        "确定要卸载 ${APP_NAME} 吗？$\n$\n所有程序文件将被删除。" \
        IDYES ContinueUninstall
    Abort
    ContinueUninstall:
FunctionEnd
