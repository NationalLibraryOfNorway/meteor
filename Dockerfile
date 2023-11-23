# syntax=docker/dockerfile:1

FROM python:3.11.6-slim-bookworm

ARG USE_GIELLA=false

WORKDIR /python-docker

COPY . .

ENV PIP_ROOT_USER_ACTION=ignore
ENV SCRIPT_NAME=/meteor

RUN pip install --upgrade pip ; \
    pip install -r requirements.txt

RUN if [ "$USE_GIELLA" = "true" ] ; then \
    pip install gielladetect ; \
    fi

CMD [ "uvicorn", "main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000" ]
