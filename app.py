import os
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-key-before-deploying")
database_url = os.environ.get("DATABASE_URL", "sqlite:///bookverse.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    books = db.relationship("Book", backref="author", lazy=True)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=False)
    genre = db.Column(db.String(60), default="Other")
    cover_url = db.Column(db.String(500), default="")
    content = db.Column(db.Text, nullable=False)
    published_at = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

def current_user():
    uid = session.get("user_id")
    return db.session.get(User, uid) if uid else None

@app.context_processor
def inject_user():
    return {"current_user": current_user()}

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("Please sign in to continue.", "info")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped

@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    genre = request.args.get("genre", "").strip()
    query = Book.query
    if q:
        query = query.filter(db.or_(Book.title.ilike(f"%{q}%"), Book.description.ilike(f"%{q}%")))
    if genre:
        query = query.filter_by(genre=genre)
    books = query.order_by(Book.published_at.desc()).all()
    genres = [g[0] for g in db.session.query(Book.genre).distinct().order_by(Book.genre).all() if g[0]]
    return render_template("index.html", books=books, q=q, genre=genre, genres=genres)

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user():
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if len(username) < 3 or len(username) > 40:
            flash("Username must be between 3 and 40 characters.", "error")
        elif "@" not in email or len(email) > 120:
            flash("Enter a valid email address.", "error")
        elif len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
        elif User.query.filter(db.or_(User.username == username, User.email == email)).first():
            flash("That username or email is already registered.", "error")
        else:
            user = User(username=username, email=email, password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            session["user_id"] = user.id
            flash("Welcome to BookVerse! Your account is ready.", "success")
            return redirect(url_for("index"))
    return render_template("auth.html", mode="register")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user():
        return redirect(url_for("index"))
    if request.method == "POST":
        identity = request.form.get("identity", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter(db.or_(User.username == identity, User.email == identity.lower())).first()
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            flash("You are now signed in.", "success")
            return redirect(request.args.get("next") or url_for("index"))
        flash("Invalid username/email or password.", "error")
    return render_template("auth.html", mode="login")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have signed out.", "info")
    return redirect(url_for("index"))

@app.route("/publish", methods=["GET", "POST"])
@login_required
def publish():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        genre = request.form.get("genre", "Other").strip()
        cover_url = request.form.get("cover_url", "").strip()
        content = request.form.get("content", "").strip()
        if not title or not description or not content:
            flash("Title, description, and book text are required.", "error")
        elif len(title) > 160 or len(description) > 3000:
            flash("Please shorten the title or description.", "error")
        elif cover_url and not cover_url.startswith(("https://", "http://")):
            flash("Cover image must be a valid http:// or https:// URL.", "error")
        else:
            book = Book(title=title, description=description, genre=genre or "Other",
                        cover_url=cover_url, content=content, author_id=current_user().id)
            db.session.add(book)
            db.session.commit()
            flash("Your book is now published!", "success")
            return redirect(url_for("book_detail", book_id=book.id))
    return render_template("publish.html")

@app.route("/book/<int:book_id>")
def book_detail(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        abort(404)
    return render_template("book.html", book=book)

@app.route("/book/<int:book_id>/edit", methods=["GET", "POST"])
@login_required
def edit_book(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        abort(404)
    if book.author_id != current_user().id:
        abort(403)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        content = request.form.get("content", "").strip()
        genre = request.form.get("genre", "Other").strip()
        cover_url = request.form.get("cover_url", "").strip()
        if not title or not description or not content:
            flash("Title, description, and book text are required.", "error")
        else:
            book.title, book.description, book.content = title, description, content
            book.genre, book.cover_url = genre or "Other", cover_url
            db.session.commit()
            flash("Book updated.", "success")
            return redirect(url_for("book_detail", book_id=book.id))
    return render_template("publish.html", book=book, editing=True)

@app.route("/book/<int:book_id>/delete", methods=["POST"])
@login_required
def delete_book(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        abort(404)
    if book.author_id != current_user().id:
        abort(403)
    db.session.delete(book)
    db.session.commit()
    flash("Book deleted.", "info")
    return redirect(url_for("my_books"))

@app.route("/my-books")
@login_required
def my_books():
    books = Book.query.filter_by(author_id=current_user().id).order_by(Book.published_at.desc()).all()
    return render_template("my_books.html", books=books)

@app.errorhandler(403)
def forbidden(error):
    return render_template("message.html", title="Access denied", message="You do not have permission to do that."), 403

@app.errorhandler(404)
def not_found(error):
    return render_template("message.html", title="Page not found", message="We couldn't find that page."), 404

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
