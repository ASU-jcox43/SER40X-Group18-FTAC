FROM python:3.13-trixie as base
WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN apt-get update
RUN apt-get -y install libgirepository-2.0-dev gcc libcairo2-dev pkg-config python3-dev gir1.2-gtk-4.0
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt
RUN python -m spacy download en_core_web_sm
COPY ./Backend /app/Backend
COPY ./credentials.json /app/credentials.json
COPY ./token.json /app/token.json
CMD fastapi run ./Backend/api.py