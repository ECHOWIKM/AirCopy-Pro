import sys
import os
import threading
import urllib.parse
import winreg
import pyautogui
import pyperclip
import time
import requests
import socket
import logging
from pystray import Icon, Menu, MenuItem
from PIL import Image
from flask import Flask, request
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTextEdit, QMessageBox, 
                             QFrame, QStackedWidget, QDialog)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, Property, QSize
from PySide6.QtGui import QIcon, QCursor, QPainter, QColor, QBrush, QPixmap

app = Flask(__name__)

# ========================================================
# 图标本地映射配置 - 100% 精准下载
# ========================================================
ICON_MAP = {
    "status": "https://cdn-icons-png.flaticon.com/128/9073/9073032.png",
    "settings": "https://cdn-icons-png.flaticon.com/128/10024/10024002.png",
    "guide": "https://cdn-icons-png.flaticon.com/128/4961/4961759.png",
    "about": "https://cdn-icons-png.flaticon.com/128/9195/9195785.png",
    "autostart": "https://cdn-icons-png.flaticon.com/128/14441/14441294.png",
    "paste": "https://cdn-icons-png.flaticon.com/128/9703/9703060.png",
    "enter": "https://cdn-icons-png.flaticon.com/128/10024/10024455.png",
    "dup": "https://cdn-icons-png.flaticon.com/128/14090/14090371.png",
    "privacy": "https://cdn-icons-png.flaticon.com/128/4413/4413865.png",
    "debug": "https://cdn-icons-png.flaticon.com/128/10061/10061742.png", # 齿轮按钮
    "about_view": "https://cdn-icons-png.flaticon.com/128/639/639371.png" # 新增：关于我们主图
}

# 自定义日志处理器
class FlaskLogHandler(logging.Handler):
    def __init__(self, signal):
        super().__init__()
        self.signal = signal
    def emit(self, record):
        msg = self.format(record)
        self.signal.emit(msg)

# ========================================================
# 1. iOS 风格平滑动画开关组件
# ========================================================
class IOSSwitch(QWidget):
    state_signal = Signal(bool)
    def __init__(self, parent=None, active_color="#34C759"):
        super().__init__(parent)
        self.setFixedSize(52, 31)
        self.is_on = False
        self.is_pressed = False
        self._active_color = QColor(active_color)
        self._off_color = QColor("#D1D1D6")
        self._thumb_color = QColor("#FFFFFF")
        self._current_background = self._off_color
        self._thumb_x = 3.0
        self._thumb_scale = 1.0
        self.anim_thumb_move = QPropertyAnimation(self, b"thumb_x")
        self.anim_thumb_move.setDuration(160)
        self.anim_thumb_move.setEasingCurve(QEasingCurve.OutQuad)
        self.anim_color = QPropertyAnimation(self, b"current_background")
        self.anim_color.setDuration(160)
        self.setCursor(Qt.PointingHandCursor)

    @Property(float)
    def thumb_x(self): return self._thumb_x
    @thumb_x.setter
    def thumb_x(self, x): self._thumb_x = x; self.update()
    @Property(QColor)
    def current_background(self): return self._current_background
    @current_background.setter
    def current_background(self, color): self._current_background = color; self.update()

    def paintEvent(self, event):
        painter = QPainter(self); painter.setRenderHint(QPainter.Antialiasing); painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self._current_background)); painter.drawRoundedRect(0, 0, self.width(), self.height(), 15.5, 15.5)
        painter.setBrush(QBrush(self._thumb_color))
        diameter = 27 * self._thumb_scale 
        painter.drawEllipse(self._thumb_x, 2, diameter, diameter)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: self.is_pressed = True; self._thumb_scale = 1.08; self.update()
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_pressed: self.is_pressed = False; self._thumb_scale = 1.0; self.toggle_state()
    def setChecked(self, checked, animate=True):
        if self.is_on == checked: return
        self.is_on = checked; self.animate_to_current_state(animate)
    def isChecked(self): return self.is_on
    def toggle_state(self): self.setChecked(not self.is_on); self.state_signal.emit(self.is_on)
    def animate_to_current_state(self, animate):
        end_x, end_color = (22.0, self._active_color) if self.is_on else (3.0, self._off_color)
        if animate:
            self.anim_thumb_move.setEndValue(end_x); self.anim_thumb_move.start()
            self.anim_color.setEndValue(end_color); self.anim_color.start()
        else: self._thumb_x = end_x; self._current_background = end_color; self.update()

