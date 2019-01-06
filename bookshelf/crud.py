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

from bookshelf import get_model
from flask import Blueprint, redirect, render_template, request, url_for, flash
from werkzeug.utils import secure_filename
from . import flickr_handler
import datetime
import bookshelf.user
from bson.objectid import ObjectId
from mhlib import isnumeric

crud = Blueprint('crud', __name__)

TEMP_USER_ID = '5c314f92602d682310ff9ecd'
#TEMP_USER_ID = '5c2a7709b9be89189c0a51e6'

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
    
    # experimenting
    users, next_page_token2 = get_model().list_user(cursor=token)

    #print(bookshelf.user.user_info)
    return render_template(
        "list.html",
        books=books_with_covers,
        users=users,
        next_page_token=next_page_token,
        next_page_token2=next_page_token2,
        user_info=bookshelf.user.user_info) 
# [END list]


@crud.route('/<id>')
def view(id):
    book = get_model().read_comic(id)
    pages, next_page_token = get_model().list_pages(id)
    book['cover'] = pages[0]['url'] if pages else 'http://placekitten.com/g/128/192'
    
    publishedBy = get_model().read_user(book['publishedBy'])
    book['publishedBy'] = publishedBy
    
    ## get current user if any
    #if loggedin == True:
    bought = get_model().is_bought(TEMP_USER_ID, id)
    like = get_model().read_like(TEMP_USER_ID, id)
    showLike = True if like is None else False
    isPublisher = True if str(publishedBy['_id']) == str(TEMP_USER_ID) else False
    
    return render_template("view.html",
        book=book,
        pages=pages,
        bought=bought,
        showLike=showLike,
        isPublisher=isPublisher,
        user_info=bookshelf.user.user_info)


@crud.route('/<comic_id>/<page_id>')
def view_page(comic_id,page_id):
    page = get_model().read_page(comic_id,page_id)
    next, prev, pages = get_model().contiguos_page(comic_id,page_id) 
    if(next):
        next["_id"] = next["id"]
    if(prev):
        prev["_id"] = prev["id"]
    return render_template("page_view.html", page=page,next=next,prev=prev,book=comic_id,pages=pages,user_info=bookshelf.user.user_info)


ALLOWED_EXTENSIONS = set(['jpg', 'png', 'jpeg'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# [START new_page]
@crud.route('<id>/new_page', methods=['GET', 'POST'])
def new_page(id):
    book = get_model().read_comic(id)

    if request.method == 'POST':
        data = request.form.to_dict(flat=True)
        data['comic_id'] = id
        data['date'] = datetime.datetime.now().strftime("%d/%m/%Y")
        
        img_path = data['url']    
        if img_path == '':
            flash('No selected file')
            return render_template("new_page.html", action="New", book=book)
        if allowed_file(img_path):
            filename = img_path
            img_id, img_url = flickr_handler.upload_img(filename)
            data['flickr_id'] = img_id
            data['url'] = img_url
            get_model().create_page(data)
            return redirect(url_for('.view', id=id))


    return render_template("new_page.html", action="New", book=book, user_info=bookshelf.user.user_info)
# [END new_page]

# [START add]
@crud.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        data = request.form.to_dict(flat=True)
        data['tags'] = data['tags'].split(',')
        data['publishedDate'] = datetime.datetime.now().strftime("%d/%m/%Y")
        data['likes'] = 0
        data['publishedBy'] = TEMP_USER_ID
        data['price'] = abs(float(data['price'])) if isnumeric(data['price']) == True else 0

        book = get_model().create_comic(data)

        return redirect(url_for('.view', id=book['id']))

    return render_template("form.html", action="Add", book={}, user_info=bookshelf.user.user_info)
# [END add]


@crud.route('/<id>/edit', methods=['GET', 'POST'])
def edit(id):
    book = get_model().read_comic(id)

    if request.method == 'POST':
        data = request.form.to_dict(flat=True)

        book = get_model().update_comic(data, id)

        return redirect(url_for('.view', id=book['id']))

    return render_template("form.html", action="Edit", book=book, user_info=bookshelf.user.user_info)


@crud.route('/<id>/delete')
def delete(id):
    get_model().delete_comic(id)
    return redirect(url_for('.list'))


@crud.route('/search', methods=['POST'])
def search():
    cadena = request.form['chain']
    
    #Make the requests
    users = get_model().find_user_name(cadena)
    print(users)
    authors = get_model().search_author(cadena)
    print(authors)
    titles = get_model().search_title(cadena)
    print(titles)
    tags = get_model().search_tags(cadena)
    print(tags)

    #return redirect(url_for('.list'))
    return render_template('search_results.html', users=users, authors=authors, titles=titles, tags=tags, user_info=bookshelf.user.user_info)


@crud.route('/<id>/like')
def like(id):
    like = get_model().like(TEMP_USER_ID, id)
    return redirect(url_for('.view', id=id))


@crud.route('/<id>/unlike')
def unlike(id):
    get_model().unlike(TEMP_USER_ID, id)
    return redirect(url_for('.view', id=id))


@crud.route('/<id>/buy')
def buy(id):
    if get_model().buy(TEMP_USER_ID, id) == False:
        flash('Not enough money')
    return redirect(url_for('.view', id=id))

