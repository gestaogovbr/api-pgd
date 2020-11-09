FROM python:3.9-alpine
RUN adduser -D api-pgd
WORKDIR /home/api-pgd
COPY requirements.txt requirements.txt
RUN \
 apk add --no-cache postgresql-libs && \
 apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev && \
 python3 -m pip install -r requirements.txt --no-cache-dir && \
 apk --purge del .build-deps
RUN chown -R api-pgd:api-pgd ./
USER api-pgd
