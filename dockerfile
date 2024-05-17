FROM python:3.10

WORKDIR /usr/src/teletop

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN [ "python", "./init_db.py"]
CMD [ "python", "./main.py" ]