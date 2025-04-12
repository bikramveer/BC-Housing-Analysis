import requests
import json
import math
import os

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

# Example
# place_name = "Vancouver, BC"
# lat, lon = get_lat_lon(place_name)
# lat = float(lat)
# lon = float(lon)
# if lat and lon:
#     print(f"Latitude: {lat}, Longitude: {lon}")
# else:
#     print(f"Could not get coordinates for {place_name}.")


def get_specific_amenities(lat, lon, radius=1000):
    # Overpass API query to find specific amenities within the radius
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # Overpass API query to find schools, transportation, convenience stores, grocery stores
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
    
    # Send request to Overpass API
    # node["amenity"="taxi"](around:{radius},{lat},{lon});
    #   node["amenity"="subway_station"](around:{radius},{lat},{lon});
    #   node["amenity"="railway_station"](around:{radius},{lat},{lon});
    # node["amenity"="fast_food"](around:{radius},{lat},{lon});
    response = requests.get(overpass_url, params={'data': query})
    
    if response.status_code == 200:
        data = response.json()
        
        # List of amenities 
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
    
def get_specific_amenities_cached(lat, lon, radius=3000):
    key = (round(lat, 4), round(lon, 4))

    if key in amenity_cache:
        return amenity_cache[key]
    
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # Overpass API query to find schools, transportation, convenience stores, grocery stores
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
        
        # List of amenities 
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
        
        amenity_cache[key] = amenities
        return amenities
    else:
        print(f"Error fetching amenities: {response.status_code}")
        return None

# Example 
# lat = 49.2827  # Lat for Vancouver
# lon = -123.1207  # Lon for Vancouver

# # Get specific amenities within 3 km (3000 meters) of the given coordinates
# amenities = get_specific_amenities(lat, lon, radius=3000)

# if amenities:
#     for amenity in amenities:
#         print(amenity)
# else:
#     print("No amenities found.")

# Haversine formula to calculate the distance between two points on the Earth
def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    # Radius of Earth in kilometers (can change to miles by using 3958.8)
    R = 6371.0
    
    # Distance in kilometers
    distance = R * c
    return distance


# Example of amenities data (list of amenities with their lat, lon, and name)
# amenities = [
#     {'name': 'Vancouver High School', 'latitude': 49.2835, 'longitude': -123.121},
#     {'name': 'Vancouver Bus Station', 'latitude': 49.2850, 'longitude': -123.118},
#     {'name': '7-Eleven Convenience Store', 'latitude': 49.2829, 'longitude': -123.122},
#     {'name': 'McDonalds', 'latitude': 49.2843, 'longitude': -123.120},
# ]

# Calculate distance to each amenity
# for amenity in amenities:
#     amenity_name = amenity['name']
#     amenity_lat = amenity['latitude']
#     amenity_lon = amenity['longitude']
    
#     # Get distance to the house using Haversine formula
#     distance = haversine(lat,lon, amenity_lat, amenity_lon)
    
#     print(f"Distance from house to {amenity_name}: {distance:.2f} km")
