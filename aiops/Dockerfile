FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --system --gid 1000 aiops \
    && useradd --uid 1000 --gid aiops --create-home --shell /usr/sbin/nologin aiops

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY config.yml main.py ./

RUN mkdir -p /app/data && chown -R aiops:aiops /app

USER aiops

CMD ["python", "main.py"]
