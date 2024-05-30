from elastic import es_get_stories, es_get_pages
from flask import current_app
from openai import OpenAI
import requests
import uuid


def build_image_prompt(image_description):
    # Build prompt for dall-e-3 to generate image
    style = \
    """
    In the style of Moebius, characterized by fluid lines, 
    intricate detail, and a surreal, dreamlike quality. The image should feature characters 
    and elements that blend futuristic and traditional aesthetics, showcasing elaborate costumes 
    and hybrid mechanical creatures. Use a vibrant color palette with an emphasis on pastel blues, 
    pinks, and purples to convey a sense of otherworldliness. Focus on the smooth integration
    of organic and architectural forms, creating a seamless and imaginative visual narrative that 
    reflects Moebius' iconic approach to visual storytelling.
    Do not include characters not mentioned in the setting description.
    """

    prompt = "Create an image of the following setting description surrounded by hashtags ##### " + image_description + " ##### with the following style: " + style 

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
    # Download image from URL, save it, and return unique image ID
    image = requests.get(url)
    image_id = str(uuid.uuid4())
    image_name = image_id + ".jpg"
    with open("./data/images/" + image_name, "wb") as file:
        file.write(image.content)

    # Also save to static folder for display
    with open("../frontend/static/" + image_name, "wb") as file:
        file.write(image.content)

    
    return(image_id)


def ai_generate_image(image_description):
    # Generate image, save locally, and return unique image ID that can be used to retrieve image
    print("Generating image ...")
    prompt = build_image_prompt(image_description)
    image_url = generate_image_dalle(prompt)
    image_id = save_image(image_url)
    return image_id