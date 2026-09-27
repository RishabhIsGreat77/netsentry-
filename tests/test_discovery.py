"""Tests for netsentry.discovery — no real network access."""

import unittest
from unittest import mock

from netsentry import discovery


class TestDiscoverHosts(unittest.TestCase):
    def test_invalid_network_raises(self):
        with self.assertRaises(ValueError):
            discovery.discover_hosts("not-a-network")

    def test_empty_results_when_no_ports_open(self):
        with mock.patch.object(discovery, "_port_open", return_value=False):
            result = discovery.discover_hosts(
                "192.168.1.0/30",
                ports=[80],
                timeout=0.01,
            )
        self.assertEqual(result, [])

    def test_structure_of_discovered_device(self):
        def fake_port_open(ip, port, timeout):
            return ip == "192.168.1.1"

        with mock.patch.object(discovery, "_port_open", side_effect=fake_port_open):
            with mock.patch.object(
                discovery,
                "_resolve_hostname",
                return_value="router",
            ):
                result = discovery.discover_hosts(
                    "192.168.1.0/30",
                    ports=[80],
                    timeout=0.01,
                )

        self.assertEqual(len(result), 1)
        dev = result[0]
        self.assertEqual(dev["ip"], "192.168.1.1")
        self.assertEqual(dev["hostname"], "router")
        self.assertEqual(dev["status"], "online")

    def test_timeout_does_not_raise(self):
        with mock.patch.object(discovery, "_port_open", return_value=False):
            result = discovery.discover_hosts(
                "10.0.0.0/30",
                ports=[1, 2, 3],
                timeout=0.001,
            )
        self.assertIsInstance(result, list)


class TestResolveHostname(unittest.TestCase):
    def test_failure_returns_dash(self):
        with mock.patch("socket.gethostbyaddr", side_effect=OSError):
            self.assertEqual(discovery._resolve_hostname("10.0.0.1"), "-")


if __name__ == "__main__":
    unittest.main()
