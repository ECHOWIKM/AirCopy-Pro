# 📱 iPhone-PC 跨设备助手 Pro (AirCopy-Pro)

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-windows-lightgrey.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**打破生态藩篱，连接此刻灵感。** AirCopy-Pro 是一款专为追求极致效率的用户打造的剪贴板互通工具。无需云端中转，通过本地局域网实现 iPhone 到 PC 的秒级同步，支持智能模拟输入，让生产力无缝衔接。

---

## ✨ 核心特性

* 🚀 **无感同步**：iPhone 触发快捷指令，PC 端毫秒级响应。
* ⌨️ **智能模拟**：支持自动粘贴 (`Ctrl+V`) 和自动回车，手机端一键“填表”。
* 🎨 **iOS 交互风格**：精美圆角 UI，完全模拟 iOS 风格的平滑动画开关。
* 🔒 **隐私保护**：本地局域网传输，内置隐私模式（日志敏感信息自动打码）。
* 🛠️ **调试透明**：内置实时 Web 日志控制台，连接问题一目了然。
* 📅 **开机自启**：集成 Windows 注册表操作，支持开机静默运行。

## 📸 界面预览

> ![主界面](https://github.com/ECHOWIKM/AirCopy-Pro/blob/main/picture/%E7%95%8C%E9%9D%A21.png)
> ![主界面2](https://github.com/ECHOWIKM/AirCopy-Pro/blob/main/picture/%E7%95%8C%E9%9D%A22.png)
> ![内置日志器](https://github.com/ECHOWIKM/AirCopy-Pro/blob/main/picture/%E5%86%85%E7%BD%AE%E6%97%A5%E5%BF%97%E5%99%A8.png)

## 🛠️ 安装与运行

### 1. 环境准备
确保你的电脑已安装 Python 3.8+。

### 2. 获取代码并安装依赖
```bash
git clone https://github.com/ECHOWIKM/AirCopy-Pro.git
cd AirCopy-Pro
pip install flask pyside6 pyautogui pyperclip requests pystray pillow 
```
### 3. 运行程序
```bash
python iphone-for-windows.py
```
## 🛠️ 打包指南 (EXE)
如果你希望生成独立的可执行文件，请按照以下步骤操作：

### 1.建议在虚拟环境下操作以减小体积：
```bash
python -m venv venv
.\venv\Scripts\activate
pip install flask pyside6 pyautogui pyperclip requests pystray pillow pyinstaller
```
### 2.执行打包命令：
```bash
pyinstaller --noconfirm --onefile --windowed --add-data "icons;icons" --icon "icons/icon_status.png" iphone-for-windows.py
```
### 📱 iPhone 端配置

#### 方案 A：一键导入指令 (推荐 ⭐️)
<p align="center">
  在 iPhone 上点击链接导入：<br>
  <a href="https://www.icloud.com/shortcuts/5782b63ecb6b415d955cc5001b27cb1d">
    <img src="https://img.shields.io/badge/AirCopy--Pro-一键导入快捷指令-007AFF?style=for-the-badge&logo=apple" alt="AirCopy-Pro 一键导入快捷指令">
  </a>
</p>

1. **导入后**，点击指令右上角的三个点进行编辑。

2. 将最上方的 **“文本”** 框内容修改为你电脑端显示的 **IP 地址** (例如 `192.168.1.5`)。

3. 保存并运行。

#### 方案 B：手动配置
1.打开 iPhone 快捷指令。

2.创建一个新指令：获取剪贴板 -> URL[下方链接内容]-> 获取 URL 内容。

3.URL 格式：http://[你的电脑IP]:5000/copy?msg=[剪贴板文本]。

> ![教程](https://github.com/ECHOWIKM/AirCopy-Pro/blob/main/icons/icon_guide_step_b.png)

推荐配合“`背面轻点`”或“`辅助触控`”使用，体验更佳。
可设置双击“`小白点`”进行粘贴板的传输。

### ❓ 常见问题 (FAQ)
Q: 无法连接到电脑？ A: 请确保手机和电脑处于同一 WiFi 下，并检查 Windows 防火墙是否允许 5000 端口通行。

Q: 打包后 EXE 报错拒绝访问？ A: 请确保后台没有正在运行的旧版本程序，关闭它后再重新打包。

Q: 隐私模式有什么用？ A: 开启后，主界面日志中的文本会以 *** 显示，防止在展示或录屏时泄露敏感剪贴板内容。

### 📜 开源协议
本项目基于 MIT License 协议开源。

---
_如果这个项目帮到了你，请给一个 ⭐️ Star！_