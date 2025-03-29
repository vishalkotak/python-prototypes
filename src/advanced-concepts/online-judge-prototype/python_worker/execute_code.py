import docker
import psycopg2
import os
import pika
from dotenv import load_dotenv


load_dotenv()
client = docker.from_env()


def get_rabbitmq_connection():
    return pika.BlockingConnection(pika.ConnectionParameters('localhost'))


def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="codedb",
        user="myuser",
        password="mypassword"
    )



def execute_code(submission_id, code):

    with open('temp_code.py', 'w') as f:
        f.write(code)
    print(f"Created file...")
    try:
        # Run the code in the Docker container
        output = client.containers.run('python-worker', 
                                     command='python temp_code.py', 
                                     volumes={os.getcwd(): {'bind': '/app', 'mode': 'rw'}},
                                     working_dir='/app',
                                     stderr=True,
                                     stdout=True)
        
        output_str = output.decode('utf-8')
        print(f"Output of code execution is {output_str}")
        result = 'success' if 'error' not in output_str.lower() else 'error'
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE submissions SET status = %s, result = %s WHERE id = %s",
                     (result, output_str, submission_id))
        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE submissions SET status = %s, result = %s WHERE id = %s",
                     ('failed', str(e), submission_id))
        conn.commit()
        cur.close()
        conn.close()

    os.remove('temp_code.py')


def callback(ch, method, properties, body):
    submission_id, code = body.decode().split(',', 1)
    print(f"Retrieved submission {submission_id}")
    execute_code(submission_id, code)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def consume_tasks():
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.queue_declare(queue='code_execution_tasks')
    channel.basic_qos(prefetch_count=1)  # Process one message at a time
    channel.basic_consume(queue='code_execution_tasks', on_message_callback=callback)
    channel.start_consuming()


if __name__ == "__main__":
    consume_tasks()