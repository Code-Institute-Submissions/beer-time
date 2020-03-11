import os
from flask import Flask, render_template, request, flash, session, redirect, url_for
import json
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import bcrypt


app = Flask(__name__)
app.config["MONGO_DBNAME"] = 'Beer-Time'
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
app.secret_key = "vRb81oq80xFpG45So4CKACqU1GvA9Fv"

mongo = PyMongo(app)

# Routes for beer time

'''
This app route is for the index page, this accesses the beers collection in order to output a list of beers 
onto the slider toward the bottom of the page. 
'''
@app.route('/')
def index():
    try:
        current_user = session['username']
        users = mongo.db.users
        return render_template("pages/index.html", body_id="home-page", page_title="Home", current_user=users.find_one({'name': session['username']}))
    except:
        return render_template("pages/index.html", body_id="home-page", page_title="Home")


'''
This 'all-beers' route is for the main beer page where all beers in the database are output to the page, the function
will check if there is a user in session and wether or not they have a 'favourites' array in the collection. If the
Array has ObjectIds present these are marked as favourites on the beer panel itself. 
'''


@app.route('/all-beers')
def all_beers():
    try:
        current_user = session['username']
        users = mongo.db.users
        current_user_obj = users.find_one({'name': session['username']})
        if len(current_user_obj['favourites']) != 0:
            current_user_favourites = current_user_obj['favourites']
        favourite_beers_id = []

        if len(current_user_obj['favourites']) != 0:
            for fav in current_user_favourites:
                current_beer = mongo.db.beers.find_one({'_id': fav})
                current_beer_id = current_beer['_id']
                favourite_beers_id.append(current_beer_id)

        return render_template("pages/beers/all-beers.html", favourite_beers_id=favourite_beers_id, beers=mongo.db.beers.find(), body_id="all-beers", current_user=users.find_one({'name': session['username']}))
    except:
        return redirect(url_for('create_account'))


@app.route('/my-list', methods=["GET", "POST"])
def my_list():
    current_user = session['username']
    users = mongo.db.users
    current_user_obj = users.find_one({'name': session['username']})
    current_user_favourites = current_user_obj['favourites']
    favourite_beers = []
    favourite_beers_id = []

    if len(current_user_obj['favourites']) != 0:
        for fav in current_user_favourites:
            current_beer = mongo.db.beers.find_one({'_id': fav})
            current_beer_id = current_beer['_id']
            favourite_beers_id.append(current_beer_id)

    for fav in current_user_favourites:
        current_beer = mongo.db.beers.find_one({'_id': fav})
        favourite_beers.append(current_beer)

    return render_template("pages/my-list.html", body_id="my-list", page_title="My List", favourite_beers_id=favourite_beers_id, favourite_beers=favourite_beers, current_user=users.find_one({'name': session['username']}))


@app.route('/add-to-fav/<beer_id>', methods=['POST'])
def addToFavourites(beer_id):
    current_user = session['username']
    users = mongo.db.users
    current_user_obj = users.find_one({'name': session['username']})
    current_user_favourites = current_user_obj['favourites']
    mongo.db.users.update(
        current_user_obj, {"$push": {"favourites": ObjectId(beer_id)}})
    return redirect(url_for('my_list'))


@app.route('/remove-from-favourites/<beer_id>', methods=['POST'])
def remove_from_favourites(beer_id):
    current_user = session['username']
    users = mongo.db.users
    current_user_obj = users.find_one({'name': session['username']})
    current_user_favourites = current_user_obj['favourites']
    mongo.db.users.update(
        current_user_obj, {"$pull": {"favourites": ObjectId(beer_id)}})
    return redirect(url_for('my_list'))


@app.route('/beer/<beer_id>')
def beer_page(beer_id):
    current_user = session['username']
    users = mongo.db.users
    the_beer = mongo.db.beers.find_one({"_id": ObjectId(beer_id)})
    you_might_like = mongo.db.beers.find().limit(3)
    return render_template('pages/beers/beer.html', beer=the_beer, you_might_like=you_might_like, body_id="beer-product", current_user=users.find_one({'name': session['username']}))


