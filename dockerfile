FROM docker.m.daocloud.io/python:3.9-slim

WORKDIR /app
# 安装指定版本的兼容组合

COPY ./src .
RUN pip install --no-cache-dir Werkzeug==2.0.3 && \
    pip install --no-cache-dir -r requirements.txt

EXPOSE 7676

CMD ["python", "app.py"]