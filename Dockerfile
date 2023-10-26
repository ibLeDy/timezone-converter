FROM python:3.12-slim-bullseye

ENV PYTHONUNBUFFERED 1

LABEL maintainer="deejaynof@gmail.com"

RUN : \
    && groupadd --gid 1001 timezone-converter \
    && useradd --uid 1001 --gid timezone-converter --system --create-home --home-dir /home/timezone-converter timezone-converter \
    && :
USER timezone-converter

WORKDIR /opt
COPY --chown=timezone-converter:timezone-converter . .

ENV PATH="/home/timezone-converter/.local/bin:$PATH"
RUN : \
    && python3 -m pip --no-cache-dir install . \
    && :

ENTRYPOINT [ "timezone-converter" ]
