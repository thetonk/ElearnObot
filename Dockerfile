FROM python:3.13-alpine
WORKDIR /elearnObot
LABEL Maintainer="Spyros"
LABEL Version="1.1"
COPY . .
RUN pip3 install --no-cache-dir -r requirements.txt
CMD ["python3","-u","bot.py"]
