"""Optional DNS-over-HTTPS resolver for DNS-level filtering."""

import ipaddress
import socket
import threading
import time

import requests


_ORIGINAL_GETADDRINFO = socket.getaddrinfo
_ACTIVE_RESOLVER = None
_INSTALL_LOCK = threading.Lock()
_HOOK_INSTALLED = False
_DOH_HOST = "cloudflare-dns.com"


class DNSOverHTTPS:
    endpoint = "https://cloudflare-dns.com/dns-query"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/dns-json"})
        self.cache = {}
        self.cache_lock = threading.Lock()

    def resolve(self, hostname):
        key = hostname.casefold().rstrip(".")
        now = time.monotonic()
        with self.cache_lock:
            cached = self.cache.get(key)
            if cached and cached[0] > now:
                return cached[1]

        addresses = []
        ttls = []
        for record_type in ("A", "AAAA"):
            response = self.session.get(
                self.endpoint,
                params={"name": key, "type": record_type},
                timeout=8,
            )
            response.raise_for_status()
            payload = response.json()
            if payload.get("Status") != 0:
                continue
            for answer in payload.get("Answer", []):
                value = answer.get("data", "").rstrip(".")
                try:
                    ipaddress.ip_address(value)
                except ValueError:
                    continue
                addresses.append(value)
                ttls.append(answer.get("TTL", 60))

        if not addresses:
            raise socket.gaierror(f"DoH could not resolve {hostname}")

        unique_addresses = tuple(dict.fromkeys(addresses))
        ttl = max(30, min(600, min(ttls) if ttls else 60))
        with self.cache_lock:
            self.cache[key] = (now + ttl, unique_addresses)
        return unique_addresses


def _getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    resolver = _ACTIVE_RESOLVER
    if resolver is None or host is None:
        return _ORIGINAL_GETADDRINFO(host, port, family, type, proto, flags)

    hostname = host.decode() if isinstance(host, bytes) else str(host)
    if hostname.casefold().rstrip(".") == _DOH_HOST:
        return _ORIGINAL_GETADDRINFO(host, port, family, type, proto, flags)
    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        return _ORIGINAL_GETADDRINFO(host, port, family, type, proto, flags)

    results = []
    for address in resolver.resolve(hostname):
        address_family = socket.AF_INET6 if ":" in address else socket.AF_INET
        if family not in (0, socket.AF_UNSPEC, address_family):
            continue
        results.extend(_ORIGINAL_GETADDRINFO(
            address,
            port,
            address_family,
            type,
            proto,
            flags | socket.AI_NUMERICHOST,
        ))
    if not results:
        raise socket.gaierror(f"No address family matched {hostname}")
    return results


def set_doh_enabled(enabled):
    """Route hostname lookups through Cloudflare DoH while enabled."""
    global _ACTIVE_RESOLVER, _HOOK_INSTALLED
    with _INSTALL_LOCK:
        if enabled:
            if not _HOOK_INSTALLED:
                socket.getaddrinfo = _getaddrinfo
                _HOOK_INSTALLED = True
            if _ACTIVE_RESOLVER is None:
                _ACTIVE_RESOLVER = DNSOverHTTPS()
        else:
            _ACTIVE_RESOLVER = None
