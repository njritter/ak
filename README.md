# Accumulated Knowledge POC

Web based tool to build and tell stories with the help of gAI.

# To run locally

Clone this repository.
Navigate to top level folder.
Create and activate a virtual environment
Install requirements
Run app

```
git clone https://github.com/njritter/ak.git
cd ak
python3 -m venv ./.venv
source ./.venv/bin/activate
pip install -r requirements.txt
flask run
```


# Run ElasticSearch

docker run --name elasticsearch -d --rm -p 9200:9200 \
    --memory="2GB" \
    -e discovery.type=single-node -e xpack.security.enabled=false \
    -v /Users/drazi/Repositories/ak/esdata:/usr/share/elasticsearch/data \
    -t docker.elastic.co/elasticsearch/elasticsearch:8.11.3