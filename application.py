import os

from flask import Flask, session, redirect, request, url_for, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import render_template
from functools import wraps
# from werkzeug.exceptions import default_exceptions
# from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__, template_folder="templates")
# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")
app.config["SECRET_KEY"] = 'ihgipeghephg'

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        rows = db.execute("SELECT * FROM users WHERE email=:email",
                          {"email": email}).fetchone()
        for len in rows:
            break
        if password in rows[3]:
            session["logged_in"] = True
            session["users"] = rows
            return redirect(url_for("search"))
        else:
            flash("email or password is incorrect", "danger")
            return render_template("/login.html")
    return render_template("/login.html")


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("You need to login first")
            return redirect(url_for('login'))

    return wrap


@app.route("/search", methods=["POST", "GET"])
@login_required
def search():
    session["users"].id
    if request.method == "POST":
        search = "%" + request.form.get("q") + "%"
        books = db.execute("SELECT * FROM book WHERE author LIKE :search OR title LIKE :search OR isbn LIKE :search",
                           {"search": search}).fetchall()
        if books:
            return render_template("search.html", books=books)
        else:
            flash("Not Found", "danger")
            return render_template("search.html")
    else:
        return render_template("/search.html")


@app.route("/review/<isbn>", methods=["POST", "GET"])
def review(isbn):
    userid = session["users"].id
    data = db.execute("SELECT * FROM book WHERE isbn=:isbn ",
                      {"isbn": isbn}).fetchall()
    rating = db.execute("SELECT * FROM review join book ON review.bid = book.id join users On review.uid = users.id WHERE isbn =:isbn ",
                        {"isbn": isbn}).fetchall()
    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": "LZdw0fSUvZVtB5Gprc6DQ", "isbns": isbn})
    bookinfo = res.json()
    avr = bookinfo['books'][0]['average_rating']
    rvr = bookinfo['books'][0]['work_ratings_count']
    if request.method == "GET":
        return render_template("review.html",
                               data=data, rating=rating, avr=avr, rvr=rvr)
    else:
        check = db.execute("SELECT * FROM review join book ON review.bid = book.id join users On review.uid = users.id WHERE(isbn =:isbn And uid =:userid)",
                           {"isbn": isbn, "userid": userid}).fetchall()
        if check:
            flash("comment already submited for this book", "danger")
            return render_template("review.html",
                                   data=data, rating=rating, avr=avr, rvr=rvr)
        else:
            bid = data[0][0]
            commenttxt = request.form.get("commenttxt")
            starnum = request.form.get("rate")
            db.execute("INSERT INTO review(rate, comment, bid, uid)VALUES(:starnum, :commenttxt, :bid, :userid)",
                       {"commenttxt": commenttxt, "starnum": starnum, "bid": bid, "userid": userid})
            db.commit()
            flash("commented successfully", "success")
            return render_template("review.html",
                                   data=data, rating=rating, avr=avr, rvr=rvr)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm = request.form.get("confirm")
        # hash=generate_password_hash(str(password))

        emaildata = db.execute("SELECT email FROM users WHERE email=:email",
                               {"email": email}).fetchone()
        if emaildata is None:
            if password == confirm:
                db.execute("INSERT INTO users(name, email, password)VALUES(:name, :email, :password)",
                           {"name": name, "email": email, "password": password})
                db.commit()
                flash("your are registered!", "success")
                return redirect(url_for("login"))
            else:
                flash("password does not match", "danger")
                return render_template("/register.html")
        else:
            flash("Email already existed", "danger")
            return redirect(url_for('register'))

    return render_template("/register.html")


@app.route("/logout")
def logout():
    session.pop("users", None)
    return redirect(url_for("login"))


@app.route("/api/<isbn>")
def api(isbn):
    countrev = db.execute("SELECT COUNT(comment) FROM review JOIN book ON review.bid = book.id WHERE isbn = :isbn ", {"isbn": isbn}).fetchone()

    avgrate = db.execute("SELECT AVG (rate) FROM review JOIN book ON review.bid = book.id WHERE isbn = :isbn ", {"isbn": isbn}).fetchone()

    forview = db.execute("SELECT * FROM book WHERE isbn like :isbn", {"isbn": isbn}).fetchone()

    return render_template("response.html", avgrate=avgrate, countrev=countrev, forview=forview)
