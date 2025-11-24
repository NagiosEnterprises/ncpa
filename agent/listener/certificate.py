import os
import socket
import time
from datetime import datetime, timedelta
from ipaddress import IPv4Address

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
            # Final fallback - try to use system openssl command
            try:
                _create_cert_with_system_openssl(target_cert, target_key)
            except Exception as e:
                raise ImportError("Neither cryptography nor pyOpenSSL libraries are available, and system openssl command failed: %s" % str(e))

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
    ).add_extension(
        x509.KeyUsage(
            digital_signature=True,
            key_encipherment=True,
            key_agreement=False,
            key_cert_sign=False,
            crl_sign=False,
            content_commitment=False,
            data_encipherment=False,
            encipher_only=False,
            decipher_only=False,
        ),
        critical=True,
    ).add_extension(
        x509.ExtendedKeyUsage([
            x509.oid.ExtendedKeyUsageOID.SERVER_AUTH,
        ]),
        critical=True,
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName(socket.gethostname()),
            x509.DNSName("localhost"),
            x509.IPAddress(IPv4Address("127.0.0.1")),
        ]),
        critical=False,
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
    
    # Add extensions for Chromium compatibility
    cert.add_extensions([
        crypto.X509Extension(b"keyUsage", True, b"digitalSignature, keyEncipherment"),
        crypto.X509Extension(b"extendedKeyUsage", True, b"serverAuth"),
        crypto.X509Extension(b"subjectAltName", False, 
                           ("DNS:%s, DNS:localhost, IP:127.0.0.1" % socket.gethostname()).encode()),
    ])
    
    cert.sign(k, 'sha256')

    # Write certificate
    with open(target_cert, "wb") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

    # Write private key
    with open(target_key, "wb") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))


def _create_cert_with_system_openssl(target_cert, target_key):
    """Create self-signed certificate using system openssl command (final fallback)"""
    import subprocess
    import tempfile
    
    # Create a temporary config file for OpenSSL
    config_content = """[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = Minnesota
L = St. Paul
O = Nagios Enterprises, LLC
OU = Development
CN = %s

[v3_req]
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = critical, serverAuth
subjectAltName = DNS:%s, DNS:localhost, IP:127.0.0.1
""" % (socket.gethostname(), socket.gethostname())
    
    try:
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as config_file:
            config_file.write(config_content)
            config_path = config_file.name
        
        # Generate private key and certificate using system openssl
        cmd = [
            'openssl', 'req', '-new', '-x509', '-days', '3650',
            '-nodes', '-out', target_cert, '-keyout', target_key,
            '-config', config_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Clean up temp file
        os.unlink(config_path)
        
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        # Clean up temp file if it exists
        try:
            os.unlink(config_path)
        except:
            pass
        raise Exception("System openssl command failed: %s" % str(e))