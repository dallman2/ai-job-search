FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py schema.sql ./
RUN mkdir -p /data

EXPOSE 8000
ENV DB_PATH=/data/job-search.db

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
