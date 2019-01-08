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

import os
from bookshelf import get_model
from flask import Flask, Blueprint, redirect, render_template, request, url_for, flash, session
from werkzeug.utils import secure_filename
from . import flickr_handler
import datetime
import bookshelf.user
from bson.objectid import ObjectId

crud = Blueprint('crud', __name__)

@crud.before_request
def before_request():

    if 'user' in session:
        print(session['user'])
        print("Before!")
    else:
        session['user'] = {'log': False, 'id': None, 'name': None}
        print(session['user'])
        print("Before!")

# [START list]
@crud.route("/")
def list():
    token = request.args.get('page_token', None)
    if token:
        token = token.encode('utf-8')

    books, next_page_token = get_model().list_comic(cursor=token)
    books_with_covers = []
    
    for book in books:
        cover = get_model().get_cover(book['id'])
        book = tuple((book, cover))
        books_with_covers.append(book)

    #print(session['user'])
    return render_template(
        "list.html",
        books=books_with_covers,
        next_page_token=next_page_token,
        user_info=session['user']) 
# [END list]


@crud.route('/<id>')
def view(id):
    book = get_model().read_comic(id)
    pages, next_page_token = get_model().list_pages(id)
    book['cover'] = pages[0]['url'] if pages else 'http://placekitten.com/g/128/192'

    showPages = request.args.get('showPages')
    showPages = bool(showPages) if showPages is not None else False
    
    publishedBy = get_model().read_user(book['publishedBy'])
    book['publishedBy'] = publishedBy
    bought, showLike, isPublisher = False, False, False
    if session['user']['log'] == True:
        bought = get_model().is_bought(session['user']['id'], id)
        like = get_model().read_like(session['user']['id'], id)
        showLike = True if like is None else False
        isPublisher = True if str(publishedBy['_id']) == str(session['user']['id']) else False
    
    return render_template("view.html",
        book=book,
        pages=pages,
        bought=bought,
        showLike=showLike,
        isPublisher=isPublisher,
        showPages=showPages,
        user_info=session['user'])


@crud.route('/<id>/pages')
def show_pages(id):
    return redirect(url_for('.view', id=id, showPages=True))


@crud.route('/<comic_id>/<page_id>')
def view_page(comic_id,page_id):

    # If the user is not logged, redirect to login
    if session['user']['log'] == False:
        return redirect(url_for('user.login'))

    page = get_model().read_page(comic_id,page_id)
    next, prev, pages = get_model().contiguos_page(comic_id,page_id) 
    if(next):
        next["_id"] = next["id"]
    if(prev):
        prev["_id"] = prev["id"]
    return render_template("page_view.html", page=page,next=next,prev=prev,book=comic_id,pages=pages,user_info=session['user'])


ALLOWED_EXTENSIONS = set(['jpg', 'png', 'jpeg'])
UPLOAD_FOLDER = 'tmp/'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# [START new_page]
@crud.route('<id>/new_page', methods=['GET', 'POST'])
def new_page(id):
    #If the user is not logged, redirect to login
    if session['user']['log'] == False:
        return redirect(url_for('crud.list'))

    book = get_model().read_comic(id)

    #If the user is not the publisher, redirect to main page
    # If the user is not logged, redirect to login
    if session['user']['id'] != book['publishedBy']:
        return redirect(url_for('user.login'))

    data = request.form.to_dict(flat=True)
    data['comic_id'] = id
    data['date'] = datetime.datetime.now().strftime("%d/%m/%Y")

    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        page_file = request.files['file']

        if page_file.filename == '':
            flash('No selected file')
            return render_template("new_page.html", action="New", book=book)
        
        if page_file and allowed_file(page_file.filename):
            filename = secure_filename(page_file.filename)
            server_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            page_file.save(server_path)
            img_id, img_url = flickr_handler.upload_img(server_path)
            data['flickr_id'] = img_id
            data['url'] = img_url
            get_model().create_page(data)
            os.remove(server_path)
            return redirect(url_for('.view', id=id))


    return render_template("new_page.html", action="New", book=book, user_info=session['user'])
