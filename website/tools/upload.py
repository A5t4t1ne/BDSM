from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
import json

class UploadFileForm(FlaskForm):
    file = FileField(label="Choose file", id="fileInput")
    submit = SubmitField("Commit")