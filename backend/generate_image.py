from elastic import es_get_stories, es_get_pages, es_get_backstory
from generate_text import summarize_context_for_image_gen, build_ai_image_description
from flask import current_app
from openai import OpenAI
import requests
import uuid


def ai_generate_image(es, page_id, image_description):
    # Generate image, save locally, and return unique image ID that can be used to retrieve image
    # ... do something better with es connection passing ... 
    print("In ai_generate_image(). Starting image generation process ...")
    prompt = build_image_prompt(es, page_id, image_description)
    image_url = generate_image_dalle(prompt)
    image_id = save_image(image_url)
    return image_id


def build_image_prompt(es, page_id, image_description):
    # Build prompt for dall-e-3 to generate image
    # Use delimiters to indicate distinct parts of the prompt
    print("\tIn build_image_prompt(). Building image prompt ...")

    description = build_image_description(es, page_id, image_description)
    
    style = f"""
    In the style of Moebius, characterized by fluid lines, 
    intricate detail, and a surreal, dreamlike quality. The image should feature characters 
    and elements that blend futuristic and traditional aesthetics, showcasing elaborate costumes 
    and hybrid mechanical creatures. Use a vibrant color palette with an emphasis on pastel blues, 
    pinks, and purples to convey a sense of otherworldliness. Focus on the smooth integration
    of organic and architectural forms, creating a seamless and imaginative visual narrative that 
    reflects Moebius' iconic approach to visual storytelling.
    """
    
    instructions = f"""
    Do not include characters in the image that are not mentioned in the description.
    Do not include any text or blocks of text in the image.
    """

    prompt = f"""
    Create an image from the following description delimited by triple backticks ```{description}```.
    Use the following style delimited by triple backticks ```{style}```.
    Keep in mind the following instructions delimited by triple backticks ```{instructions}```.
    """

    # print("Prompt:", prompt)

    return prompt


def build_image_description(es, page_id, image_description):
    # Build image description taking into account the story so far
    # Specify the steps required to build the image description.
    print("\t\tIn build_image_description(). Building image description from context ...")

    # Get pages of story so far
    page = es_get_pages(es, page_id)
    story_id = page[0]["story_id"]
    page_number = page[0]["page_number"]
    backstory = es_get_backstory(es, story_id, page_number)
    print("Backstory:", backstory)
    if backstory is not None:
        backstory_summary = summarize_context_for_image_gen(backstory)
        ai_image_description = build_ai_image_description(backstory_summary, image_description)
    else:
        ai_image_description = image_description
    
    return ai_image_description


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
    # Download image from URL, save it, and return unique image ID
    image = requests.get(url)
    image_id = str(uuid.uuid4())
    image_name = image_id + ".jpg"
    image_path=current_app.config['DATA'] + "/images/"
    print("Data Path:", image_path)
    with open(image_path + image_name, "wb") as file:
        file.write(image.content)

    return(image_id)
