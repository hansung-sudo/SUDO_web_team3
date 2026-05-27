from flask import Flask, render_template, request, redirect, url_for
import json
from flask import Flask, render_template
import os

app = Flask(__name__, static_folder='static', template_folder='templates')

POSTS_FILE = "posts.txt"
COMMENTS_FILE = "comments.txt"


def ensure_file_exists(filename):
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            pass


def load_posts():
    ensure_file_exists(POSTS_FILE)

    posts = []

    with open(POSTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line:
                posts.append(json.loads(line))

    return posts


def save_post(title, content):
    posts = load_posts()

    if posts:
        new_id = max(post["id"] for post in posts) + 1
    else:
        new_id = 1

    post = {
        "id": new_id,
        "title": title,
        "content": content
    }

    with open(POSTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(post, ensure_ascii=False) + "\n")


def find_post(post_id):
    posts = load_posts()

    for post in posts:
        if post["id"] == post_id:
            return post

    return None


def load_comments():
    ensure_file_exists(COMMENTS_FILE)

    comments = []

    with open(COMMENTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line:
                comments.append(json.loads(line))

    return comments


def save_comment(post_id, content):
    comments = load_comments()

    if comments:
        new_id = max(comment["id"] for comment in comments) + 1
    else:
        new_id = 1

    comment = {
        "id": new_id,
        "post_id": post_id,
        "content": content
    }

    with open(COMMENTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(comment, ensure_ascii=False) + "\n")


def get_comments_by_post_id(post_id):
    comments = load_comments()

    result = []

    for comment in comments:
        if comment["post_id"] == post_id:
            result.append(comment)

    return result


@app.route("/")
def home():
    return redirect(url_for("board"))


@app.route("/board", methods=["GET", "POST"])
def board():
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")

        if title and content:
            save_post(title, content)

        return redirect(url_for("board"))

    posts = load_posts()
    posts.reverse()

    return render_template("board.html", posts=posts)


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def post_detail(post_id):
    post = find_post(post_id)

    if post is None:
        return "게시글을 찾을 수 없습니다."

    if request.method == "POST":
        comment_content = request.form.get("comment")

        if comment_content:
            save_comment(post_id, comment_content)

        return redirect(url_for("post_detail", post_id=post_id))

    comments = get_comments_by_post_id(post_id)

    return render_template("post_detail.html", post=post, comments=comments)


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
<<<<<<< HEAD
    app.run(debug=True)
=======
    app.run(debug=True)
##alsrms002 first commit
>>>>>>> dc827d2 (first commit)
