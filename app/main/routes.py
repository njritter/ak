import cv2
from datetime import datetime, timezone
from flask import render_template, flash, redirect, url_for, request, g, \
    current_app
from flask_login import current_user, login_required
import sqlalchemy as sa
from app import db
from app.main.forms import EditProfileForm, EmptyForm, \
    SearchForm, craftPageForm, addPageForm, removePageForm
from app.models import User, Post, Project, Page
from app.craft import createTestPage, addPage, removePage, craftPage
from app.main import bp
from app.navigate import getUsers, getProjects, getPages, checkPageStatus
import os
from PIL import Image
import re


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    users = getUsers()
    projects = getProjects(users)
    return render_template('index.html', title='Explore',
                           projects=projects)


@bp.route('/home')
@login_required
def home():
    u = [current_user.username]
    projects = getProjects(u)
    return render_template('home.html', title='Home',
                           projects=projects)


@bp.route('/craft', methods=['GET', 'POST'])
@login_required
def craft():
    u = [current_user.username]
    projects = getProjects(u)
    return render_template('craft/craft.html', title='Craft',
                           projects=projects)


@bp.route('/craft/<project>', methods=['GET', 'POST'])
@login_required
def craft_project(project):
    # Check that project exists for user ... return to craft if not
    newPageImage = '_ak/empty_scroll.png'
    story_pages = getPages(current_user.username, project)
    workshop_pages = getPages(current_user.username, project, 'workshop')
    return render_template('craft/craft_project.html', title='Craft', 
                           story_pages=story_pages, workshop_pages=workshop_pages,
                           newPageImage=newPageImage)


@bp.route('/craft/<project>/<page>', methods=['GET', 'POST'])
@login_required
def craft_project_page(project, page):
    # Check that project exists for user ... return to craft if not
    if page == 'new':
        page_image = '_ak/new_page.png'

    craftForm = craftPageForm(description="test")
    addForm = addPageForm()
    removeForm = removePageForm()

    if 'craft_page' in request.form and craftForm.validate_on_submit():
        if 'use_openai' in request.form:
            print("Creating real page")
            description = request.form['description']
            global_context = "Steampunk fantasy. World full of airships, gears, machines powered by steam and gemstones. Has a little bit of a Hayao Miyazaki Studio Ghibli Nausicaä of the Valley of the Wind combined with Moebius Heavy Metal feel."
            # P0 =  "This image is the title panel for a graphic novel called Kaldor with the word 'Kaldor' written on it. It features a small airshop flying near a mountain that has a medium sized cave entrance. The mountain is part of a chain of mountains and there is a dense forrest at the base of the chain. The cave entrance has a lot of machinery and fortification around it. The cave is about two thirds of the way up the mountain right above the tree line."
            # P1 = "Small airship flying along mountain range with two passengers."
            # P2 = "Small airshop comes across a small town near the base of the mountain range. Something is wrong. There is no one there and some of the buildings look like they have been damaged."
            # P3 = "The two passengers from the airship disembark and explore the abandoned and town that was clearly ravaged by magical beasts"
            # P4 = "The two passengers from the airship disembark and explore the abandoned and town that was clearly ravaged by magical beasts"
            # P5 = "The two passengers find interesting clues in the town that lead them to the cave entrance."
            prompt = global_context + description
            page_image = craftPage(current_user.username, project=project, prompt=prompt)
        else:
            print("Creating test page")
            print(request.form)
            print(request.form['description'])
            print("##########")
            page_image = createTestPage(current_app, current_user.username, project)
        
        return redirect(url_for('main.craft_project_page', project=project, page=page_image))

    # Check if page is in story or workshop
    page_status = checkPageStatus(current_user.username, project, page)
    print(page_status)
    if page_status == 'story':
        page_image = current_user.username + '/' + project + '/' + page + '.png'
    if page_status == 'workshop':
        page_image = current_user.username + '/' + project + '/workshop/' + page + '.png'

    if 'add_page_story' in request.form and addForm.validate_on_submit():
        print("Added page to Story")
        addPage(current_app, current_user.username, project, page)
        return redirect(url_for('main.craft_project_page', project=project, page='new'))
    
    if 'remove_page_story' in request.form:
        print("Removed page from Story")
        removePage(current_app, current_user.username, project, page)
        return redirect(url_for('main.craft_project_page', project=project, page='new'))

    story_pages = getPages(current_user.username, project)
    workshop_pages = getPages(current_user.username, project, 'workshop')

    return render_template('craft/craft_project_page.html', title='Craft', 
                           craftForm=craftForm, addForm=addForm, removeForm=removeForm,
                           story_pages=story_pages, workshop_pages=workshop_pages,
                           newPageImage=page_image, page=page, page_status=page_status)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    page = request.args.get('page', 1, type=int)
    query = user.posts.select().order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page,
                        per_page=current_app.config['POSTS_PER_PAGE'],
                        error_out=False)
    next_url = url_for('main.user', username=user.username,
                       page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username,
                       page=posts.prev_num) if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(username + ' not found.')
            return redirect(url_for('main.index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('main.user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are following ' + username + '!')
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash('User %(username)s not found.', username=username)
            return redirect(url_for('main.index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('main.user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are not following ' + username)
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page,
                               current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title='Search', posts=posts,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/<user>/<project>/<pagenumber>', methods=['GET', 'POST'])
def page(user, project, pagenumber):
    page = str(user) + '/' + str(project) + '/' + str(pagenumber) + '.png'
    
    project_path = os.path.join(current_app.root_path, 'static', user, project)
    pages = os.listdir(project_path)
    print(pages)

    # Function to extract number from filename
    def extract_number(page):
        match = re.search(r'\d+', page)
        return int(match.group()) if match else None

    # Extract numbers and remove None values
    numbers = [extract_number(page) for page in pages]
    numbers = [num for num in numbers if num is not None]

    last = str(max(numbers))
    previous = str(int(pagenumber) - 1)
    if int(previous) < 0:
        previous = str(0)
    next = str(int(pagenumber) + 1)
    if int(next) > int(last):
        next = last

    return render_template('page.html', title='Scroll', page=page, user=user, 
                           project=project,previous=previous, next=next, last=last)
