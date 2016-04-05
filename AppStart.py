# -*- coding: UTF-8 -*-
from flask import Flask, request, redirect, session
from ProxyFactory import ProxyFactory
import time
import json
import sae.kvdb
import urllib2
import requests
import sae.const
from sae.taskqueue import TaskQueue

app = Flask(__name__)
app.debug = True
app.secret_key = 'test'

@app.route('/fetchproxy')
def FetchProxy():
    start = time.clock()
    pf = ProxyFactory()
    proxys = pf.FetchProxies()
    end = time.clock()
    result = {'proxys': proxys, "time":(end-start)}
    #kv = sae.kvdb.Client()
    #for proxy in proxys:
        #kv.set(proxy, "ok", 0)
    return json.dumps(result)

@app.route('/test')
def test():
    return  str([sae.const.MYSQL_DB,sae.const.MYSQL_USER,sae.const.MYSQL_PASS,sae.const.MYSQL_HOST,sae.const.MYSQL_PORT])
 
@app.route('/task/failure')
def TaskFailure():
    print 'run task failue'
    return 'run task failue'

@app.route('/task/validateproxy', methods=['GET', 'POST'])
def ValidateProxy():
    if request.method == 'POST':
        for strdata in request.form:
            print 'data', strdata
            address = strdata.split(':')[0]
            port = strdata.split(':')[1]
            print 'validate proxy',address,port
            pf = ProxyFactory()
            ret = pf.ValidateProxy(address, port)
            print 'ret is', ret
            return ret
    return "Error"

@app.route('/task/queuelen')
def QueueLen():
    queuelen = TaskQueue('ValidateProxyTaskQueue').size()
    return str(queuelen)

@app.route('/removeproxy')
def RemoveInvaildProxy():
    pf = ProxyFactory()
    pf.QueryAllProxy()
    return 'OK'

@app.route('/task/removeproxy', methods=['POST'])
def RemoveInvaildProxyTask():
    for strdata in request.form:
        proxyUrlList = json.loads(strdata)
        for proxyUrl in proxyUrlList:
            print 'remove data', proxyUrl
            pf = ProxyFactory()
            ret = pf.RemoveProxy(proxyUrl)
            print 'Remove proxy {0} result is {1}'.format(proxyUrl, ret)
    return "OK"

if __name__ == '__main__':
    app.run(debug=True)