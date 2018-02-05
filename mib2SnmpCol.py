#!/usr/bin/python3

# Rough & rugged conversion from NET-SNMP parsible MIB
# structure to snmpCollectoir "SNMP Metric" and "Influx
# Measurement" objects.

# Relies on system-installed NET-SNMP and mib2c libraries

import subprocess
import argparse
import sys
from snmpColConn import SnmpColConn

def begin():
    args=getArgs()

    # Get text output from mib2c of parsed Mib files:
    tableText=runMib2C("tables.conf", args.oid)
    scalarText=runMib2C("scalars.conf", args.oid)

    # Iterate over text to get structured dicts:
    tables=parseText(tableText, args.module)
    scalars=parseText(scalarText, args.module)

    # Create connection to the SNMP Collector server:
    snmpColConn=SnmpColConn(args.server, args.tcpport, args.username, args.password)
   
    for table in tables:
        addSnmpMeasurement(snmpColConn, table, tables[table], True)
 
    for scalarGroup in scalars:
        addSnmpMeasurement(snmpColConn, scalarGroup, scalars[scalarGroup], False)

def addSnmpMeasurement(snmpColConn, groupName, groupData, isTable):
    # Adds an Influx Measurement object to SNMP Collector

    # Add all the metrics to the DB:
    groupMembers, splitOid = addSnmpMetrics(snmpColConn, groupName, groupData, isTable)

    # Create our data object for the measurement:
    measurementData = {
        "ID": groupName,
        "Name": groupName,
        "GetMode": "value",
        "Fields": groupMembers,
        "Description": ""
    }

    # Add and modify data if the group is a table:
    if isTable:
        # Assume Index OID is at .1 in table tree:
        splitOid[-1]="1"
        del splitOid[0]
        indexOid=""
        for item in splitOid:
            indexOid += ".{0}".format(item)

        # Modify measurementData object:
        measurementData['GetMode']="indexed"
        measurementData['IndexOID']=indexOid
        measurementData['IndexTag']="snmpIndex"
        measurementData['IndexTagFormat']=""
        measurementData['IndexAsValue']=True

    # Create "Influx Measurement" in SNMPCollector for the group:
    print("Adding Influx Measurement {0}".format(measurement))
    snmpColConn.add("measurement", measurementData)


def addSnmpMetrics(snmpColConn, groupName, groupData, isTable):
    # Adds a series of SNMP Metrics to SNMP Collector, returns 
    # a list of the member names.
    groupMembers=[]
    splitOid=[]

    for metric in groupData:
        # Get normalised type field for element:
        metricType=normalizeElement(groupData[metric]['type'])
        # Record element name for addition to group later:
        groupMembers.append({"ID": metric, "Report": "1"})

        oid=groupData[metric]['oid']
        isCounter=(metricType=='COUNTER32' or metricType=='COUNTER64')
        isTag=False

        if isTable:
            # Then set elements at .1 and .2 as InfluxDB tags
            # Needs more robust logic
            splitOid=oid.split('.')
            if splitOid[-1]=="2":
                if metricType=="OCTETSTRING":
                    isTag=True
            elif splitOid[-1]=="1":
                isTag=True
        else:
            # It's a scalar, so we need to add .0 to oid for it in SNMPCollector:
            oid += ".0"

        metricData = {
            "ID": metric,
            "FieldName": metric,
            "DataSrcType": metricType,
            "IsTag": isTag,
            "GetRate": isCounter,
            "Description": "",
            "BaseOID": oid,
            "Scale": 0,
            "Shift": 0
        }

        # Write the metric to SNMP Collector:
        print("Adding SNMP Metric {0}".format(metric))
        snmpColConn.add("metric", metricData)
    return groupMembers, splitOid
        

def runMib2C(mib2c_conf_file, oid):
    # Run external 'mib2c' command to parse MIB tree tables to TXT file:
    command=subprocess.run(["mib2c", '-q', '-c', mib2c_conf_file, oid], stdout=subprocess.PIPE)
    # If it didn't run cleanly print error and quit:
    if(command.returncode != 0):
        print("Error running mib2c conf file {0} on {1}\n".format(mib2c_conf_file, oid))
        print(command.stdout.decode('utf-8') + "\n")
        sys.exit(command.returncode)
    else:
        return command.stdout.decode('utf-8')


def parseText(textData, appendMod):
    output={}
    for line in textData.splitlines():
        lineData=line.split()

        if appendMod: 
            parentName=lineData[4].replace("-MIB", "") + "_" + lineData[0]
        else:
            parentName=lineData[0]
        entryName=lineData[1]
        entryType=lineData[2]
        entryOID=lineData[3]

        if not parentName in output:
            output[parentName]={}

        output[parentName][entryName]={}
        output[parentName][entryName]['type']=entryType
        output[parentName][entryName]['oid']=entryOID
    return output


def normalizeElement(elementName):
    # Converts Object Type names from mib2c to SNMPCollector format
    if(elementName=='ASN_COUNTER'):
        return "COUNTER32"
    elif(elementName=='ASN_COUNTER64'):
        return "COUNTER64"
    elif(elementName=='ASN_GAUGE'):
        return "Gauge32"
    elif(elementName=='ASN_INTEGER'):
        return "Integer32"
    elif(elementName=='ASN_IPADDRESS'):
        return "IpAddress"
    elif(elementName=='ASN_OBJECT_ID'):
        return "OID"
    elif(elementName=='ASN_OCTET_STR'):
        return "OCTETSTRING"
    elif(elementName=='ASN_TIMETICKS'):
        return "TimeTicks"
    elif(elementName=='ASN_UNSIGNED'):
        return "Unsigned32"
        

def getArgs():
    parser = argparse.ArgumentParser(description='SNMP Collector Device Adder')
    parser.add_argument('-s', '--server', help ='IP or hostname of SNMPCollector Server', required=True)
    parser.add_argument('-t', '--tcpport', help='TCP Port of SNMP Collector HTTP endpoint (default 8090)', type=int, default=8090)
    parser.add_argument('-u', '--username', help='SNMP Collector web interface username', type=str, required=True)
    parser.add_argument('-p', '--password', help='SNMP Collector web interface password', type=str, required=True)
    parser.add_argument('-o', '--oid', help='SNMP OID, e.g. IF-MIB::interfaces', type=str, required=True)
    parser.add_argument('-m', '--module', help='Set to prefix influx measurement name with the mib module name', action='store_true')
    return parser.parse_args()


if __name__=="__main__":
    begin()
