import ipaddress
from dataclasses import dataclass


@dataclass(frozen=True)
class NetworkInfo:
    network: str
    broadcast: str
    netmask: str
    first_host: str
    last_host: str
    host_count: int


def network_info(cidr: str) -> NetworkInfo:
    network = ipaddress.ip_network(cidr, strict=False)
    first_host = next(iter(network.hosts()))
    last_host = (
        network.broadcast_address - 1
        if network.version == 4 and network.num_addresses > 2
        else network.broadcast_address
    )

    return NetworkInfo(
        network=str(network.network_address),
        broadcast=str(network.broadcast_address),
        netmask=str(network.netmask),
        first_host=str(first_host),
        last_host=str(last_host),
        host_count=int(last_host) - int(first_host) + 1,
    )
