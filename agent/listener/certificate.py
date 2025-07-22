import os
import socket
import time
from datetime import datetime, timedelta

try:
    # Try to use the cryptography library (preferred)
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False
    # Fallback - use OpenSSL if available
    try:
        import cffi
        from OpenSSL import crypto
        HAS_OPENSSL = True
    except ImportError:
        HAS_OPENSSL = False

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
        
        if HAS_CRYPTOGRAPHY:
            # Use the modern cryptography library
            _create_cert_with_cryptography(target_cert, target_key)
        elif HAS_OPENSSL:
            # Fallback to pyOpenSSL
            _create_cert_with_openssl(target_cert, target_key)
        else:
            raise ImportError("Neither cryptography nor pyOpenSSL libraries are available for certificate generation")

    return target_cert, target_key

def _create_cert_with_cryptography(target_cert, target_key):
    """Create self-signed certificate using the cryptography library"""
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # Create certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Minnesota"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "St. Paul"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Nagios Enterprises, LLC"),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Development"),
        x509.NameAttribute(NameOID.COMMON_NAME, socket.gethostname()),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        int(time.time())
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=3650)  # 10 years
    ).sign(private_key, hashes.SHA256())
    
    # Write certificate
    with open(target_cert, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    
    # Write private key
    with open(target_key, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))

def _create_cert_with_openssl(target_cert, target_key):
    """Create self-signed certificate using pyOpenSSL (fallback)"""
    
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

    # Write certificate
    with open(target_cert, "wb") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

    # Write private key
    with open(target_key, "wb") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))