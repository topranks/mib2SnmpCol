#!/usr/bin/python3

# Class to connect to SNMP Collector

import os
import requests
import json
import sys
import time

class SnmpColConn:

    def __init__(self, server, port, username, password):
        self.server=server
        self.port=port
        self.username=username
        self.password=password
        
        self.headers = {'Content-Type':'application/json'}

        self.connect()
        
    def connect(self):
        # Logs in to SNMP collector, returns request module 'cookies' object
        url="http://{0}:{1}/login".format(self.server, self.port)
        creds = {"username": self.username, "password": self.password}
        headers = {'Content-Type':'application/json'}

        r = requests.post(url, json=creds, headers=headers)
        if r.status_code == 200:
            self.cookies=r.cookies
        else:
            print("Error logging on to server, return code {0}\n".format(r.status_code))
            sys.exit(1)

    def add(self, elementType, data):
        # Check if the element already exists:
        itExists=self.exists(['ID'], elementType)

        # Add or ammend element [POST or PUT]:
        if(itExists):
            url="http://{0}:{1}/api/cfg/{2}/{3}".format(self.server, self.port, elementType, data['ID'])
            r = requests.put(url, json=data, headers=self.headers, cookies=self.cookies)
        else:
            url="http://{0}:{1}/api/cfg/{2}".format(self.server, self.port, elementType)
            r = requests.post(url, json=data, headers=self.headers, cookies=self.cookies)

        if(r.status_code==200):
            time.sleep(0.2)
        else:
            print("Somethng went wrong adding element {0}, status code: {1} .".format(data['ID'], r.status_code))
            print(r.json)
            print(r.text)
            sys.exit(1)


    def exists(self, elementName, elementType):
        url="http://{0}:{1}/api/cfg/{2}/{3}".format(self.server, self.port, elementType, elementName)
        r = requests.get(url, headers=self.headers, cookies=self.cookies)
        if r.status_code==200:
            return 1
        else:
            return 0


    def get(self, elementName, elementType):
        url="http://{0}:{1}/api/cfg/{2}/{3}".format(self.server, self.port, elementType, elementName)
        r = requests.get(url, headers=self.headers, cookies=self.cookies)
        if r.status_code==200:
            return r.text()
        else:
            return ""

                    
    def delete(self, elementName, elementType):
        url="http://{0}:{1}/api/cfg/{2}/{3}".format(self.server, self.port, elementType, elementName)
        r = requests.delete(url, headers=self.headers, cookies=self.cookies)
        return r.status_code

