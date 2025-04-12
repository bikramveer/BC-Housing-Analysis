import requests
import json
import math
import os
from functools import lru_cache
import numpy as np

CACHE_FILE = 'amenity_cache.json'

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'r') as file:
        raw = json.load(file)
        amenity_cache = {eval(k): v for k, v in raw.items()}
else:
    amenity_cache = {}

def save_cache():
    with open(CACHE_FILE, 'w') as f:
        json.dump({str(k): v for k, v in amenity_cache.items()}, f)

# if we didn't have latitudes and longitudes, we could use general area names (eg. 'Vancouver, BC')
# to get the lat and lon of that area for the other functions in this document
def get_lat_lon(place_name):
    # URL encode the place name to handle spaces and special characters
    from urllib.parse import quote
    encoded_place_name = quote(place_name)

    # Construct the Nominatim URL with the encoded place name
    url = f'https://nominatim.openstreetmap.org/search?q={encoded_place_name}&format=json'
    
    # a custom User-Agent header for Nominatim's usage policy
    headers = {
        'User-Agent': 'ConvertToLatLonProject' 
    }
    
    # Send the request with the headers
    response = requests.get(url, headers=headers)
    
    # Check if the response is valid and contains results
    if response.status_code == 200:
        data = response.json()
        if data:
            lat = data[0]['lat']
            lon = data[0]['lon']
            return lat, lon
        else:
            print(f"No data found for {place_name}.")
            return None, None
    else:
        print(f"Error: Received status code {response.status_code}.")
        return None, None
    
def get_specific_amenities_uncached(lat, lon, radius=3000):
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    query = f"""
    [out:json];
    (
      node["amenity"="school"](around:{radius},{lat},{lon});
      node["amenity"="university"](around:{radius},{lat},{lon});
      node["amenity"="bus_station"](around:{radius},{lat},{lon});
      node["shop"="convenience"](around:{radius},{lat},{lon});
      node["shop"="grocery"](around:{radius},{lat},{lon});
    );
    out body;
    """
    response = requests.get(overpass_url, params={'data': query})
    
    if response.status_code == 200:
        data = response.json()
        amenities = []
        
        for element in data['elements']:
            if 'tags' in element:
                amenity = {
                    'type': element.get('type'),
                    'id': element.get('id'),
                    'name': element['tags'].get('name', 'N/A'),
                    'amenity': element['tags'].get('amenity', 'N/A'),
                    'shop': element['tags'].get('shop', 'N/A'),
                    'latitude': element['lat'] if 'lat' in element else None,
                    'longitude': element['lon'] if 'lon' in element else None
                }
                amenities.append(amenity)
        
        return amenities
    else:
        print(f"Error fetching amenities: {response.status_code}")
        return None
    
@lru_cache(maxsize=10000)
def get_specific_amenities_cached(lat, lon, radius=3000):
    rounded_lat = round(lat, 4)
    rounded_lon = round(lon, 4)
    return get_specific_amenities_uncached(rounded_lat, rounded_lon, radius)

# Haversine formula to calculate the distance between two points on the Earth
def haversine(lat1, lon1, lat2, lon2):
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(np.array(lat2))
    lon2 = np.radians(np.array(lon2))
    
    #Haversine Formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))

    # Radius of earth (in km)
    R = 6371.0

    # Distance (in km)
    return R * c
