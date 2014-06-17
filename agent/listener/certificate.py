"""This script was pulled directly from 

http://skippylovesmalorie.wordpress.com/2010/02/12/how-to-generate-a-self-signed-certificate-using-pyopenssl/

All rights go to the writer of this script.
"""

from OpenSSL import crypto
from socket import gethostname
from os.path import exists, join

def create_self_signed_cert(cert_dir, cert_file, key_file):

    target_cert = join(cert_dir, cert_file)
    target_key = join(cert_dir, key_file)
    if not exists(target_cert) or not exists(target_key):
        
        # create a key pair
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 1024)

        # create a self-signed cert
        cert = crypto.X509()
        cert.get_subject().C = "US"
        cert.get_subject().ST = "Minnesota"
        cert.get_subject().L = "St. Paul"
        cert.get_subject().O = "Nagios LLC"
        cert.get_subject().OU = "Nagios LLC"
        cert.get_subject().CN = gethostname()
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(10*365*24*60*60)
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(k)
        cert.sign(k, 'sha1')

        open(target_cert, "wt").write(
            crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        open(target_key, "wt").write(
            crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
    return target_cert, target_key
