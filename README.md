# Social network posts

This repository presents the application that implements some logic of posts work and users work of social network.

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
4) Make .env
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