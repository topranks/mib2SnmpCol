# Introduction

Toni Moreno's SNMP Collector is an excellent tool focused on polling devices via SNMP, and recording the resulting data in InfluxDB.

mib2SnmpCol is a basic Python3 tool that parses an SNMP MIB, or part of a MIB tree, and adds all metrics it finds within to SNMP Collector.  It also adds "Influx Measurement" groups for the metrics it finds, corresponding to the table they come from, or the immediate SNMP parent element in the case of scalar values.

It can be used on any part of a MIB tree / OID structure, from a single value or table right up to an entire MIB, automatically adding each element it finds.

SNMP Collector can be found here:  https://github.com/toni-moreno/snmpcollector

InfluxDB can be found here:  https://www.influxdata.com/


## snmpColConn

snmpColConn.py implements a Python class which can be used to interact with SNMP Collector via its REST API.

It provides the core functionality to talk to SNMP Collector that mib2SnmpCol.py uses.  snmpColConn.py can be used independently with any Python project that needs to interact with SNMP Collector.  mib2SnmpCol.py provides a good example of how it can be used.


# Instalation & Usage

## Dependencies

I can't pretend that this code is very elegent.  Instead of doing everything within the confines of Python it spawns an external call to 'mib2c'.  This is part of the NET-SNMP project and can be used to iterate over MIB definitions, outputing text or code based on the contents of a supplied conf file.

To install the dependencies on a debian-based system you can run:

    sudo apt-get install snmp libsnmp-dev libsnmp-perl
    

You can run 'mib2c' in a shell afterwards to verify the command is available.

## Download

Download the tool using git as follows:

    git clone --depth 1 https://github.com/topranks/mib2SnmpCol.git

Move into the newly created directory to use it:

    cd mib2SnmpCol


## Command-Line Arguments

mib2SnmpCol can be run using python3 only.  From the command line it takes several arguments:

|Argument|Name|Type|Default|Required|Description|
|---------|----|----|-------|----------|----------|
|-s|Server|Argument||Yes|Hostname or IP of the SNMP Collector instance.|
|-t|TCP Port|Argument|8090|No|Port the SNMP Collector instance is running on.|
|-u|Username|Argument||Yes|Username with rights to use SNMP Collector HTTP interface.|
|-p|Password|Argument||Yes|Password for username.|
|-o|OID|Argument||Yes|OID of MIB tree location to begin parsing.|
|-m|Module|Switch|No|No|Prefix measurement names with their SNMP 'module' name.|


## Usage

A typical example would be like this:

    python3 mib2SnmpCol.py -o OPENBSD-PF-MIB::pfCounters -s 192.168.240.82 -u admin -p password
    

Provided everything goes ok you should see output on the screen as it adds elements:
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


## MIBs

The tool can only add elements from MIBs that are correctly installed on the local system in advance.  

On a Debian-based system the standard IANA and IETF MIBs can be added as follows:

    sudo apt-get install snmp-mibs-downloader
    
#### Custom MIBs

Custom MIBs can also be added.  A brief example on Debian would be as follows:

1.  Download required MIB files to /usr/share/mibs/$some_subfolder

2.  Add a line to /etc/snmp/snmp.conf as follows, to tell the system to include this path when looking for MIBs:

        mibdirs +/usr/share/mibs/$some_subfolder
    
3.  For each of the MIB files inside that folder add another line to /etc/snmp/snmp.conf as follows:

        mibs +MIB-NAME-1
        mibs +MIB-NAME-2
        mibs +MIB-NAME-3
        
If your MIB files have ".txt" or ".my" extensions do not include that part in snmp.conf.  Just include the file (MIB) name without any extenstion.
    

So for instance if I had added MIBs for 'OpenBSD' I might end up with something like this in /etc/snmp/snmp.conf:

    mibdirs +/usr/share/mibs/openbsd
    mibs +OPENBSD-BASE-MIB
    mibs +OPENBSD-PF-MIB
    
    
If I have sucessfully added the MIBs to my system I should be able to verify with the 'snmptranslate' tool.  For instance:

    topranks@pc:~/$ snmptranslate -On OPENBSD-BASE-MIB::openBSD
    .1.3.6.1.4.1.30155


mib2SnmpCol can only add SNMP elements that the local system knows about, so make sure to check that 'snmptranslate' works for you beforehand.


## Issues / Improvements

The code is far from perfect.  Especially when it comes to SNMP Tables some shortcuts are taken which may not always work.

- The tool assumes that the element at .1 under the Table OID is the Index for the table.  It will add this as the 'IndexOID' in the Influx Measurement definition.

- If the element at .2 under a Table OID is of type OCTETSTRING then it will automatically set 'IsTag' to true for the corresponding SNMP Metric.  This generally helps, as often the element at this location is an interface name, description etc.  However it may not always be the case, so some manual validation could be required afterwards.

- All COUNTER metric types are configured to write "cooked" delta values to InfluxDB.  In other words "GetRate" is set to true for all counters.  A flag could be added to make this optional and record the absolute counter value instead.
