from flask import Flask, send_from_directory, jsonify, request, redirect

app = Flask(__name__, static_url_path='/static')

e = {
    "events": [{
        "date": "2018-02-23",
        "name": "test1"
    }, {
        "date": "2019-01-20",
        "name": "Test2"
    }]
}

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/events')
def events():
    # todo: Connect it to datastore
    return jsonify(e)

@app.route('/event',methods=['POST'])
def AddEvent():
    name = request.form['name']
    date = request.form['date']
    d = {
        "date": date,
        "name": name
    }
    e['events'].append(d)
    return 'Done'

if __name__ == '__main__':
    app.run(debug=True)
