# BookVerse — Read & Publish Books

A small community publishing website built with Flask, SQLAlchemy, and PostgreSQL. Readers can browse/search books and read full text. Registered authors can publish, edit, and delete their own books.

## Features
- Register and sign in (passwords are hashed)
- Browse books and search by title/description
- Filter by genre
- Publish a book with title, description, genre, optional cover image URL, and full text
- Read published books
- Manage your own books (edit/delete)
- PostgreSQL for Render, SQLite fallback for local development
- Responsive UI

## Run locally
1. Install Python 3.10+.
2. Create and activate a virtual environment.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run:
   ```bash
   python app.py
   ```
5. Open http://127.0.0.1:5000

By default, local data is saved in `bookverse.db`.

## Deploy on Render
### Easiest method
1. Create a GitHub repository and upload all files in this folder.
2. In Render, choose **New + → Blueprint** and connect that repository.
3. Render reads `render.yaml` and creates the web service and PostgreSQL database.
4. Wait for the deploy to finish and open the generated URL.

If you create the web service manually, use:
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Add `SECRET_KEY` as a long random secret
- Add `DATABASE_URL` using a Render PostgreSQL connection string

## Notes before public launch
This is an MVP starter, not a fully moderated commercial publishing platform. Add email verification, password reset, rate limiting/CSRF protection, content reporting/moderation, backups, and a clear copyright/takedown process before opening it to a large public audience. Authors should only upload content they own or have permission to publish. Cover images are entered as URLs; the app does not upload image files.

## Live deployment

**Live website:** [BookVerse — Read & Publish Books](https://bookverse-read-publish-books.onrender.com)

Visit the deployed website to browse books, create an account, and publish or read stories.
