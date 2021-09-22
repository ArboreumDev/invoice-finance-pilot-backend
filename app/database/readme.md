# create db

```
docker run --name=<name> -e POSTGRES_USER=<USERNAME> -e POSTGRES_PASSWORD=<password> -e POSTGRES_DB=<name> -p  5432:5432 -d postgres:12
```