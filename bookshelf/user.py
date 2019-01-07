# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from bookshelf import get_model, cryptography
from flask import Blueprint, redirect, render_template, request, url_for, flash, session
from wtforms import Form, TextField, PasswordField, validators, StringField, SubmitField
import os
from bson.objectid import ObjectId

user = Blueprint('user', __name__)

# Variable to check logged user
user_info = {'log': False, 'id': None}

## Classes for the forms
class LoginForm(Form):
    email = TextField('Email:', validators=[validators.required()])
    password = PasswordField('Password:', validators=[validators.required()])

class RegisterForm(Form):
    name = TextField('Name:', validators=[validators.required()])
    email = TextField('Email:', validators=[validators.required()])
    pass1 = PasswordField('Password:', validators=[validators.required()])
    pass2 = PasswordField('Repass:', validators=[validators.required()])

class SearchForm(Form):
    chain = TextField('Chain:', validators=[validators.required()])

## [BEGIN]
# Users log logic

#Function called before accessing any protected function
@user.before_request
def before_request():
    global user_info

    if 'user' in session:
        user_info = session['user']
        print(user_info)
        print("Before!")

@user.route('/login', methods=['GET','POST'])
def login():
    global user_info
    print(user_info['id'])

    if user_info['id'] is not None:
        return redirect(url_for('crud.list'))

    form = LoginForm(request.form)
 
    if request.method == 'POST':
        if form.validate():
            # Log valid
            result = get_model().find_user_email(request.form['email'])
            print(result)
            if result is None:
                flash("Email is not valid.")
            
            elif not cryptography.check_pass(request.form['password'], result['password']):
                flash("Password is incorrect")
            
            else:
                session['user'] = {'log': True, 'id': result['id']}
                user_info = session['user']
                print(session)
                print(session['user'])
                return redirect(url_for('crud.list'))

        else:
            flash('All the form fields are required. ')
    
    return render_template('login.html', form=form, user_info=user_info)

# Logout function
@user.route('/logout')
def logout():
    global user_info
    user_info = {'log': False, 'id': None}
    session.pop('user', None)
    return redirect(url_for('crud.list'))

# Register function
@user.route('/signup', methods=['GET','POST'])
def signup():

    global user_info
    if user_info['id'] is not None:
        return redirect(url_for('crud.list'))

    form = RegisterForm(request.form)
 
    if request.method == 'POST':
        if form.validate():
            #Checks if the email is already in use
            result = get_model().find_user_email(request.form['email'])
            print(result)
            if result is not None:
                flash('Email is already registered.')
            else:
                # Register successfully
                # We add the user to the database
                data = {}
                data['name'] = request.form['name']
                data['email'] = request.form['email']
                data['balance'] = 0
                data['password'] = cryptography.encrypt_pass(request.form['pass1'])
                result = get_model().create_user(data)
                print(result)
                return redirect(url_for('user.login'))
        else:
            flash('All the form fields are required.')

    return render_template('signup.html', form=form, user_info=user_info)


## [END Users Log Logic]
@user.route('/<id>')
def view_user(id):
    global user_info
    user = get_model().read_user(id)

    #If the user is not logged, redirect to main page
    if user_info['id'] is None:
        return redirect(url_for('crud.list'))

    #If the user is trying to access the profile of another user, redirect to main page
    print(user['id'])
    print(user_info['id'])
    if user_info['id'] != user['id']:
        return redirect(url_for('crud.list'))

    list = request.args.get('list')
    list = int(list) if list is not None else 0
    
    books_with_covers = []
    next_page_token = None
    sales = []
    
    if list > 0 and list < 4:
        token = request.args.get('page_token', None)
        if token:
            token = token.encode('utf-8')
    
        books, next_page_token = get_model().list_comic(cursor=token, list=list, user_id=id)
        books_with_covers = []
        
        for book in books:
            cover = get_model().get_cover(book['id'])
            book = tuple((book, cover))
            books_with_covers.append(book)
    elif list == 4:
        payments = get_model().list_sold_comics(id)
        sales = []
        for payment in payments:
            buyer = get_model().read_user(payment['buyer_id'])
            comic = get_model().read_comic(payment['comic_id'])
            sale = {
                'price': payment['price'],
                'date': payment['date'],
                'title': comic['title'],
                'buyer': buyer['name']
                }
            sales.append(sale)
    
    return render_template("user.html",
        user=user,
        list=list,
        books=books_with_covers,
        next_page_token=next_page_token,
        sales=sales,
        user_info=user_info)


@user.route('/<id>/edit', methods=['GET', 'POST'])
def edit_user(id):
    global user_info
    user = get_model().read_user(id)

    #If the user is not logged, redirect to main page
    if user_info['id'] is None:
        return redirect(url_for('crud.list'))

    #If the user is trying to access the profile of another user, redirect to main page
    if user_info['id'] != user['id']:
        return redirect(url_for('crud.list'))

    if request.method == 'POST':
        data = request.form.to_dict(flat=True)
        
        user = get_model().update_user(data, id)

        return redirect(url_for('user.view_user', id=id))

    return render_template("user_form.html", action="Edit user", user=user, user_info=user_info)


@user.route('/<id>/delete')
def delete(id):
    global user_info
    user = get_model().read_user(id)

    #If the user is not logged, redirect to main page
    if user_info['id'] is None:
        return redirect(url_for('crud.list'))

    #If the user is trying to access the profile of another user, redirect to main page
    if user_info['id'] != user['id']:
        return redirect(url_for('crud.list'))

    get_model().delete_user(id)
    return redirect(url_for('crud.list'))

@user.route('/<id>/liked')
def list_liked(id):
    return redirect(url_for(".view_user", id=id, list=1))


@user.route('/<id>/bought')
def list_bought(id):
    return redirect(url_for(".view_user", id=id, list=2))


@user.route('/<id>/published')
def list_published(id):
    return redirect(url_for(".view_user", id=id, list=3))


@user.route('/<id>/sales')
def list_sales(id):
    return redirect(url_for(".view_user", id=id, list=4))

@user.route('/publications/<id>')
def publications(id):
    global user_info
    publications = get_model().find_publications(id)
    return render_template('published.html', publications=publications, user_info=user_info)


