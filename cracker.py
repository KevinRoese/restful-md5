#!/usr/bin/env python
# -*- coding: utf-8 -*-

from random import random
from time import sleep, time
from flask import Flask, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import threading

async_mode = 'threading'

app = Flask(__name__)
#app.config['SECRET_KEY'] = 'thisisanexamplesecretkey'
CORS(app)
socketio = SocketIO(app, async_mode=async_mode)

def task(start):
    sum = 0
    while (sum < 30):
        sleep(1)
        sum += random() + 0.5
        print(sum)
        if(sum >= 30):
            runtime = time() - start
            socketio.emit('result', {'time': runtime, 'sum': sum})
            break

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
    print(rhash)
    global seconds
    seconds = time()
    task_thread = threading.Thread(target=task, name='Task', args=(seconds,))
    task_thread.start()

@socketio.event
def status():
    global seconds
    if(seconds == None):
        print('Status call before hash received!')
        emit('error', {'message': 'Status call before hash received!'})
        return
    runtime = time() - seconds
    print('''Time: {}'''.format(runtime))
    emit('time', {'time': runtime})

@socketio.event
def finished(data):
    print('''Finished at {} seconds!'''.format(data['time']))

if __name__ == '__main__':
    socketio.run(app)