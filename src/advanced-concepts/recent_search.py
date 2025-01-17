import logging
import time
import random
from datetime import datetime
from elasticsearch import Elasticsearch
from pythonjsonlogger import jsonlogger

ES_HOST = "http://localhost:9200"
ES_INDEX = "queries"

es = Elasticsearch(
    ["http://localhost:9200"],
    request_timeout=30,
    meta_header=False  # Disable strict product checks
)

class ElasticSearchJSONFormatter(jsonlogger.JsonFormatter):
    def format(self, record):
        record.timestamp = datetime.utcnow().isoformat()
        record.service = "ecommerce"
        return super().format(record)
    

logger = logging.getLogger("ElasticLogger")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = ElasticSearchJSONFormatter('%(timestamp)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def send_search_query_to_elasticsearch(data):
    try:
        es.index(index=ES_INDEX, body=data)
    except Exception as e:
        print(f"Failed to send search query to ElasticSearch: {e}")

def generate_searches():
    users = ["user1", "user2", "user3", "user4"]
    search_queries = [
        "shampoo",
        "conditioner",
        "milk",
        "banana",
        "cereal",
        "cookies"
    ]
    for _ in range(20):
        user = random.choice(users)
        query = random.choice(search_queries)
        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "userId": user,
            "query": query,
            "service": "ecommerce"
        }
        print(f"{data}")
        send_search_query_to_elasticsearch(data)
        time.sleep(random.randint(1, 3))


if __name__ == "__main__":
    if not es.indices.exists(index=ES_INDEX):
        es.indices.create(index=ES_INDEX)
        print(f"Created index {ES_INDEX}")

    print("Starting log generation...")
    generate_searches()