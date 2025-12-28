from flask_wtf import FlaskForm
from wtforms import HiddenField, SubmitField
from wtforms.validators import DataRequired


class DeleteVideoForm(FlaskForm):
    """Form to delete a video file."""
    video_path = HiddenField(validators=[DataRequired()])
    submit = SubmitField("Löschen")

