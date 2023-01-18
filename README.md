# Social network posts

This repository contains an application that implements some logic of the work of posts and users of the social network.

## How to use
clone the repo
```commandline
git clone https://github.com/Unuseptiy/soc_network
```

You need poetry and docker installed.

You need to get your hunter api key on https://hunter.io.
Write your API KEY on new line on the files **.env.sample**, **.env.compose.sample** like that 

```HUNTER_API_KEY=YOUR HANTER API KEY```.

You need to get your clearbit api key on https://clearbit.com.
Write your API KEY on new line on the files **.env.sample**, **.env.compose.sample** like that 

```CLEARBIT_API_KEY=YOUR CLEARBIT SECRET API KEY```.

Also on this files you can adjust postgres env variables.

Run on host:
1) Install dependencies
    ```commandline
    poetry install
    ```
2) Activate virtual environment
```commandline
poetry shell
```
3) Make env file
```commandline
make env
```
4) Make db
```commandline
make db
```
5) Make migrate
```commandline
make migrate head
```
6) Application start
```commandline
make run
```


Run on container
1) Make env file
```commandline
make env
```
2) build containers
```commandline
docker-compose build
```
3) start containers
```commandline
docker-compose up
```
4) migrate db (only with first launch of container)(make commands in another CLI)
```commandline
cd PROJECT_DIR
make migrate head
```

After launching the application, Swagger is available via the link
**http://127.0.0.1:8000/docs**