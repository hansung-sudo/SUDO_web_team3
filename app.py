from flask import Flask, render_template, request, redirect, url_for, abort, session
import os
import sqlite3
import uuid
from datetime import datetime

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = "sudo-board-secret-key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "sudo.db")


def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS visitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visitor_key TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            writer TEXT NOT NULL,
            content TEXT NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL,
            views INTEGER NOT NULL DEFAULT 0
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            writer TEXT NOT NULL,
            content TEXT NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (post_id) REFERENCES posts (id)
        )
    """)

    conn.commit()
    conn.close()


def get_current_visitor_name():
    if "visitor_key" not in session:
        session["visitor_key"] = str(uuid.uuid4())

    visitor_key = session["visitor_key"]

    conn = get_db_connection()

    visitor = conn.execute(
        "SELECT * FROM visitors WHERE visitor_key = ?",
        (visitor_key,)
    ).fetchone()

    if visitor:
        conn.close()
        return visitor["name"]

    count = conn.execute("SELECT COUNT(*) FROM visitors").fetchone()[0]
    new_name = f"방문자{count + 1}"

    conn.execute(
        """
        INSERT INTO visitors (visitor_key, name, created_at)
        VALUES (?, ?, ?)
        """,
        (
            visitor_key,
            new_name,
            datetime.now().strftime("%Y-%m-%d %H:%M")
        )
    )

    conn.commit()
    conn.close()

    return new_name


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


@app.route("/apply")
def apply():
    return render_template("apply.html")


@app.route("/board")
def board():
    get_current_visitor_name()

    conn = get_db_connection()
    posts = conn.execute(
        "SELECT * FROM posts ORDER BY id DESC"
    ).fetchall()
    conn.close()

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
            conn = get_db_connection()
            conn.execute(
                """
                INSERT INTO posts (title, writer, content, password, created_at, views)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    title,
                    visitor_name,
                    content,
                    password,
                    datetime.now().strftime("%Y-%m-%d %H:%M"),
                    0
                )
            )
            conn.commit()
            conn.close()

            return redirect(url_for("board"))

    return render_template("write_post.html", visitor_name=visitor_name)


@app.route("/board/<int:post_id>")
def post_detail(post_id):
    get_current_visitor_name()

    conn = get_db_connection()

    post = conn.execute(
        "SELECT * FROM posts WHERE id = ?",
        (post_id,)
    ).fetchone()

    if post is None:
        conn.close()
        abort(404)

    conn.execute(
        "UPDATE posts SET views = views + 1 WHERE id = ?",
        (post_id,)
    )
    conn.commit()

    post = conn.execute(
        "SELECT * FROM posts WHERE id = ?",
        (post_id,)
    ).fetchone()

    comments = conn.execute(
        "SELECT * FROM comments WHERE post_id = ? ORDER BY id ASC",
        (post_id,)
    ).fetchall()

    conn.close()

    return render_template("post_detail.html", post=post, comments=comments)


@app.route("/board/<int:post_id>/comment", methods=["POST"])
def add_comment(post_id):
    visitor_name = get_current_visitor_name()

    content = request.form.get("content")
    password = request.form.get("password")

    if not is_valid_password(password):
        return password_error()

    conn = get_db_connection()

    post = conn.execute(
        "SELECT * FROM posts WHERE id = ?",
        (post_id,)
    ).fetchone()

    if post is None:
        conn.close()
        abort(404)

    if content:
        conn.execute(
            """
            INSERT INTO comments (post_id, writer, content, password, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                post_id,
                visitor_name,
                content,
                password,
                datetime.now().strftime("%Y-%m-%d %H:%M")
            )
        )
        conn.commit()

    conn.close()

    return redirect(url_for("post_detail", post_id=post_id))


@app.route("/board/<int:post_id>/delete", methods=["POST"])
def delete_post(post_id):
    input_password = request.form.get("password")

    conn = get_db_connection()

    post = conn.execute(
        "SELECT * FROM posts WHERE id = ?",
        (post_id,)
    ).fetchone()

    if post is None:
        conn.close()
        abort(404)

    if post["password"] != input_password:
        conn.close()
        return wrong_password_error()

    conn.execute("DELETE FROM comments WHERE post_id = ?", (post_id,))
    conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("board"))


@app.route("/board/<int:post_id>/comment/<int:comment_id>/delete", methods=["POST"])
def delete_comment(post_id, comment_id):
    input_password = request.form.get("password")

    conn = get_db_connection()

    comment = conn.execute(
        """
        SELECT * FROM comments
        WHERE id = ? AND post_id = ?
        """,
        (comment_id, post_id)
    ).fetchone()

    if comment is None:
        conn.close()
        abort(404)

    if comment["password"] != input_password:
        conn.close()
        return wrong_password_error()

    conn.execute(
        "DELETE FROM comments WHERE id = ? AND post_id = ?",
        (comment_id, post_id)
    )
    conn.commit()
    conn.close()

    return redirect(url_for("post_detail", post_id=post_id))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
