from flask import Flask, render_template, request, redirect, url_for, abort, session
import os
import json
import uuid
from datetime import datetime

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = "sudo-board-secret-key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POSTS_FILE = os.path.join(BASE_DIR, "posts.txt")
COMMENTS_FILE = os.path.join(BASE_DIR, "comments.txt")
VISITORS_FILE = os.path.join(BASE_DIR, "visitors.txt")


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
    posts = load_json_lines(POSTS_FILE)

    for post in posts:
        if "writer" not in post:
            post["writer"] = "방문자?"
        if "views" not in post:
            post["views"] = 0
        if "created_at" not in post:
            post["created_at"] = ""
        if "password" not in post:
            post["password"] = ""

    return posts


def save_posts(posts):
    save_json_lines(POSTS_FILE, posts)


def load_comments():
    comments = load_json_lines(COMMENTS_FILE)

    for comment in comments:
        if "writer" not in comment:
            comment["writer"] = "방문자?"
        if "created_at" not in comment:
            comment["created_at"] = ""
        if "password" not in comment:
            comment["password"] = ""

    return comments


def save_comments(comments):
    save_json_lines(COMMENTS_FILE, comments)


def load_visitors():
    return load_json_lines(VISITORS_FILE)


def save_visitors(visitors):
    save_json_lines(VISITORS_FILE, visitors)


def get_next_id(items):
    if items:
        return max(item["id"] for item in items) + 1
    return 1


def get_current_visitor_name():
    if "visitor_key" not in session:
        session["visitor_key"] = str(uuid.uuid4())

    visitor_key = session["visitor_key"]
    visitors = load_visitors()

    for visitor in visitors:
        if visitor["visitor_key"] == visitor_key:
            return visitor["name"]

    new_name = f"방문자{len(visitors) + 1}"

    visitors.append({
        "id": len(visitors) + 1,
        "visitor_key": visitor_key,
        "name": new_name,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

    save_visitors(visitors)

    return new_name


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


def is_valid_password(password):
    return password and password.isdigit() and len(password) == 4


def password_error():
    return """
    <script>
      alert('비밀번호는 숫자 4자리로 입력해야 합니다.');
      history.back();
    </script>
    """


def wrong_password_error():
    return """
    <script>
      alert('비밀번호가 일치하지 않습니다.');
      history.back();
    </script>
    """


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/intro")
def intro():
    return render_template("intro.html")


@app.route("/board")
def board():
    get_current_visitor_name()

    posts = load_posts()
    posts.sort(key=lambda post: post["id"], reverse=True)

    return render_template("board.html", posts=posts)


@app.route("/board/write", methods=["GET", "POST"])
def write_post():
    visitor_name = get_current_visitor_name()

    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        password = request.form.get("password")

        if not is_valid_password(password):
            return password_error()

        if title and content:
            posts = load_posts()

            new_post = {
                "id": get_next_id(posts),
                "title": title,
                "writer": visitor_name,
                "content": content,
                "password": password,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "views": 0
            }

            posts.append(new_post)
            save_posts(posts)

            return redirect(url_for("board"))

    return render_template("write_post.html", visitor_name=visitor_name)


@app.route("/board/<int:post_id>")
def post_detail(post_id):
    get_current_visitor_name()

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
    visitor_name = get_current_visitor_name()

    post = find_post(post_id)

    if post is None:
        abort(404)

    content = request.form.get("content")
    password = request.form.get("password")

    if not is_valid_password(password):
        return password_error()

    if content:
        comments = load_comments()

        new_comment = {
            "id": get_next_id(comments),
            "post_id": post_id,
            "writer": visitor_name,
            "content": content,
            "password": password,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

        comments.append(new_comment)
        save_comments(comments)

    return redirect(url_for("post_detail", post_id=post_id))


@app.route("/board/<int:post_id>/delete", methods=["POST"])
def delete_post(post_id):
    input_password = request.form.get("password")

    posts = load_posts()
    comments = load_comments()

    target_post = None

    for post in posts:
        if post["id"] == post_id:
            target_post = post
            break

    if target_post is None:
        abort(404)

    if target_post.get("password") != input_password:
        return wrong_password_error()

    posts = [post for post in posts if post["id"] != post_id]
    comments = [comment for comment in comments if comment["post_id"] != post_id]

    save_posts(posts)
    save_comments(comments)

    return redirect(url_for("board"))


@app.route("/board/<int:post_id>/comment/<int:comment_id>/delete", methods=["POST"])
def delete_comment(post_id, comment_id):
    input_password = request.form.get("password")

    comments = load_comments()

    target_comment = None

    for comment in comments:
        if comment["id"] == comment_id and comment["post_id"] == post_id:
            target_comment = comment
            break

    if target_comment is None:
        abort(404)

    if target_comment.get("password") != input_password:
        return wrong_password_error()

    comments = [
        comment for comment in comments
        if not (comment["id"] == comment_id and comment["post_id"] == post_id)
    ]

    save_comments(comments)

    return redirect(url_for("post_detail", post_id=post_id))


@app.route("/apply")
def apply():
    return render_template("apply.html")


if __name__ == "__main__":
    app.run(debug=True)