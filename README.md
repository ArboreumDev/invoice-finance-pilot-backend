# Tusker Pilot Stack

A backend that manages creditlines between suppliers & purchasers. Each creditline is limited by

- the total credit each supplier can avail to
- the total credit each purchaser can avail to
- the individual credit limit of each purchaser-supplier relationship

Credit is given against individual invoices (correspond to shipments of goods).

A typical invoice lifecycle looks like this:

- Once requested to be financed, The backend checks whether the invoice-value is within the limits of the associated creditline.
- If approved, the backend tracks its delivery-status by querying the delivery-company.
- Once delivered, it marks it as to be financed (Admin-Dashboard)
- Once per day, the admin can bundle all invoices to be financed into a disbursal and manually trigger the release of the money (external to this backend)
- Once the money is released, the invoices can be marked as disbursed, and the respective disbursal & loan-ID will be stored with them
- The dashboards will show the invoice-status, the total credit that is left and the amounts to be repaid (live and at the end of the term)
- The Admin can use the admin-dashboard to mark invoices as fully repaid, freeing the respective amounts from the creditlines.

## Setup

rename .example.env to `.env` and add the missing variables

```
JWT_SECRET_KEY="someSecretKey"
EMAIL_PASSWORD=""

...and more
```

## Backend

- A [fastAPI](https://fastapi.tiangolo.com/)-backend
- A postgres DB, using MySQLAlchemy to define [schemas](/app/database/schemas/) for invoices & customers and credit-relationships
- dedicated classes to do CRUD-updates to the DB (e.g. [invoice-service](/app/database/crud/invoice_service.py))
- [pydantic models](/app/database/models.py) to specify the API-datamodels (openAPI/swagger docs)
- [unit-tests](/app/database/test/) and [integration-tests](/app/test/integration/) using pytest-fixtures (see [here](/app/test/integration/conftest.py) and [here](/app/database/test/conftest.py)
- error-, debug- and info-[logging](/app/utils/logger.py) for each service according to [python logging-cookbook](https://docs.python.org/3/howto/logging-cookbook.html#logging-cookbook)
- linting & formatting with flake8 & black
- [github-actions](/.github/workflows/python-app.yml) for linting & testing on pull-requests
- [docker-compose commands](/Makefile) to run backend & db & test_db as local-containers, or bind-mounted to the local folder

## Setup

### Virtualenv

a local virtual env running python version 3.8

e.g. using `virtualenv` -library:

setup virtualenv (e.g named 'tenv') and point it to your local executable of python 3.8 like this:

> virtualenv tenv --python=/usr/bin/python3.8
> source tenv/bin/activate
> pip install -r requirememts.txt

### for local development

check the [Makefile](/Makefile) for a bunch of helpful commands.

Creates a test-db, db & backend

> make dev-api-local
> (-> set # POSTGRES_HOST="localhost" in .env)

then, create the DB-schemas

> cd app
> python -m database.create

or

> make create_db

or

> alembic head upgrade

Then, seed the db with a user

> cd app
> python -m database.seed

_BUG_: Not sure how to make the bind-mount use the virtualenv -> you might need to manually install a bunch of python libraries (argon-cff2, fastapi,psycopg2-binary, pendulum, python-multipart,...)

### run backend as container

(-> set # POSTGRES_HOST="db" in .env)

> make dev-api

attach into backend container & run database.create & database.seed manually

### Migrations

Creating a new revision

```console
$ alembic revision --autogenerate -m "Add column last_name to User model"
```

Don't forget to commit new revision to git.

Switching to the latest migration

```console
$ alembic upgrade head
```

## troubleshooting

delete the docker container (-s stops if running)

> docker-compose rm -s -v db

reset the volume the container is mounted on manuallyk

> docker-volume ls
> docker-volume rm <NAME>

if running the api-containerized:

get a shell into the

> docker-compose --profile local-mount exec backend /bin/bash

to reflect changes from compose file to running containers (e.g port mappings)

> (tenv) ➜ tusker-pilot-backend git:(docker-setup) ✗ docker-compose --profile testing up

## test

> make test

## Documentation

run the api and check out the swagger-docs at http://localhost:8000/docs# (or http://localhost:8000/redoc )

its possible to use the docs link to do simple testing of the APIs via the "TRY IT OUT" button

### PRODUCTION

set .env variable ENVIRONMENT=PRODUCTION
