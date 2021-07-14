FROM python:3.8-alpine

WORKDIR /app

RUN pip install flask gunicorn

COPY app.py /app

ENV PYTHONUNBUFFERED=1

CMD gunicorn app:app -b 0.0.0.0