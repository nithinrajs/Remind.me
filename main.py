from flask import Flask, send_from_directory, jsonify, request, redirect, url_for, make_response
from google.cloud import datastore
from random import randint

app = Flask(__name__, static_url_path='/static')
# client = datastore.Client('remind-me-663')
client = datastore.Client('remind-me-1089')

# e = {
#     "events": [{
#         "date": "2018-02-23",
#         "name": "CIP Exam"
#     }, {
#         "date": "2019-01-20",
#         "name": "Course Add/Drop"
#     }]
# }

creds = {
    'username':None,
    'sessionID':None
}

def rand():
    return str(randint(100000000000,999999999999))

def auth(user_input,db_input):
    if user_input == db_input:
        return True
    else:
        return False


@app.route('/', methods=['GET'])
def index():
    # todo: Make a check for session cookie!
    print(creds)
    if request.cookies.get('sessionID') == None:
        # print(request.cookies.get('sessionID'))
        return app.send_static_file('login.html')

    query = client.query(kind='users')
    query.add_filter('sessionID','=',request.cookies.get('sessionID'))  

    if(list(query.fetch()) == []):
          return app.send_static_file('login.html')

    print(request.cookies.get('sessionID'))
    return app.send_static_file('index.html')


@app.route('/login', methods=['GET','POST'])
def login():
    print(creds)
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        key = client.key('users', username)
        if(client.get(key)):
            data = client.get(key)
            test = data['password']
            
            if(auth(password,test)):
                print('inside')
                random = rand()
                # task = datastore.Entity(key=key)
                task = client.get(key)
                task['sessionID'] = random
                
                client.put(task)
                creds['username'] = username
                creds['sessionID'] = random

                resp = make_response(redirect(url_for('index')))
                resp.set_cookie("sessionID", random, max_age=60 * 60 * 24)
                return resp
            else:
                return 'Wrong Creds' # ! NEED to change this
                
    else:
        return app.send_static_file('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    resp = make_response(redirect(url_for('index')))
    resp.set_cookie('sessionID', expires=0)
    return resp



@app.route('/register', methods=['POST', 'GET'])
def register():
     # todo: Set Session cookie if username does not exist!
    if request.method == 'GET':
        return app.send_static_file('signup.html')
   
    else:
        username = request.form['username']
        password = request.form['password']
        random = rand()
        complete_key = client.key('users', username)
        task = datastore.Entity(key=complete_key)
        task.update({
            'username':username,
            'password':password,
            'sessionID': random
        })
        creds['username'] = username
        creds['sessionID'] = random
        # print(task)
        client.put(task)
        resp = make_response(redirect(url_for('index')))
        resp.set_cookie("sessionID", random, max_age=60 * 60 * 24)
        return resp


@app.route('/events', methods=['POST','GET'])
def events():
    # ! Data Store section
    # todo: get events of that username
    # query = client.query(kind='events')
    # query.add_filter("username", "=" , "sunny")
    if (request.cookies.get('sessionID')):
        query = client.query(kind='users')
        query.add_filter('sessionID','=',request.cookies.get('sessionID'))

        if(list(query.fetch()) != []):
            result = list(query.fetch())
            parent_key = result[0].key

            # parent_key = client.key('users', request.cookies.get('username'))
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
            return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))

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
            return redirect(url_for('index'))
        else:
            pass
    key = client.key('events',parent=parent_key)
    task = datastore.Entity(key=key)
    task.update(d)
    client.put(task)
    return redirect(url_for('index'))
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
    print(key)
    # ! **********************
    return redirect(url_for('index'))

@app.route('/sucess')
def DeleteSuccess():
    return 'Deletion Successfull'
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
