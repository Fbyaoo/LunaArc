FROM python:3.12-slim

ARG INSTALL_VISION=false

WORKDIR /app

COPY requirements.txt .
COPY agent/requirements.txt ./agent-requirements.txt
COPY vision/requirements.txt ./vision-requirements.txt

RUN pip install --no-cache-dir -r requirements.txt -r agent-requirements.txt \
    && if [ "$INSTALL_VISION" = "true" ]; then \
         pip install --no-cache-dir -r vision-requirements.txt; \
       fi

COPY alembic.ini ./
COPY migrations ./migrations
COPY app ./app
COPY agent ./agent
COPY vision ./vision

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && fastapi run app/main.py --host 0.0.0.0 --port 8000"]
