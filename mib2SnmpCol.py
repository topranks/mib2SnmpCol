#!/usr/bin/python3

# Rough & rugged conversion from NET-SNMP parsible MIB
# structure to snmpCollectoir "SNMP Metric" and "Influx
# Measurement" objects.

# Relies on system-installed NET-SNMP and mib2c libraries

import subprocess
import argparse
import sys
from snmpColConn import SnmpColConn

parser = argparse.ArgumentParser(description='SNMP Collector Device Adder')
parser.add_argument('-s', '--server', help ='IP or hostname of SNMPCollector Server', required=True)
parser.add_argument('-t', '--tcpport', help='TCP Port of SNMP Collector HTTP endpoint (default 8090)', type=int, default=8090)
parser.add_argument('-u', '--username', help='SNMP Collector web interface username', type=str, required=True)
parser.add_argument('-p', '--password', help='SNMP Collector web interface password', type=str, required=True)
parser.add_argument('-o', '--oid', help='SNMP OID, e.g. IF-MIB::interfaces', type=str, required=True)
parser.add_argument('--prefix_meas', help='Set to prefix influx measurement name with some string', type=str, default="")
parser.add_argument('--prefix_metric', help='Set to prefix influx field names with some string', type=str, default="")
parser.add_argument('--fixint', help='Render INT types as FLOAT conversions to avoid InfluxDB bug in v0.8 of SNMP Collector.', action='store_true')
parser.add_argument('--getrate', help='Set all COUNTER types to calculate deltas before pushing to InfluxDB (set getRate=True)', action='store_true')
parser.add_argument('--overwrite', help='Overwrite existing SNMP metrics, by default will skip', action='store_true')
args = parser.parse_args()

def main():

    # Get text output from mib2c of parsed Mib files:
    tableText=runMib2C("tables.conf", args.oid)
    scalarText=runMib2C("scalars.conf", args.oid)

    # Iterate over text to get structured dicts:
    tables=parseText(tableText)
    scalars=parseText(scalarText)

    # Create connection to the SNMP Collector server:
    snmpColConn=SnmpColConn(args.server, args.tcpport, args.username, args.password)
   
    for table in tables:
        addSnmpMeasurement(snmpColConn, str(table).replace('-', '_'), tables[table], True)
 
    for scalarGroup in scalars:
        addSnmpMeasurement(snmpColConn, str(scalarGroup).replace('-', '_'), scalars[scalarGroup], False)


def addSnmpMeasurement(snmpColConn, groupName, groupData, isTable):
    # Adds an Influx Measurement object to SNMP Collector
    print("Adding Influx Measurement {0}...".format(groupName))

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
    snmpColConn.add("measurement", measurementData, True)
    print("{0} measurement added OK.\n".format(groupName))


def addSnmpMetrics(snmpColConn, groupName, groupData, isTable):
    # Adds a series of SNMP Metrics to SNMP Collector, returns 
    # a list of the member names.
    groupMembers=[]
    splitOid=[]

    for metric in groupData:
        # Get normalised type field for element:
        metricType=normalizeElement(groupData[metric]['type'])
        # If the metric is one of the few types (like 'Opaque')
        # that SNMP Collector doesn't support just skip it:
        if(metricType)==None:
            continue

        # Record element name for addition to group later:
        groupMembers.append({"ID": metric, "Report": 1})

        oid=groupData[metric]['oid']
        getRate = (metricType=='COUNTERXX' and args.getrate)
        isInteger = not (metricType=='IpAddress' or metricType=='OID' or metricType=='OCTETSTRING')
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
            "GetRate": getRate,
            "Description": "",
            "BaseOID": oid,
            "Scale": 0,
            "Shift": 0
        }

        if args.fixint:
            metricData['conversion'] = 0
            metricData['Conversion'] = 0

        # Write the metric to SNMP Collector:
        returnCode = snmpColConn.add("metric", metricData, args.overwrite)
        if returnCode != 0:
            print("   Metric {0} ({1}) added OK.".format(metric, metricType.lower()))
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


def parseText(textData):
    output={}
    for line in textData.splitlines():
        lineData=line.split()

        if args.prefix_meas == "":
            parentName = lineData[0]
        else:
            parentName = args.prefix_meas + lineData[0][0].upper() + lineData[0][1:]
        if args.prefix_metric == "":
            entryName = lineData[1]
        else:
            entryName = args.prefix_metric + lineData[1][0].upper() + lineData[1][1:]

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
        return "COUNTERXX"
    elif(elementName=='ASN_COUNTER64'):
        return "COUNTERXX"
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
        

if __name__=="__main__":
    main()
