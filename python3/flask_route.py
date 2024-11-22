from flask import Flask, jsonify, request
import time
import logging as log

app = Flask(__name__)

# define a route
@app.route('/hello', methods=['POST'])
def hello():
    req = request.get_json()
    log.info(f'Received request: {req}')
    name = req["name"]
    age = req["age"]
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    response = jsonify({'message': f'Now is {now}, Hello {name}, you are {age} years old.'})
    response.headers['X-Another-Custom-Header'] = 'AnotherValue'
    response.headers['access-control-allow-methods:'] = 'POST, GET, PUT, OPTIONS, DELETE'
    response.headers['content-type:'] = 'application/json'
    return response, 200

# define after_request function to add headers to response
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST')
    return response

# Run the application
app.run(host='localhost', port=5009, debug=False)