# Tusker Pilot Stack

The simplemost hacky solution to get us started
## setup

create a `.env.staging` file and add the following variables
```
JWT_SECRET_KEY="someSecretKey"
EMAIL_PASSWORD=""
EMAIL_HOST="email-smtp.eu-west-2.amazonaws.com"
EMAIL_USERNAME=""
EMAIL_PORT=""
```

## Backend

A very simple backend with [fastAPI](https://fastapi.tiangolo.com/) to pretend connecting to a DB
it runs at port 8000

### setup 
a local virtual env running python version 3.8

e.g. using `virtualenv` -library:

setup virtualenv (e.g named 'tenv') and point it to your local executable of python 3.8 like this:

> virtualenv tenv --python=/usr/bin/python3.8
> source tenv/bin/activate
> pip install -r requirememts.txt

# create the db

first time, create the docker container:

docker run --name=arboreum_backend -e POSTGRES_USER=<SOME_VARIABLE> -e POSTGRES_PASSWORD={<SOME_VARIABLE> -e POSTGRES_DB=arboreum_backend -p  5433:5432 -d postgres:12

then store the Variables in `db/const` or in an .env file


> python3 -m database.create

### test

> make test

#### To start it up
``` 
make dev-server
```

and check out the swagger-docs at http://localhost:8000/docs# (or http://localhost:8000/redoc )

its possible to use the docs link to do simple testing of the APIs via the "TRY IT OUT" button
