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


def summarize_context_for_image_gen(context):
    # Return an AI generated summary of the story so far as context
    # Return output from this in json format
    print("\t\t\tIn summarize_context_for_image_gen().")

    prompt = f"""
    You are a master storyteller summarizing details about the world and characters from the 
    story delimited by triple backticks ```{context}```.
    """
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
    print("Context Summary:", response)
    print("####################")

    return response


def build_ai_image_description(backstory_summary, image_description):
    # 
    print("\t\t\tIn build_ai_image_description().")
    
    prompt = f"""
    You are a master prompt engineer designing a prompt to generate an image from the following 
    description triple backticks ```{image_description}```. This image should take into account the
    following summary of the story so far delimited by triple backticks ```{backstory_summary}```.
    """ 
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
    print("Prompt:", response)
    print("####################")

    return response