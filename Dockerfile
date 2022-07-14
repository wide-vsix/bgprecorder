FROM python:3.8-slim-bullseye

WORKDIR /opt/bgprecorder

RUN apt-get update && apt-get install -y bgpdump bzip2

RUN pip install poetry
RUN poetry config virtualenvs.create false    

COPY poetry.lock  /opt/bgprecorder/
COPY pyproject.toml  /opt/bgprecorder/
RUN poetry install --no-dev

COPY bgprecorder /opt/bgprecorder/bgprecorder

CMD [ "poetry", "run", "bgprecorder"]