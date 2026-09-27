"""Tests for netsentry.network."""

import ipaddress
import unittest
from unittest import mock

from netsentry import network


class TestGetLocalIP(unittest.TestCase):
    def test_returns_string(self):
        with mock.patch("socket.socket") as sock_cls:
            sock_cls.return_value.getsockname.return_value = ("192.168.1.10", 0)
            self.assertEqual(network.get_local_ip(), "192.168.1.10")

    def test_raises_on_socket_error(self):
        with mock.patch("socket.socket") as sock_cls:
            sock_cls.return_value.connect.side_effect = OSError("no route")
            with self.assertRaises(ConnectionError):
                network.get_local_ip()


class TestGetNetwork(unittest.TestCase):
    def test_returns_ipv4network(self):
        net = network.get_network("192.168.1.10")
        self.assertIsInstance(net, ipaddress.IPv4Network)
        self.assertEqual(str(net), "192.168.1.0/24")

    def test_invalid_ip_raises(self):
        with self.assertRaises(ValueError):
            network.get_network("not-an-ip")

    def test_prefix_and_netmask(self):
        net = network.get_network("10.0.0.5")
        self.assertEqual(net.prefixlen, 24)
        self.assertEqual(str(net.netmask), "255.255.255.0")


class TestGetNetworkInfo(unittest.TestCase):
    def test_structure(self):
        info = network.get_network_info("192.168.1.42")
        for key in ("local_ip", "network", "netmask", "broadcast", "usable_hosts"):
            self.assertIn(key, info)
        self.assertEqual(info["local_ip"], "192.168.1.42")
        self.assertEqual(info["network"], "192.168.1.0/24")
        self.assertEqual(info["netmask"], "255.255.255.0")
        self.assertEqual(info["broadcast"], "192.168.1.255")
        self.assertEqual(info["usable_hosts"], 254)


if __name__ == "__main__":
    unittest.main()
