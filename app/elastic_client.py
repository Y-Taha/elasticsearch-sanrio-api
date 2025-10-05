import time
from elasticsearch import Elasticsearch
from elastic_transport import ConnectionError

ES_HOST = "http://elasticsearch:9200"

def get_es_client(retries=10, delay=5):
    for attempt in range(retries):
        try:
            es = Elasticsearch(ES_HOST)
            es.info()  # test connection
            return es
        except ConnectionError as e:
            print(f"[Elasticsearch] not reachable, retrying {attempt+1}/{retries}...")
            time.sleep(delay)
    raise RuntimeError(f"Elasticsearch not reachable at {ES_HOST} after {retries} retries")
