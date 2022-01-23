FROM python:3.10.1-slim-buster

WORKDIR /src

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get -y update --allow-releaseinfo-change && apt-get install curl gnupg -y && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get -y update --allow-releaseinfo-change && ACCEPT_EULA=Y apt-get install gcc libpq-dev build-essential msodbcsql17 mssql-tools unixodbc-dev -y
RUN echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bash_profile && echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bashrc

RUN apt-get install -y openssh-server && echo "root:Docker!" | chpasswd

RUN pip install --upgrade pip
COPY ./app/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY ./app ./app
COPY ./database_interface ./database_interface

EXPOSE 8000 2222

RUN chmod 755 ./app/entrypoint.sh

ENTRYPOINT ["./app/entrypoint.sh"]