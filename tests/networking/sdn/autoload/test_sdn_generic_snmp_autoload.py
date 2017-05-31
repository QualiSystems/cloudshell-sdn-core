import unittest

from cloudshell.networking.sdn.autoload.sdn_generic_snmp_autoload import SDNGenericSNMPAutoload


class TestSDNGenericSNMPAutoload(unittest.TestCase):
    def setUp(self):
        self.autoload = SDNGenericSNMPAutoload()
