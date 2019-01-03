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
from flask import Blueprint, redirect, render_template, request, url_for


user = Blueprint('user', __name__)


@user.route('/login')
def login():
    return render_template("login.html")


# TBD ...
@user.route('/<id>')
def view_user(id):
    user = get_model().read_user(id)
    return render_template("user.html", user=user)


# [START add]
@user.route('/add', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        data = request.form.to_dict(flat=True)

        user = get_model().create_user(data)

        return redirect(url_for('crud.list'))

    return render_template("user_form.html", action="Create new user", user={})
# [END add]


@user.route('/<id>/edit', methods=['GET', 'POST'])
def edit_user(id):
    user = get_model().read_user(id)

    if request.method == 'POST':
        data = request.form.to_dict(flat=True)

        user = get_model().update_user(data, id)

        return redirect(url_for('crud.list'))

    return render_template("user_form.html", action="Edit user", user=user)


@user.route('/<id>/delete')
def delete(id):
    get_model().delete_user(id)
    return redirect(url_for('crud.list'))

