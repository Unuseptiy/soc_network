# Social network posts

This repository contains an application that implements some logic of the work of posts and users of the social network.

## How to use
You need poetry and docker installed.

Run on host:
1) clone the repo
```commandline
git clone https://github.com/Unuseptiy/soc_network
```
2) Install dependencies
```commandline
poetry install
```
3) Activate virtual environment
```commandline
poetry shell
```
4) Make env file
```commandline
make env
```
5) Make db
```commandline
make db
```
6) Make migrate
```commandline
make migrate head
```
7) Application start
```commandline
make run
```


Run on container
1) clone the repo
```commandline
git clone https://github.com/Unuseptiy/soc_network
```
2) Make env file
```commandline
make env
```
3) build containers
```commandline
docker-compose build
```
4) start containers
```commandline
docker-compose up
```
5) migrate db (only with first launch of container)(make commands in another CLI)
```commandline
cd PROJECT_DIR
make migrate head
```

After launching the application, Swagger is available via the link
**http://127.0.0.1:8000/docs**