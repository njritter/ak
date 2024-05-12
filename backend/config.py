import os


class Config:
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', 'your-openai-api-key')
    ELASTICSEARCH = os.environ.get('ELASTICSEARCH', 'http://localhost:9200')
