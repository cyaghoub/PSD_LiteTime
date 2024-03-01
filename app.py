from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def hello():
    return '<h1>Hello, World!</h1>'

def index():
    return render_template('index.html')


