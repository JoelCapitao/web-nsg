from wtforms import Form, StringField, validators, FileField, ValidationError, PasswordField
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

class RegisterForm(Form):
    firstname = StringField('Firstname', [validators.DataRequired(), validators.Length(max=25)])
    lastname = StringField('Lastname', [validators.DataRequired(), validators.Length(max=25)])
    email = StringField('Email', [validators.Email, validators.Length(max=320,
                                                                    message='Email must be less than 320 characters')])
    uid = StringField('User Id', [validators.DataRequired(), validators.Length(max=7,
                                                                    message='User If must be less thant 7 characters')])
    password = PasswordField('New Password', [validators.DataRequired(), validators.EqualTo('confirm',
                                                                    message='Passwords must match')])
    confirm = PasswordField('Repeat Password')

class LoginForm(Form):
    email = StringField('Email', [validators.Email, validators.Length(max=320,
                                                                    message='Email must be less than 320 characters')])
    password = PasswordField('Password', [validators.DataRequired()])
