## Elastic Search queries

#### Query to execute fuzzy matches with edit distance = 1
```
curl -X GET "http://localhost:9200/queries/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "fuzzy": {
      "query": {
        "value": "shampo",
        "fuzziness": 1
      }
    }
  }
}'
```

#### Query to execute fuzzy matches with edit distance = 2
```
curl -X GET "http://localhost:9200/queries/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "fuzzy": {
      "query": {
        "value": "shmpo", 
        "fuzziness": 2
      }
    }
  }
}'
```

#### Query to execute fuzzy matches with edit distance = 2 and prefix_length = 2 i.e. beginning characters should match.
```
curl -X GET "http://localhost:9200/products/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "fuzzy": {
      "query": {
        "value": "shmpo",
        "fuzziness": 2,
        "prefix_length": 2
      }
    }
  }
}'
```