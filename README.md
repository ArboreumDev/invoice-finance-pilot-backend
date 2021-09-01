# Tusker Pilot Stack

The simplemost hacky solution to get us started
## setup

rename .example.env  to `.env` and add the missing variables
```
JWT_SECRET_KEY="someSecretKey"
EMAIL_PASSWORD=""

...and more
```

## Backend

A very simple backend with [fastAPI](https://fastapi.tiangolo.com/) connecting to a DB running at port 8000

### setup 

#### for local development

creates a test-db, db & backend

> make dev-api-local

seed the db with a user
> alembic head upgrade
> cd app
> python -m database.seed

#### troubleshooting

delete the docker container (-s stops if running)
> docker-compose rm -s -v db

reset the volume the container is mounted on manuallyk
> docker-volume ls
> docker-volume rm <NAME>

get a shell into the 
> docker-compose --profile local-mount exec backend /bin/bash

to reflect changes from compose file to running containers (e.g port mappings)
>(tenv) ➜  tusker-pilot-backend git:(docker-setup) ✗ docker-compose --profile testing up


###

### virtualenv
a local virtual env running python version 3.8

e.g. using `virtualenv` -library:

setup virtualenv (e.g named 'tenv') and point it to your local executable of python 3.8 like this:

> virtualenv tenv --python=/usr/bin/python3.8
> source tenv/bin/activate
> pip install -r requirememts.txt

# create the db

first time, create the docker container:

docker run --name=arboreum_backend_<test/prod> -e POSTGRES_USER=<SOME_VARIABLE> -e POSTGRES_PASSWORD={<SOME_VARIABLE> -e POSTGRES_DB=arboreum_backend{test/prod} -p  <desired_port>:5432 -d postgres:12

then store the Variables in `db/const` or in an .env file


> python3 -m database.create

# Migrations
Creating a new revision
```console
$ alembic revision --autogenerate -m "Add column last_name to User model"
```
Don't forget to commit new revision to git.

Switching to the latest migration
```console
$ alembic upgrade head
```

# seed the db with whitelist

add gurugrupas receiver into whitelist:

> python3 -m database.seed
### test

> make test

#### To start it up
``` 
make dev-server
```


and check out the swagger-docs at http://localhost:8000/docs# (or http://localhost:8000/redoc )

its possible to use the docs link to do simple testing of the APIs via the "TRY IT OUT" button

### PRODUCTION

set .env variable ENVIRONMENT=PRODUCTION
