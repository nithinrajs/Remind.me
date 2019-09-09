from flask import Flask, send_from_directory, jsonify

app = Flask(__name__, static_url_path='/static')

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/events')
def events():
    # todo: Connect it to datastore
    e = {
    "events": [{
        "date": "2018-02-23",
        "name": "test1"
    }, {
        "date": "2019-01-20",
        "name": "Test2"
    }]
}
    return jsonify(e)

if __name__ == '__main__':
    app.run(debug=True)
