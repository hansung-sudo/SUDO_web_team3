from flask import Flask, render_template
import os

app = Flask(__name__, static_folder='static', template_folder='templates')

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/intro")
def intro():
    return render_template("intro.html")

@app.route("/board")
def board():
    return render_template("board.html")

@app.route("/apply")
def apply():
    return render_template("apply.html")

if __name__ == "__main__":
    app.run(debug=True)


