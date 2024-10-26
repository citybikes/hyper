FROM python:3.12

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/hyper hyper
CMD python -m hyper.producer
