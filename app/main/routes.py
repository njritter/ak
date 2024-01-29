from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
    current_app
from flask_login import current_user, login_required
import sqlalchemy as sa
from app import db
from app.crafting import craft_image, get_user_projects, get_project, get_projects
from app.main import bp
from app.main.forms import EditProfileForm, EmptyForm, \
    SearchForm, craftPageForm
from app.models import User, Post, Project, Page
from app.navigate import get_pages, load_page, update_page, new_page
import os
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
    projects = get_projects()
    return render_template('index.html', title='Explore', projects=projects)


@bp.route('/home')
@login_required
def home():
    projects = get_projects()
    return render_template('home.html', title='Home', projects=projects)


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


####################################################################################################
##### Craft Routes
####################################################################################################


@bp.route('/craft/', methods=['GET', 'POST'])
@login_required
def craft():
    # Pull up all info for user's craft page that lists all their projects
    print("In craft")
    projects = get_user_projects(current_user.username)

    return render_template('craft/craft.html', title='Craft',
                           projects=projects)


@bp.route('/craft/<project>', methods=['GET', 'POST'])
@login_required
def craft_project(project):
    # Project Home Page
    print("Working on project:", project)
    project = get_project(current_user.username, project)
    story_pages = get_pages(current_user.username, project.name, 'story')
    return render_template('craft/craft_project.html', title='Craft', 
                           story_pages=story_pages, project=project)


@bp.route('/craft/<project>/<pageId>', methods=['GET', 'POST'])
@login_required
def craft_project_pageId(project, pageId):
    # Workspace for crafting Page: pageId

    # Update existing page
    if 'update_page' in request.form:
        page = update_page(pageId=pageId, parameters=request.form)    
        return redirect(url_for('main.craft_project_pageId', project=project, pageId=page.id))
    
    # Craft something new
    if 'craft_page' in request.form:
        
        # If 'use_openai' is checked, then use OpenAI to generate image
        if 'use_openai' in request.form:
            test = False
        else:
            test = True
        
        # Make sure to include most recent updates to page
        page = update_page(pageId=pageId, parameters=request.form)    
        page = craft_image(page, test=test)

        return redirect(url_for('main.craft_project_pageId', project=project, pageId=page.id))
    
    if pageId == 'new':
        # Make this its own endpoint ...
        page = new_page(project, request.form)
        return redirect(url_for('main.craft_project_pageId', project=project, pageId=page.id))
    else:
        page = load_page(pageId)
    print("Loading page:", page.id)
    print("Page:", page)

    craftForm = craftPageForm(
        description=page.userImageDescription,
        text = page.storyText,
        page_status = page.status,
        page_number = page.pageNumber)
    
    story_pages = get_pages(current_user.username, project, 'story')
    workshop_pages = get_pages(current_user.username, project, 'workshop')

    return render_template('craft/craft_project_page.html', title='Craft', 
                           craftForm=craftForm, story_pages=story_pages, 
                           workshop_pages=workshop_pages, project=project, page=page)


# @bp.route('/craft/add/<project>', methods=['POST'])
# @login_required
# def craft_add_project(project):
#     # Takes a dictionary of Project info and adds a new Project to user
#     return()


# @bp.route('/craft/update/<project>', methods=['POST'])
# @login_required
# def craft_update_project(project):
#     return()


# @bp.route('/craft/add/<page>', methods=['POST'])
# @login_required
# def craft_add_page(page):
#     # Takes a dictionary of Page info and adds a new Page to project
#     return()


# @bp.route('/craft/update/<page>', methods=['POST'])
# @login_required
# def craft_update_page(page):
#     return()