from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField, IntegerField
from wtforms.validators import ValidationError, DataRequired, Length, NumberRange
import sqlalchemy as sa
from app import db
from app.models import User


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me',
                             validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = db.session.scalar(sa.select(User).where(
                User.username == self.username.data))
            if user is not None:
                raise ValidationError('Please use a different username.')


class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')


class craftPageForm(FlaskForm):
    text = TextAreaField('Story text')
    description = TextAreaField('Describe page', validators=[DataRequired()])
    page_status = SelectField('Page Status:', choices=[
        ('workshop', 'Workshop'), 
        ('story', 'Story'), 
        ('storage', 'Storage')], validators=[DataRequired()])
    page_number = IntegerField('Page Number', validators=[DataRequired(), NumberRange(min=0)])
    craft_page = SubmitField('Craft')
    use_openai = BooleanField('Use OpenAI')
    update_page = SubmitField('Update')


class PostForm(FlaskForm):
    post = TextAreaField('Describe page', validators=[DataRequired()])
    submit = SubmitField('Submit')


class SearchForm(FlaskForm):
    q = StringField('Search', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'meta' not in kwargs:
            kwargs['meta'] = {'csrf': False}
        super(SearchForm, self).__init__(*args, **kwargs)
