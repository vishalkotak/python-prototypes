import mysql.connector
from mysql.connector import Error
import threading
import time

def connect_to_mysql():
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1', 
            port=3306,
            user='root',
            password='my-secret-pw' # adding password here just for ease of use, don't do it in real environments
        )
        return connection
    except Error as e:
        print(f"Error: {e}")

# Closing connection after query execution
def execute_query_with_new_connection():
    sleep_seconds = 1
    query = f"SELECT SLEEP({sleep_seconds});"
    connection = connect_to_mysql()
    cursor = connection.cursor()
    cursor.execute(query)
    connection.close()

def concurrent_operations(num_operations: int):
    threads = []
    start_time = time.time()
    for _ in range(num_operations):
        thread = threading.Thread(target=execute_query_with_new_connection)
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    end_time = time.time()
    print(f'Time taken by concurrent_operations: {end_time - start_time}')

def initialize_connections(min_size: int):
    connections = []
    for _ in range(min_size):
        connections.append(connect_to_mysql())
    return connections

def get_connection_from_queue(connections, list_lock):
    list_lock.acquire()
    connection = None
    if connections:
        connection = connections.pop(0)
    list_lock.release()
    return connection

def add_connection_to_queue(connections, list_lock, connection):
    list_lock.acquire()
    connections.append(connection)
    list_lock.release()

def execute_query_with_existing_connections(connections, list_lock, i, max_connections):
    sleep_seconds = 0.1
    query = f"SELECT SLEEP({sleep_seconds});"
    while True:
        connection = get_connection_from_queue(connections, list_lock)
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute(query)
                # Fetch all results to clear the result set as I was getting a message:
                # Unread result found
                cursor.fetchall()  
                # print(f'Query executed {i}')
            except Error as e:
                print(f"{e}")
            finally:
                add_connection_to_queue(connections, list_lock, connection)
            break
        elif len(connections) < max_connections:
            connection = connect_to_mysql()
            add_connection_to_queue(connections, list_lock, connection)
            continue
        else:
            # Retrying to get a connection after 0.1 seconds
            time.sleep(0.1)

def concurrent_operations_with_queue(num_operations: int, min_connections: int, max_connections: int):
    threads = []
    connections = initialize_connections(min_connections)
    list_lock = threading.Lock()
    start_time = time.time()
    for i in range(num_operations):
        thread = threading.Thread(target=execute_query_with_existing_connections, 
                                  args=(connections, list_lock, i, max_connections))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    end_time = time.time()
    print(f'Time taken by concurrent_operations_with_queue: {end_time - start_time}')

concurrent_operations(500)
# Currently it doesn't clear ideal connections. Should do that too.
concurrent_operations_with_queue(500, 3, 10)