# 📱 iPhone-PC 跨设备助手 Pro (AirCopy-Pro)

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-windows-lightgrey.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**打破生态藩篱，连接此刻灵感。** 这是一个专为追求极致效率的用户打造的剪贴板互通工具。通过本地局域网，实现从 iPhone 剪贴板到 PC 的秒级同步，并支持智能模拟输入。

---

## ✨ 核心特性

* 🚀 **无感同步**：iPhone 触发快捷指令，PC 端瞬间响应。
* ⌨️ **智能模拟**：支持自动粘贴 (`Ctrl+V`) 和自动回车，实现数据从手机到电脑的一键直达。
* 🎨 **iOS 交互风格**：基于 PySide6 打造的高颜值 UI 界面，平滑的动画开关。
* 🔒 **隐私保护**：内置隐私模式，日志敏感信息自动打码。
* 🛠️ **调试透明**：内置实时 Web 日志控制台，方便排查连接问题。
* 📅 **开机自启**：集成 Windows 注册表操作，支持开机自动运行。

## 📸 界面预览

*(此处建议上传几张你运行程序的截图到 GitHub，并替换下方的链接)*
> ![主界面](https://your-image-link-here.com/main.png)

## 🛠️ 安装与运行

### 1. 环境准备
确保你的电脑已安装 Python 3.8+。

### 2. 安装依赖
```bash
pip install flask pyside6 pyautogui pyperclip requests pystray pillow