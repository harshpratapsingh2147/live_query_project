FROM python:3.10.12
ENV PYTHONUNBUFFERED 1
RUN mkdir /app
WORKDIR /app
COPY req.txt /app/
RUN pip install -r req.txt
COPY . /app/
EXPOSE 8000
