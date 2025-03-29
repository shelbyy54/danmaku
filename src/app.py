from flask import Flask, render_template, request, abort, send_file
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
from collections import defaultdict, deque
import json
import logging
import os

# 初始化 Flask 应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# 配置日志
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

# 读取配置文件
config_path = os.path.join(os.path.dirname(__file__), "config.json")
if not os.path.exists(config_path):
    logging.error("配置文件 config.json 不存在")
    raise FileNotFoundError("配置文件 config.json 不存在")
with open(config_path, "r", encoding="utf-8") as config_file:
    config = json.load(config_file)

# 获取服务器地址
server_url = config.get("server_url", "127.0.0.1:7676")

# 每个直播间的弹幕历史记录和在线用户
MAX_HISTORY = 100
rooms_data = defaultdict(lambda: {
    "danmu_history": deque(maxlen=MAX_HISTORY),
    "online_users": {}
})


@app.route("/")
def index():
    """主页，输入直播间号"""
    return render_template("index.html", server_url=server_url)


@app.route("/<room_id>")
def danmuku(room_id):
    """渲染指定直播间页面"""
    if not room_id.isdigit():
        logging.warning(f"非法房间号访问: {room_id}")
        abort(400, description="非法的房间号")
    return render_template("danmuku.html", server_url=server_url, room_id=room_id)


@app.route('/download_teacher_client')
def download_teacher_client():
    """提供教师端下载（受限）"""
    # 明确指定允许下载的文件路径
    file_path = os.path.join(os.path.dirname(__file__), "TeacherClient.exe")
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        logging.error("尝试下载的文件不存在")
        abort(404, description="文件不存在")
    
    # 返回文件
    return send_file(file_path, as_attachment=True)


@socketio.on('join_room')
def handle_join_room(data):
    """处理用户加入直播间"""
    room_id = data.get('room_id')
    username = data.get('username', '匿名用户')
    join_room(room_id)

    rooms_data[room_id]["online_users"][request.sid] = username
    logging.info(f"用户 {username} 加入直播间 {room_id}")

    for message in list(rooms_data[room_id]["danmu_history"])[-10:]:
        emit('new_danmu', message, to=request.sid)

    emit('user_list_updated', list(rooms_data[room_id]["online_users"].values()), room=room_id)


@socketio.on('leave_room')
def handle_leave_room(data):
    """处理用户离开直播间"""
    room_id = data.get('room_id')
    leave_room(room_id)

    if request.sid in rooms_data[room_id]["online_users"]:
        username = rooms_data[room_id]["online_users"].pop(request.sid)
        logging.info(f"用户 {username} 离开直播间 {room_id}")

    emit('user_list_updated', list(rooms_data[room_id]["online_users"].values()), room=room_id)


@socketio.on('send_danmu')
def handle_danmu(data):
    """处理弹幕"""
    room_id = data.get('room_id')
    username = rooms_data[room_id]["online_users"].get(request.sid, '匿名用户')
    message = {
        "username": username,
        "content": data.get('content'),
        "color": data.get('color', '#ffffff'),
        "timestamp": datetime.now().isoformat()
    }

    rooms_data[room_id]["danmu_history"].append(message)
    logging.info(f"弹幕来自 {username} 在直播间 {room_id}: {message['content']}")

    emit('new_danmu', message, room=room_id)


@socketio.on('disconnect')
def handle_disconnect():
    """处理用户断开连接"""
    for room_id, room_data in rooms_data.items():
        if request.sid in room_data["online_users"]:
            username = room_data["online_users"].pop(request.sid)
            logging.info(f"用户 {username} 断开连接，离开直播间 {room_id}")

            emit('user_list_updated', list(room_data["online_users"].values()), room=room_id)
            break


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=7676, debug=True)