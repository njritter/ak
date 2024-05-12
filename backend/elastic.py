from flask import current_app
import uuid


# Page Mapping
page_mapping = {
    "settings": {},
    "mappings": {
        "properties": {
            "name": {
                "type": "keyword"
            },
            "url": {
                "type": "text"
            },
            "text": {
                "type": "text"
            },
            "textVector": {
                "type": "dense_vector",
                "dims": 256
            }
        }
    }
}

# Story Mapping
story_mapping = {
    "settings": {},
    "mappings": {
        "properties": {
            "pages": {
                "type": "text",
                "index": False,
                "fields": {
                    "keyword": {
                        "type": "keyword"
                    }
                }
            },
            "story": {
                "type": "keyword"
            },
            "title": {
                "type": "keyword"
            }
        }
    }
}


def elasticsearch_startup(es):
    # Create story and page indices if they don't exist
    if not es.indices.exists(index="story"):
        print("No story index found. Creating story index")
        es.indices.create(index="story", body=story_mapping)
    if not es.indices.exists(index="page"):
        print("No page index found. Creating page index")
        es.indices.create(index="page", body=page_mapping)


def es_create_story(es, title):
    # Add story 'title' to the story index
    body = {
        "title": title,
        "pages": [],
        "url": "/story"}
    # Generate a unique ID for the story
    story_id = str(uuid.uuid4())
    response = es.index(index="story", id=story_id, body=body)
    es.indices.refresh(index="story")  # Refresh the story index
    es_create_page(es, story_id, 1)  # Add first page to the story
    
    return response


def es_get_stories(es, ids):
    # Get all info about stories with [ids] from story index.
    # If ids is empty [], return all stories
    # If no stories are found, return a test story
    
    if ids:  # Return stories with ids
        response = es.search(index="story", body={"query": {"ids": {"values": ids}}}, size=100)
    else:  # Return all stories
        response = es.search(index="story", body={"query": {"match_all": {}}}, size=100)
    
    stories = []
    for hit in response['hits']['hits']:
        story = hit['_source']
        story['id'] = hit['_id']  # Add the document ID to the story
        stories.append(story)
    
    if stories:
        return stories
    else:
        return [{"id": "1", "title": "Test Story 1", "url": "/story", "pages": []}]
    

def es_create_page(es, story_id, page_num):
    # Add page to page index with associated story_id, page_num, and default values

    story_text = "Update the image above and the text you see here with the story creation tools below."

    new_story_text = 'Replace this text with text for your story. \n\n' + \
        '"Generate Text" will suggest a continuation to the story. \n' + \
        '"Update Text" will replace the text above with the text here.'

    new_image_description = 'Describe the image you want to generate here. The more detail the better! \n\n' + \
        '"Generate Image" will replace the image below with a new one. It can take about 10 seconds. \n' + \
        '"Update Image" will update the image above with the one below.'

    body = {
        "story_id": story_id,
        "page_number": page_num,
        "image_url": "ak/default_page.png",
        "story_text": story_text,
        "new_story_text": new_story_text,
        "new_image_description": new_image_description,
        "new_image_url": "ak/default_page.png"}
    
    # Add the page to the page index
    page_id = str(uuid.uuid4())
    response = es.index(index="page", id=page_id, body=body)
    es.indices.refresh(index="page")  # Refresh the page index
    print("Page created")
    
    # Add reference to page to the story
    story = es.get(index="story", id=story_id)  # Get the current story document
    pages = story['_source']['pages']  # Get the current pages list
    pages.append(page_id)  # Add page_id to the pages list
    print("Pages:", pages)
    es.update(index="story", id=story_id, body={"doc": {"pages": pages}})  # Add page_id to the pages list
    es.indices.refresh(index="story")  # Refresh the story index
    print("Page added to story")
    
    return response


def es_get_page(es, story_id, page_num):
    # Get info for page with page_num from story with story_id
    
    body = {"query": {"bool": {"must": [{"match": {"story_id": story_id}}, {"match": {"page_number": page_num}}]}}}
    response = es.search(index="page", body=body)
    page = response['hits']['hits'][0]['_source']
    page['id'] = response['hits']['hits'][0]['_id']  # Add the document ID to the page

    return page


def es_get_pages(es, pages):
    # Get all pages with ids in [pages] from page index
    # !!!! merge with es_get_page ... 
    
    body = {"query": {"ids": {"values": pages}}}
    response = es.search(index="page", body=body)
    pages = []
    for hit in response['hits']['hits']:
        page = hit['_source']
        page['id'] = hit['_id']
        pages.append(page)

    return pages


def es_update_page(es, page_id, updates):
    # Update page with new values
    for key, value in updates.items():
        print("Updating", key, "to", value)
        es.update(index="page", id=page_id, body={"doc": {key: value}})
    es.indices.refresh(index="page")  # Refresh the page index
    print("Page updated")
    return None