import sys
import os

sys.path.append(os.path.dirname(__file__) + '/..')

import certificate
import unittest
import tempfile
import time


class TestCertificate(unittest.TestCase):
    
    def setUp(self):
        self.setup_key_crt()
        self.delete_key_crt()

    def test_create_self_signed_certificate_existing_file(self):
        key = "%s/%s" % (self.testing_dir, self.testing_key)
        crt = "%s/%s" % (self.testing_dir, self.testing_crt)

        key_file = open(key, 'w')
        crt_file = open(crt, 'w')

        kc, cc = os.path.getmtime(key), os.path.getmtime(crt)

        certificate.create_self_signed_cert(self.testing_dir, self.testing_crt, self.testing_key)

        kcm, ccm = os.path.getmtime(key), os.path.getmtime(crt)

        self.assertEquals(kc, kcm, "File modified times do not match, they should.")
        self.assertEquals(cc, ccm, "File modified times do not match, they should.")

        key_file.close()
        crt_file.close()
    
    def test_create_self_signed_certificate_nonexisting_file(self):
        key = "%s/%s" % (self.testing_dir, self.testing_key)
        crt = "%s/%s" % (self.testing_dir, self.testing_crt)

        certificate.create_self_signed_cert(self.testing_dir, self.testing_crt, self.testing_key)

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