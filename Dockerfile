FROM python:3.11.4-slim-bullseye

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

COPY src/ .
COPY run_after_db.py run_after_db.py
COPY init/configure_fief.py configure_fief.py
RUN chmod +x configure_fief.py