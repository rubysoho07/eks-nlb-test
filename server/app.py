from random import randint

from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello_world():
    return f"Hello!! {randint(1, 100)}"