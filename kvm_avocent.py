#!/usr/bin/python

import bs4 as BeautifulSoup
import collections
import os
import os.path
import requests
import shutil
import subprocess
import sys
import time
import urlparse
import urllib3

if len(sys.argv) != 5:
    print("%s <user> <password> <ipmi address> <system>" % (sys.argv[0],))
    sys.exit(1)
user = sys.argv[1]
pswd = sys.argv[2]
host = sys.argv[3]
syst = sys.argv[4].lower()

# Silence SSL Certification warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def meta_redirect(content):
    soup  = BeautifulSoup.BeautifulSoup(content, 'html.parser')

    result=soup.find("meta",attrs={"http-equiv":"Refresh"})
    if result:
        wait,text=result["content"].split(";")
        if text.strip().lower().startswith("url="):
            url=text[4:]
            return url
    return None


# Start a requests Session to have persistent cookies
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:63.0) Gecko/20100101 Firefox/63.0',
                  'Accept-Language': 'en-US,en;q=0.5'})
s.verify = False

# Grab login page
s.get('https://%s/' % (host,))

# Login
data = collections.OrderedDict([('action', 'SAVE'), ('filename', 'login'), ('htmlLanguage', 0), ('id', '(NULL)'), ('index', '(NULL)'), ('loginPassword', pswd), ('loginUsername', user),
                                 ('saveParms', 'login'), ('spcDevice', '(NULL)'), ('spcInlet', '(NULL)'), ('spcSocket', '(NULL)'), ('userindex', '(NULL)')])
r = s.post('https://%s/cgi-bin/kvm.cgi?&file=login' % (host,), headers={'Referer': 'https://%s/cgi-bin/kvm.cgi?&file=login' % (host,)}, data=data)

# Verify we correctly authenticated
assert('User Login' not in r.text)

# Follow meta redirects until we have the main page on the device
while meta_redirect(r.text):
        r = s.get('https://%s%s' % (host, meta_redirect(r.text)), headers={'Referer': 'https://%s/cgi-bin/kvm.cgi?&file=login' % (host,)})

# Extract userid from url
userid = urlparse.parse_qs(urllib3.util.parse_url(r.url).query)['userid'][0]

# Parse our available hosts and their IDs
soup = BeautifulSoup.BeautifulSoup(r.text, 'html.parser')
devices = {}
i = 1
for item in soup.find(id='progressContent').find_all('table')[2].find('table').find_all('tr')[1:]:
  index = i
  i += 1

  name = item.find_all('span')[1].text
  devices[name.lower()] = {'idx': index,
                   'intf': item.find_all('span')[2].text,
                   'state': item.find_all('span')[3].text,
                   'device_url': item.find_all('a')[0].attrs.get('href', None),
                   'action_url': item.find_all('a')[1].attrs.get('href', None)}

# Bail if the system is not found
assert(syst in devices)

# Download viewer
r = s.get('https://%s/cgi-bin/kvm.cgi?&file=jnlp&userID=%s&index=%s' % (host, userid, devices[syst]['idx']), headers={'Referer': r.url})
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
data = collections.OrderedDict([('file', 'logout'), ('userID', userid)])
r = s.get('https://%s/cgi-bin/kvm.cgi' % (host,), headers={'Referer': r.url})
