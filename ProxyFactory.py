#coding=utf-8 

from bs4 import BeautifulSoup
import urllib2
import os
import requests
import MySQLdb
import sae.const
import logging
from sae.taskqueue import add_task
from flask import request
import json

def getres(reslist):
    return reslist[1]+':'+str(reslist[2])

class ProxyFactory:

    def FetchProxies(self):
        print 'start to fetch html page'
        user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'  
        headers = { 'User-Agent' : user_agent }
        req = urllib2.Request('http://www.xicidaili.com/wn/', headers=headers)  
        response = urllib2.urlopen(req)
        html = response.read()
        #print html
        print 'start to analysis html page'
        soup = BeautifulSoup(html, 'html5lib')
        tbody = soup.find_all('tbody')
        proxylistitems = tbody[0].find_all('tr')
        proxies = []
        
        print 'start to validate proxys, count is',len(proxylistitems)
        for proxylistitem in proxylistitems:
            itemtexts = proxylistitem.find_all('td')
            if len(itemtexts) < 4:
                continue
            address = itemtexts[2].string.strip()
            port = itemtexts[3].string.strip()
            postdata = '{0}:{1}'.format(address, port)
            add_task('ValidateProxyTaskQueue', 'http://1.fetchproxy.applinzi.com/task/validateproxy', postdata)
            proxies += [postdata]
        return proxies

    def CheckProxy(self, address, port):
        proxies = {
          "http": "{0}:{1}".format(address,port),
        }
        try:
            htmlpage = requests.get("http://www.baidu.com", proxies=proxies)
            return ('baidu' in htmlpage.text)
        except Exception, e:
            print(e)
            print("[Proxy {0}:{1}]: error".format(address,port))
            return False

    def ValidateProxy(self, address, port):
        if self.CheckProxy(address, port): 
            #连接
            conn=MySQLdb.connect(host=sae.const.MYSQL_HOST,user=sae.const.MYSQL_USER,passwd=sae.const.MYSQL_PASS,db=sae.const.MYSQL_DB,port=int(sae.const.MYSQL_PORT),charset="utf8")    
            cursor = conn.cursor() 
            cursor.execute("select * from app_proxys where proxy_url = %s and proxy_port = %s", (address, port))
            queryres = cursor.fetchone()
            print 'query db res',queryres
            if not bool(queryres):
                print 'insert into db',address,port
                sql = "insert into app_proxys(proxy_url,proxy_port) values(%s,%s)"     
                param = (address, port)
                insertres = cursor.execute(sql,param)
                print 'commit db res',insertres
            logging.info('validate ok, current proxy is %s:%s', address, port)
            return 'validate ok, current proxy is {0}:{1}'.format(address, port)
        else :
            print("[Proxy {0}:{1}]: wrong".format(address,port))
            return "[Proxy {0}:{1}]: wrong".format(address,port)

    def QueryAllProxy(self):
        conn=MySQLdb.connect(host=sae.const.MYSQL_HOST,user=sae.const.MYSQL_USER,passwd=sae.const.MYSQL_PASS,db=sae.const.MYSQL_DB,port=int(sae.const.MYSQL_PORT),charset="utf8")    
        cursor = conn.cursor() 
        cursor.execute("select * from app_proxys")
        queryret = cursor.fetchall()
        for i in range(0,len(queryret),10):
            b=queryret[i:i+10]
            c = map(getres, b)
            add_task('ValidateProxyTaskQueue', 'http://1.fetchproxy.applinzi.com/task/removeproxy', json.dumps(c))
        return len(queryret)

    def RemoveProxy(self, proxyUrl):
        address = proxyUrl.split(':')[0]
        port = proxyUrl.split(':')[1]
        if  not self.CheckProxy(address, port):
            conn=MySQLdb.connect(host=sae.const.MYSQL_HOST,user=sae.const.MYSQL_USER,passwd=sae.const.MYSQL_PASS,db=sae.const.MYSQL_DB,port=int(sae.const.MYSQL_PORT),charset="utf8")    
            cursor = conn.cursor()            
            try:
               # 执行SQL语句
               cursor.execute("delete from app_proxys where proxy_url = %s and proxy_port = %s", (address, port))
               # 向数据库提交
               conn.commit()
               return True
            except:
               # 发生错误时回滚
               conn.rollback() 
        return False

if __name__ == '__main__':
    
    pf = ProxyFactory()
    pf.FetchProxies()
