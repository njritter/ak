from datetime import datetime, timezone
from flask import render_template, flash, redirect, url_for, request, g, \
    current_app
from flask_login import current_user, login_required
import sqlalchemy as sa
from app import db
from app.main.forms import EditProfileForm, EmptyForm, PostForm, SearchForm
from app.models import User, Post, Project
from app.main import bp
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
    # get users, projects, and pages from db ... filler class here now
    static = os.path.join(current_app.root_path, 'static')
    users = os.listdir(static)
    users = [u for u in users if not u.startswith('.')]
    projects = []
    for u in users:
        user_projects = os.listdir(os.path.join(static, u))
        user_projects = [p for p in user_projects if not p.startswith('.')]
        for p in user_projects:
            project = Project(user = u, 
                              project = p, 
                              url_start = u + '/' + p + '/cover.png')
            projects.append(project)
    return render_template('index.html', title='Explore',
                           projects=projects)


@bp.route('/home')
@login_required
def home():
    project_path = os.path.join(current_app.root_path, 'static', current_user.username)
    page = request.args.get('page', 1, type=int)
    posts = db.paginate(current_user.following_posts(), page=page,
                        per_page=current_app.config['POSTS_PER_PAGE'],
                        error_out=False)
    next_url = url_for('main.index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('home.html', title='Home',
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/craft', methods=['GET', 'POST'])
@login_required
def craft():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('main.index'))
    return render_template('craft.html', title='Craft', form=form)


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
            flash(_('User %(username)s not found.', username=username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash(_('You cannot unfollow yourself!'))
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
