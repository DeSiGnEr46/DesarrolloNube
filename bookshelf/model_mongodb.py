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

from bson.objectid import ObjectId
from flask_pymongo import PyMongo


builtin_list = list


mongo = None


def _id(id):
    if not isinstance(id, ObjectId):
        return ObjectId(id)
    return id


# [START from_mongo]
def from_mongo(data):
    """
    Translates the MongoDB dictionary format into the format that's expected
    by the application.
    """
    if not data:
        return None

    data['id'] = str(data['_id'])
    return data
# [END from_mongo]


def init_app(app):
    global mongo

    mongo = PyMongo(app)
    mongo.init_app(app)

## START COMICS 

# [START list]
def list_comic(limit=10, cursor=None):
    cursor = int(cursor) if cursor else 0

    results = mongo.db.comics.find(skip=cursor, limit=10).sort('title')
    comics = builtin_list(map(from_mongo, results))

    next_page = cursor + limit if len(comics) == limit else None
    return (comics, next_page)
# [END list]


# [START read]
def read_comic(id):
    result = mongo.db.comics.find_one({'_id': _id(id)})
    return from_mongo(result)
# [END read]


# [START create]
def create_comic(data):
    result = mongo.db.comics.insert_one(data)
    return read_comic(result.inserted_id)
# [END create]


# [START update]
def update_comic(data, id):
    mongo.db.comics.replace_one({'_id': _id(id)}, data)
    return read_comic(id)
# [END update]


def delete_comic(id):
    mongo.db.comics.delete_one({'_id': _id(id)})

def search_tags(chain):
    result = mongo.db.comics.find({'tags': chain}, limit=10)
    result = builtin_list(map(from_mongo, result))
    return result

def search_author(chain):
    result = mongo.db.comics.find({'author': chain}, limit=10)
    result = builtin_list(map(from_mongo, result))
    return result

def search_title(chain):
    result = mongo.db.comics.find({'title': chain}, limit=10)
    result = builtin_list(map(from_mongo, result))
    return result

## ENDS COMICS

## START PAGES

# [START CREATE]
def create_page(data):
    result = mongo.db.pages.insert_one(data)
    return read_comic(data['comic_id'])

# [END CREATE]

# [START LIST]
def list_pages(comic_id, limit=10, cursor=None):
    cursor = int(cursor) if cursor else 0

    results = mongo.db.pages.find({'comic_id': comic_id}).sort('order',-1)

    pages = builtin_list(map(from_mongo, results))

    print("pages")
    for page in results:
        print(str(page)+'\n')

    next_page = cursor + limit if len(pages) == limit else None
    return (pages, next_page)
# [END LIST]




# [START READ]
def read_page(comic_id,page_id):
    result = mongo.db.pages.find_one({'_id': _id(page_id)})
    return from_mongo(result)

# [END READ]

# [START CONTIGUOS]
def contiguos_page(comic_id,page_id):
    pages,cursor = list_pages(comic_id)
    pages.reverse()
    page = from_mongo(mongo.db.pages.find_one({'_id': _id(page_id)}))
    next = pages[int(page['order'])] if int(page['order'])<len(pages) else None
    prev = pages[int(page['order'])-2] if (int(page['order'])-2)>-1 else None
    return (next,prev,pages)

# [END CONTIGUOS]

## END PAGES

## START USERS 

## not sure if users need list function. maybe for admins, but we dont need admins
# [START list]
def list_user(limit=10, cursor=None):
    cursor = int(cursor) if cursor else 0

    results = mongo.db.users.find(skip=cursor, limit=10).sort('name')
    users = builtin_list(map(from_mongo, results))

    next_page = cursor + limit if len(users) == limit else None
    return (users, next_page)
# [END list]


# [START read]
def read_user(id):
    result = mongo.db.users.find_one({'_id': _id(id)})
    return from_mongo(result)
# [END read]


# [START create]
def create_user(data):
    result = mongo.db.users.insert_one(data)
    return read_user(result.inserted_id)
# [END create]


# [START update]
def update_user(data, id):
    mongo.db.users.replace_one({'_id': _id(id)}, data)
    return read_user(id)
# [END update]


def delete_user(id):
    mongo.db.users.delete_one({'_id': _id(id)})

def find_user_email(email):
    result = mongo.db.users.find_one({'email': email})
    return from_mongo(result)

def find_user_name(name):
    result = mongo.db.users.find({'name': name}, limit=10)
    result = builtin_list(map(from_mongo, result))
    return result

## ENDS USERS


# [START list]
def list(limit=10, cursor=None):
    cursor = int(cursor) if cursor else 0

    results = mongo.db.books.find(skip=cursor, limit=10).sort('title')
    books = builtin_list(map(from_mongo, results))

    next_page = cursor + limit if len(books) == limit else None
    return (books, next_page)
# [END list]


# [START read]
def read(id):
    result = mongo.db.books.find_one({'_id': _id(id)})
    return from_mongo(result)
# [END read]


# [START create]
def create(data):
    result = mongo.db.books.insert_one(data)
    return read(result.inserted_id)
# [END create]


# [START update]
def update(data, id):
    mongo.db.books.replace_one({'_id': _id(id)}, data)
    return read(id)
# [END update]


def delete(id):
    mongo.db.books.delete_one({'_id': _id(id)})

## END COMICS