from wtforms import Form, StringField, validators, FileField, ValidationError
from wtforms.widgets import FileInput
import os

def check_excelfile(form, field):
    if field.data:
        filename = field.data.filename
        ALLOWED_EXTENSIONS = ['xlsx']
        if not ('.' in filename and filename.rsplit('.',1)[1] in ALLOWED_EXTENSIONS):
            raise ValidationError('Wrong Filetype, you can upload only xlsx files')
        else:
            raise ValidationError('field not Present') # I added this justfor some debugging.

def check_templatefile(form, field):
    if field.data:
        filename = field.data.filename
        ALLOWED_EXTENSIONS = ['txt']
        if not ('.' in filename and filename.rsplit('.',1)[1] in ALLOWED_EXTENSIONS):
            raise ValidationError('Wrong Filetype, you can upload only xlsx files')
        else:
            raise ValidationError('field not Present') # I added this justfor some debugging.


class ProjectForm(Form):
    client = StringField('Client', [validators.DataRequired(), validators.Length(max=25)])
    project_name = StringField('Project Name', [validators.DataRequired(), validators.Length(max=35)])
    subproject_name = StringField('Subproject Name', [validators.optional(), validators.Length(max=35)])
    excel_file = FileField(u'Excel Workbook', validators=[check_templatefile])
    template_file = FileField(u'Template File', validators=[check_excelfile])

