FROM python:3.11.4-slim-bullseye

ARG TAG_NAME
ENV TAG_NAME=$TAG_NAME

WORKDIR /api-pgd

COPY requirements.txt requirements.txt

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    python3 -m pip install --upgrade pip && \
    python3 -m pip install -r requirements.txt --no-cache-dir && \
    apt-get purge --auto-remove -yqq $buildDeps && \
    apt-get autoremove -yqq --purge && \
    apt-get clean && \
    rm -rf \
        /var/lib/apt/lists/* \
        /tmp/* \
        /var/tmp/* \
        /usr/share/man \
        /usr/share/doc \
        /usr/share/doc-base

COPY src/ src/

EXPOSE 5057

ENTRYPOINT ["sh", "-c", "cd /api-pgd/src && uvicorn api:app --host 0.0.0.0 --port 5057 --reload"]

