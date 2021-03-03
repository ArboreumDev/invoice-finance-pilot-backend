# Tusker Pilot Stack

The simplemost hacky solution to get us started
## setup

create a `.env.staging` file and add the following variables
```
JWT_SECRET_KEY="someSecretKey"
```

## Backend

A very simple backend with [fastAPI](https://fastapi.tiangolo.com/) to pretend connecting to a DB
it runs at port 8000

#### Setup:
- python 3.8
- create a virtualenv
- cd server; pip install -r requirements.txt

#### To start it up
``` 
make dev-api
```

and check out the swagger-docs at http://localhost:8000/docs# (or http://localhost:8000/redoc )

its possible to use the docs link to do simple testing of the APIs via the "TRY IT OUT" button


## Frontend

A simple frontend with Next.js + Tyepscript for you that...
- shows available invoices 
- shows total Owed (TODO) 
- can request an invoice to be financed (TODO)
- has an admin  interface to change the shipment or finance status of the loans (TODO)
- can add new shipments (TODO)


Install all requirements:
```
yarn
```

fire it up:
```
make dev-webapp
```

go to http://localhost:3000/ to see it in action 
