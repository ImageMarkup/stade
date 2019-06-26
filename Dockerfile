FROM python:3.7-slim
RUN apt-get update && \
    apt-get install --no-install-recommends -y postgresql-server-dev-all gcc netcat linux-libc-dev libc6-dev && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
RUN mkdir /uploads
WORKDIR /code
ENV PYTHONPATH=/code
COPY . /code/
RUN pip install psycopg2-binary
RUN pip install -r /code/requirements.txt
RUN pip install -r /code/requirements-dev.txt
RUN cd /usr/local/lib/python3.7/site-packages && python /code/setup.py develop

COPY ./scripts/web-entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
