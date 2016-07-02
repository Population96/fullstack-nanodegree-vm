from flask import Flask, render_template, url_for, request, redirect, \
    flash, jsonify
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User
from flask import session as login_session
import random, string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
import urlparse

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']

engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# LOGIN
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits +
        string.ascii_lowercase) for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" %login_session['state']
    return render_template('login.html', STATE=state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data
    try:
        # Upgrade authorization code into credentials object.
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade the '
                                            'authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Check to see if access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
        % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
    # Verify access token is for intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("Token's User ID doesn't match "
            "given User ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Verify that access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps("Token's Client ID doesn't match "
            "this application."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response
    # Check to see if user is already logged in.
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already '
            'connected'), 200)
        response.headers['Content-Type'] = 'application/json'

    # Store the access token in the session for later use.
    login_session['provider'] = 'google'
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id
    #response = make_response(json.dumps('Successfully connected user.', 200))

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt':'json'}
    answer = requests.get(userinfo_url, params = params)
    data = json.loads(answer.text)

    login_session['username'] = data["name"]
    login_session['picture'] = data["picture"]
    login_session['email'] = data["email"]

    # Create a new user if they do not already exist
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output

#DISCONNECT - Revoke current users token and reset their login_session.
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Execute HTTP GET request to revoke current token.
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(json.dumps('Failed to revoke token for '
            'given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data

    # Exchange client token for long-lived server-side token with GET
    app_id = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_id']
    app_secret = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/v2.4/oauth/' \
          'access_token?grant_type=fb_exchange_token&client_id=%s' \
          '&client_secret=%s&fb_exchange_token=%s' % (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    print "\nResult = " + result

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.4/me"
    # Strip expire tag from access token
    #token = result['access_token'][0]
    #result2 = (dict(result))
    #token = result['access_token']
    result = result.split(",")[0]
    print "\nResult split comma: " + result
    token = result.split(":")[1]
    print "\nToken split colon: " + token
    token = token.replace("\"", "")
    print "\nToken replace quotes:  " + token

    url = 'https://graph.facebook.com/v2.4/me?fields=name,id,email&access_token=%s' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    print "\nResult = " + result
    print "\nToken = " + token
    print "url sent for API access: %s" % url
    print "API JSON results: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    #stored_token = token.split("=")[1]
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?access_token=%s' \
          '&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # See if the user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '" style="width:300px; height:300px; border-radius:150px; ' \
              '-webkit-border-radius: 150px; -moz-border-radius: 150px;">'
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "You have been logged out..."


@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['credentials']
            del login_session['gplus_id']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']

        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have been successfully logged out.")
        return redirect(url_for('showCatalog'))
    else:
        flash("You were not logged in to begin with!")
        redirect(url_for('showCatalog'))


#Making an API Endpoint (GET Request)
@app.route('/catalog/JSON')
def catalogJSON():
    catalog = session.query(Category).all()
    return jsonify(Catalog=[i.serializeR for i in catalog])

@app.route('/catalog/<int:category_id>/item/JSON')
def categoryJSON(category_id):
    category = session.query(Category).filter_by(id = category_id).one()
    items = session.query(Item).filter_by(category_id = category_id).all()
    return jsonify(Items=[i.serializeMI for i in items])

@app.route('/catalog/<int:category_id>/item/<int:item_id>/JSON')
def itemJSON(category_id, item_id):
    item = session.query(Item).filter_by(id = item_id).one()
    return jsonify(Item = item.serializeMI)

@app.route('/')
@app.route('/catalog')
@app.route('/catalog/')
def showCatalog():
    catalog = session.query(Category).order_by(Category.name)
    if 'username' not in login_session:
        return render_template('publicCatalog.html', catalog = catalog)
    else:
        user = getUserInfo(login_session['user_id'])
        return render_template('catalog.html', catalog = catalog)

# CREATE A NEW CATEGORY
@app.route('/category/new/', methods=['GET','POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newCat = Category(name = request.form['name'],
                             user_id = login_session['user_id'])
        session.add(newCat)
        session.commit()
        flash("New Category created!")
        return redirect(url_for('showCatalog'))
    else:
        return render_template('newCategory.html')

# EDIT A CATEGORY
@app.route('/catalog/<int:category_id>/edit/', methods=['GET','POST'])
def editCategory(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedCategory = session.query(Category).filter_by(id = category_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
            session.add(editedCategory)
            session.commit()
            flash("Category successfully edited!")
        return redirect(url_for('showCatalog'))
    else:
        return render_template('editCategory.html', category_id =
            category_id, category = editedCategory)


# DELETE A CATEGORY
@app.route('/catalog/<int:category_id>/delete/', methods=['GET','POST'])
def deleteCategory(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    deletedCat = session.query(Category).filter_by(id = category_id).one()
    if deletedCat.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized" \
               "to delete this category.  Please create your own category" \
               "or contact the current category owner.');}</script><body " \
               "onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(deletedCat)
        session.commit()
        flash("Category successfully deleted!")
        return redirect(url_for('showCatalog'))
    else:
        return render_template('deleteCategory.html', category_id =
            category_id, category = deletedCat)


# SHOW A CATEGORY MENU
@app.route('/catalog/<int:category_id>/')
def showCategory(category_id):
    category = session.query(Category).filter_by(id = category_id).one()
    items = session.query(Item).filter_by(category_id = category.id)
    creator = getUserInfo(category.user_id)
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('publicCategory.html', items = items,
                               category = category, creator = creator)
    else:
        return render_template('category.html', category = category, items = items,
                           creator = creator)

# CREATE NEW MENU ITEM
@app.route('/catalog/<int:category_id>/item/new/', methods=['GET','POST'])
def newItem(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newItem = Item(name = request.form['name'], category_id =
            category_id, description = request.form['description'],
            price = request.form['price'], user_id = login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash("Item created!")
        return redirect(url_for('showCategory', category_id =
            category_id))
    else:
        return render_template('newItem.html', category_id =
            category_id)

# EDIT A MENU ITEM
@app.route('/catalog/<int:category_id>/item/<int:item_id>/edit/', methods=['GET','POST'])
def editItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(Item).filter_by(id = item_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
            editedItem.description = request.form['description']
            editedItem.price = request.form['price']
            session.add(editedItem)
            session.commit()
            flash("Item successfully edited!")
        return redirect(url_for('showCategory', category_id = category_id))
    else:
        return render_template('editItem.html', category_id =
            category_id, item_id = item_id, item = editedItem)

# DELETE A MENU ITEM
@app.route('/catalog/<int:category_id>/item/<int:item_id>/delete/', methods=['GET','POST'])
def deleteItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    deletedItem = session.query(Item).filter_by(id = item_id).one()
    if request.method == 'POST':
        session.delete(deletedItem)
        session.commit()
        flash("Item successfully deleted!")
        return redirect(url_for('showCategory', category_id = category_id))
    else:
        return render_template('deleteItem.html', category_id =
            category_id, item_id = item_id, item = deletedItem)

def createUser(login_session):
    newUser = User(name = login_session['username'], email =
        login_session['email'], picture = login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email = login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    user = session.query(User).filter_by(id = user_id).one()
    return user

def getUserID(email):
    try:
        user = session.query(User).filter_by(email = email).one()
        return user.id
    except:
        return None

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
