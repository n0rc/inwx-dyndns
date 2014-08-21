# coding: utf-8
# (c)2014 n0rc
#
# This WSGI script can be used to update an existing A-record at InterNetworX (inwx) using a Fritz!Box
# to run a dyndns service with own domains. The script must be called by the Fritz!Box together with a
# specific key that identifies the A-record to be updated. Additionally, a TXT-record is updated with
# the timestamp of the last update.
#
# You must define your A- and TXT-records in 'dns_records' below. For each of your subdomains you must
# provide the following data:
# - key: the key to identify this record set, must be sent by the Fritz!Box 
# - a: the inwx id of the A-record
# - txt: the inwx id of the TXT-record
#
# To find the inwx ids of your A- and TXT-records, check the div ids "record_div_#########" in the dns
# record table at inwx.

from cgi import parse_qs, escape
from datetime import datetime
import re
import sys
import requests
import xmlrpclib

# subdomains to be used for dyndns
dns_records = {
    'subdomain1': {'key': '78af46762b5fc78e50d1d26e6dc70c044ad37f9ab8703d8a9f67ea1296a35ffc', 'a': 123456789, 'txt': 098765432},
    'subdomain2': {'key': '97d2fa1bedd46792ee4ae79cadfa881839c8aec8b0c46d3509caf5d11d56d5a7', 'a': 111111111, 'txt': 222222222},
}

# inwx login credentials
inwx_user = 'your_user'
inwx_pass = 'your_password'

# handles the dns record update process
def request(url, data, headers, mode):

    data = xmlrpclib.dumps(tuple([data]), mode)
    headers['Content-Length'] = str(len(data))

    resp = requests.post(url, data=data, headers=headers)
    respdata = resp.content 

    if headers['Cookie'] is None:
        headers['Cookie'] = resp.headers['set-cookie']

    ret = xmlrpclib.loads(resp.content)
    ret = ret[0][0]

    if (ret['code'] != 1000):
        raise NameError('There was a problem: %s (Error code %s)' % (ret['msg'], ret['code']), ret)

    return ret

# handles incoming update requests of a Fritz!Box
def application(environ, start_response):
    ua = environ['HTTP_USER_AGENT']
    d = parse_qs(environ['QUERY_STRING'])
    key = d.get('key', [''])[0]
    headers = [('Content-Type', 'text/plain')]
    ret = ''
    status = '403 Forbidden'

    # only allow fritzbox useragents
    if ua.startswith('Fritz!Box DDNS'):
        for where in dns_records:
            if key == dns_records[where]['key']:
                ip = environ['REMOTE_ADDR']
                url = 'https://api.domrobot.com/xmlrpc/'
                req_headers = {'Cookie': None, 'Content-Type': 'text/xml'}

                # login, then update A record and TXT record
                request(url, {'lang': 'en', 'user': inwx_user, 'pass': inwx_pass}, req_headers, 'account.login')
                request(url, {'id': dns_records[where]['a'], 'type': 'A', 'content': ip}, req_headers, 'nameserver.updateRecord')
                request(url, {'id': dns_records[where]['txt'], 'type': 'TXT', 'content': 'updated on %s' % datetime.now()}, req_headers, 'nameserver.updateRecord')

                status = '200 OK'
                ret = ip
                break

    start_response(status, headers)

    return [ret]
