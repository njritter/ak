from datetime import datetime, timezone
from hashlib import md5
from time import time
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from app import db, login
from app.search import add_to_index, remove_from_index, query_index


class SearchableMixin:
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return [], 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        query = sa.select(cls).where(cls.id.in_(ids)).order_by(
            db.case(*when, value=cls.id))
        return db.session.scalars(query), total

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in db.session.scalars(sa.select(cls)):
            add_to_index(cls.__tablename__, obj)


db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)


followers = sa.Table(
    'followers',
    db.metadata,
    sa.Column('follower_id', sa.Integer, sa.ForeignKey('user.id'),
              primary_key=True),
    sa.Column('followed_id', sa.Integer, sa.ForeignKey('user.id'),
              primary_key=True)
)


class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True,
                                                unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True,
                                             unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(
        default=lambda: datetime.now(timezone.utc))

    posts: so.WriteOnlyMapped['Post'] = so.relationship(
        back_populates='author')
    following: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        back_populates='followers')
    followers: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.followed_id == id),
        secondaryjoin=(followers.c.follower_id == id),
        back_populates='following')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def follow(self, user):
        if not self.is_following(user):
            self.following.add(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    def is_following(self, user):
        query = self.following.select().where(User.id == user.id)
        return db.session.scalar(query) is not None

    def followers_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.followers.select().subquery())
        return db.session.scalar(query)

    def following_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.following.select().subquery())
        return db.session.scalar(query)

    def following_posts(self):
        Author = so.aliased(User)
        Follower = so.aliased(User)
        return (
            sa.select(Post)
            .join(Post.author.of_type(Author))
            .join(Author.followers.of_type(Follower), isouter=True)
            .where(sa.or_(
                Follower.id == self.id,
                Author.id == self.id,
            ))
            .group_by(Post)
            .order_by(Post.timestamp.desc())
        )

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except Exception:
            return
        return db.session.get(User, id)


@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))


class Post(SearchableMixin, db.Model):
    __searchable__ = ['body']
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id),
                                               index=True)
    language: so.Mapped[Optional[str]] = so.mapped_column(sa.String(5))

    author: so.Mapped[User] = so.relationship(back_populates='posts')

    def __repr__(self):
        return '<Post {}>'.format(self.body)
    

class Project:
    def __init__(self, id=None, name=None, username=None, overview=None, globalContext=None, status=None, createdDate=None, updatedDate=None, icon=None):
        self.id = id
        self.name = name
        self.username = username
        self.overview = overview
        self.globalContext = globalContext
        self.status = status
        self.createdDate = createdDate
        self.updatedDate = updatedDate
        self.icon = icon

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def get_info(self):
        """Returns a formatted string with project details."""
        info = f"Project ID: {self.id}\n"
        info += f"Name: {self.name}\n"
        info += f"Username: {self.username}\n"
        info += f"Overview: {self.overview}\n"
        info += f"Global Context: {self.globalContext}\n"
        info += f"Status: {self.status}\n"
        info += f"Created Date: {self.createdDate}\n"
        info += f"Updated Date: {self.updatedDate}\n"
        info += f"Icon: {self.icon}\n"
        return info

    def __repr__(self):
        """Returns a formal string representation of the Project object."""
        return f"Project(id={self.id}, name={self.name}, username={self.username}, overview={self.overview}, globalContext={self.globalContext}, status={self.status}, createdDate={self.createdDate}, updatedDate={self.updatedDate}, icon={self.icon})"


class Page:
    def __init__(self, id=None, username=None, projectId=None, storyText=None, 
                 userImageDescription=None, akImageDescription=None, iconURL=None, 
                 imageURL=None, status=None, pageNumber=None, createdDate=None, 
                 updatedDate=None):
        self.id = id
        self.username = username
        self.projectId = projectId
        self.storyText = storyText
        self.userImageDescription = userImageDescription
        self.akImageDescription = akImageDescription
        self.iconURL = iconURL
        self.imageURL = imageURL
        self.status = status
        self.pageNumber = pageNumber
        self.createdDate = createdDate
        self.updatedDate = updatedDate

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def get_info(self):
        info = (
            f"Project ID: {self.id}, "
            f"Username: {self.username}, "
            f"Project ID: {self.projectId}, "
            f"Story Text: {self.storyText}, "
            f"User Image Description: {self.userImageDescription}, "
            f"AK Image Description: {self.akImageDescription}, "
            f"Icon URL: {self.iconURL}, "
            f"Image URL: {self.imageURL}, "
            f"Status: {self.status}, "
            f"Page Number: {self.pageNumber}, "
            f"Created Date: {self.createdDate}, "
            f"Updated Date: {self.updatedDate}"
        )
        return info
    
    def __repr__(self):
        return (f"Page(id={self.id}, username={self.username}, projectId={self.projectId}, "
                f"storyText={self.storyText}, userImageDescription={self.userImageDescription}, "
                f"akImageDescription={self.akImageDescription}, iconURL={self.iconURL}, "
                f"imageURL={self.imageURL}, status={self.status}, pageNumber={self.pageNumber}, "
                f"createdDate={self.createdDate}, updatedDate={self.updatedDate})")
