# helper functions for index management and mapping

CHAR_INDEX = 'sanrio_characters'
CHAR_MAPPING = {
  "mappings": {
    "properties": {
      "name": {"type": "text", "analyzer": "standard"},
      "franchise": {"type": "keyword"},
      "species": {"type": "keyword"},
      "debut_year": {"type": "integer"},
      "tags": {"type": "keyword"},
      "description": {"type": "text"}
    }
  }
}

def ensure_index(es):
    if not es.indices.exists(index=CHAR_INDEX):
        es.indices.create(index=CHAR_INDEX, body=CHAR_MAPPING)
