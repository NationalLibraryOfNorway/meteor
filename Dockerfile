# syntax=docker/dockerfile:1

FROM python:3.11.1-slim-buster

WORKDIR /python-docker

COPY . .

ENV PIP_ROOT_USER_ACTION=ignore
ENV SCRIPT_NAME=/meteor

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD [ "uvicorn", "main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000" ]