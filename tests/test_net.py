import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from multitool import main
from multitool.net import NetworkInfo, network_info


class NetTests(unittest.TestCase):
    def test_ipv4_network_info(self) -> None:
        self.assertEqual(
            network_info("192.0.2.42/24"),
            NetworkInfo(
                network="192.0.2.0",
                broadcast="192.0.2.255",
                netmask="255.255.255.0",
                first_host="192.0.2.1",
                last_host="192.0.2.254",
                host_count=254,
            ),
        )

    def test_ipv6_network_info(self) -> None:
        self.assertEqual(
            network_info("2001:db8::/126"),
            NetworkInfo(
                network="2001:db8::",
                broadcast="2001:db8::3",
                netmask="ffff:ffff:ffff:ffff:ffff:ffff:ffff:fffc",
                first_host="2001:db8::1",
                last_host="2001:db8::3",
                host_count=3,
            ),
        )

    def test_small_networks_follow_ipaddress_host_semantics(self) -> None:
        cases = (
            ("192.0.2.0/31", "192.0.2.0", "192.0.2.1", 2),
            ("192.0.2.1/32", "192.0.2.1", "192.0.2.1", 1),
            ("2001:db8::/127", "2001:db8::", "2001:db8::1", 2),
            ("2001:db8::1/128", "2001:db8::1", "2001:db8::1", 1),
        )

        for cidr, first_host, last_host, host_count in cases:
            with self.subTest(cidr=cidr):
                info = network_info(cidr)
                self.assertEqual(info.first_host, first_host)
                self.assertEqual(info.last_host, last_host)
                self.assertEqual(info.host_count, host_count)

    def test_ipv4_command(self) -> None:
        self.assertEqual(
            self.run_command("192.0.2.42/24"),
            "network: 192.0.2.0\n"
            "broadcast: 192.0.2.255\n"
            "netmask: 255.255.255.0\n"
            "first_host: 192.0.2.1\n"
            "last_host: 192.0.2.254\n"
            "host_count: 254\n",
        )

    def test_ipv6_command(self) -> None:
        self.assertEqual(
            self.run_command("2001:db8::/126"),
            "network: 2001:db8::\n"
            "broadcast: 2001:db8::3\n"
            "netmask: ffff:ffff:ffff:ffff:ffff:ffff:ffff:fffc\n"
            "first_host: 2001:db8::1\n"
            "last_host: 2001:db8::3\n"
            "host_count: 3\n",
        )

    def test_bad_input_exits_with_code_2(self) -> None:
        with patch.object(sys, "argv", ["mt", "net", "not-a-cidr"]):
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
                main()

        self.assertEqual(raised.exception.code, 2)

    def run_command(self, cidr: str) -> str:
        output = io.StringIO()

        with patch.object(sys, "argv", ["mt", "net", cidr]), redirect_stdout(output):
            main()

        return output.getvalue()
