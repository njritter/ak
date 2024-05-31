from config import Config
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from forms import createStory, storyImage, storyPageNav, storyText
from models import Page, Story
import requests

app = Flask(__name__)
app.config.from_object(Config)
IMAGE_PATH = app.config['DATA'] + "/images"


def make_request(url, method='GET', json=None):
    # Error handling for making requests to backend
    try:
        if method == 'GET':
            response = requests.get(url)
        elif method == 'POST':
            response = requests.post(url, json=json)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to make {method} request to {url}: {e}")
        return None
    

@app.route('/app/data/images/<filename>')
def serve_image(filename):
    return send_from_directory(IMAGE_PATH, filename)
    # return send_from_directory('../data/images/', filename)


@app.route('/', methods=['GET', 'POST'])
def index():
    # Display Accumulated Knowledge home page. 
    # Contains overview, a form to create a new story, and existing stories.

    # Initialize form for creating a new story
    create_story_form = createStory()

    # If create story form submitted, ping the create_story endpoint on backend
    # to create a new story with submitted title.
    if request.method == 'POST' and create_story_form.validate_on_submit():
        title = create_story_form.data['title']
        result = make_request(app.config['BACKEND_URL'] + "create_story", 'POST', {'title': title})
        if result is None:
            print("Failed to create story.")

    # Default behavior when page is loaded:
    # Get list of existing stories to display under Library
    stories = make_request(app.config['BACKEND_URL'] + "get_stories")
    if stories is None:
        print("Failed to load stories.")
        stories = []

    return render_template('index.html', 
                           create_story_form=create_story_form,
                           stories=stories)


@app.route('/<story_id>/<page_num>', methods=['GET', 'POST'])
def story(story_id, page_num):
    
    # Get info for story with story_id
    response = requests.get(app.config['BACKEND_URL'] + "get_stories", params={'ids': [story_id]})
    story_dict = response.json()[0]
    story = Story(**story_dict)
    print("Retrieved story with id:", story.id, "and title:", story.title)

    # Ensure page_num is within bounds
    if int(page_num) > len(story.pages):
        page_num = len(story.pages)

    # Get info for page with page_num from story with story_id
    response = requests.get(app.config['BACKEND_URL'] + "get_page", params={'story_id':story_id, 'page_num': page_num})
    page_dict = response.json()
    page = Page(**page_dict)
    print("Retrieved page:", page.page_number, "from story:", page.story_id)

    # Initialize forms for page nav, image generation, and text generation
    page_nav_form = storyPageNav()
    story_image_form = storyImage(image_description=page.new_image_description)
    story_text_form = storyText(story_text=page.new_story_text)

    if request.method == 'POST':  # if a form was submitted
        # if 'Next' button clicked, load next page
        if page_nav_form.next.data:
            max_page_num = len(story.pages)
            page_num = min(int(page_num) + 1, max_page_num)
        # if 'Previous' button clicked, load previous page
        elif page_nav_form.previous.data:
            page_num = max(int(page_num) - 1, 1)
        # if 'New Page' button clicked, create new page at end of story and load it
        elif page_nav_form.new.data:
            page_num = len(story.pages) + 1
            print("Creating page", page_num, "in story", story.id)
            response = requests.post(app.config['BACKEND_URL'] + "create_page", json={'story_id': story_id, 'page_num': page_num})

        # if 'Generate Text' button clicked, use AI to generate text continuation
        elif story_text_form.generate_text.data:
            print("Generating text ...")
            response = requests.get(app.config['BACKEND_URL'] + "generate_text", params={
                "story_id": story_id,
                "page_id": page.id,
                'text': story_text_form.story_text.data})
            resp_json = response.json()
            print(resp_json)
            response = requests.post(app.config['BACKEND_URL'] + "update_page", json={
                "page_id": page.id,
                "updates": {'new_story_text': resp_json}})
            
        # if 'Update Text' button clicked, update story text with new text
        elif story_text_form.update_text.data:
            print("Updating story text")
            print(story_text_form.story_text.data)
            response = requests.post(app.config['BACKEND_URL'] + "update_page", json={
                "page_id": page.id,
                "updates": {'story_text': story_text_form.story_text.data}})
        
        # if 'Generate Image' button clicked, use AI to generate a new image
        elif story_image_form.generate_image.data:
            print("Generating image")
            response = requests.post(app.config['BACKEND_URL'] + "generate_image", json={
                "page_id": page.id,
                "image_description": story_image_form.image_description.data})
        # if 'Update Image' button clicked, update current story image with new image
        elif story_image_form.update_image.data:
            print("Updating image")
            response = requests.post(app.config['BACKEND_URL'] + "update_page", json={
                "page_id": page.id,
                "updates": {'image_url': page.new_image_url}})
            
                
        # load the new page
        return redirect(url_for('story', story_id=story_id, page_num=page_num))        
            
    return render_template('story.html',
                           story = story,
                           page = page,
                           page_nav_form=page_nav_form,
                           story_image_form=story_image_form,
                           story_text_form=story_text_form)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)