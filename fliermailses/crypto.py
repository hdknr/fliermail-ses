from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidSignature
from cryptography import x509
from cryptography.hazmat.backends import default_backend


def verify_signature(x509_pem, signing_input, signature):
    ''' PKCS V1.5 SHA1 '''
    try:
        public_key = import_pubkey_from_x509(x509_pem)
        public_key.verify(
            signature, signing_input, padding.PKCS1v15(), hashes.SHA1())
        return True
    except InvalidSignature:
        return False


def import_pubkey_from_x509(pem):
    cert = x509.load_pem_x509_certificate(pem, default_backend())
    return cert.public_key()