# ========================================================
# 2. 调试日志对话框
# ========================================================
class DebugConsole(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系统调试日志 (Flask Console)")
        self.resize(700, 400)
        layout = QVBoxLayout(self)
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet("""
            background-color: #1C1C1E; 
            color: #FFFFFF; 
            font-family: 'Consolas', monospace; 
            font-size: 11px;
            border-radius: 8px;
            padding: 10px;
        """)
        layout.addWidget(self.log_view)
        clear_btn = QPushButton("清空实时日志")
        clear_btn.setStyleSheet("padding: 8px; border-radius: 5px; background: #3A3A3C; color: white;")
        clear_btn.clicked.connect(self.log_view.clear)
        layout.addWidget(clear_btn)
    def append_log(self, text):
        self.log_view.append(text)
        self.log_view.ensureCursorVisible()

# ========================================================
# 3. 主程序
# ========================================================
class SyncApp(QMainWindow):
    log_signal = Signal(str)
    ask_signal = Signal(str)
    device_signal = Signal(str)
    flask_debug_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self.is_running = True
        self.last_text = ""
        self.icons_dir = os.path.join(os.getcwd(), "icons")
        
        # 获取信息
        self.local_hostname = socket.gethostname()
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            self.local_ip = s.getsockname()[0]
            s.close()
        except: self.local_ip = "127.0.0.1"

        pyautogui.PAUSE = 0.05
        pyautogui.FAILSAFE = False
        
        self.ensure_icons_ready()
        self.init_ui()
        self.create_tray_icon()
        self.debug_window = DebugConsole(self)
        self.flask_debug_signal.connect(self.debug_window.append_log)
        flask_logger = logging.getLogger('werkzeug')
        flask_logger.setLevel(logging.INFO)
        flask_logger.addHandler(FlaskLogHandler(self.flask_debug_signal))
        self.start_server()

    def ensure_icons_ready(self):
        if not os.path.exists(self.icons_dir): os.makedirs(self.icons_dir)
        self.main_icon_path = os.path.join(self.icons_dir, "main_icon.png")
        if not os.path.exists(self.main_icon_path):
            try:
                r = requests.get("https://cdn-icons-png.flaticon.com/512/644/644458.png", timeout=5)
                with open(self.main_icon_path, 'wb') as f: f.write(r.content)
            except: pass
        for key, url in ICON_MAP.items():
            path = os.path.join(self.icons_dir, f"icon_{key}.png")
            if not os.path.exists(path):
                try:
                    r = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
                    with open(path, 'wb') as f: f.write(r.content)
                except: print(f"下载图标 {key} 失败")

    def get_icon(self, key):
        path = os.path.join(self.icons_dir, f"icon_{key}.png")
        return QIcon(path) if os.path.exists(path) else QIcon()

    def init_ui(self):
        self.setWindowTitle("iPhone-PC 跨设备助手 Pro")
        if os.path.exists(self.main_icon_path): self.setWindowIcon(QIcon(self.main_icon_path))
        self.resize(900, 680)
        self.setStyleSheet("""
            QMainWindow { background-color: #F2F2F7; }
            #Sidebar { background-color: #FFFFFF; border-right: 1px solid #E5E5EA; min-width: 200px; }
            #NavBtn { 
                background: transparent; border: none; border-radius: 10px; 
                padding: 12px 20px; text-align: left; font-size: 15px; color: #3A3A3C; outline: none; 
            }
            #NavBtn:hover { background-color: #F2F2F7; }
            #NavBtn[active="true"] { background-color: #007AFF; color: white; font-weight: bold; }
            #GlassCard { background-color: white; border-radius: 15px; border: 1px solid #E5E5EA; }
            #InfoCard { background-color: #F2F2F7; border-radius: 10px; padding: 10px; margin-top: 10px; }
            #DebugBtn { background: transparent; border: none; padding: 5px; cursor: pointer; }
            #DebugBtn:hover { background: #E5E5EA; border-radius: 8px; }
        """)

        central_widget = QWidget(); self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)

        sidebar = QFrame(); sidebar.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(sidebar); sidebar_layout.setContentsMargins(15, 30, 15, 20)
        sidebar_layout.addWidget(QLabel("📱", styleSheet="font-size: 45px;", alignment=Qt.AlignCenter))
        sidebar_layout.addWidget(QLabel("iPhone-PC", styleSheet="font-size: 18px; font-weight: bold;", alignment=Qt.AlignCenter))

        info_card = QFrame(); info_card.setObjectName("InfoCard")
        info_layout = QVBoxLayout(info_card)
        info_layout.addWidget(QLabel(f"本机: {self.local_hostname}"))
        ip_lbl = QLabel(f"IP: {self.local_ip}"); ip_lbl.setStyleSheet("color: #007AFF; font-weight: bold;")
        info_layout.addWidget(ip_lbl)
        self.connected_device_label = QLabel("连接设备: 等待中...")
        info_layout.addWidget(self.connected_device_label)
        sidebar_layout.addWidget(info_card); sidebar_layout.addSpacing(20)

        self.nav_btns = []
        self.nav_btns.append(self.create_nav_btn("  运行状态", "status", True))
        self.nav_btns.append(self.create_nav_btn("  功能设置", "settings", False))
        self.nav_btns.append(self.create_nav_btn("  新手教程", "guide", False))
        self.nav_btns.append(self.create_nav_btn("  关于我们", "about", False))
        for b in self.nav_btns: sidebar_layout.addWidget(b)
        sidebar_layout.addStretch(); layout.addWidget(sidebar)

        self.pages = QStackedWidget()
        self.init_status_page(); self.init_settings_page(); self.init_guide_page(); self.init_about_page()
        layout.addWidget(self.pages)

        self.log_signal.connect(self.update_log)
        self.ask_signal.connect(self.show_confirm_dialog)
        self.device_signal.connect(lambda name: self.connected_device_label.setText(f"连接设备: {name}"))

    def create_nav_btn(self, text, icon_key, is_active):
        btn = QPushButton(text); btn.setObjectName("NavBtn"); btn.setFocusPolicy(Qt.NoFocus)
        btn.setProperty("active", is_active); btn.setCursor(Qt.PointingHandCursor)
        btn.setIcon(self.get_icon(icon_key)); btn.setIconSize(QSize(20, 20))
        btn.clicked.connect(self.handle_nav_click)
        return btn

    def handle_nav_click(self):
        clicked_btn = self.sender()
        for i, btn in enumerate(self.nav_btns):
            is_match = (btn == clicked_btn)
            btn.setProperty("active", is_match); btn.style().unpolish(btn); btn.style().polish(btn)
            if is_match: self.pages.setCurrentIndex(i)

    def init_status_page(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(30, 30, 30, 30)
        layout.addWidget(QLabel("运行状态", styleSheet="font-size: 24px; font-weight: bold; margin-bottom: 15px;"))
        card = QFrame(); card.setObjectName("GlassCard"); cl = QHBoxLayout(card); cl.setContentsMargins(20,20,20,20)
        self.status_lbl = QLabel("● 服务运行中"); self.status_lbl.setStyleSheet("color: #34C759; font-size: 18px; font-weight: bold;")
        self.switch_btn = QPushButton("暂停接收服务"); self.switch_btn.setFocusPolicy(Qt.NoFocus)
        self.switch_btn.setStyleSheet("background: #FF3B30; color: white; border-radius: 8px; padding: 10px 20px; font-weight: bold;")
        self.switch_btn.clicked.connect(self.toggle_service)
        cl.addWidget(self.status_lbl); cl.addStretch(); cl.addWidget(self.switch_btn); layout.addWidget(card)
        layout.addWidget(QLabel("\n实时同步日志:")); self.log_area = QTextEdit(); self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background: #1C1C1E; color: #32D74B; border-radius: 12px; padding: 15px; font-family: 'Consolas';")
        layout.addWidget(self.log_area); self.pages.addWidget(page)

    def init_settings_page(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(30, 30, 30, 30)
        layout.addWidget(QLabel("功能设置", styleSheet="font-size: 24px; font-weight: bold; margin-bottom: 15px;"))
        card = QFrame(); card.setObjectName("GlassCard"); card_layout = QVBoxLayout(card)
        def add_item(text, icon_key, color="#34C759", chk=True):
            w = QWidget(); l = QHBoxLayout(w); l.setContentsMargins(15, 12, 15, 12)
            icon_lbl = QLabel(); icon_lbl.setFixedSize(22, 22)
            path = os.path.join(self.icons_dir, f"icon_{icon_key}.png")
            if os.path.exists(path): icon_lbl.setPixmap(QPixmap(path).scaled(22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            sw = IOSSwitch(active_color=color); sw.setChecked(chk, False)
            l.addWidget(icon_lbl); l.addWidget(QLabel(text)); l.addStretch(); l.addWidget(sw)
            card_layout.addWidget(w); return sw
        self.auto_start_sw = add_item("系统开机自动启动", "autostart", chk=self.check_auto_start_status())
        self.auto_paste_sw = add_item("智能模拟输入 (自动粘贴)", "paste")
        self.auto_enter_sw = add_item("模拟输入后自动发送 (回车)", "enter")
        self.dup_check_sw = add_item("开启重复内容校验确认弹窗", "dup")
        self.privacy_sw = add_item("隐私保护模式 (打码日志)", "privacy", color="#FF9500")
        self.auto_start_sw.state_signal.connect(lambda s: self.toggle_auto_start(2 if s else 0))
        layout.addWidget(card); layout.addStretch()

        # 右下角调试齿轮 - 彻底移除了多余默认图标
        debug_box = QHBoxLayout()
        debug_box.addStretch()
        self.debug_btn = QPushButton(); self.debug_btn.setObjectName("DebugBtn")
        self.debug_btn.setIcon(self.get_icon("debug")); self.debug_btn.setIconSize(QSize(28, 28))
        self.debug_btn.setToolTip("打开原始调试控制台")
        self.debug_btn.clicked.connect(lambda: self.debug_window.show())
        debug_box.addWidget(self.debug_btn)
        layout.addLayout(debug_box)
        self.pages.addWidget(page)

    def init_guide_page(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(30, 30, 30, 30)
        layout.addWidget(QLabel("新手使用教程", styleSheet="font-size: 24px; font-weight: bold; margin-bottom: 15px;"))
        guide_area = QTextEdit(); guide_area.setReadOnly(True)
        guide_area.setStyleSheet("background: white; border-radius: 12px; padding: 20px; font-size: 14px;")
        guide_content = f"""
        <h2 style='color: #007AFF;'>第一步：网络配置</h2>
        <p>确保手机和电脑在同一 Wi-Fi。</p>
        <h2 style='color: #007AFF;'>第二步：快捷指令配置</h2>
        <p>URL 填写：<code style='background: #F2F2F7;'>http://{self.local_ip}:5000/copy?msg=[剪贴板]&device=iPhone</code></p>
        <p>方法建议选择 <b>GET</b>。</p>
        """
        guide_area.setHtml(guide_content); layout.addWidget(guide_area); self.pages.addWidget(page)

    def init_about_page(self):
        """重构：关于我们页，添加主图和精美介绍"""
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(30, 30, 30, 30)
        layout.setAlignment(Qt.AlignCenter)

        # 添加商务主图
        about_img_lbl = QLabel()
        path = os.path.join(self.icons_dir, "icon_about_view.png")
        if os.path.exists(path):
            about_img_lbl.setPixmap(QPixmap(path).scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        about_img_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(about_img_lbl)
        layout.addSpacing(20)

        # 好看、有愿景的 HTML 介绍
        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setStyleSheet("background: transparent; border: none; font-size: 14px;")
        
        # 介绍文本，介绍功能与愿景
        intro_content = """
        <div style='color: #3A3A3C; font-family: system-ui; text-align: center; line-height: 1.6;'>
            <h1 style='color: #007AFF; margin-bottom: 5px;'>iPhone-PC 跨设备助手 Pro</h1>
            <p style='color: #8E8E93; font-size: 12px; margin-top: 0;'>Version 2.6.0</p>
            
            <p style='margin-top: 20px; font-size: 15px;'>
                打破生态藩篱，连接此刻灵感。<br>
                这是一个专为追求极致效率的用户打造的剪贴板互通工具。
            </p>
            
            <p style='color: #007AFF; font-weight: bold; margin-top: 20px;'>--- 功能核心 ---</p>
            <p>基于本地局域网，实现 iPhone 剪贴板<b>文本与链接</b>秒级同步至 PC。<br>
               配合智能模拟输入，让你不仅是同步，更是直接应用。
            </p>

            <p style='color: #007AFF; font-weight: bold; margin-top: 20px;'>--- 愿景使命 ---</p>
            <p>我们致力于在多设备碎片化的时代，打造最无感的跨端体验。<br>
               让信息在不同系统间自由流动，把时间还给创造力本身。
            </p>
            
            <p style='color: #8E8E93; margin-top: 30px; font-size: 12px;'>图标提供: Flaticon</p>
        </div>
        """
        about_text.setHtml(intro_content)
        layout.addWidget(about_text)
        self.pages.addWidget(page)

    def show_confirm_dialog(self, text):
        self.msg_dialog = QMessageBox(self)
        self.msg_dialog.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)
        self.msg_dialog.setWindowTitle("重复同步确认")
        self.msg_dialog.setText("内容已存入剪贴板。")
        self.msg_dialog.setInformativeText("是否需要再次触发模拟输入动作？")
        btn_yes = self.msg_dialog.addButton("再次同步", QMessageBox.YesRole)
        self.msg_dialog.addButton("仅保留复制", QMessageBox.NoRole)
        self.msg_dialog.exec()
        if self.msg_dialog.clickedButton() == btn_yes: self.execute_typing_action(text)

    def execute_typing_action(self, text):
        self.last_text = text; pyperclip.copy(text) 
        if self.isActiveWindow() or (hasattr(self, 'msg_dialog') and self.msg_dialog.isVisible()):
            self.hide(); time.sleep(0.4) 
        try:
            if self.auto_paste_sw.isChecked(): pyautogui.hotkey('ctrl', 'v'); time.sleep(0.1)
            if self.auto_enter_sw.isChecked(): pyautogui.press('enter')
        except Exception as e: self.log_signal.emit(f"模拟失败: {e}")
        disp = f"{text[:4]}***" if self.privacy_sw.isChecked() else text
        self.log_signal.emit(f"同步成功: {disp}")

    def create_tray_icon(self):
        def on_open(): self.showNormal(); self.activateWindow()
        img = Image.open(self.main_icon_path) if os.path.exists(self.main_icon_path) else Image.new('RGB',(64,64),(0,122,255))
        menu = Menu(MenuItem('显示助手', on_open, default=True), MenuItem('退出', lambda: os._exit(0)))
        self.tray = Icon("iPhoneSync", img, "iPhone 同步助手", menu)
        threading.Thread(target=self.tray.run, daemon=True).start()

    def toggle_service(self):
        self.is_running = not self.is_running
        self.status_lbl.setText("● 服务运行中" if self.is_running else "○ 服务已暂停")
        self.switch_btn.setText("暂停接收服务" if self.is_running else "开启接收服务")
        self.switch_btn.setStyleSheet(f"background: {'#FF3B30' if self.is_running else '#34C759'}; color: white; border-radius: 8px; padding: 10px 20px; font-weight: bold;")

    def update_log(self, text): self.log_area.append(f"[{time.strftime('%H:%M:%S')}] {text}")

    def start_server(self):
        def run():
            @app.route('/copy')
            def copy_route():
                msg = request.args.get('msg', '')
                device = request.args.get('device', 'iPhone')
                if msg:
                    self.device_signal.emit(device)
                    self.handle_sync_logic(urllib.parse.unquote(msg).strip()); return "OK", 200
                return "Empty", 400
            app.run(host='0.0.0.0', port=5000, threaded=True)
        threading.Thread(target=run, daemon=True).start()

    def handle_sync_logic(self, text):
        if not self.is_running: return
        pyperclip.copy(text) 
        if self.dup_check_sw.isChecked() and text == self.last_text: self.ask_signal.emit(text)
        else: self.execute_typing_action(text)

    def check_auto_start_status(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, "iPhoneClipboardSync"); return True
        except: return False

    def toggle_auto_start(self, state):
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_WRITE)
        if state == 2: winreg.SetValueEx(key, "iPhoneClipboardSync", 0, winreg.REG_SZ, f'"{os.path.realpath(sys.argv[0])}"')
        else: 
            try: winreg.DeleteValue(key, "iPhoneClipboardSync")
            except: pass

    def closeEvent(self, event): event.ignore(); self.hide()

if __name__ == "__main__":
    qt_app = QApplication(sys.argv)
    window = SyncApp(); window.show(); sys.exit(qt_app.exec())