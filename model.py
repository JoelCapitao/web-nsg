from app import db
from sqlalchemy.exc import SQLAlchemyError


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, db.Integer, primary_key=True)
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
    __tablename__ = 'customer'

    id = db.Column(db.Integer, db.Integer, primary_key=True)
    firstname = db.Column(db.String(255), nullable=False)
    lastname = db.Column(db.String(255), nullable=False)
    mail = db.Column(db.String(255))
    company = db.Column(db.String(255))
    created_on = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    def __init__(self, firstname, lastname, mail, company):
        self.firstname = firstname
        self.lastname = lastname
        self.mail = mail
        self.company = company

    def add(self, customer):
        db.session.add(customer)
        return session_commit()

    def update(self):
        return session_commit()

    def delete(self, customer):
        db.session.delete(customer)
        return session_commit()


class Project(db.Model):
    __tablename__ = 'project'

    id = db.Column(db.Integer, db.Integer, primary_key=True)
    projectName = db.Column(db.String(255), nullable=False)
    projectReferenceId = db.Column(db.String(255), nullable=False)
    excelFile = db.Column(db.String(255))
    templateFile = db.Column(db.String(255))
    scripts = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    created_on = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    user = db.relationship('User', foreign_keys=[user_id])
    customer = db.relationship('Customer', foreign_keys=[customer_id])

    def __init__(self, projectName, projectReferenceId, excelFile, templateFile):
        self.projectName = projectName
        self.projectReferenceId = projectReferenceId
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


def session_commit():
    try:
        db.session.commit()
    except SQLAlchemyError as e:
        reason = str(e)