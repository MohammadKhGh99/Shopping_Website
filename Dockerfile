FROM python:3.10-alpine
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt && rm -rf /root/.cache/pip
COPY . .

CMD ["python3", "app.py"]
