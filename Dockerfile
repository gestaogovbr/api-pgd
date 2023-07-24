FROM python:3.11.4-slim-bullseye
RUN useradd -ms /bin/bash -d /home/api-pgd api-pgd
WORKDIR /home/api-pgd
COPY requirements.txt requirements.txt
RUN \
    apt-get update -yqq && \
    apt-get upgrade -yqq && \
    python3 -m pip install --upgrade pip
RUN \
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
RUN chown -R api-pgd:api-pgd ./
COPY ./ /home/api-pgd
USER api-pgd
