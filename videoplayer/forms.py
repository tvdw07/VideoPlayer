from flask_wtf import FlaskForm
from wtforms import HiddenField, SubmitField
from wtforms.validators import DataRequired


class DeleteVideoForm(FlaskForm):
    """Form für sicheres Löschen von Videos mit CSRF-Protection."""
    video_path = HiddenField(validators=[DataRequired()])
    submit = SubmitField("Löschen")

