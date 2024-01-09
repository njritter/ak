from app.navigate import getPages
import cv2
import numpy as np
import os
from PIL import Image
import shutil
import time

def createTestPage(current_app, current_user, project):
    
    # Generate image (already exists)
    stock_image_path = os.path.join(current_app.root_path, 'static', '_ak/Kaldor_P1.png')
    print(stock_image_path)

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