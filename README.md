# BookVerse — Read & Publish Books

A community publishing platform built with Flask, SQLAlchemy, and PostgreSQL.

## Live deployment

**Live website:** [BookVerse — Read & Publish Books](https://bookverse-read-publish-books.onrender.com)

Visit the deployed website to browse books, create an account, and publish or read stories.

## Features
- User registration and sign-in with hashed passwords
- Browse, search, and filter books
- Publish and read books online
- Authors can edit/delete their own books
- Admin dashboard for site statistics, book management, and user management
- Project manager and contact information in the footer and admin panel
- PostgreSQL on Render and SQLite for local development

## Run locally
```bash
pip install -r requirements.txt
```
Set environment variables before running. On macOS/Linux:
```bash
export SECRET_KEY="use-a-long-random-secret"
export ADMIN_EMAIL="your-admin-email@example.com"
export SITE_MANAGER_NAME="Lakshya Kansal"
export SITE_CONTACT_EMAIL="optional-contact@example.com"
python app.py
```
On Windows PowerShell use `$env:ADMIN_EMAIL="your-admin-email@example.com"` etc. Open http://127.0.0.1:5000. Register using the exact email configured as `ADMIN_EMAIL` to receive administrator access.

## Deploy/update on Render
1. Push all project files to your GitHub repository.
2. In Render, connect the repository using a Blueprint, or update your existing web service.
3. Set `ADMIN_EMAIL` to the email address you will use for the administrator account. Set `SITE_MANAGER_NAME` and optional `SITE_CONTACT_EMAIL`.
4. Keep `SECRET_KEY` private and keep `DATABASE_URL` connected to the Render PostgreSQL database.
5. Deploy the latest commit. Sign in with the configured admin email and visit `/admin`.

Build command: `pip install -r requirements.txt`  
Start command: `gunicorn app:app`

## Admin dashboard
- URL: `/admin`
- Admin access is granted when the signed-in user's email matches the `ADMIN_EMAIL` environment variable.
- The dashboard lists users and books and provides actions to delete books and other user accounts.
- If you already registered, set `ADMIN_EMAIL` to that account's email. Otherwise, set the variable first and then register with that email.
- Never share your password or `SECRET_KEY`.

## Project information
- **Project:** BookVerse — Read & Publish Books
- **Project manager:** `SITE_MANAGER_NAME` (default: Lakshya Kansal)
- **Contact:** optional `SITE_CONTACT_EMAIL`
- **Deployment:** Render
- **Backend:** Flask / Python
- **Database:** PostgreSQL on Render, SQLite locally

## Before public launch
This is an MVP starter. Before broad public use, add CSRF protection, rate limiting, email verification, password recovery, moderation/reporting, backups, and a copyright takedown process. Publish only content you own or have permission to share.



<div align="center">

Developed by Lakshya Kansal

</div>
