from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import Length


class createStory(FlaskForm):
    title = StringField('Story Title:', validators=[Length(min=2, max=32)])
    create = SubmitField('Create Story')


class storyImage(FlaskForm):
    image_description = TextAreaField()
    generate_image = SubmitField('Generate Image')
    update_image = SubmitField('Update Image')


class storyPageNav(FlaskForm):
    previous = SubmitField('Previous')
    next = SubmitField('Next')
    new = SubmitField('New Page')


class storyText(FlaskForm):
    story_text = TextAreaField()
    generate_text = SubmitField('Generate Text')
    update_text = SubmitField('Update Text')
    