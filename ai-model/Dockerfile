FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --system --gid 1000 ai-model \
    && useradd --uid 1000 --gid ai-model --create-home --shell /usr/sbin/nologin ai-model

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY config.yml main.py ./

RUN mkdir -p /app/data && chown -R ai-model:ai-model /app

USER ai-model

EXPOSE 8090

CMD ["python", "main.py"]
