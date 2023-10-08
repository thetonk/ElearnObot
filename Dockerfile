FROM python:3.9-slim-bullseye
WORKDIR /elearnObot
LABEL Maintainer="Spyros"
LABEL Version="1.1"
COPY . .
ARG DEBIAN_FRONTEND=noninteractive
RUN pip3 install --no-cache-dir -r requirements.txt
ENTRYPOINT ["python3", "bot.py"]
