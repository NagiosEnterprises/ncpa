import os
import listener.certificate
import unittest
import tempfile
import time


class TestCertificate(unittest.TestCase):
    
    def setUp(self):
        self.setup_key_crt()
        self.delete_key_crt()

    # Tests if an existing file (that isn't empty) is not removed when the
    # cert and key are created
    def test_create_self_signed_certificate_existing_file(self):
        key = "%s/%s" % (self.testing_dir, self.testing_key)
        crt = "%s/%s" % (self.testing_dir, self.testing_crt)

        key_file = open(key, 'w').write("test key")
        crt_file = open(crt, 'w').write("test cert")

        kc, cc = os.path.getmtime(key), os.path.getmtime(crt)

        listener.certificate.create_self_signed_cert(self.testing_dir, self.testing_crt, self.testing_key)

        kcm, ccm = os.path.getmtime(key), os.path.getmtime(crt)

        self.assertEquals(kc, kcm, "Key file edited. File modified times do not match.")
        self.assertEquals(cc, ccm, "Cert file edited. File modified times do not match.")

    # Tests whether or not the empty .crt and .key file will be removed
    # and properly replaced with new cert files
    def test_create_self_signed_certificate_empty_file(self):
        key = "%s/%s" % (self.testing_dir, self.testing_key)
        crt = "%s/%s" % (self.testing_dir, self.testing_crt)

        key_file = open(key, 'w')
        crt_file = open(crt, 'w')

        kc, cc = os.path.getmtime(key), os.path.getmtime(crt)

        listener.certificate.create_self_signed_cert(self.testing_dir, self.testing_crt, self.testing_key)

        kcm, ccm = os.path.getmtime(key), os.path.getmtime(crt)

        self.assertNotEquals(kc, kcm, "Empty key file was not removed.")
        self.assertNotEquals(cc, ccm, "Empty cert file was not removed.")

        key_file.close()
        crt_file.close()
    
    def test_create_self_signed_certificate_nonexisting_file(self):
        key = "%s/%s" % (self.testing_dir, self.testing_key)
        crt = "%s/%s" % (self.testing_dir, self.testing_crt)

        listener.certificate.create_self_signed_cert(self.testing_dir, self.testing_crt, self.testing_key)

        self.assertTrue(os.path.isfile(key), "Key was not created.")
        self.assertTrue(os.path.isfile(crt), "Certificate was not created.")

    def setup_key_crt(self):
        testing_file_base = hash(time.time())
        self.testing_dir = tempfile.gettempdir()
        self.testing_key = "%s.key" % testing_file_base
        self.testing_crt = "%s.crt" % testing_file_base

    def delete_key_crt(self):
        key = "%s/%s" % (self.testing_dir, self.testing_key)
        crt = "%s/%s" % (self.testing_dir, self.testing_crt)

        try:
            os.unlink(key)
        except OSError:
            pass

        try:
            os.unlink(crt)
        except OSError:
            pass

    def tearDown(self):
        self.delete_key_crt()