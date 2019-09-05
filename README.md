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

| Vendor     | Device       | Executable      | Notes                |
|------------|--------------|-----------------|----------------------|
| Avocent    | DSR Series   | kvm_avocent.py  | Tested on a DSR8032  |
| Cisco      | UCS C-Series | kvm_cimc.py     | Tested on a C22 M3   |
| Supermicro | x7 Series    | kvm_x7.py       | Tested on a SIMLP-3+ |
| Supermicro | x8 Series    | kvm_x8.py       | Incomplete           |
| Supermicro | x9 Series    | kvm_x9.py       | Planned              |
| Supermicro | x10 Series   | kvm_x10.py      | Planned              |
| StorageTek | L20/40/80    | status_stk.py   | Tested on a STK L40  |

Requirements
============

 1. Installed and working javaws and appletviewer binaries. Appletviewer
    is only needed for Supermicro x7 and StorageTek support.
 2. Python
