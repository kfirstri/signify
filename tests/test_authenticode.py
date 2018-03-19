# This is a derivative, modified, work from the verify-sigs project.
# Please refer to the LICENSE file in the distribution for more
# information. Original filename: auth_data_test.py
#
# Parts of this file are licensed as follows:
#
# Copyright 2012 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import hashlib
import unittest
import pathlib

import binascii

import datetime

from pesigcheck.fingerprinter import AuthenticodeFingerprinter
from pesigcheck.signed_pe import SignedPEFile
from pesigcheck.authenticode import Certificate, trusted_certificate_store, VerificationContext, \
    AuthenticodeVerificationError, CertificateStore

root_dir = pathlib.Path(__file__).parent


class AuthenticodeParserTestCase(unittest.TestCase):
    def test_software_update(self):
        with open(str(root_dir / "test_data" / "SoftwareUpdate.exe"), "rb") as f:
            fingerprinter = AuthenticodeFingerprinter(f)
            fingerprinter.add_authenticode_hashers(hashlib.sha1)
            hashes = fingerprinter.hash()

            # Sanity check that the authenticode hash is still correct
            self.assertEqual(binascii.hexlify(hashes['sha1']).decode('ascii'),
                             '978b90ace99c764841d2dd17d278fac4149962a3')

            pefile = SignedPEFile(f)

            # This should not raise any errors.
            signed_datas = list(pefile.get_signed_datas())
            # There may be multiple of these, if the windows binary was signed multiple
            # times, e.g. by different entities. Each of them adds a complete SignedData
            # blob to the binary. For our sample, there is only one blob.
            self.assertEqual(len(signed_datas), 1)
            signed_data = signed_datas[0]

            self.assertEqual(signed_data._rest_data, b'\0')

            signed_data.verify()

    def test_pciide(self):
        with open(str(root_dir / "test_data" / "pciide.sys"), "rb") as f:
            pefile = SignedPEFile(f)
            signed_datas = list(pefile.get_signed_datas())
            self.assertEqual(len(signed_datas), 1)
            signed_data = signed_datas[0]
            signed_data.verify()


class CertificateTestCase(unittest.TestCase):
    def test_all_trusted_certificates_are_trusted(self):
        context = VerificationContext(trusted_certificate_store)
        for certificate in trusted_certificate_store:
            # Trust depends on the timestamp
            context.timestamp = certificate.valid_to
            self.assertListEqual(certificate.verify(context), [[certificate]])

    def test_all_trusted_certificates_are_only_trusted_within_their_validity(self):
        context = VerificationContext(trusted_certificate_store)
        for certificate in trusted_certificate_store:
            # Trust depends on the timestamp
            context.timestamp = certificate.valid_to + datetime.timedelta(seconds=1)
            self.assertRaises(AuthenticodeVerificationError, certificate.verify, context)
            context.timestamp = certificate.valid_from - datetime.timedelta(seconds=1)
            self.assertRaises(AuthenticodeVerificationError, certificate.verify, context)

    def test_trust_fails(self):
        # we get a certificate we currently trust
        certificate = list(trusted_certificate_store)[0]
        # we add it to an untrusted store
        store = CertificateStore()
        store.append(certificate)
        # and verify using this store
        context = VerificationContext(store)
        self.assertRaises(AuthenticodeVerificationError, certificate.verify, context)
