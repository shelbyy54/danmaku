import socketio
import json
from PyQt6.QtCore import QThread, pyqtSignal

# 读取配置文件
try:
    with open("config.json", "r", encoding="utf-8") as config_file:
        config = json.load(config_file)
except (FileNotFoundError, json.JSONDecodeError):
    # 如果配置文件不存在或格式错误，使用默认配置
    config = {
        "server_url": "hacktb.com:7676"  # 默认服务器地址
    }

# Socket.IO 客户端
sio = socketio.Client()

class SocketIOThread(QThread):
    """负责与服务器通信的 Socket.IO 客户端"""
    new_danmu_signal = pyqtSignal(dict)  # 信号，用于传递接收到的弹幕数据
    connection_error_signal = pyqtSignal(str)  # 信号，用于通知连接错误

    def __init__(self, room_id, username, server_url):
        super().__init__()
        self.room_id = room_id
        self.username = username
        self.server_url = server_url  # 从参数接收服务器地址

    def run(self):
        """运行 Socket.IO 客户端"""
        @sio.event
        def connect():
            print("[DEBUG] 连接到服务器成功")
            sio.emit('join_room', {'room_id': self.room_id, 'username': self.username})

        @sio.event
        def new_danmu(data):
            print(f"[DEBUG] 收到弹幕数据: {data}")  # Debug
            self.new_danmu_signal.emit(data)  # 通过信号传递弹幕数据

        @sio.event
        def disconnect():
            print("[DEBUG] 与服务器断开连接")

        try:
            print(f"[DEBUG] 尝试连接到服务器: {self.server_url}")
            sio.connect(f"http://{self.server_url}", wait_timeout=5)  # 使用 server_url
            sio.wait()  # 保持连接
        except Exception as e:
            error_message = f"连接服务器失败: {e}"
            print(f"[DEBUG] {error_message}")  # Debug
            self.connection_error_signal.emit(error_message)  # 通过信号通知主线程

    def send_danmu(self, content, color):
        """发送弹幕到服务器"""
        print(f"[DEBUG] 发送弹幕: {content}, 颜色: {color}")  # Debug
        sio.emit('send_danmu', {
            'room_id': self.room_id,
            'username': self.username,
            'content': content,
            'color': color
        })