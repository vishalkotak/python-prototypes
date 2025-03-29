from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
import psycopg2
import redis
import pika # For RabitMQ
import asyncio
from dotenv import load_dotenv
import json

load_dotenv()

app = FastAPI()
r = redis.Redis(host='localhost', port=6379, db=0)


class Submission(BaseModel):
    code: str
    problem_id: int
    user_id: int

def get_rabbitmq_connection():
    return pika.BlockingConnection(pika.ConnectionParameters('localhost'))


def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="codedb",
        user="myuser",
        password="mypassword"
    )


@app.post("/submit")
async def submit(submission: Submission):
    submission_id = str(uuid.uuid4())
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO submissions (id, problem_id, user_id, code, status) VALUES (%s, %s, %s, %s, %s)",
        (submission_id, submission.problem_id, submission.user_id, submission.code, "pending"),
    )
    conn.commit()
    cur.close()
    conn.close()


    # Send task to RabbitMQ
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.queue_declare(queue='code_execution_tasks')
    channel.basic_publish(exchange='', routing_key='code_execution_tasks', body=f'{submission_id},{submission.code}')
    connection.close()

    return {"submission_id": submission_id}


@app.get("/status/{submission_id}")
async def get_status(submission_id: str):
    result_json = r.get(f"submission:{submission_id}")
    print(f"Results JSON {result_json}")
    if result_json:
        result = json.loads(result_json)
        r.delete(f"submission:{submission_id}")
        return {"status": result['status'], "result": result.get('result')} if result.get('result') else {"status": result['status']}

    while True:
        await asyncio.sleep(0.1)
        result_json = r.get(f"submission:{submission_id}")
        if result_json:
            result = json.loads(result_json)
            r.delete(f"submission:{submission_id}")
            return {"status": result['status'], "result": result.get('result')} if result.get('result') else {"status": result['status']}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)