from flask import Flask, send_from_directory, jsonify, request, redirect, url_for, make_response
from google.cloud import datastore
from random import randint
import bcrypt
import logging 
import requests, uuid, json, base64

app = Flask(__name__, static_url_path='/static')
#Datastore
# client = datastore.Client('remind-me-1089')
client = datastore.Client('remind-me-oauth')
client_id = "236868157229-5qo5ucudtv3tshrsigvvih360p4p0f8f.apps.googleusercontent.com"

@app.route('/', methods=['GET','POST'])
def root():
    logging.warning('This is an error message')
    if (request.cookies.get('sessionID') == None):
        logging.warning(request.cookies.get('sessionID'))
        return redirect(url_for('login'))

    else:
        query = client.query(kind='users')
        query.add_filter('sessionID','=',request.cookies.get('sessionID'))  

        if(list(query.fetch()) == []):
            return redirect(url_for('login'))
        else:
            logging.warning(request.cookies.get('sessionID'))
            return app.send_static_file('home.html')
    return redirect(url_for('login'))


@app.route('/login', methods=['GET','POST'])
def login():
    # logging.warning('in login')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        key = client.key('users', username)
        if(client.get(key)):
            data = client.get(key)
            test = data['password']
            salt = data['salt']
            
            if(auth(password,test,salt)):
                random = rand()
                task = client.get(key)
                task['sessionID'] = random
                
                client.put(task)

                resp = make_response(redirect(url_for('root')))
                resp.set_cookie("sessionID", random, max_age=60 * 60 * 1) # Setting cookie time 1 hour
                return resp, 307
            else:
                return app.send_static_file('login.html')
        else:
            return app.send_static_file('login.html')               
    else:
        # creds['state']= rand()
        # creds['nounce'] = rand()
        
        resp = make_response(app.send_static_file('login.html'))
        resp.set_cookie("state", rand() , max_age=60 * 60 * 1)
        resp.set_cookie("nounce", rand(), max_age=60 * 60 * 1)
        resp.set_cookie("clientID", client_id, max_age=60 * 60 * 1)
        return resp
        # return app.send_static_file('login.html')

@app.route('/oidauth', methods=['GET'])
def oauth():
    logging.warning(request.cookies.get('state'))
    if request.args['state'] == request.cookies.get('state'):
        state = request.args['state']
        code = request.args['code']
        secret = client.get(client.key('secret', 'oidc'))['client-secret']

        response = requests.post("https://www.googleapis.com/oauth2/v4/token",
            {"code": code,
            "client_id": client_id,
            "client_secret": secret,
            "redirect_uri": "https://remind-me-oauth.appspot.com/oidauth",
            "grant_type": "authorization_code"})
        id_token = response.json()['id_token']
        _, body, _ = id_token.split('.')
        body += '=' * (-len(body) % 4)
        claims = json.loads(base64.urlsafe_b64decode(body.encode('utf-8')))
        logging.warning(claims)

        if claims['nonce'] == request.cookies.get('nounce'):
            logging.warning(claims['sub'])
            logging.warning(claims['email'])
            random = rand()
            complete_key = client.key('users', claims['sub'])
            task = datastore.Entity(key=complete_key)
            task.update({
                'username':claims['sub'],
                'password':'',
                'salt':'',
                'email':claims['email'],
                'sessionID':random
            })
            client.put(task)
            resp = make_response(redirect(url_for('root')))
            resp.set_cookie("sessionID", random, max_age=60 * 60 * 1) # Setting cookie time 1 hour
            return resp, 307

        else:
            return app.send_static_file('login.html')    

    else:
        return app.send_static_file('login.html')


@app.route('/logout', methods=['POST']) # Expiring the cookie
def logout():
    resp = make_response(redirect(url_for('root')))
    resp.set_cookie('sessionID','', expires=0)
    return resp, 307

@app.route('/register', methods=['POST', 'GET'])
def register():
    logging.warning('register')
     # todo: Set Session cookie if username does not exist!
    if request.method == 'GET':
        return app.send_static_file('signup.html')
   
    else:
        username = request.form['username']
        password = request.form['password']
        random = rand()
        complete_key = client.key('users', username)
        task = datastore.Entity(key=complete_key)
        hashed,salt = hasher(password)
        task.update({
            'username':username,
            'password':hashed,
            'salt':salt,
            'email':'',
            'sessionID':random
        })
        client.put(task)
        resp = make_response(redirect(url_for('root')))
        resp.set_cookie("sessionID", random, max_age=60 * 60 * 1) # Setting cookie time 1 hour
        return resp, 307

@app.route('/events', methods=['POST','GET'])
def events():
    # ! Data Store section
    if (request.cookies.get('sessionID')):
        query = client.query(kind='users')
        query.add_filter('sessionID','=',request.cookies.get('sessionID'))

        if(list(query.fetch()) != []):
            result = list(query.fetch())
            parent_key = result[0].key
            query = client.query(kind='events', ancestor=parent_key)
            results = list(query.fetch())
            keys = ['id','date','name']
            d = dict.fromkeys(keys, None)
            arr = []
            #print(results)
            for result in results:
                d = dict.fromkeys(keys, None)
                d['id'] = result.id
                d['name']=result['name']
                d['date']=result['date']
                arr.append(d)
            # print(arr)
        # ! *****************
            return jsonify({'events': arr})
        else:
            return redirect(url_for('root'))
    else:
        return redirect(url_for('root'))

@app.route('/event',methods=['POST'])
def AddEvent():
    name = request.form['name']
    date = request.form['date']
    d = {
        "date": date,
        "name": name
        # "id" : rand()
    }
    # ! Data Store Implementation
    query = client.query(kind='users')
    query.add_filter('sessionID','=',request.cookies.get('sessionID'))
    result = list(query.fetch())
    parent_key = result[0].key

    # parent_key = client.key('users', request.cookies.get('usernamese'))
    query = client.query(kind='events', ancestor=parent_key)
    results = list(query.fetch())
    #print(results)
    for result in results:
        #print(result['name'])
        if str(result['name']) == str(name):
            print("Do not use duplicate event names!!")
            return redirect(url_for('root'))
        else:
            pass
    key = client.key('events',parent=parent_key)
    task = datastore.Entity(key=key)
    task.update(d)
    client.put(task)
    return redirect(url_for('root'))
    # ! **********************
    
@app.route('/delete/<key>',methods=['POST'])
def DeleteEvent(key):
    # ! Data Store Implementation

    query = client.query(kind='users')
    query.add_filter('sessionID','=',request.cookies.get('sessionID'))
    result = list(query.fetch())
    parent_key = result[0].key
    # parent_key = client.key('users', creds['username'])
    key = client.key('events', int(key), parent=parent_key)
    deleted = client.delete(key)
    # print(key)
    # ! **********************
    return redirect(url_for('root'))

@app.route('/sucess',methods=['GET'])
def DeleteSuccess():
    logging.warning(request.cookies.get('sessionID'))
    return 'Deletion Successfull'

def rand(): # Generating session
    return str(uuid.uuid4())

def auth(user_input, db_input, salt): #Checking hash
    test = bcrypt.hashpw(user_input.encode(), salt)

    if test == db_input:
        return True
    else:
        return False

def hasher(pwd): #hashing the user inout password
    password = pwd.encode()
    salt = bcrypt.gensalt(10)
    hashed = bcrypt.hashpw(password, salt)
    return hashed , salt

@app.after_request
def set_response_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
