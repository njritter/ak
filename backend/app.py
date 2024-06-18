from elasticsearch import Elasticsearch
from flask import Flask, jsonify, request
from config import Config
from elastic import elasticsearch_startup, es_create_story, es_get_stories, es_get_page, es_create_page, es_update_page
from generate_text import ai_generate_text
from generate_image import ai_generate_image


app = Flask(__name__)
app.config.from_object(Config)
es = Elasticsearch([app.config['ELASTICSEARCH']])
elasticsearch_startup(es)


@app.route('/create_story', methods=['POST'])
def create_story():
    # Add story 'title' to the story index
    # Add checks here. No same name, no special char, length check, ...
    
    data = request.get_json()
    title = data.get('title', 'Test Title')        
    
    print("Creating story with name:", title, "in story index")
    story = es_create_story(es, title)

    return(jsonify("Story created"))


@app.route('/get_stories', methods=['GET'])
def get_stories(ids=[]):
    # Return all stories with associated info from story index
    # List of dictionaries [{}, {}, {}]
    if request.method == 'GET':
        ids = request.args.getlist('ids')
        print("Getting stories with ids:", ids)
    else:
        print("Getting all stories")
    stories = es_get_stories(es, ids)
    return jsonify(stories)


@app.route('/create_page', methods=['POST'])
def create_page(story_id="", page_num=0):
    # Add page to page index with associated story_id, page_num, and default values
    if request.method == 'POST':
        data = request.get_json()
        story_id = data.get('story_id', '1')
        page_num = data.get('page_num', 0)
        print("Creating page", page_num, "in story", story_id)
    response = es_create_page(es, story_id, page_num)

    return jsonify(message="Hello, Page!")


@app.route('/get_page', methods=['GET'])
def get_page(story_id="", page_num=0):
    story_id = request.args.get('story_id')
    page_num = request.args.get('page_num')
    print("Getting page", page_num, "from story", story_id)
    page = es_get_page(es, story_id, page_num)
    return jsonify(page)


@app.route('/update_page', methods=['POST'])
def update_page(updates={}):
    if request.method == 'POST':
        data = request.get_json()
        print("data:", data)
        page_id = data.get('page_id', None)
        updates = data.get('updates', {})
        es_update_page(es, page_id, updates)
        
    return jsonify(message="Hello, Page!")


@app.route('/generate_text', methods=['GET'])
def generate_text(text=""): 

    starting_text = request.args.get('text', 'test text')
    story_id = request.args.get('story_id', 'test story id')
    page_id = request.args.get('page_id', 'test page id')
    story_text = ai_generate_text(es, story_id, page_id, starting_text)
    return jsonify(story_text)


@app.route('/generate_image', methods=['POST'])
def generate_image():
    # Generate new image for story using image description
    # Save image locally and add reference to the new_image field of page_id in page index
    # Return page info with updated new_image field
    data = request.get_json()
    image_description = data.get('image_description', 'test image description')
    page_id = data.get('page_id', 'test page id')
    image_id = ai_generate_image(es, page_id, image_description)
    es_update_page(es, page_id, {'new_image_url': image_id + ".jpg"})

    # return updated page?
    return jsonify(message="Hello, Image!")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)