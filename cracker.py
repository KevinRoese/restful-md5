#!/usr/bin/env python
# -*- coding: utf-8 -*-

from time import time
from flask import Flask, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import threading
import re
import numpy as np
import pycuda.driver as cuda
from pycuda.compiler import SourceModule
import pycuda.tools

async_mode = 'threading'

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, async_mode=async_mode)

def task(start, hash):
    cuda.init()
    ctx = pycuda.tools.make_default_context()
    dev = ctx.get_device()
    print(dev.name(), dev.pci_bus_id())

    mod = SourceModule("""
    //cuda
    __global__ void md5Crack(char *out, char *hash)
    {
        const int i = threadIdx.x;
        out[i] = char (int (hash[i]) + 1);
    }
    //!cuda
    """)

    md5 = mod.get_function("md5Crack")

    dt = np.dtype('B')

    out = np.zeros(16, dtype=dt)
    chash = np.fromstring(bytes.fromhex(hash), dtype=dt)#np.fromstring(hash, dtype=dt)
    print(hash, chash)
    md5(cuda.Out(out), cuda.In(chash), block=(32,1,1), grid=(1,1))
    print(out)
    runtime = time() - start
    socketio.emit('result', {'time': runtime, 'sum': np.array2string(out)})
    ctx.pop()

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
    print('Received hash: {}'.format(rhash))
    if(rhash == ''):
        emit('error', {'message': 'No Hash received!'})
        return
    emit('info', {'message': '''Hash {} received!'''.format(rhash)})
    print(rhash)
    if(not re.fullmatch(r"([a-fA-F\d]{32})", rhash)):
        emit('error', {'message': 'Invalid hash received!'})
        return
    emit('starting', {'message': 'Starting!'})
    global seconds
    seconds = time()
    task_thread = threading.Thread(target=task, name='Task', args=(seconds,rhash))
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