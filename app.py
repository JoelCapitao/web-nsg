import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
db = SQLAlchemy(app)

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/<name>')
def hello_name(name):
    return "Hello {}!".format(name)


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=9999)
