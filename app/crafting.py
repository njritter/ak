from app.models import Page, Project
from app.navigate import get_pages, load_page
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


############################################################
#################### Craft Image ###########################
############################################################

def craft_image(page, test=False):

    print("Generating image for page: " + page.id)
    print(page.imageURL)

    if page.imageURL != "_ak/new_page.png":
        print("Image already exists")
        return()

    # Get all info relevant to story
    # all_context = get_story_context(current_user.username, project)

    # Prioritize context for prompt building
    # priority_context = prioritize_context(all_context, image)

    # Build prompt for generating image
    # prompt = build_image_prompt(priority_context)
    prompt = page.userImageDescription
    print(prompt)

    # Generate image with OpenAI API which returns a URL for image
    image_url = generate_image(page, test=test)
    print(image_url)

    # Save image to User's project folder
    # ... this is currently overwriting the image with the same name ...
    image_path = save_image(page, image_url)
    page.imageURL = page.username + '/' + page.projectId + '/' + page.id + '.png'
    print("Saved image to User's project folder at:", page.imageURL)

    # Compress image to generate icon
    icon_path = compress_image(page, image_path)
    page.iconURL = page.username + '/' + page.projectId + '/' + page.id + 'm.png'
    print("Saved icon to User's project folder at:", page.iconURL)

    # Update page in ElasticSearch with image info
    print("#############################################")
    page = update_page(page)
    print("Updated page:", page)
    print("#############################################")

    return(page)


def update_page(page):
    # ... reconcile this with navigate update page ...

    print("Updating page: " + page.id)

    # Replace page with update page in page index
    response = current_app.elasticsearch.index(
        index='page', 
        id=page.id, 
        document=page.__dict__)
    
    current_app.elasticsearch.indices.refresh(index='page')

    print("Updated page in ElasticSearch index: " + str(response))
    page = load_page(page.id)
    # print("Page after update:", page)
    return(page)


def compress_image(page, image_path):
    
    icon_path = os.path.join(current_app.root_path, 'static', page.username, page.projectId, page.id + 'm.png')

    # Load image
    image = Image.open(image_path)

    # Generate image icon
    image_np = np.array(image)
    image_icon_np = cv2.resize(image_np, (256, 256), interpolation=cv2.INTER_AREA)
    image_icon = Image.fromarray(image_icon_np)

    # Save image icon
    image_icon.save(icon_path)
    
    return()


def save_image(page, image_url):
    # Get image (.png) from URL and save to User's project folder
    # Add Test: check for existence of path and create or store in default location if not
    
    # Path to User's project folder
    path = os.path.join(current_app.root_path, 'static', page.username, page.projectId, page.id + '.png')
    
    # Get image from URL
    response = requests.get(image_url)

    # Check if the request was successful and the content type is correct
    if response.status_code == 200 and response.headers['Content-Type'] == 'image/png':
        # Write image to file
        with open(path, 'wb') as file:
            file.write(response.content)
        print(f"Image saved at {path}")
    else:
        return "Failed to download the image or incorrect content type"
    return(path)


def generate_image(page, test=False):
    # Takes a page object and generates an image using OpenAI API

    if test:  # return path to image in static folder
        image_path = "http://127.0.0.1:5000/static/drazi/kaldor/170560689883.png"
        print("Returning test image:", image_path)
        return(image_path)
    
    # Generate image with OpenAI API
    client = OpenAI(api_key=current_app.config['OPENAI_API_KEY'])
    response = client.images.generate(
        model="dall-e-3",
        prompt=page.userImageDescription,
        size="1024x1024",
        quality="standard",
        n=1)

    image_url = response.data[0].url
    print("#########################")
    print(image_url)
    print("#########################")

    return(image_url)


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

############################################################
#################### Projects ##########################
############################################################

def get_projects():
    # Get all projects from ElasticSearch and return Project object
    # ... check that only one result ...
    print("Getting projects")
    search_query = {
        "query": {
            "match_all": {}
        }
    }
    response = current_app.elasticsearch.search(index="project", body=search_query)
    projects = []
    for project in response['hits']['hits']:
        p = Project.from_dict(project['_source'])
        projects.append(p)

    return(projects)


def get_user_projects(username):
    # Get project info from ElasticSearch and return Project object
    # ... check that only one result ...
    print("Getting projects for user:", username)
    search_query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"username": username}},
                ]
            }
        }
    }
    response = current_app.elasticsearch.search(index="project", body=search_query)
    projects = []
    for project in response['hits']['hits']:
        p = Project.from_dict(project['_source'])
        projects.append(p)

    return(projects)


def get_project(username, project_name):
    # Get project info from ElasticSearch and return Project object
    # ... check that only one result ...

    search_query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"username": username}},
                    {"match": {"name": project_name}},
                ]
            }
        }
    }
    response = current_app.elasticsearch.search(index="project", body=search_query)
    project = Project.from_dict(response['hits']['hits'][0]['_source'])
    print("Project response:", project)

    return(project)