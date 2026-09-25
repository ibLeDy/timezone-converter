FROM python:3.13-slim-bookworm

ENV PYTHONUNBUFFERED=1

LABEL maintainer="iago@iagoalonso.xyz"

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

# A container has no timezone of its own. Left unset, the LOCAL column is
# UTC; pass one at run time with `docker run -e TZ=Europe/Madrid ...` or
# `--local`. TZ is resolved through the bundled tzdata wheel, so the image
# does not need the operating system timezone database.
ENTRYPOINT [ "timezone-converter" ]
