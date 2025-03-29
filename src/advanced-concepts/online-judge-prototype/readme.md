```
# Code Execution Prototype with FastAPI, PostgreSQL, RabbitMQ, and Redis

This project demonstrates a prototype for a code execution platform using FastAPI, PostgreSQL, RabbitMQ, and Redis. It allows users to submit code, execute it in isolated Docker containers, and retrieve the execution status.

## Features

* **Code Submission:** Users can submit code via a POST request to the FastAPI server.
* **Asynchronous Code Execution:** Code execution is handled asynchronously using RabbitMQ as a message queue.
* **Isolated Execution:** Code is executed in isolated Docker containers to ensure security and prevent interference.
* **Status Retrieval:** Users can retrieve the execution status of their submissions via a GET request to the FastAPI server.
* **Persistent Storage:** Submission data is stored in a PostgreSQL database.
* **Shared State Management:** Redis is used for sharing the submission status between the FastAPI server and the worker.
* **Unique Filename Generation:** Generates unique filenames for each submission to avoid concurrency issues.
* **Single Status Check:** Client checks the status once, and the server returns the result only when available.

## Prerequisites

* Python 3.7+
* Docker
* Docker Compose (optional, for easier setup)

## Setup

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd code-execution-prototype
    ```

2.  **Create a virtual environment:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**

    ```bash
    pip install fastapi uvicorn psycopg2-binary redis docker python-dotenv pika
    ```

4.  **Start Docker containers:**

    * **PostgreSQL:**

        ```bash
        docker run -d -p 5432:5432 -e POSTGRES_USER=myuser -e POSTGRES_PASSWORD=mypassword -e POSTGRES_DB=codedb postgres
        ```

    * **Redis:**

        ```bash
        docker run -d -p 6379:6379 redis
        ```

    * **RabbitMQ:**

        ```bash
        docker run -d -p 5672:5672 -p 15672:15672 rabbitmq:3-management
        ```

5.  **Create PostgreSQL tables:**

    * Connect to the PostgreSQL container:

        ```bash
        docker exec -it <container_id> psql -U myuser -d codedb
        ```

    * Execute the following SQL commands:

        ```sql
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

6.  **Build the Docker image for the worker:**

    ```bash
    docker build -t python-worker -f python_worker/Dockerfile .
    ```

## Running the Application

1.  **Start the FastAPI server:**

    ```bash
    python main.py
    ```

2.  **Start the worker:**

    ```bash
    python python_worker/execute_code.py
    ```

3.  **Run the client:**

    ```bash
    python client.py
    ```

## API Endpoints

* **POST /submit:** Submit code for execution.

    * Request body:

        ```json
        {
            "code": "print('Hello, World!')",
            "problem_id": 1,
            "user_id": 1
        }
        ```

    * Response:

        ```json
        {
            "submission_id": "..."
        }
        ```

* **GET /status/{submission_id}:** Get the execution status of a submission.

    * Response:

        ```json
        {
            "status": "success",
            "result": "Hello, World!\n"
        }
        ```

        or

        ```json
        {
            "status": "pending"
        }
        ```

        or

        ```json
        {
            "status": "failed",
            "result": "..."
        }
        ```

## Notes

* This is a prototype and may require further development for production use.
* Error handling and security measures should be implemented.
* Consider using a more robust message queue like AWS SQS or RabbitMQ with advanced features.
* Database migrations should be implemented for managing database schema changes.
* Authentication and authorization should be added to secure the API.
```
