import os
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me-before-production")
url = os.environ.get("DATABASE_URL", "sqlite:///bookverse.db")
if url.startswith("postgres://"):
    url = url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    books = db.relationship("Book", backref="author", lazy=True, cascade="all, delete-orphan")

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=False)
    genre = db.Column(db.String(60), default="Fiction")
    cover_url = db.Column(db.String(500), default="")
    content = db.Column(db.Text, nullable=False)
    published_at = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

def user_now():
    return db.session.get(User, session.get("user_id")) if session.get("user_id") else None

def admin_check(user=None):
    user = user or user_now()
    admin_email = os.environ.get("ADMIN_EMAIL", "").strip().lower()
    return bool(user and admin_email and user.email.lower() == admin_email)

@app.context_processor
def globals_for_templates():
    return {"current_user": user_now(), "is_admin": admin_check,
            "site_manager": os.environ.get("SITE_MANAGER_NAME", "Lakshya Kansal"),
            "site_contact": os.environ.get("SITE_CONTACT_EMAIL", "")}

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not user_now():
            flash("Please sign in first.", "info")
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not user_now():
            return redirect(url_for("login", next=request.path))
        if not admin_check():
            abort(403)
        return fn(*args, **kwargs)
    return wrapper

@app.route("/")
def index():
    q, genre = request.args.get("q", "").strip(), request.args.get("genre", "").strip()
    query = Book.query
    if q:
        query = query.filter(db.or_(Book.title.ilike(f"%{q}%"), Book.description.ilike(f"%{q}%")))
    if genre:
        query = query.filter_by(genre=genre)
    books = query.order_by(Book.published_at.desc()).all()
    genres = [r[0] for r in db.session.query(Book.genre).distinct().order_by(Book.genre).all() if r[0]]
    return render_template("index.html", books=books, q=q, genre=genre, genres=genres)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if len(username) < 3:
            flash("Username must be at least 3 characters.", "error")
        elif "@" not in email:
            flash("Enter a valid email.", "error")
        elif len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
        elif User.query.filter(db.or_(User.username == username, User.email == email)).first():
            flash("Username or email is already registered.", "error")
        else:
            user = User(username=username, email=email, password_hash=generate_password_hash(password))
            db.session.add(user); db.session.commit()
            session["user_id"] = user.id
            flash("Account created. Welcome to BookVerse!", "success")
            return redirect(url_for("admin_dashboard") if admin_check(user) else url_for("index"))
    return render_template("auth.html", mode="register")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identity = request.form.get("identity", "").strip()
        user = User.query.filter(db.or_(User.username == identity, User.email == identity.lower())).first()
        if user and check_password_hash(user.password_hash, request.form.get("password", "")):
            session["user_id"] = user.id
            return redirect(url_for("admin_dashboard") if admin_check(user) else (request.args.get("next") or url_for("index")))
        flash("Incorrect username/email or password.", "error")
    return render_template("auth.html", mode="login")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/publish", methods=["GET", "POST"])
@login_required
def publish():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        content = request.form.get("content", "").strip()
        cover = request.form.get("cover_url", "").strip()
        genre = request.form.get("genre", "Fiction").strip() or "Fiction"
        if not title or not description or not content:
            flash("Title, description, and book text are required.", "error")
        elif cover and not cover.startswith(("https://", "http://")):
            flash("Cover URL must start with http:// or https://.", "error")
        else:
            book = Book(title=title, description=description, content=content, cover_url=cover,
                        genre=genre, author_id=user_now().id)
            db.session.add(book); db.session.commit()
            return redirect(url_for("book_detail", book_id=book.id))
    return render_template("publish.html", book=None, editing=False)

@app.route("/book/<int:book_id>")
def book_detail(book_id):
    book = db.session.get(Book, book_id)
    if not book: abort(404)
    return render_template("book.html", book=book)

@app.route("/book/<int:book_id>/edit", methods=["GET", "POST"])
@login_required
def edit_book(book_id):
    book = db.session.get(Book, book_id)
    if not book: abort(404)
    if book.author_id != user_now().id and not admin_check(): abort(403)
    if request.method == "POST":
        book.title = request.form.get("title", "").strip()
        book.description = request.form.get("description", "").strip()
        book.content = request.form.get("content", "").strip()
        book.genre = request.form.get("genre", "Fiction").strip() or "Fiction"
        book.cover_url = request.form.get("cover_url", "").strip()
        if not book.title or not book.description or not book.content:
            flash("Title, description, and book text are required.", "error")
        else:
            db.session.commit()
            flash("Book updated.", "success")
            return redirect(url_for("book_detail", book_id=book.id))
    return render_template("publish.html", book=book, editing=True)

@app.route("/book/<int:book_id>/delete", methods=["POST"])
@login_required
def delete_book(book_id):
    book = db.session.get(Book, book_id)
    if not book: abort(404)
    if book.author_id != user_now().id and not admin_check(): abort(403)
    db.session.delete(book); db.session.commit()
    flash("Book deleted.", "info")
    return redirect(url_for("admin_dashboard") if admin_check() else url_for("my_books"))

@app.route("/my-books")
@login_required
def my_books():
    books = Book.query.filter_by(author_id=user_now().id).order_by(Book.published_at.desc()).all()
    return render_template("my_books.html", books=books)

@app.route("/admin")
@admin_required
def admin_dashboard():
    return render_template("admin.html",
        users=User.query.order_by(User.joined_at.desc()).all(),
        books=Book.query.order_by(Book.published_at.desc()).all(),
        user_count=User.query.count(), book_count=Book.query.count())

@app.route("/admin/user/<int:user_id>/delete", methods=["POST"])
@admin_required
def admin_delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user: abort(404)
    if user.id == user_now().id:
        flash("You cannot delete the administrator account you are currently using.", "error")
    else:
        db.session.delete(user); db.session.commit()
        flash("User and their books were deleted.", "info")
    return redirect(url_for("admin_dashboard"))

@app.errorhandler(403)
def forbidden(error):
    return render_template("message.html", title="Access denied", message="You do not have permission to access this page."), 403

@app.errorhandler(404)
def not_found(error):
    return render_template("message.html", title="Page not found", message="We couldn't find that page."), 404

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
