from wtforms import Form, StringField, validators, FileField, ValidationError, PasswordField, BooleanField
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
    firstname = StringField('Firstname', [validators.DataRequired(), validators.Length(max=25)],
                            render_kw={"placeholder": "First Name"})
    lastname = StringField('Lastname', [validators.DataRequired(), validators.Length(max=25)],
                           render_kw={"placeholder": "Last Name"})
    email = StringField('Email', [validators.DataRequired(),
                                  validators.Email(),
                                  validators.Length(max=320)],
                        render_kw={"placeholder": "Email Address"})
    uid = StringField('User Id', [validators.DataRequired(),
                                  validators.Length(max=7)],
                      render_kw={"placeholder": "User Id"})
    password = PasswordField('New Password',
                             [validators.DataRequired(),
                              validators.EqualTo('confirm', message='Passwords must match'),
                              validators.Length(min=7),
                              validators.Length(max=32)],
                             render_kw={"placeholder": "Password"})
    confirm = PasswordField('Repeat Password',
                            [validators.DataRequired(),
                             validators.Length(min=7),
                             validators.Length(max=32)],
                            render_kw={"placeholder": "Confirm Password"})

class LoginForm(Form):
    email = StringField('Email', [validators.Email(),
                                  validators.Length(max=320)],
                        render_kw={"placeholder": "Email Address"})
    password = PasswordField('Password', [validators.DataRequired()],
                             render_kw={"placeholder": "Password"})
    remember_me = BooleanField('Remember me')
