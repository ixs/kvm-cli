#!/usr/bin/python

import Crypto.Hash
import Crypto.Hash.HMAC
import Crypto.Hash.SHA512
import Crypto.Random
import Crypto.Cipher
import base64
import collections
import hashlib
import hmac
import os
import os.path
import requests
import shutil
import simplexml
import subprocess
import sys
import time
import urllib3

if len(sys.argv) != 4:
    print("%s <user> <password> <ipmi address>" % (sys.argv[0],))
    sys.exit(1)
user = sys.argv[1]
pswd = sys.argv[2]
host = sys.argv[3]

BLOCK_SIZE = 16

def keyFnv32(data):
    n = 40389
    for i in range(0, len(data) / 4):
        n = n ^ ord(data[i])
        n = n + (n << 1)
    return n


def hashFnv32(message, key):
    '''session id, url'''
    kmsg = str(keyFnv32(message))
    signed = hmac.new(kmsg, key, hashlib.sha512)
    return signed.hexdigest()


def bytes_to_key(data, salt, output=48):
    # extended from https://gist.github.com/gsakkis/4546068
    assert len(salt) == 8, len(salt)
    data += salt
    key = hashlib.md5(data).digest()
    final_key = key
    while len(final_key) < output:
        key = hashlib.md5(key + data).digest()
        final_key += key
    return final_key[:output]


def pad(data):
    length = BLOCK_SIZE - (len(data) % BLOCK_SIZE)
    return data + (chr(length)*length).encode()


def encrypt(message, passphrase):
    salt = Crypto.Random.new().read(8)
    key_iv = bytes_to_key(passphrase, salt, 32+16)
    key = key_iv[:32]
    iv = key_iv[32:]
    aes = Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_CBC, iv)
    return base64.b64encode(b"Salted__" + salt + aes.encrypt(pad(message)))

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
data = collections.OrderedDict([('user', user), ('password', encrypt(pswd, str(keyFnv32(user))))])
r = s.post('https://%s/data/login' % (host,), headers={'Referer': 'https://%s/login.html' % (host,)}, data=data)
xml = simplexml.loads(r.text)

# Verify we correctly authenticated
assert int(xml['root']['authResult']) == 0

# Fetch the main menu
r = s.get('https://%s/%s' % (host, xml['root']['forwardUrl']), headers={'Referer': 'https://%s/login.html' % (host,)})

# Build viewer filename
host_ipv6 = 0
viewer_filename = 'viewer.jnlp(%s@%s@%i000)' % (host, host_ipv6, int(time.time()))
cspg_key = hashFnv32(xml['root']['sidValue'], '/' + viewer_filename)
data = collections.OrderedDict([('sessionID', xml['root']['sidValue']), ('CSPG_VAR', cspg_key)])

# Download viewer
r = s.post('https://%s/%s' % (host, viewer_filename), data = data, headers={'Referer': 'https://%s/%s' % (host, xml['root']['forwardUrl'])})
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
#os.remove('viewer.jnlp')
os.remove('java.security')

# Logout
data = collections.OrderedDict([('sessionID', xml['root']['sidValue'])])
r = s.post('https://%s/data/logout' % (host,), data = data, headers={'Referer': 'https://%s/%s' % (host, xml['root']['forwardUrl'])})
