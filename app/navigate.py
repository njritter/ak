from datetime import datetime
from flask import current_app
from flask_login import current_user
from app.models import User, Project, Page
import os
import re
import time


def getUsers():
    users = []
    static = os.path.join(current_app.root_path, 'static')
    users = os.listdir(static)
    users = [u for u in users if not u.startswith(('.', '_'))]
    print(users)

    return(users)


def getProjects(users):
    # Takes a list of users and returns a list of Projects
    projects = []
    static = os.path.join(current_app.root_path, 'static')
    for user in users:
        user_projects = os.listdir(os.path.join(static, user))
        user_projects = [p for p in user_projects if not p.startswith('.')]
        for p in user_projects:
            project = Project(user = user, 
                              project = p, 
                              url_start = user + '/' + p + '/cover.png')
            projects.append(project)

    return(projects)


def load_page(pageId):
    search_query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"id": pageId}},
                ]
            }
        }
    }
    response = current_app.elasticsearch.search(index="page", body=search_query)
    if response['hits']['total']['value']:
        page = Page.from_dict(response['hits']['hits'][0]['_source'])
        return(page)
    else:
        print("No page found with id: " + pageId)
        return(None)


def get_pages(username, project, status=None):
    # Take a user and project and returns a list of all Pages for Project
    # Filter by status if provided
    search_query = {
        "size": 1000,
        "query": {
            "bool": {
                "must": [
                    {"match": {"username": username}},
                    {"match": {"projectId": project}},
                ]
            }
        }
    }

    response = current_app.elasticsearch.search(index="page", body=search_query)

    pages = []
    for hit in response['hits']['hits']:
        page = Page.from_dict(hit['_source'])
        if status is None:
            pages.append(page)
        else:
            if page.status == status:
                pages.append(page)

    return(pages)


def get_new_page(username, project):

    page_json = {
        "id": "new",
        "username": username,
        "projectId": project,
        "storyText": "Add your story here",
        "userImageDescription": "Describe associated image here",
        "akImageDescription": "",
        "iconURL":  "_ak/new_page_small.png",
        "imageURL":  "_ak/new_page.png",
        "status": "workshop",
        "pageNumber": None,
        "createdDate": datetime.now().isoformat(),
        "updatedDate": datetime.now().isoformat(),
    }

    page = Page.from_dict(page_json)

    return(page)


def add_page(page):
    # Add page to Elasticsearch
    response = current_app.elasticsearch.index(index='page', id=page.id, body=page.__dict__)
    print("Added page:", response)
    return()


def new_page(project, args):

    page = Page(
        id = str(round(time.time() * 100)),
        username = current_user.username,
        projectId = project,
        storyText = "Add your story here",
        userImageDescription= "Describe associated image here",
        akImageDescription =  "",
        status = "workshop",
        iconURL = "_ak/new_page_small.png",
        imageURL = "_ak/new_page.png",
        pageNumber = None,
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


def update_page(pageId, parameters={}):
    # ... what checks should be here ...
    # ... should this be a property of the page object? ...
    # Update updatedDate if changes made

    print("Updating page: " + pageId)

    page = load_page(pageId)
    print("Page before update:", page)

    if text := parameters.get('text'):
        page.storyText = text

    if description := parameters.get('description'):
        page.userImageDescription = description

    if page_status := parameters.get('page_status'):
        page.status = page_status

    # Replace page with update page in page index
    response = current_app.elasticsearch.index(
        index='page', 
        id=page.id, 
        document=page.__dict__)
    
    current_app.elasticsearch.indices.refresh(index='page')

    print("Updated page in ElasticSearch index: " + str(response))
    page = load_page(pageId)
    print("Page after update:", page)

    
    return(page)
