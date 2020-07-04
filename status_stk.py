#!/usr/bin/env python3

import bs4 as BeautifulSoup
import collections
import os
import os.path
import requests
import shutil
import subprocess
import sys
import time
import urllib3

if len(sys.argv) != 2:
    print("%s <address>" % (sys.argv[0],))
    sys.exit(1)
host = sys.argv[1]

# Silence SSL Certification warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Start a requests Session to have persistent cookies
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:63.0) Gecko/20100101 Firefox/63.0',
                  'Accept-Language': 'en-US,en;q=0.5'})
s.verify = False

# Download the applet page
r = s.get('http://%s' % host)
# Verify we actually got some data
assert (len(r.text) > 0)
soup = BeautifulSoup.BeautifulSoup(r.text, 'html.parser')

orig_port = 5002
redir_port = 5002

with open('library_admin.html', 'w') as f:
#    f.write(soup.prettify())
     f.write('''
<HTML>
<HEAD>
<TITLE>Library Admin</TITLE>
</HEAD>
<BODY>
<APPLET  CODE = "libconnect.App.class" ARCHIVE = libconnect.jar WIDTH = 847 HEIGHT = 700 >
<PARAM NAME = type VALUE ="shipxafff">
</APPLET>
</BODY>
</HTML>
''')
jars = [x.strip() for x in soup('embed')[0]['java_archive'].replace(',', ' ').split()]
for jar in jars:
    r = s.get('http://%s/%s' % (host, jar))
    assert (len(r.text) > 0)
    with open(jar, 'w') as f:
        f.write(r.content)

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
with open('java.policy', 'w') as f:
  f.write('''grant {
   permission java.security.AllPermission;
};''')

# Start port redirection
redirect1 = subprocess.Popen(['socat', 'TCP-LISTEN:%s,fork,reuseaddr' % (5001,), 'TCP:%s:%s' % (host, 5001)])
redirect2 = subprocess.Popen(['socat', 'TCP-LISTEN:%s,fork,reuseaddr' % (5002,), 'TCP:%s:%s' % (host, 5002)])

# Start javaws viewer
subprocess.call(['appletviewer', '-J-Djava.security.properties=java.security', '-J-Djava.security.policy=java.policy', 'library_admin.html'])

# Stop port redirection
redirect1.kill()
redirect2.kill()

# Remove our temporary files
os.remove('library_admin.html')
os.remove('java.security')
os.remove('java.policy')
for jar in jars:
    os.remove(jar)
