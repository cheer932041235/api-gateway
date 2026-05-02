FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY proxy.py codex-proxy.py secrets.example.json ./

EXPOSE 8082 8083 5678

CMD ["python", "proxy.py"]
