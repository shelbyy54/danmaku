import random
import qrcode
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QTimer, QPoint
from PyQt6.QtGui import QFont, QColor, QPixmap, QImage, QWheelEvent
from PyQt6.QtWidgets import QMainWindow, QLabel, QPushButton, QApplication, QFrame


class DanmuOverlay(QMainWindow):
    """负责渲染弹幕的覆盖窗口"""

    def __init__(self, base_url, room_id):
        super().__init__()
        # 设置窗口标志
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # 设置窗口大小
        screen = QApplication.primaryScreen()
        self.setGeometry(0, 0, screen.size().width(), screen.size().height())

        self.danmu_labels = []
        self.active_animations = []

        # 初始化二维码窗口
        self.qr_code_window = self.create_qr_code_window(base_url, room_id)

        # 关闭按钮
        self.close_btn = QPushButton("×", self)
        self.close_btn.setStyleSheet("""
            QPushButton {
                color: white;
                background-color: rgba(255, 0, 0, 150);
                border-radius: 10px;
                font-size: 16px;
                min-width: 20px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 200);
            }
        """)
        self.close_btn.move(10, 10)
        self.close_btn.clicked.connect(self.close)
        self.close_btn.hide()

        # 鼠标悬停控制
        self.enter_timer = QTimer(self)
        self.enter_timer.setSingleShot(True)
        self.enter_timer.timeout.connect(self.close_btn.hide)

        # 测试弹幕
        QTimer.singleShot(1000, self.show_test_danmu)

    def create_qr_code_window(self, base_url, room_id):
        """创建二维码窗口"""
        # 动态生成二维码内容
        url = f"{base_url}/{room_id}"

        qr_code_window = QFrame(self)
        qr_code_window.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        qr_code_window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        qr_code_window.setStyleSheet("background-color: rgba(255, 255, 255, 128); border: 1px solid #000;")
        qr_code_window.setGeometry(self.width() - 160, 20, 140, 140)

        # 生成二维码
        qr = qrcode.QRCode(box_size=4, border=1)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        qimage = QImage(img.tobytes(), img.size[0], img.size[1], QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage)

        # 显示二维码
        qr_label = QLabel(qr_code_window)
        qr_label.setPixmap(pixmap)
        qr_label.setScaledContents(True)
        qr_label.setGeometry(10, 10, 120, 120)
        qr_code_window.qr_label = qr_label  # 保存引用以便调整大小

        # 添加关闭按钮
        close_button = QPushButton("×", qr_code_window)
        close_button.setStyleSheet("""
            QPushButton {
                color: white;
                background-color: red;
                border-radius: 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: darkred;
            }
        """)
        close_button.setGeometry(110, 0, 30, 30)
        close_button.clicked.connect(qr_code_window.hide)

        # 允许拖动窗口
        qr_code_window.mousePressEvent = self.start_drag
        qr_code_window.mouseMoveEvent = self.perform_drag

        # 支持调整大小
        qr_code_window.mousePressEvent = self.start_resize
        qr_code_window.mouseMoveEvent = self.perform_resize

        # 支持透明度调整
        qr_code_window.wheelEvent = self.adjust_opacity

        qr_code_window.show()
        return qr_code_window

    def start_drag(self, event):
        """记录拖动起始位置"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.globalPosition().toPoint()

    def perform_drag(self, event):
        """执行拖动"""
        if event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self.drag_start_position
            self.qr_code_window.move(self.qr_code_window.pos() + delta)
            self.drag_start_position = event.globalPosition().toPoint()

    def start_resize(self, event):
        """记录调整大小的起始位置"""
        if event.button() == Qt.MouseButton.RightButton:
            self.resize_start_position = event.globalPosition().toPoint()
            self.original_geometry = self.qr_code_window.geometry()

    def perform_resize(self, event):
        """执行调整大小"""
        if event.buttons() == Qt.MouseButton.RightButton:
            delta = event.globalPosition().toPoint() - self.resize_start_position
            new_width = max(100, self.original_geometry.width() + delta.x())
            new_height = max(100, self.original_geometry.height() + delta.y())
            self.qr_code_window.setGeometry(
                self.original_geometry.x(),
                self.original_geometry.y(),
                new_width,
                new_height
            )
            self.qr_code_window.qr_label.setGeometry(10, 10, new_width - 20, new_height - 20)

    def adjust_opacity(self, event: QWheelEvent):
        """调整窗口透明度"""
        current_opacity = self.qr_code_window.windowOpacity()
        delta = event.angleDelta().y() / 1200  # 每次滚动调整透明度
        new_opacity = max(0.1, min(1.0, current_opacity + delta))
        self.qr_code_window.setWindowOpacity(new_opacity)

    def enterEvent(self, event):
        self.close_btn.show()
        self.enter_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.enter_timer.start(2000)
        super().leaveEvent(event)

    def show_danmu(self, text, color="#ffffff", is_teacher=False, font_size=20):
        """显示弹幕"""
        try:
            # 验证颜色值
            if not QColor(color).isValid():
                color = "#ffffff"

            # 创建标签
            label = QLabel(text, self)

            # 构建安全的样式表
            style_parts = [
                f"color: {color}",
                f"font-size: {font_size}px",
                "font-weight: bold" if is_teacher else "font-weight: normal",
                f"background-color: rgba(0, 0, 0, {0.5 if is_teacher else 0.3})",
                "padding: 2px 8px",
                "border-radius: 4px"
            ]
            style_sheet = f"QLabel {{ {'; '.join(style_parts)}; }}"

            label.setStyleSheet(style_sheet)
            label.setFont(QFont("Arial", font_size))
            label.adjustSize()

            # 设置初始位置
            screen_height = self.height()
            y_position = random.randint(50, screen_height - 100)
            label.move(self.width(), y_position)
            label.show()
            label.raise_()

            # 创建动画
            animation = QPropertyAnimation(label, b"geometry")
            duration = max(5000, min(15000, 10000 - (len(text) * 50)))
            animation.setDuration(duration)
            animation.setStartValue(
                QRect(self.width(), y_position, label.width(), label.height()))
            animation.setEndValue(
                QRect(-label.width(), y_position, label.width(), label.height()))

            # 动画完成处理
            animation.finished.connect(lambda: self.remove_danmu(label))
            animation.start()

            self.danmu_labels.append(label)
            self.active_animations.append(animation)

        except Exception as e:
            print(f"显示弹幕错误: {e}")

    def remove_danmu(self, label):
        """移除弹幕"""
        try:
            if label in self.danmu_labels:
                self.danmu_labels.remove(label)
            if hasattr(label, 'animation'):
                self.active_animations.remove(label.animation)
            label.deleteLater()
        except:
            pass

    def show_test_danmu(self):
        """显示测试弹幕"""
        colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF"]
        for i in range(5):
            self.show_danmu(f"测试弹幕 {i+1}", colors[i], i == 0)

    def closeEvent(self, event):
        """关闭时清理资源"""
        for anim in self.active_animations:
            anim.stop()
        for label in self.danmu_labels:
            label.deleteLater()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication([])

    # 测试窗口
    base_url = "http://hacketb.com:7676"  # 替换为实际服务器地址
    room_id = "1145"  # 测试直播间号
    overlay = DanmuOverlay(base_url, room_id)
    overlay.showFullScreen()

    app.exec()
