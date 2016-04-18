from sqlalchemy.exc import SQLAlchemyError
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
db = SQLAlchemy(app)


class User(db.Model):

    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(255), nullable=False)
    lastname = db.Column(db.String(255), nullable=False)
    mail = db.Column(db.String(255))
    password = db.Column(db.String(255))
    uid = db.Column(db.String(7))
    function = db.Column(db.String(32))
    service = db.Column(db.String(32))
    admin = db.Column(db.Boolean)
    created_on = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    def __init__(self, firstname, lastname, mail, password, uid, function, service):
        self.firstname = firstname
        self.lastname = lastname
        self.mail = mail
        self.set_password(password)
        self.uid = uid
        self.function = function
        self.service = service
        self.admin = False

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def update_password(self, password):
        self.set_password(password)
        return session_commit()

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def is_admin(self):
        return self.admin

    def get_id(self):
        id = str(self.id)
        return id.encode('utf-8')

    def add(self, user):
        db.session.add(user)
        return session_commit()

    def update(self, data):
        for key, value in data.items():
            setattr(self, key, value)
        return session_commit()

    def delete(self, user):
        db.session.delete(user)
        return session_commit()


class Customer(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(255), nullable=False)
    lastname = db.Column(db.String(255), nullable=False)
    mail = db.Column(db.String(255))
    company = db.Column(db.String(255))
    landline = db.Column(db.String(255))
    function = db.Column(db.String(255))
    created_on = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    def __init__(self, firstname, lastname, mail, company, landline, function):
        self.firstname = firstname
        self.lastname = lastname
        self.mail = mail
        self.company = company
        self.landline = landline
        self.function = function

    def add(self, customer):
        db.session.add(customer)
        return session_commit()

    def update(self):
        return session_commit()


    def delete(self, customer):
        db.session.delete(customer)
        return session_commit()


project_users = db.Table('project_users',
                         db.Column('project_id', db.Integer, db.ForeignKey('project.id')),
                         db.Column('user_id', db.Integer, db.ForeignKey('user.id')))


class Project(db.Model):

    __tablename__ = 'project'
    id = db.Column(db.Integer, primary_key=True)
    client = db.Column(db.String(255), nullable=False)
    projectName = db.Column(db.String(255), nullable=False)
    subProjectName = db.Column(db.String(255), nullable=True)
    version = db.relationship('ProjectVersioning', backref='project', lazy='dynamic')
    public = db.Column(db.Boolean)
    created_on = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    userId = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('user', lazy='dynamic'))
    users = db.relationship('User', secondary=project_users,
                            primaryjoin=(project_users.c.project_id == id),
                            secondaryjoin=(project_users.c.user_id == User.id),
                            backref=db.backref('project_users', lazy='dynamic'),
                            lazy='dynamic')

    def __init__(self, client, projectName, subProjectName, public=None):
        self.client = client
        self.projectName = projectName
        self.subProjectName = subProjectName
        if public is None:
            self.public = False

    def add_user(self, user):
        if not self.is_user(user):
            self.users.append(user)
            session_commit()
            return True
        else:
            return False

    def delete_user(self, user):
        if self.is_user(user):
            self.users.remove(user)
            session_commit()
            return True
        else:
            return False

    def is_user(self, user):
        return self.users.filter(project_users.c.user_id == user.id).count() > 0

    def add(self, project):
        db.session.add(project)
        return session_commit()

    def update(self, project, columns):
        for column_name, value in columns.items():
            setattr(project, column_name, value)
        return session_commit()

    def delete(self, project):
        db.session.delete(self)
        return session_commit()


class ProjectVersioning(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.Integer, nullable=False)
    excelFile = db.Column(db.String(255))
    templateFile = db.Column(db.String(255))
    numberOfVarToFill = db.Column(db.Integer)
    numberOfVarFilled = db.Column(db.Integer)
    fillingRatio = db.Column(db.String(255))
    zipFile = db.Column(db.String(255))
    projectId = db.Column(db.Integer, db.ForeignKey('project.id'))
    userId = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_on = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    def __init__(self, version, excelFile, templateFile, numberOfVarToFill, numberOfVarFilled, fillingRatio, zipFile,
                 project, user):
        self.version = version
        self.excelFile = excelFile
        self.templateFile = templateFile
        self.numberOfVarToFill = numberOfVarToFill
        self.numberOfVarFilled = numberOfVarFilled
        self.fillingRatio = fillingRatio
        self.zipFile = zipFile
        self.project = project
        self.user = user

    def add(self, projectVersioning):
        db.session.add(projectVersioning)
        return session_commit()

    def update(self):
        return session_commit()

    def delete(self, projectVersioning):
        db.session.delete(projectVersioning)
        return session_commit()


db.create_all()
db.session.commit()


def last_project():
    return db.session.query(Project).order_by(Project.id.desc()).first()

def last_id_of_the_table_project():
    obj = db.session.query(Project).order_by(Project.id.desc()).first()
    return str(obj.id)

def last_version_of_the_project_id_equal_to(id):
    project = Project.query.get(id)
    list_all_versions_of_the_project = project.version.all()
    return list_all_versions_of_the_project[-1]

def session_commit():
    try:
        db.session.commit()
    except SQLAlchemyError as e:
        reason = str(e)