"""This script was pulled directly from 
http://skippylovesmalorie.wordpress.com/2010/02/12/how-to-generate-a-self-signed-certificate-using-pyopenssl/
All rights go to the writer of this script.
"""

import OpenSSL
import socket
import os
import time
import appdirs
import packaging
import packaging.version
import packaging.specifiers
import packaging.requirements


def create_self_signed_cert(cert_dir, cert_file, key_file):
    target_cert = os.path.join(cert_dir, cert_file)
    target_key = os.path.join(cert_dir, key_file)

    if not os.path.exists(target_cert) or not os.path.exists(target_key):
        # create a key pair
        k = OpenSSL.crypto.PKey()
        k.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)

        # create a self-signed cert
        cert = OpenSSL.crypto.X509()
        cert.get_subject().C = "US"
        cert.get_subject().ST = "Minnesota"
        cert.get_subject().L = "St. Paul"
        cert.get_subject().O = "Nagios Enterprises, LLC"
        cert.get_subject().OU = "Development"
        cert.get_subject().CN = socket.gethostname()
        
        sn = int(time.time())
        cert.set_serial_number(sn)
        
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(k)
        cert.sign(k, 'sha256')

        open(target_cert, "w").write(OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert))
        open(target_key, "w").write(OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, k))

    return target_cert, target_key