# mib2SnmpCol

mib2SnmpCol is a simple Python3 script that parses a MIB or part of a MIB tree and adds all OIDs within as SNMP Metrics in SNMP Collector.

For more information on the excellent SNMP Collector project please see its homepage:

https://github.com/toni-moreno/snmpcollector


## snmpColConn

The snmpColConn.py file implements a class which can be used to interact with SNMP Collector via its REST API.

This file can be used independently with any Python project that wishes to interact with SNMP Collector.  In this instance it is used by mib2SnmpCol.py, which gives a good example of how it can be used.


## Dependencies

I can't pretend that this effort is very elegent.  Instead of doing everything within the confines of Python the code makes an  external call to 'mib2c'.  This is part of the NET-SNMP project and can be used to parse a MIB tree that the system has installed and output text or code referencing the elements it finds.

To install on a debian-based system you can run:

    sudo apt-get install snmp libsnmp-dev
    

You can run 'mib2c' in a shell afterwards to verify the command has been installed.


## MIBs

MIB files need to be installed on the local system so that the NET-SNMP tools and libraries can find them.  This process can vary depending on the operating system you are using.  A brief guide on Debian would be as follows:

1.  Download required MIB files to /usr/share/mibs/$some_subfolder

2.  Add a line to /etc/snmp/snmp.conf as follows to tell it to search this subfolder for MIB files:

        mibdirs +/usr/share/mibs/$some_subfolder
    
3.  For each of the MIB files inside that folder you wish to include add another line to /etc/snmp/snmp.conf as follows:

        mibs +MIB-NAME-1
        mibs +MIB-NAME-2
        mibs +MIB-NAME-3
    

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

-
Argument|Type|Default|Required|Description
---------|----|-------|----------
-s|Argument||Yes|Hostname or IP of the SNMP Collector instnace.
-t|Argument|8090|No|TCP Port the SNMP Collector is running on.
-u|Argument||Yes|Username with rights to use SNMP Collector HTTP interface.


