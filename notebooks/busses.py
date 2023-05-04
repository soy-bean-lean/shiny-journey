import folium
import requests
from folium import DivIcon
from flask import Flask, render_template_string
from flask import Flask, render_template_string, request, jsonify

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

app = Flask(__name__)

@app.route('/')
def display_map():
    # API key and endpoint
    API_KEY = "f6c7ea10acff485cac8372b013e7bd11"
    API_URL = f"https://developer.cumtd.com/api/v2.2/json/getvehicles?key={API_KEY}"

    # Fetch data from the API
    response = requests.get(API_URL)
    data = response.json()

    # Extract the vehicle locations
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
        bus_icon = DivIcon(
            icon_size=(20, 20),
            icon_anchor=(10, 10),
            html='<div style="font-size: 12pt; color: blue;"><i class="fas fa-truck"></i></div>'
        )
        folium.Marker([lat, lon], popup=popup_text, icon=bus_icon).add_to(m)

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
