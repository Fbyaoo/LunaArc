FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 配置apt源
RUN sed -i \
        -e 's|deb.debian.org/debian-security|mirrors.aliyun.com/debian-security|g' \
        -e 's|deb.debian.org/debian|mirrors.aliyun.com/debian|g' \
        /etc/apt/sources.list.d/*.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        libglib2.0-0 \
        libgl1 \
        libsm6 \
        libxext6 \
        libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# 🔥 改用清华源（更稳定）并使用 HTTP
RUN pip config set global.index-url http://pypi.tuna.tsinghua.edu.cn/simple && \
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

COPY requirements.txt requirements-dev.txt ./
COPY vision/requirements.txt /tmp/vision-requirements.txt
COPY agent/requirements.txt /tmp/agent-requirements.txt

# 分层安装
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt
RUN pip install --no-cache-dir -r /tmp/vision-requirements.txt
RUN pip install --no-cache-dir -r /tmp/agent-requirements.txt

COPY alembic.ini ./
COPY migrations ./migrations
COPY app ./app
COPY agent ./agent
COPY vision ./vision

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && fastapi run app/main.py --host 0.0.0.0 --port 8000"]
