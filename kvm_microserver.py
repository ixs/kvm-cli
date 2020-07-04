#!/usr/bin/env python3

import collections
import os
import os.path
import requests
import shutil
import subprocess
import sys
import time
import simplexml
import urllib3

if len(sys.argv) != 4:
    print("%s <user> <password> <ipmi address>" % (sys.argv[0],))
    sys.exit(1)
user = sys.argv[1]
pswd = sys.argv[2]
host = sys.argv[3]

# Silence SSL Certification warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Start a requests Session to have persistent cookies
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:63.0) Gecko/20100101 Firefox/63.0',
                  'Accept-Language': 'en-US,en;q=0.5'})
s.verify = False

# Grab login page
s.get('https://%s/login.html' % (host,))

# Login
data = collections.OrderedDict([('user', user), ('password', pswd)])
r = s.post('https://%s/data/login' % (host,), headers={'Referer': 'https://%s/login.html' % (host,)}, data=data)
xml = simplexml.loads(r.text)

# Verify we correctly authenticated
assert int(xml['root']['authResult']) == 0

# Fetch the main menu
r = s.get('https://%s/%s' % (host, xml['root']['forwardUrl']), headers={'Referer': 'https://%s/login.html' % (host,)})

# Build viewer filename
host_ipv6 = 0
viewer_filename = 'viewer.jnlp(%s@%s@%i000)' % (host, host_ipv6, int(time.time()))

# Download viewer
r = s.post('https://%s/%s' % (host, viewer_filename), headers={'Referer': 'https://%s/%s' % (host, 'vkvm.html')})
with open('viewer.jnlp', 'w') as f:
  f.write(r.text)

# Verify we actually got some data
assert os.path.getsize('viewer.jnlp') > 0

# Write out temporary weak java security settings. Just to make sure we're not breaking on old KVM viewers
with open('java.security', 'w') as f:
  f.write('''jdk.certpath.disabledAlgorithms=
jdk.jar.disabledAlgorithms=
jdk.tls.disabledAlgorithms=
jdk.tls.legacyAlgorithms= \
        K_NULL, C_NULL, M_NULL, \
        DHE_DSS_EXPORT, DHE_RSA_EXPORT, DH_anon_EXPORT, DH_DSS_EXPORT, \
        DH_RSA_EXPORT, RSA_EXPORT, \
        DH_anon, ECDH_anon, \
        RC4_128, RC4_40, DES_CBC, DES40_CBC, \
        3DES_EDE_CBC''')

# Start javaws viewer
subprocess.call(['javaws', '-J-Djava.security.properties=java.security', '-wait', 'viewer.jnlp'])

# Remove our temporary files
os.remove('viewer.jnlp')
os.remove('java.security')

# Logout
r = s.get('https://%s/data/logout' % (host,), headers={'Referer': 'https://%s/%s' % (host, 'vkvm.html')})
