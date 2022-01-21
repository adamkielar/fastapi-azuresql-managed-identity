FROM python:3.10.1-slim-buster

WORKDIR /src

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update \
  && apt-get -y install netcat gcc \
  && apt-get install -y openssh-server \
  && echo "root:Docker!" | chpasswd \
  && apt-get clean

RUN pip install --upgrade pip
COPY ./app/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY ./app ./app

EXPOSE 8000 2222

RUN chmod 755 ./app/entrypoint.sh

ENTRYPOINT ["./app/entrypoint.sh"]