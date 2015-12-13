from sqlalchemy.exc import SQLAlchemyError
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
db = SQLAlchemy(app)


class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(255), nullable=False)
    lastname = db.Column(db.String(255), nullable=False)
    mail = db.Column(db.String(255))
    password = db.Column(db.String(255))
    uid = db.Column(db.String(7))
    created_on = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    def __init__(self, firstname, lastname, mail, password, uid):
        self.firstname = firstname
        self.lastname = lastname
        self.mail = mail
        self.password = password
        self.uid = uid

    def add(self, user):
        db.session.add(user)
        return session_commit()

    def update(self):
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


class Project(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    client = db.Column(db.String(255), nullable=False)
    projectName = db.Column(db.String(255), nullable=False)
    subProjectName = db.Column(db.String(255), nullable=True)
    excelFile = db.Column(db.String(255))
    templateFile = db.Column(db.String(255))
    created_on = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())


    def __init__(self, client, projectName, subProjectName, excelFile, templateFile):
        self.client = client
        self.projectName = projectName
        self.subProjectName = subProjectName
        self.excelFile = excelFile
        self.templateFile = templateFile

    def add(self, project):
        db.session.add(project)
        return session_commit()

    def update(self):
        return session_commit()

    def delete(self, project):
        db.session.delete(project)
        return session_commit()



db.create_all()
db.session.commit()

def lastIDofProject():
    return db.session.query(Project).order_by(Project.id.desc()).first()


def session_commit():
    try:
        db.session.commit()
    except SQLAlchemyError as e:
        reason = str(e)