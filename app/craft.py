from app.models import Page
from app.navigate import get_pages
from datetime import datetime
import cv2
from flask import current_app
from flask_login import current_user
import numpy as np
from openai import OpenAI
import os
from PIL import Image
import requests
import shutil
import time


def add_page(page):
    # Add page to Elasticsearch
    response = current_app.elasticsearch.index(index='page', id=page.id, body=page.__dict__)
    print(response)
    return()


def craft_page(project, args):

    page = Page(
        id = str(round(time.time() * 100)),
        username = current_user.username,
        projectId = project,
        status="workshop",
        createdDate = datetime.now().isoformat(),
        updatedDate = datetime.now().isoformat(),
    )

    fields = page.__dict__.keys()

    for key, value in args.items():
        if key in fields:
            setattr(page, key, value)

    # Add page to Elasticsearch page index
    add_page(page)
    time.sleep(1)

    return(page)


def compressImage(image_id, image_path=None, icon_path=None):

    if image_path == None:
        image_path = os.path.join(current_app.root_path, 'static', '_temp', image_id + '.png')

    if icon_path == None:    
        icon_path = os.path.join(current_app.root_path, 'static', '_temp', image_id + 'm.png')

    # Load image
    image = Image.open(image_path)

    # Generate image icon
    image_np = np.array(image)
    image_icon_np = cv2.resize(image_np, (256, 256), interpolation=cv2.INTER_AREA)
    image_icon = Image.fromarray(image_icon_np)

    # Save image icon
    image_icon.save(icon_path)
    
    return()


def moveImage(current_user, project, image_id, shelf='workshop'):
    print("Moving image")
    # Move image and icon from temp to workshop
    oldImagePath = os.path.join(current_app.root_path, 'static', '_temp', image_id + '.png')
    oldIconPath = os.path.join(current_app.root_path, 'static', '_temp', image_id + 'm.png')

    newImagePath = os.path.join(current_app.root_path, 'static', current_user, project, shelf, image_id + '.png')
    newIconPath = os.path.join(current_app.root_path, 'static', current_user, project, shelf, image_id + 'm.png')

    shutil.move(oldImagePath, newImagePath)
    shutil.move(oldIconPath, newIconPath)

    return()


def saveImageURL(image_url):

    page_id = str(round(time.time() * 100))
    path = os.path.join(current_app.root_path, 'static', '_temp', page_id + '.png')
    response = requests.get(image_url)
    # Check if the request was successful and the content type is correct
    if response.status_code == 200 and response.headers['Content-Type'] == 'image/png':
        # Write the content of the response to a file
        with open(path, 'wb') as file:
            file.write(response.content)
        print(f"Image saved at {path}")
    else:
        return "Failed to download the image or incorrect content type"
    return(page_id)


def generateImage(prompt):
    
    client = OpenAI(api_key=current_app.config['OPENAI_API_KEY'])
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1)

    image_url = response.data[0].url
    print(image_url)
    
    return(image_url)


def craftPage(current_user, project, prompt):
    # Get info relevant to story
    print("####################")
    
    image_url = generateImage(prompt)
    image_id = saveImageURL(image_url)
    print(image_id)
    compressImage(image_id)
    moveImage(current_user, project, image_id)

    print("####################")
    
    return(image_id)


def createTestPage(current_app, current_user, project):
    
    # Generate image (already exists)
    stock_image_path = os.path.join(current_app.root_path, 'static', '_ak/Kaldor_P1.png')

    # Load image
    image = Image.open(stock_image_path)

    # Generate image icon
    image_np = np.array(image)
    image_icon_np = cv2.resize(image_np, (256, 256), interpolation=cv2.INTER_AREA)
    image_icon = Image.fromarray(image_icon_np)

    # Save image and icon to workshop (do this for all images for now)
    page_id = str(round(time.time() * 100))
    image_path = os.path.join(current_app.root_path, 'static', current_user, project, 
                              'workshop', page_id + '.png')
    icon_path = os.path.join(current_app.root_path, 'static', current_user, project, 
                              'workshop', page_id + 'm.png') 
    image.save(image_path)
    image_icon.save(icon_path)
    
    return(page_id)


def addPage(current_app, current_user, project, page):
    # Check to see if page and icon exist in workshop ...
    oldPagePath = os.path.join(current_app.root_path, 'static', current_user, project, 'workshop', page + '.png')
    oldPageIconPath = os.path.join(current_app.root_path, 'static', current_user, project, 'workshop', page + 'm.png')  
    
    # Generate new name for image and icon
    pages = getPages(current_user, project)
    numbers = []
    for page in pages:
        numbers.append(int(page.number))
    if numbers:
        next = max(numbers) + 1
    else:
        next = 0

    newPagePath = os.path.join(current_app.root_path, 'static', current_user, project, str(next) + '.png')
    newPageIconPath = os.path.join(current_app.root_path, 'static', current_user, project, str(next) + 'm.png')
    
    # Move Page and Icon from Workshop to Story and rename
    shutil.move(oldPagePath, newPagePath)
    shutil.move(oldPageIconPath, newPageIconPath)
    
    return(newPagePath)


def removePage(current_app, current_user, project, page):
    # Check to see if page and icon exist in story ...
    oldPagePath = os.path.join(current_app.root_path, 'static', current_user, project, page + '.png')
    oldPageIconPath = os.path.join(current_app.root_path, 'static', current_user, project, page + 'm.png')      
    
    # Generate new name for image and icon
    page_id = str(round(time.time() * 100))

    newPagePath = os.path.join(current_app.root_path, 'static', current_user, project, 'workshop', page_id + '.png')
    newPageIconPath = os.path.join(current_app.root_path, 'static', current_user, project, 'workshop', page_id + 'm.png')
    
    # Move Page and Icon from Workshop to Story and rename
    shutil.move(oldPagePath, newPagePath)
    shutil.move(oldPageIconPath, newPageIconPath)

    renumberPages(current_app, current_user, project)
    
    return()


def renumberPages(current_app, current_user, project):
    # Get list of pages in story
    pages = getPages(current_user, project)
    numbers = []
    for page in pages:
        numbers.append(int(page.number))
    numbers = sorted(numbers)
    
    # Rename pages in story
    for i in range(len(numbers)):
        oldPagePath = os.path.join(current_app.root_path, 'static', current_user, project, str(numbers[i]) + '.png')
        oldPageIconPath = os.path.join(current_app.root_path, 'static', current_user, project, str(numbers[i]) + 'm.png')      
        
        newPagePath = os.path.join(current_app.root_path, 'static', current_user, project, str(i) + '.png')
        newPageIconPath = os.path.join(current_app.root_path, 'static', current_user, project, str(i) + 'm.png')
        
        shutil.move(oldPagePath, newPagePath)
        shutil.move(oldPageIconPath, newPageIconPath)
    
    return()