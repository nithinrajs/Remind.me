from flask import Flask, send_from_directory, jsonify, request, redirect, url_for
from google.cloud import datastore

app = Flask(__name__, static_url_path='/static')
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

@app.route('/', methods=['GET'])
def index():
    return app.send_static_file('index.html')

@app.route('/events')
def events():
    # ! Data Store section
    query = client.query(kind='events')
    results = list(query.fetch())
    keys = ['id','date','name']
    d = dict.fromkeys(keys, None)
    arr = []

    for result in results:
        d = dict.fromkeys(keys, None)
        d['id'] = result.id
        d['name']=result['name']
        d['date']=result['date']
        arr.append(d)
    # print(arr)
    # ! *****************
    return jsonify({'events': arr})
    #return jsonify(e)

@app.route('/event',methods=['POST'])
def AddEvent():
    name = request.form['name']
    date = request.form['date']
    d = {
        "date": date,
        "name": name
    }
    # ! Data Store Implementation
    query = client.query(kind='events')
    results = list(query.fetch())
    #print(results)
    for result in results:
        #print(result['name'])
        if str(result['name']) == str(name):
            print("Do not use duplicate event names!!")
            return redirect(url_for('index'))
        else:
            pass
    key = client.key('events')
    item = datastore.Entity(key)
    item.update(d)
    key = client.put(item)
    return redirect(url_for('index'))
    # ! **********************
    
    

@app.route('/delete/<key>',methods=['POST'])
def DeleteEvent(key):
    # ! Data Store Implementation
    key = client.key('events', int(key))
    deleted = client.delete(key)
    print(key)
    # ! **********************
    return redirect(url_for('index'))

@app.route('/sucess')
def DeleteSuccess():
    return 'Deletion Successfull'
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
