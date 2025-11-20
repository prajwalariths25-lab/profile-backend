from typing import Any, Dict

import requests

GEO_ENDPOINT = 'https://ipapi.co/{ip}/json/'


def fetch_geo_details(ip_address: str) -> Dict[str, Any]:
    """
    Look up approximate geo information for the provided IP using ipapi.co.
    Localhost IPs return an empty payload.
    """

    if not ip_address or ip_address in {'127.0.0.1', '::1'}:
        return {}

    try:
        response = requests.get(GEO_ENDPOINT.format(ip=ip_address), timeout=5)
        response.raise_for_status()
    except requests.RequestException:
        return {}

    payload = response.json()
    return {
        'city': payload.get('city'),
        'region': payload.get('region'),
        'country': payload.get('country_name') or payload.get('country'),
        'postal': payload.get('postal'),
        'latitude': payload.get('latitude'),
        'longitude': payload.get('longitude'),
    }

