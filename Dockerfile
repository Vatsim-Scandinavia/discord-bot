FROM python:3.12-bullseye

COPY requirements.txt /app/
WORKDIR /app

RUN pip install -r requirements.txt

COPY . .

CMD [ "python3", "bot.py" ]