# [END new_page]

# [START add]
@crud.route('/add', methods=['GET', 'POST'])
def add():
    #If the user is not logged, redirect to login
    if session['user']['log'] == False:
        return redirect(url_for('user.login'))

    if request.method == 'POST':
        data = request.form.to_dict(flat=True)
        data['author'] = session['user']['name']
        data['tags'] = data['tags'].split(',')
        data['publishedDate'] = datetime.datetime.now().strftime("%d/%m/%Y")
        data['likes'] = 0
        data['publishedBy'] = session['user']['id']
        data['price'] = abs(float(data['price'])) if data['price'].isdigit() == True else 0

        book = get_model().create_comic(data)

        return redirect(url_for('.view', id=book['id']))

    return render_template("form.html", action="Add", book={}, user_info=session['user'])
# [END add]


@crud.route('/<id>/edit', methods=['GET', 'POST'])
def edit(id):
    #If the user is not logged, redirect to login
    if session['user']['log'] == False:
        return redirect(url_for('user.login'))

    book = get_model().read_comic(id)

    #If the user is not the publisher, redirect to main page
    # If the user is not logged, redirect to login
    if session['user']['id'] != book['publishedBy']:
        return redirect(url_for('user.login'))

    if request.method == 'POST':
        data = request.form.to_dict(flat=True)
        data['author'] = book['author']
        data['publishedDate'] = book['publishedDate']
        
        book = get_model().update_comic(data, id)

        return redirect(url_for('.view', id=book['id']))

    return render_template("form.html", action="Edit", book=book, user_info=session['user'])


@crud.route('/<id>/delete')
def delete(id):

    #If the user is not logged, redirect to login
    if session['user']['log'] == False:
        return redirect(url_for('user.login'))

    book = get_model().read_comic(id)

    #If the user is not the publisher, redirect to main page
    # If the user is not logged, redirect to login
    if session['user']['id'] != book['publishedBy']:
        return redirect(url_for('user.login'))

    get_model().delete_comic(id)
    return redirect(url_for('.list'))


@crud.route('/search', methods=['POST'])
def search():
    cadena = request.form['chain']
    
    # Make the requests
    # Search for users
    users = get_model().find_user_name(cadena)
    print(users)

    #Search for authors
    authors = get_model().search_author(cadena)
    print(authors)
    
    #Search for book titles
    titles = get_model().search_title(cadena)
    titles_with_cover = []
    for book in titles:
        cover = get_model().get_cover(book['id'])
        book = tuple((book, cover))
        titles_with_cover.append(book)

    print(titles_with_cover)

    #Search for book tags
    tags = get_model().search_tags(cadena)
    tags_with_cover = []
    for book in tags:
        cover = get_model().get_cover(book['id'])
        book = tuple((book, cover))
        tags_with_cover.append(book)
    print(tags_with_cover)

    #return redirect(url_for('.list'))
    return render_template('search_results.html', users=users, authors=authors, titles=titles_with_cover, tags=tags_with_cover, user_info=session['user'])


@crud.route('/<id>/like')
def like(id):
    #If the user is not logged, redirect to login
    if session['user']['log'] == False:
        return redirect(url_for('user.login'))

    like = get_model().like(session['user']['id'], id)
    return redirect(url_for('.view', id=id))


@crud.route('/<id>/unlike')
def unlike(id):
    #If the user is not logged, redirect to login
    if session['user']['log'] == False:
        return redirect(url_for('user.login'))

    get_model().unlike(session['user']['id'], id)
    return redirect(url_for('.view', id=id))


@crud.route('/<id>/buy')
def buy(id):
    #If the user is not logged, redirect to login
    if session['user']['log'] == False:
        return redirect(url_for('user.login'))
        
    if get_model().buy(session['user']['id'], id) == False:
        flash('Not enough money')
    return redirect(url_for('.view', id=id))

