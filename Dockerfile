FROM python:3.10.12
ENV PYTHONUNBUFFERED 1
RUN mkdir /app
WORKDIR /app
COPY req.txt /app/
COPY gunicorn_config.py /app/
RUN  apt update && apt install nano vim sudo poppler-utils -y 
RUN pip install --no-cache-dir -r req.txt
COPY . /app/
