kvm-cli
=======

Commandline interface to start IPMI/OOB KVM interfaces

Most serious servers nowadays come with baseboard management controllers
which offer not just standardized IPMI access via ipmitool or similar
programs but will also offer full KVM access.
KVM stands for Keyboard Video Mouse, not for Kernel Virtual Machine.

This allows one to administrate a remote server as if one is standing
right in front of it.

Unfortunately, nearly all these KVM systems are web based and use Java-
Applets or Java WebStart and sometimes use outdated protocols such as SSLv3.

This makes it difficult to use such systems with current browsers which have
much stricter defaults on TLS protocols etc.

To make things easier this repository contains a number of Python based
commandline programs that will log into the remote system, fetch the necessary
data and then fire off a local java process running the KVM client.


Supported systems
=================

| Vendor     | Device           | Executable            | Notes                                 |
|------------|------------------|-----------------------|---------------------------------------|
| Avocent    | DSR Series       | kvm_avocent.py        | Tested on a DSR8032                   |
| Cisco      | UCS C-Series     | kvm_cimc.py           | Tested on a C22 M3                    |
| HP         | Gen1 Microserver | kvm_microserver.py    | Tested on a N36L                      |
| Supermicro | x7 Series        | kvm_x7.py             | Tested on a SIMLP-3+                  |
| Supermicro | x8 Series        | kvm_x8.py             | Tested on a X8SIU                     |
| Supermicro | x9 Series        | kvm_x9.py             | Supported by x8, tested on a X9SCL-F  |
| Supermicro | x10 Series       | kvm_x10.py            | Supported by x8, tested on a X10SRL-F |
| Supermicro | x11 Series       | kvm_x11.py            | Supported by x8, no testing currently |
| StorageTek | L20/40/80        | status_stk.py         | Tested on a STK L40                   |


Requirements
============

 1. Python
 2. Installed and working javaws binary.
 3. For X7 and StorageTek support, the appletviewer and the socat binaries are needed.


Security Notes
==============

Under most circumstances it will be necessary to include the URLs/Hostnames of the IPMI interfaces
in the Java Security Exception list. Otherwise you'll see a warning about "Application blocked by
Java Security".

The Site Exception list can be accessed via the Java control panel in the system settings:
  Java Control Panel -> Security -> Exception Site List -> Edit Site List...

Under MacOS the file can be found at ~/Library/Application\ Support/Oracle/Java/Deployment/security/exception.sites
and edited easily.
Windows supposedly has the file at c:\Users\%username%\AppData\LocalLow\Sun\Java\Deployment\security\exception.sites
and Linux at ~/.java/deployment/security/exception.sites


Java Notes
==========

With the exception of the Supermicro X7 and the StorageTek applet, all KVMs are using the Java Webstart
method to download a Java program and then execute it on the local system.
Unfortunately JavaWS has been deprecated by Oracle in the Java8 release. Same for appletviewer it seems.
Free java releases such as AdoptOpenJDK did not include javaws. With the recent restrictive license changes
for Oracle Java, this is a problem.
There is a project at https://openwebstart.com that intends to ship a free replacement for javaws based on
IcedTea. Unfortunately it currently does not work on MacOS: https://github.com/karakun/OpenWebStart/issues/280

As such, it might be useful to keep a Java8 copy around. Download a copy from https://www.java.com/en/download/manual.jsp
but pay attention to the License, it seems Java8 is only free for personal use nowadays...
