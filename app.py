from flask import Flask, render_template, request, redirect, url_for, abort
import os
import json
from datetime import datetime

app = Flask(__name__, static_folder="static", template_folder="templates")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POSTS_FILE = os.path.join(BASE_DIR, "posts.txt")
COMMENTS_FILE = os.path.join(BASE_DIR, "comments.txt")


def ensure_file_exists(file_path):
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            pass


def load_json_lines(file_path):
    ensure_file_exists(file_path)

    data = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line:
                data.append(json.loads(line))

    return data


def save_json_lines(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def load_posts():
    return load_json_lines(POSTS_FILE)


def save_posts(posts):
    save_json_lines(POSTS_FILE, posts)


def load_comments():
    return load_json_lines(COMMENTS_FILE)


def save_comments(comments):
    save_json_lines(COMMENTS_FILE, comments)


def get_next_id(items):
    if items:
        return max(item["id"] for item in items) + 1
    return 1


def find_post(post_id):
    posts = load_posts()

    for post in posts:
        if post["id"] == post_id:
            return post

    return None


def get_comments_by_post_id(post_id):
    comments = load_comments()
    result = []

    for comment in comments:
        if comment["post_id"] == post_id:
            result.append(comment)

    return result


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/intro")
def intro():
    return render_template("intro.html")


@app.route("/board")
def board():
    posts = load_posts()
    posts.sort(key=lambda post: post["id"], reverse=True)

    return render_template("board.html", posts=posts)


@app.route("/board/write", methods=["GET", "POST"])
def write_post():
    if request.method == "POST":
        title = request.form.get("title")
        writer = request.form.get("writer")
        content = request.form.get("content")

        if title and writer and content:
            posts = load_posts()

            new_post = {
                "id": get_next_id(posts),
                "title": title,
                "writer": writer,
                "content": content,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "views": 0
            }

            posts.append(new_post)
            save_posts(posts)

            return redirect(url_for("board"))

    return render_template("write_post.html")


@app.route("/board/<int:post_id>")
def post_detail(post_id):
    posts = load_posts()

    post = None

    for p in posts:
        if p["id"] == post_id:
            post = p
            p["views"] = p.get("views", 0) + 1
            break

    if post is None:
        abort(404)

    save_posts(posts)

    comments = get_comments_by_post_id(post_id)

    return render_template("post_detail.html", post=post, comments=comments)


@app.route("/board/<int:post_id>/comment", methods=["POST"])
def add_comment(post_id):
    post = find_post(post_id)

    if post is None:
        abort(404)

    writer = request.form.get("writer")
    content = request.form.get("content")

    if writer and content:
        comments = load_comments()

        new_comment = {
            "id": get_next_id(comments),
            "post_id": post_id,
            "writer": writer,
            "content": content,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

        comments.append(new_comment)
        save_comments(comments)

    return redirect(url_for("post_detail", post_id=post_id))


@app.route("/apply")
def apply():
    return render_template("apply.html")


if __name__ == "__main__":
    app.run(debug=True)