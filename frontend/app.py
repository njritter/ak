from config import Config
from flask import Flask, render_template, request, redirect, url_for
from forms import createStory, storyImage, storyPageNav, storyText
from models import Page, Story
import requests

app = Flask(__name__)
app.config.from_object(Config)


@app.route('/', methods=['GET', 'POST'])
def index():
    create_story_form = createStory()
    if request.method == 'POST':  # The form was submitted 
        if create_story_form.validate_on_submit():  # The form data is valid
            # Add a story with name to the database
            title = create_story_form.data['title']
            print("Creating story with title:", title)
            # Send a POST request to the create_story route with the title of the story
            response = requests.post(app.config['BACKEND_URL'] + "create_story", json={'title': title})

    # Get list of stories to display under Library
    try:
        response = requests.get(app.config['BACKEND_URL'] + "get_stories")
        response.raise_for_status()  # Raise an exception if the request failed
        stories = response.json()  # Convert JSON data to Python list ... use Story class instead
    except requests.exceptions.RequestException as e:
        # An error occurred, use the default stories data
        # logging.error(f"Failed to get stories from backend: {e}")
        stories = Story(id="1", title="Test Story 1", url="/story", pages=[])     

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
        # if 'Update Image' button clicked, update current story image with new image
        elif story_image_form.update_image.data:
            print("Updating image")
            # response = requests.post(app.config['BACKEND_URL'] + "generate_image")
            # print(response.json())

                
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