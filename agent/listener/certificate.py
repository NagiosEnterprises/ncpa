import cffi
from OpenSSL import crypto
import socket
import os
import time

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

        try:
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
            
            # Use localhost as CN for better client compatibility
            hostname = socket.gethostname()
            cert.get_subject().CN = hostname

            sn = int(time.time())
            cert.set_serial_number(sn)

            cert.gmtime_adj_notBefore(0)
            cert.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)
            cert.set_issuer(cert.get_subject())
            cert.set_pubkey(k)
            
            # Add Subject Alternative Names for better client compatibility
            try:
                san_list = [
                    "DNS:localhost",
                    "DNS:" + hostname,
                    "IP:127.0.0.1",
                    "IP:::1"
                ]
                
                # Add local IP addresses
                import socket
                try:
                    local_ip = socket.gethostbyname(hostname)
                    if local_ip not in ["127.0.0.1"]:
                        san_list.append("IP:" + local_ip)
                except:
                    pass
                
                san_extension = crypto.X509Extension(
                    b"subjectAltName",
                    False,
                    ", ".join(san_list).encode('utf-8')
                )
                cert.add_extensions([san_extension])
            except Exception as e:
                # If SAN fails, continue without it
                print(f"Warning: Could not add Subject Alternative Names: {e}")
            
            cert.sign(k, 'sha256')

            # Write certificate file with proper error handling
            try:
                with open(target_cert, "wb") as cfh:
                    cfh.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
            except IOError as e:
                print(f"Error writing certificate file {target_cert}: {e}")
                raise

            # Write key file with proper error handling
            try:
                with open(target_key, "wb") as kfh:
                    kfh.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
                # Set restrictive permissions on private key
                os.chmod(target_key, 0o600)
            except IOError as e:
                print(f"Error writing key file {target_key}: {e}")
                raise

        except Exception as e:
            print(f"Error creating self-signed certificate: {e}")
            # Clean up partial files on error
            if os.path.exists(target_cert):
                os.remove(target_cert)
            if os.path.exists(target_key):
                os.remove(target_key)
            raise

    return target_cert, target_key