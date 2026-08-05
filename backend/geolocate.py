import requests
import functools

class IPThreatIntelligenceService:
    """
    IP Threat Intelligence & Geolocation Service
    Resolves attacker IP addresses to geographical coordinates, countries, cities,
    and ASN/ISP metadata while providing caching to prevent API rate limiting.
    """

    @staticmethod
    @functools.lru_cache(maxsize=1024)
    def lookup_ip(ip_address: str) -> dict:
        """
        Performs IP Geolocation and ISP/ASN Threat Lookup with LRU caching.
        """
        # Internal / Local Network Fallbacks
        if ip_address in ["127.0.0.1", "localhost", "::1"] or ip_address.startswith("192.168.") or ip_address.startswith("10."):
            return {
                "ip": ip_address,
                "country": "Local Network",
                "city": "Internal Node",
                "latitude": 0.0,
                "longitude": 0.0,
                "isp": "Private LAN",
                "asn": "AS0 Internal",
                "is_proxy": False
            }

        try:
            # Query free public IP Geolocation API
            res = requests.get(f"http://ip-api.com/json/{ip_address}?fields=status,country,city,lat,lon,isp,as,mobile,proxy", timeout=3)
            if res.status_code == 200:
                data = res.json()
                if data.get("status") == "success":
                    return {
                        "ip": ip_address,
                        "country": data.get("country", "Unknown"),
                        "city": data.get("city", "Unknown"),
                        "latitude": data.get("lat", 0.0),
                        "longitude": data.get("lon", 0.0),
                        "isp": data.get("isp", "Unknown ISP"),
                        "asn": data.get("as", "Unknown ASN"),
                        "is_proxy": data.get("proxy", False)
                    }
        except Exception as e:
            print(f"[-] IP Threat Lookup failed for {ip_address}: {e}")

        return {
            "ip": ip_address,
            "country": "Unknown",
            "city": "Unknown",
            "latitude": 0.0,
            "longitude": 0.0,
            "isp": "Unknown",
            "asn": "Unknown",
            "is_proxy": False
        }
