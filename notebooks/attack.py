import requests

def update_vehicle_location(base_url, vehicle_id, lat, lon):
    url = f"{base_url}/update_vehicle_location"
    data = {
        "vehicle_id": vehicle_id,
        "lat": lat,
        "lon": lon
    }
    response = requests.post(url, data=data)
    print(response.json())

if __name__ == "__main__":
    # Replace with the actual URL of your Flask app if running on a different host or port
    base_url = "http://localhost:5000"

    # Chicago, IL coordinates
    chicago_lat = 41.8781
    chicago_lon = -87.6298

    # Update vehicles 1196 and 1604
    update_vehicle_location(base_url, "1196", chicago_lat, chicago_lon)
    update_vehicle_location(base_url, "1604", chicago_lat, chicago_lon)
