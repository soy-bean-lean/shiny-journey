import folium
import requests
from folium import DivIcon
from flask import Flask, render_template_string, request, jsonify
import math

app = Flask(__name__)

vehicles = []

def update_vehicle_location(vehicle_id, new_lat, new_lon):
    global vehicles
    for vehicle in vehicles:
        if vehicle['vehicle_id'] == vehicle_id:
            vehicle['location']['lat'] = new_lat
            vehicle['location']['lon'] = new_lon
            break

@app.route('/update_vehicle_location', methods=['POST'])
def set_vehicle_location():
    vehicle_id = request.form.get('vehicle_id')
    new_lat = float(request.form.get('lat'))
    new_lon = float(request.form.get('lon'))

    update_vehicle_location(vehicle_id, new_lat, new_lon)

    return jsonify({'status': 'success'}), 200

def get_weather_data():
    # Define the weather API endpoint and parameters
    API_KEY = "your-api-key-here"
    API_URL = f"https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": "Urbana,US",
        "appid": API_KEY,
        "units": "metric"
    }

    # Fetch the weather data from the API
    response = requests.get(API_URL, params=params)
    data = response.json()

    # Extract the relevant weather data
    temperature = data["main"]["temp"]
    humidity = data["main"]["humidity"]
    wind_speed = data["wind"]["speed"]
    wind_direction = data["wind"]["deg"]
    description = data["weather"][0]["description"]

    # Create a table to display the weather data
    table_html = f"""
        <table style="width: 250px;">
            <tr><td><b>Temperature:</b></td><td>{temperature} &deg;C</td></tr>
            <tr><td><b>Humidity:</b></td><td>{humidity}%</td></tr>
            <tr><td><b>Wind Speed:</b></td><td>{wind_speed} km/h</td></tr>
            <tr><td><b>Wind Direction:</b></td><td>{wind_direction} &deg;</td></tr>
            <tr><td><b>Description:</b></td><td>{description}</td></tr>
        </table>
    """
    return table_html

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = (math.sin(dLat / 2) * math.sin(dLat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dLon / 2) * math.sin(dLon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def is_congested(vehicle1, vehicle2, threshold):
    lat1 = vehicle1["location"]["lat"]
    lon1 = vehicle1["location"]["lon"]
    lat2 = vehicle2["location"]["lat"]
    lon2 = vehicle2["location"]["lon"]

    distance = haversine(lat1, lon1, lat2, lon2)
    return distance < threshold

def find_congested_routes(vehicles, threshold):
    congested_pairs = []
    for i, vehicle1 in enumerate(vehicles):
        for j, vehicle2 in enumerate(vehicles[i+1:], i+1):
            if is_congested(vehicle1, vehicle2, threshold):
                congested_pairs.append((vehicle1["vehicle_id"], vehicle2["vehicle_id"]))
    return congested_pairs

@app.route('/')
def display_map():
    # API key and endpoint
    API_KEY = "f6c7ea10acff485cac8372b013e7bd11"
    API_URL = f"https://developer.cumtd.com/api/v2.2/json/getvehicles?key={API_KEY}"

    # Fetch data from the API
    response = requests.get(API_URL)
    data = response.json()

    # Extract the vehicle locations
    global vehicles
    vehicles = data["vehicles"]

    # Latitude and longitude for Urbana, IL
    urbana_lat = 40.1106
    urbana_lon = -88.2073

    # Create a map centered at Urbana, IL
    m = folium.Map(location=[urbana_lat, urbana_lon], zoom_start=13)

    # Add the ESRI World Street Map tile layer
    esri_tile = folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
        attr='ESRI',
        name='ESRI World Street Map',
        overlay=False,
        control=True
    )
    esri_tile.add_to(m)

    # Detect congested routes
    congestion_threshold = 0.1  #in kilometers
    congested_pairs = find_congested_routes(vehicles, congestion_threshold)
    congested_vehicle_ids = set(sum(congested_pairs, ()))

    # Add markers for each vehicle location
    for vehicle in vehicles:
        lat = vehicle["location"]["lat"]
        lon = vehicle["location"]["lon"]
        popup_text = f"""
        <div style="width: 225px;">
            <b>Vehicle ID:</b> <i>{vehicle['vehicle_id']}</i><br>
            <b>Previous Stop ID:</b> <i>{vehicle['previous_stop_id']}</i><br>
            <b>Next Stop ID:</b> <i>{vehicle['next_stop_id']}</i><br>
            <b>Origin Stop ID:</b> <i>{vehicle['origin_stop_id']}</i><br>
            <b>Destination Stop ID:</b> <i>{vehicle['destination_stop_id']}</i><br>
            <b>Last Updated:</b> <i>{vehicle['last_updated']}</i>
        </div>
        """

        # Set the icon color based on the congestion status
        icon_color = "orange" if vehicle["vehicle_id"] in congested_vehicle_ids else "blue"
        bus_icon = DivIcon(
            icon_size=(20, 20),
            icon_anchor=(10, 10),
            html=f'<div style="font-size: 12pt; color: {icon_color};"><i class="fas fa-truck"></i></div>'
        )
        folium.Marker([lat, lon], popup=popup_text, icon=bus_icon).add_to(m)

    # Add the weather data as a floating table
    weather_html = get_weather_data()
    float_image = FloatImage(html=weather_html, bottom=50, left=50)
    float_image.add_to(m)

    # Save the map as an HTML string
    map_html = m.get_root().render()

    # Return the HTML string to the browser
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Vehicle Map</title>
            <script>
                function refreshMap() {
                    location.reload();
                }
                setInterval(refreshMap, 60000);
            </script>
        </head>
        <body>
            {{map_html|safe}}
        </body>
        </html>
    ''', map_html=map_html)

if __name__ == '__main__':
    app.run(debug=True)

