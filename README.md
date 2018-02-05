# Introduction

Toni Moreno's SNMP Collector is an excellent tool focused on polling devices via SNMP, and recording the resulting data in InfluxDB.

More info on SNMP Collector is here:  https://github.com/toni-moreno/snmpcollector

More info on InfluxDB is here:  https://www.influxdata.com/

# mib2SnmpCol

mib2SnmpCol is a basic Python3 script that parses an SNMP MIB, or part of a MIB tree, and adds all metrics it finds within to SNMP Collector.  It also adds "Influx Measurement" groups for the metrics it finds, corresponding to the table they come from, or just the immediate SNMP parenet element in the case of scalar values.


# snmpColConn

The snmpColConn.py file implements a Python class which can be used to interact with SNMP Collector via its REST API.

This file can be used independently with any Python project that wishes to interact with SNMP Collector.  In this instance it is used by mib2SnmpCol.py, which gives a good example of how it can be used.


## Dependencies

I can't pretend that this code is very elegent.  Instead of doing everything within the confines of Python it spawns an external call to 'mib2c'.  This is part of the NET-SNMP project and can be used to iterate over MIB definitions, outputing text or code based on the contents of a supplied conf file.

To install the dependencies on a debian-based system you can run:

    sudo apt-get install snmp libsnmp-dev
    

You can run 'mib2c' in a shell afterwards to verify the command has been installed.

## MIBs

MIB files need to be installed on the local system so that the NET-SNMP tools and libraries can find them.  This process can vary depending on the operating system you are using.  A brief guide on Debian would be as follows:

1.  Download required MIB files to /usr/share/mibs/$some_subfolder

2.  Add a line to /etc/snmp/snmp.conf as follows to tell it to search this subfolder for MIB files:

        mibdirs +/usr/share/mibs/$some_subfolder
    
3.  For each of the MIB files inside that folder add another line to /etc/snmp/snmp.conf as follows:

        mibs +MIB-NAME-1
        mibs +MIB-NAME-2
        mibs +MIB-NAME-3
        
If your MIB files have ".txt" or ".my" extensions do not include that part in snmp.conf.  Just include the file (MIB) name without the extenstion.
    

So for instance if I had added MIBs for 'OpenBSD' I might end up with something like this in /etc/snmp/snmp.conf:

    mibdirs +/usr/share/mibs/openbsd
    mibs +OPENBSD-BASE-MIB
    mibs +OPENBSD-PF-MIB
    
    
If I have sucessfully added the MIBs to my system I should be able to verify with the 'snmptranslate' tool.  For instance:

    topranks@pc:~/$ snmptranslate -On OPENBSD-BASE-MIB::openBSD
    .1.3.6.1.4.1.30155


mib2SnmpCol will only be able to add SNMP elements that are found in the local systems MIB tree and can be iterated over with mib2c.


## Usage & Arguments

mib2SnmpCol can be run using python3 only.  From the command line it takes several arguments:

|Argument|Type|Default|Required|Description|
|---------|----|-------|----------|----------|
|-s|Argument||Yes|Hostname or IP of the SNMP Collector instnace.|
|-t|Argument|8090|No|TCP Port the SNMP Collector is running on.|
|-u|Argument||Yes|Username with rights to use SNMP Collector HTTP interface.|
|-p|Argument||Yes|Password for username|
|-o|Argument||Yes|OID of MIB tree location to begin parsing|
|-m|Switch|No|No|If added will prefix the SNMP 'module' to measurement names.|



A typical example would be like this:

    python3 mib2SnmpCol.py -o OPENBSD-PF-MIB::pfCounters -s 192.168.240.82 -u admin -p password
    
    
Provided everything goes ok you should it begin to add elements as follows:
```
topranks@pc:~/mib2SnmpCol$ python3 mib2SnmpCol.py -o OPENBSD-BASE-MIB::pfMIBObjects -s 192.168.240.82 -u admin -p admin
Adding Influx Measurement pfLabelTable...
   Metric pfLabelEvals added OK.
   Metric pfLabelOutPkts added OK.
   Metric pfLabelName added OK.
   Metric pfLabelOutBytes added OK.
   Metric pfLabelInBytes added OK.
   Metric pfLabelInPkts added OK.
   Metric pfLabelPkts added OK.
   Metric pfLabelIndex added OK.
   Metric pfLabelTotalStates added OK.
   Metric pfLabelBytes added OK.
pfLabelTable measurement added.

Adding Influx Measurement pfTblTable...
   Metric pfTblStatsCleared added OK.
   Metric pfTblInPassBytes added OK.
   Metric pfTblOutMatchPkts added OK.
   Metric pfTblOutXPassPkts added OK.
```
(output cut).


## Issues / Improvements

The code is far from perfect.  Especially when it comes to SNMP Tables some shortcuts are taken which may not always work.

- The system assumes that the element at .1 under the Table OID is the Index for the table.  It will add this as the 'IndexOID' in the Influx Measurement definition.

- If the element at .2 under a Table OID is of type OCTETSTRING then it will automatically set 'IsTag' to true for the corresponding SNMP Metric.  This generally helps, as often the element at this location is an interface name, description etc.  However it may not always be the case, so some manual validation could be required afterwards.
