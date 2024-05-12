from elastic import es_get_stories, es_get_pages
from flask import current_app
from openai import OpenAI
import requests


def ai_generate_text(es, story_id, page_id, text):
    # Generate text continuation using GPT-3.5 model
    
    system_context = get_context(es, story_id, page_id)
    page_context = text
    
    prompt = "You are a master story teller continuing to tell a story." + \
        "A summary of the story so far is: " + system_context + \
        "Now continue the story startng with the following text: " + page_context
    
    print("####################")
    print("Prompt:", prompt)
    print("####################")

    client = OpenAI(api_key=current_app.config['OPENAI_API_KEY'])
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo", 
        max_tokens=200,
        messages=[
            {"role": "system", "content": prompt},
            ]
        )

    response = completion.choices[0].message.content

    print("####################")
    print("Response:", response)
    print("####################")
    
    return response


def get_context(es, story_id, page_id):
    # Return an AI generated summary of the story so far as context
    story = es_get_stories(es, story_id)
    pages = story[0]['pages']
    print("####################")
    print("Number of pages:", len(pages))
    
    pages = es_get_pages(es, pages)
    
    text = ""
    for page in pages:
        if page['id'] != page_id:
            print("Page Text:", page['story_text'])
            text += " " + page['story_text']
    
    print("####################")

    return text


def build_image_prompt():
    # Build prompt for dall-e-3 to generate image
    prompt = "An image in epic anime style of two people playing the board game Go"
    return prompt


def generate_image_dalle(prompt):
    # Pass prompt to dall-e-3 to generate image with OpenAI API
    # URL of image is returned
    client = OpenAI(api_key=current_app.config['OPENAI_API_KEY'])
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1)
    image_url = response.data[0].url
    
    # Print URL of image every time. If something goes wrong later you can still get image!
    print("Image URL:", image_url)  

    return(image_url)


def save_image(url):
    # Download image from URL and save it to local directory

    # Download image from URL
    image = requests.get(url)

    # Save image to local directory
    with open("../data/generated_image.jpg", "wb") as file:
        file.write(image.content)


def ai_generate_image():
    # Generate image using dall-e-3 model
    prompt = build_image_prompt()
    image_url = generate_image_dalle(prompt)
    save_image(image_url)

    return image_url