@app.route('/add-beer')
def add_beer():
    return render_template('pages/beers/add-beer.html', body_id="add-beer", types=mongo.db.types.find())


@app.route('/insert-beer', methods=['POST'])
def insert_beer():
    beers = mongo.db.beers
    beers.insert_one(request.form.to_dict())
    return redirect(url_for('all_beers'))


@app.route('/edit-beer/<beer_id>')
def edit_beer(beer_id):
    current_user = session['username']
    users = mongo.db.users
    the_beer = mongo.db.beers.find_one({"_id": ObjectId(beer_id)})
    all_types = mongo.db.types.find()
    return render_template('pages/beers/edit-beer.html', body_id='edit-page', beer=the_beer, types=all_types, current_user=users.find_one({'name': session['username']}))


@app.route('/update-beer/<beer_id>', methods=['POST'])
def update_beer(beer_id):
    beer = mongo.db.beers
    beer.update({'_id': ObjectId(beer_id)},
                {
                'name': request.form.get('name'),
                'brewery': request.form.get('brewery'),
                'type': request.form.get('type'),
                'excerpt': request.form.get('excerpt'),
                'notes': request.form.get('notes'),
                'abv': request.form.get('abv'),
                'image': request.form.get('image')
                }
                )
    return redirect(url_for('add_beer'))


@app.route('/delete-beer/<beer_id>')
def delete_beer(beer_id):
    mongo.db.beers.remove({'_id': ObjectId(beer_id)})
    return redirect(url_for('all_beers'))


@app.route('/register', methods=["GET", "POST"])
def create_account():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'name': request.form['username']})
        favourites_array = []
        password = request.form['password']
        repeat_password = request.form['repeat_password']

        if password == repeat_password:
            if existing_user is None:
                hashpass = bcrypt.hashpw(
                    request.form['password'].encode('utf-8'), bcrypt.gensalt())
                users.insert({
                    'name': request.form['username'].lower(),
                    'password': hashpass,
                    'favourites': favourites_array
                })
                session['username'] = request.form['username']
                return redirect(url_for('index'))
            flash('That username already exists, try something else.')
        flash('The passwords dont match.')
    return render_template("pages/account-nav.html", body_id="register-page", page_title="Create an Account")


"""
Route for the sign-in page
"""


@app.route('/sign-in', methods=["POST", "GET"])
def sign_in():
    return render_template("pages/account-nav.html", body_id="sign-in", page_title="Sign In")


@app.route('/login', methods=["POST", "GET"])
def login():
    users = mongo.db.users
    login_user = users.find_one({'name': request.form['username'].lower()})

    if login_user:
        if bcrypt.hashpw(request.form['password'].encode('utf-8'), login_user['password']) == login_user['password']:
            session['username'] = request.form['username']
            return redirect(url_for('index'))
    flash('That username/password combination was incorrect')
    return redirect(url_for('sign_in'))


"""
Route for sign-out
"""
@app.route('/sign-out')
def sign_out():
    session.clear()
    return redirect('/')


"""
Route for the contact page
"""
@app.route('/contact', methods=["GET", "POST"])
def contact():
    try:
        current_user = session['username']
        users = mongo.db.users
        if request.method == "POST":
            flash("Thanks {} we have recieved your message!".format(
                request.form["name"]))
        return render_template("pages/contact-us.html", body_id="contact-page", page_title="Contact Us", current_user=users.find_one({'name': session['username']}))
    except:
        if request.method == "POST":
            flash("Thanks {} we have recieved your message!".format(
                request.form["name"]))
        return render_template("pages/contact-us.html", body_id="contact-page", page_title="Contact Us")


if __name__ == '__main__':
    app.run(host=os.getenv('IP'), port=os.getenv('PORT'), debug=True)
