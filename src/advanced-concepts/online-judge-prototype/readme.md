- Run a RabitMQ Container

```
docker run -d -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```

The management plugin on port 15672 provides a web UI for monitoring RabbitMQ.

- Run a Redis Container

```
docker run -d -p 6379:6379 redis
```

- Run a Postgres Container

```
docker run -d -p 5432:5432 -e POSTGRES_USER=myuser -e POSTGRES_PASSWORD=mypassword -e POSTGRES_DB=codedb postgres

docker exec -it <container_id> psql -U myuser -d codedb

```

- Necessary Tables

```
CREATE TABLE submissions (
    id UUID PRIMARY KEY,
    problem_id INTEGER,
    user_id INTEGER,
    code TEXT,
    status VARCHAR(20),
    result TEXT
);

CREATE TABLE problems (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255),
    description TEXT
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255)
);
```