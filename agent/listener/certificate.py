import cffi
from OpenSSL import crypto
import socket
import os
import time
import appdirs
import packaging
import packaging.version
import packaging.specifiers
import packaging.requirements

def remove_empty_file(file):
    if os.path.exists(file):
        if os.stat(file).st_size == 0:
            os.remove(file)
            return True
    return False

def create_self_signed_cert(cert_dir, cert_file, key_file):
    
    # Cert files
    target_cert = os.path.join(cert_dir, cert_file)
    target_key = os.path.join(cert_dir, key_file)

    # Verify cert files are not "empty"
    remove_empty_file(target_cert)
    remove_empty_file(target_key)

    # Create cert if it does not exist
    if not os.path.exists(target_cert) or not os.path.exists(target_key):

        # Create a key pair
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 2048)

        # Create a self-signed cert
        cert = crypto.X509()
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

        open(target_cert, "w").write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        open(target_key, "w").write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))

    return target_cert, target_key