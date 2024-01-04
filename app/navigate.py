from flask import current_app
from app.models import User, Project, Page
import os
import re


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


def getPages(user, project, shelf=None):
    # Takes a user and project and returns a list of all Pages for Project
    project_path = os.path.join(current_app.root_path, 'static', user, project)
    stub = user + '/' + project + '/'
    if shelf == 'workshop':
        project_path = os.path.join(project_path, 'workshop')
        stub = user + '/' + project + '/workshop/'
    page_image_names = os.listdir(project_path)

    # Function to extract number from filename
    def extract_number(filename):
        match = re.search(r'\d+', filename)
        return int(match.group()) if match else None

    # Extract numbers and remove None values
    page_numbers = [extract_number(num) for num in page_image_names]
    page_numbers = [num for num in page_numbers if num is not None]
    unique_sorted_page_numbers = sorted(set(page_numbers))

    pages = []
    for page_number in unique_sorted_page_numbers:      
        page = Page(username = user,
                    project = project,
                    number = page_number,
                    url = stub + str(page_number) + 'm.png')
        pages.append(page)
        print(page)
        print(project_path)

    return(pages)