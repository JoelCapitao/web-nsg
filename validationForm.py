from wtforms import Form, StringField, validators, FileField, ValidationError
from flask.ext.wtf.file import FileRequired, FileAllowed, FileField as wtfFileField

def check_excelfile(form, field):
    if field.data:
        filename = field.data.filename
        ALLOWED_EXTENSIONS = ['xlsx']
        if not ('.' in filename and filename.rsplit('.',1)[1] in ALLOWED_EXTENSIONS):
            raise ValidationError('Wrong Filetype, you can upload only xlsx files')



def check_templatefile(form, field):
    if field.data:
        filename = field.data.filename
        ALLOWED_EXTENSIONS = ['txt']
        if not ('.' in filename and filename.rsplit('.',1)[1] in ALLOWED_EXTENSIONS):
            raise ValidationError('Wrong Filetype, you can upload only txt files')


class ProjectForm(Form):
    client = StringField('Client', [validators.DataRequired(), validators.Length(max=25)])
    project_name = StringField('Project Name', [validators.DataRequired(), validators.Length(max=35)])
    subproject_name = StringField('Subproject Name', [validators.optional(), validators.Length(max=35)])
    excel_file = wtfFileField(u'Excel Workbook', validators=[check_excelfile])
    template_file = FileField(u'Template File', validators=[check_templatefile])

class NewProjectVersionForm(Form):
    excel_file = FileField(u'Excel Workbook', validators=[check_excelfile])
    template_file = FileField(u'Template File', validators=[check_templatefile])

class ProjectUpdateForm(Form):
    client = StringField('Client', [validators.DataRequired(), validators.Length(max=25)])
    project_name = StringField('Project Name', [validators.DataRequired(), validators.Length(max=35)])
    subproject_name = StringField('Subproject Name', [validators.optional(), validators.Length(max=35)])
