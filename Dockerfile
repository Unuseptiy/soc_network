FROM python:3.10
WORKDIR /src
COPY ../requirements.txt .
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt
COPY /soc_network ./soc_network/
#COPY ../.env .
ENTRYPOINT python -m soc_network