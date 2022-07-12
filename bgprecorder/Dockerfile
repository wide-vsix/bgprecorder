FROM python:3.8-slim-bullseye

WORKDIR /opt/bgprecorder

RUN pip install poetry
RUN poetry config virtualenvs.create false    

COPY pyproject.toml /opt/bgprecorder/
COPY poetry.lock /opt/bgprecorder/

RUN poetry install 
COPY main.py /opt/bgprecorder/

RUN apt-get update && apt-get install -y bgpdump bzip2

CMD [ "poetry","run","python3","main.py" ]