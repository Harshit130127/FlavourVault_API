FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt

ARG DEV=false
RUN python -m venv /py \
    && /py/bin/pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt \
    &&    if [ "$DEV" = "true" ]; then \
        /py/bin/pip install --no-cache-dir -r /tmp/requirements.dev.txt \
        && rm -f /tmp/requirements.dev.txt; \
    fi && \
    adduser \
        --disabled-password \
        --no-create-home \
        django-user

COPY . /app

WORKDIR /app

ENV PATH="/py/bin:$PATH"

USER django-user