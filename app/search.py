from datetime import datetime
from flask import current_app
from flask_login import current_user
import os
import time


def add_page(project, data):
    # Adds page to page index in ElasticSearch
    # page should be a page object defined in models.py!

    id = str(round(time.time() * 100))
    print(id)

    page = {
        "id": id,
        "username": current_user.username,
        "projectId": project,
        "storyText": data["text"],
        "userImageDescription": data["description"],
        "akImageDescription": "Description of the AK image",
        "imageURL":  os.path.join(current_app.root_path, 'static', current_user.username, project, id),
        "status": "workshop",
        "pageNumber": None,
        "createdDate": datetime.now().isoformat(),
        "updatedDate": None,
    }

    # add the page to the page index in ElasticSearch
    response = current_app.elasticsearch.index(
        index='page', 
        id=page["id"], 
        document=page)
    print("Added page to ElasticSearch index: " + str(response))
    return(id)


def add_to_index(index, model):
    if not current_app.elasticsearch:
        return
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    current_app.elasticsearch.index(index=index, id=model.id, document=payload)


def remove_from_index(index, model):
    if not current_app.elasticsearch:
        return
    current_app.elasticsearch.delete(index=index, id=model.id)


def query_index(index, query, page, per_page):
    if not current_app.elasticsearch:
        return [], 0
    search = current_app.elasticsearch.search(
        index=index,
        query={'multi_match': {'query': query, 'fields': ['*']}},
        from_=(page - 1) * per_page,
        size=per_page)
    ids = [int(hit['_id']) for hit in search['hits']['hits']]
    return ids, search['hits']['total']['value']