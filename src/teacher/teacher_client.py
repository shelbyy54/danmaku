import sys
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLineEdit, QPushButton, QWidget,
    QMessageBox, QTextEdit, QSlider, QLabel, QHBoxLayout
)
from PyQt6.QtCore import Qt
from socket_client import SocketIOThread
from danmu_renderer import DanmuOverlay


class TeacherClient(QMainWindow):
    """教师端主窗口"""
    def __init__(self, room_id, username, server_url):
        super().__init__()
        self.room_id = room_id
        self.username = username
        self.server_url = server_url
        self.setWindowTitle(f"教师端 - 直播间 {room_id}")
        self.setGeometry(100, 100, 800, 600)

        # 弹幕颜色和字号
        self.danmu_color = "#ff0000"  # 默认红色
        self.danmu_font_size = 20  # 默认字号

        # 初始化UI
        self.init_ui()

        # 初始化覆盖弹幕窗口
        self.overlay_window = DanmuOverlay()
        self.overlay_active = False

        # 初始化 Socket.IO 客户端
        self.socket_client = SocketIOThread(room_id, username, server_url)
        self.socket_client.new_danmu_signal.connect(self.handle_new_danmu)
        self.socket_client.connection_error_signal.connect(self.handle_connection_error)
        self.socket_client.start()

    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout()

        # 输入弹幕
        self.danmu_input = QLineEdit(self)
        self.danmu_input.setPlaceholderText("输入弹幕内容")
        layout.addWidget(self.danmu_input)

        # 发送弹幕按钮
        self.send_button = QPushButton("发送弹幕", self)
        self.send_button.clicked.connect(self.send_danmu)
        layout.addWidget(self.send_button)

        # 弹幕字号调节
        font_size_layout = QHBoxLayout()
        font_size_label = QLabel("弹幕字号:", self)
        font_size_layout.addWidget(font_size_label)

        self.font_size_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.font_size_slider.setRange(10, 50)  # 字号范围 10 到 50
        self.font_size_slider.setValue(self.danmu_font_size)
        self.font_size_slider.valueChanged.connect(self.update_font_size)
        font_size_layout.addWidget(self.font_size_slider)

        self.font_size_display = QLabel(f"{self.danmu_font_size}px", self)
        font_size_layout.addWidget(self.font_size_display)

        layout.addLayout(font_size_layout)

        # 启动覆盖弹幕窗口按钮
        self.overlay_button = QPushButton("启动覆盖", self)
        self.overlay_button.clicked.connect(self.toggle_overlay)
        layout.addWidget(self.overlay_button)

        # 弹幕历史记录
        self.history_box = QTextEdit(self)
        self.history_box.setReadOnly(True)  # 设置为只读
        self.history_box.setAcceptRichText(True)  # 确保支持 HTML 渲染
        layout.addWidget(self.history_box)

        # 主窗口设置
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def update_font_size(self, value):
        """更新弹幕字号"""
        self.danmu_font_size = value
        self.font_size_display.setText(f"{value}px")

    def handle_new_danmu(self, data):
        """处理新弹幕"""
        print(f"[DEBUG] 处理新弹幕: {data}")  # Debug: 打印收到的弹幕数据
        username = data.get('username', '匿名用户')
        content = data.get('content', '')
        color = data.get('color', '#ffffff')
        is_teacher = username == "教师"

        # 更新历史记录
        self.history_box.append(f'<span style="color:{color}">[{username}] {content}</span>')

        # 如果覆盖窗口激活，则显示弹幕
        if self.overlay_active:
            self.overlay_window.show_danmu(content, color, is_teacher, self.danmu_font_size)

    def send_danmu(self):
        """发送弹幕"""
        content = self.danmu_input.text().strip()
        if not content:
            QMessageBox.warning(self, "输入错误", "弹幕内容不能为空！")
            return

        self.socket_client.send_danmu(content, self.danmu_color)

    def toggle_overlay(self):
        """切换覆盖弹幕窗口的状态"""
        if self.overlay_active:
            self.overlay_window.hide()
            self.overlay_button.setText("启动覆盖")
            self.overlay_active = False
        else:
            self.overlay_window.showFullScreen()
            self.overlay_button.setText("关闭覆盖")
            self.overlay_active = True

    def handle_connection_error(self, error_message):
        """处理连接错误"""
        QMessageBox.warning(self, "连接错误", error_message)  # 显示警告弹窗


class MainWindow(QWidget):
    """教师端启动界面"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("教师端弹幕系统")
        self.setGeometry(100, 100, 400, 300)
        self.center_window()

        try:
            # 尝试读取配置文件
            with open("config.json", "r", encoding="utf-8") as config_file:
                self.config = json.load(config_file)
        except (FileNotFoundError, json.JSONDecodeError):
            # 如果配置文件不存在或格式错误，使用默认配置
            self.config = {
                "server_url": "hacktb.com:7676"  # 默认服务器地址
            }

        # 布局
        layout = QVBoxLayout()

        # 输入服务器地址
        self.server_input = QLineEdit(self)
        self.server_input.setPlaceholderText(f"请输入服务器地址（默认：{self.config.get('server_url', 'hacktb.com:7676')}）")
        layout.addWidget(self.server_input)

        # 输入用户名
        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("请输入您的名称（默认：教师）")
        layout.addWidget(self.name_input)

        # 输入直播间号
        self.room_input = QLineEdit(self)
        self.room_input.setPlaceholderText("请输入直播间号")
        layout.addWidget(self.room_input)

        # 启动按钮
        self.start_button = QPushButton("进入直播间", self)
        self.start_button.clicked.connect(self.start_client)
        layout.addWidget(self.start_button)

        self.setLayout(layout)

    def center_window(self):
        """将窗口居中"""
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )

    def start_client(self):
        """启动教师端主窗口"""
        room_id = self.room_input.text().strip()
        if not room_id:
            QMessageBox.warning(self, "输入错误", "直播间号不能为空！")
            return

        username = self.name_input.text().strip() or "教师"
        server_url = self.server_input.text().strip() or self.config.get("server_url", "hacktb.com:7676")

        # 启动教师端主窗口
        self.client_window = TeacherClient(room_id, username, server_url)
        self.client_window.show()
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 创建主窗口
    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec())