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

@app.route('/')
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
    key = client.key('events')
    item = datastore.Entity(key)
    item.update(d)
    key = client.put(item)
    # ! **********************
    #e['events'].append(d)
    return redirect(url_for('index'))

@app.route('/event',methods=['POST'])
def DeleteEvent():
    pass

if __name__ == '__main__':
    app.run(debug=True)
