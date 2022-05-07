#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from time import sleep, time
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit

async_mode = None

app = Flask(__name__)
#app.config['SECRET_KEY'] = 'thisisanexamplesecretkey'
CORS(app)
socketio = SocketIO(app, async_mode=async_mode)

@app.route('/')
def index():
    return render_template("index.html", async_mode=socketio.async_mode)

@socketio.event
def connecting(data):
    print('Received: {}'.format(data))
    emit('connected', {'data': 'Connected!'})

@socketio.event
def hash(data):
    rhash = data['hash']
    print('Received data: {}'.format(rhash))
    if(rhash == ''):
        emit('error', {'message': 'No Hash received!'})
        return
    emit('info', {'message': '''Hash {} received!'''.format(rhash)})
    global seconds
    seconds = time()
    return

@socketio.event
def status():
    global seconds
    if(seconds == None):
        print('Status call before hash received!')
        emit('error', {'message': 'Status call before hash received!'})
    runtime = time() - seconds
    print('''Time: {}'''.format(runtime))
    emit('time', {'time': runtime})
    if(runtime >= 30):
        emit('result', {'time': runtime})

@socketio.event
def finished(data):
    print('''Finished at {} seconds!'''.format(data['time']))

if __name__ == '__main__':
    socketio.run(app)