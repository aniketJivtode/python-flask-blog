from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from datetime import datetime
import json
import math
import pymysql

pymysql.install_as_MySQLdb()
'''Loading config file'''
with open("config.json", "r") as f:
    params = json.load(f)['params']

app = Flask(__name__)
app.secret_key = 'defamed76f7al7ia8da8944hh34h3'

'''Email Configurations'''
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['mail-user'],
    MAIL_PASSWORD=params['mail-password']
)

'''Initialize mail service'''
mail = Mail(app)

'''Param taken form config.json'''
if params['local_server']:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

'''Initialize Mysql Database'''
db = SQLAlchemy(app)

'''Models'''


class Contacts(db.Model):
    # ID, name, email, phone_num, message, date
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    phone_num = db.Column(db.String(12), unique=True, nullable=False)
    message = db.Column(db.String(120), unique=True, nullable=False)
    date = db.Column(db.String(12), unique=True, nullable=False)


class Posts(db.Model):
    # ID, name, email, phone_num, message, date
    id = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(80), unique=True, nullable=False)
    Description = db.Column(db.String(50), unique=False, nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    Date = db.Column(db.String(12), unique=False, nullable=False)
    AddedBy = db.Column(db.String(12), unique=False, nullable=False)


'''Routes'''


@app.route('/')
def home():
    post = Posts.query.filter_by().all()
    last = math.ceil(len(post) / params['no_of_posts'])
    page = request.args.get('page')
    if not str(page).isnumeric():
        page = 1
    page = int(page)
    posts = post[(page - 1) * int(params['no_of_posts']):(page-1) * int(params['no_of_posts']) + int(params['no_of_posts'])]

    if page == 1:
        prev = "#"
        nextpage = "/?page=" + str(page + 1)
    elif page == last:
        prev = "/?page=" + str(page - 1)
        nextpage = "#"
    else:
        prev = "/?page=" + str(page - 1)
        nextpage = "/?page=" + str(page + 1)
    return render_template('index.html', params=params, posts=posts, prev=prev, next=nextpage)


@app.route('/about')
def about():
    return render_template('about.html', params=params)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        '''Add contact to database'''
        name = request.form.get('name')
        message = request.form.get('message')
        phone_num = request.form.get('phone_num')
        email = request.form.get('email')
        contactObj = Contacts(name=name, message=message, date=datetime.now(), phone_num=phone_num, email=email)
        db.session.add(contactObj)
        db.session.commit()
        mail.send_message('New message from ' + name,
                          sender=email,
                          recipients=[params['mail-user']],
                          body=message + "\n\n\n" + "Contact No: " + phone_num + "\n" + "Email: " + email)
    return render_template('contact.html', params=params)


@app.route('/post/<string:post_slug>', methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard_route():
    if 'user' in session and session['user'] == params['admin-user']:
        post = Posts.query.filter_by().all()
        return render_template('dashboard.html', params=params, posts=post)

    if request.method == 'POST':
        uname = request.form.get('uname')
        password = request.form.get('pass')
        if uname == params['admin-user'] and password == params['admin-password']:
            session['user'] = params['admin-user']
            post = Posts.query.filter_by().all()
            return render_template('dashboard.html', params=params, posts=post)

        else:
            return render_template('login.html', params=params)
    else:
        return render_template('login.html', params=params)


@app.route('/edit/<string:postID>', methods=['GET', 'POST'])
def edit_post_page(postID):
    if 'user' in session and session['user'] == params['admin-user']:
        if request.method == 'POST':
            req_title = request.form.get('title')
            req_description = request.form.get('description')
            req_slug = request.form.get('slug')
            req_addedby = request.form.get('addedBy')
            date = datetime.now()
            if postID == '0':
                post = Posts(Title=req_title, Description=req_description, Date=date, slug=req_slug,
                             AddedBy=req_addedby)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(id=postID).first()
                post.Title = req_title
                post.Description = req_description
                post.Date = date
                post.slug = req_slug
                post.AddedBy = req_addedby
                db.session.add(post)
                db.session.commit()
                return redirect('/dashboard')

        post = Posts.query.filter_by(id=postID).first()
        return render_template('edit.html', params=params, post=post)


@app.route('/delete/<string:postID>', methods=['GET'])
def delete(postID):
    if 'user' in session and session['user'] == params['admin-user']:
        post = Posts.query.filter_by(id=postID).first()
        db.session.delete(post)
        db.session.commit()
        return redirect('/dashboard')


@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user')
    return redirect('/dashboard')


app.run(debug=True)
