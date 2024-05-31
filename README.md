# Accumulated Knowledge

Accumulated Knowledge (AK) is a tool to help you tell a story using text and pictures with the help of gAI.

Quick Start (Docker):
- Run an Elasticsearch instance with (give it 30 seconds to start before next step):

docker run --name elasticsearch -d --rm -p 9200:9200 \
    --memory="2GB" \
    -e discovery.type=single-node -e xpack.security.enabled=false \
    -t docker.elastic.co/elasticsearch/elasticsearch:8.11.3    

- Run 'docker compose up' from the top level directory with the docker-compose.yml file to run the backend and frontend
- Navigate to localhost:5001 in a browser window.
- For full functionality add your-openai-api-key to ./backend/config.py and run 'docker-compose up --build'

# Overview

AK uses the content of your story in various ways to improve its suggestions. As content accumulates, suggestions (hopefully) improve. 

Story content is stored in a searchable database to be used as part of Retrieval-Augmented Generation (RAG) pipeline.

# Development

Each piece (Elasticsearch, Backend, Frontend) can be run separately.

# Launch ElasticSearch
docker run --name elasticsearch -d --rm -p 9200:9200 \
    --memory="2GB" \
    -e discovery.type=single-node -e xpack.security.enabled=false \
    -t docker.elastic.co/elasticsearch/elasticsearch:8.11.3    

# Launch Backend
Navigate to /backend
python3 -m venv ./.venv
source .venv/bin/activate
export FLASK_ENV=development
export FLASK_APP=app.py
flask run --port 5000

# Launch Frontend
Navigate to /frontend
python3 -m venv ./.venv
source .venv/bin/activate
export FLASK_ENV=development
export FLASK_APP=app.py
flask run --port 5001    

