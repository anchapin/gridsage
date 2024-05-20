import os
from flask import Flask, render_template
import folium
from pykml import parser
import random
import json
from shapely.geometry import Point, Polygon
import pandas as pd

app = Flask(__name__)

def load_projects_from_geojson(geojson_path):
    with open(geojson_path, 'r') as file:
        geojson = json.load(file)
    projects = []
    for feature in geojson['features']:
        if feature["geometry"] and feature["geometry"]["type"] == "Point":  # Ensure the feature has a geometry and is of type Point
            projects.append({
                "name": feature["properties"]["Property Name"],
                "location": [feature["geometry"]["coordinates"][1], feature["geometry"]["coordinates"][0]],  # latitude, longitude
                "csv_file": find_csv_file(feature["properties"]["Property Name"])
            })
    return projects

def find_csv_file(property_name, folder_path='hourly_profiles'):
    normalized_name = property_name.replace(" ", "_")
    for filename in os.listdir(folder_path):
        if filename.startswith(normalized_name) and filename.endswith('_Load_Profile.csv'):
            return os.path.join(folder_path, filename)
    return None

def calculate_peak_demand(csv_file):
    if csv_file:
        df = pd.read_csv(csv_file)
        if 'Modified Power Demand (kW)' in df.columns:
            return df['Modified Power Demand (kW)'].max()
    return 0

projects = load_projects_from_geojson('projects.geojson')

def kml_to_geojson(kml_path):
    with open(kml_path, 'rt', encoding='utf-8') as file:
        root = parser.parse(file).getroot()
    geojson = {"type": "FeatureCollection", "features": []}
    legend_info = []
    for placemark in root.findall('.//{http://www.opengis.net/kml/2.2}Placemark'):
        name = placemark.find('{http://www.opengis.net/kml/2.2}name').text
        geometry = placemark.find('.//{http://www.opengis.net/kml/2.2}Polygon')
        if geometry is not None:
            coords = geometry.find('.//{http://www.opengis.net/kml/2.2}coordinates').text.strip()
            coordinates = [[list(map(float, coord.split(',')))[:2] for coord in coords.split()]]
            polygon = Polygon(coordinates[0])
            color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
            peak_demand_sum = 0
            for project in projects:
                point = Point(project["location"][1], project["location"][0])  # Note: Point takes (longitude, latitude)
                if polygon.contains(point):
                    peak_demand_sum += calculate_peak_demand(project["csv_file"]) or 0
            feature = {
                "type": "Feature",
                "properties": {"name": name, "color": color, "peak_demand": peak_demand_sum},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": coordinates
                }
            }
            legend_info.append({"name": name, "color": color, "peak_demand": peak_demand_sum})
            geojson["features"].append(feature)
    return geojson, legend_info

@app.route('/')
def index():
    # Create a map centered around Boston
    m = folium.Map(location=[42.3601, -71.0589], zoom_start=13)

    # Convert KML to GeoJSON and get legend info
    geojson_data, legend_info = kml_to_geojson('Substations.kml')

    # Style function to apply unique colors to each polygon
    def style_function(feature):
        return {
            'fillColor': feature['properties']['color'],
            'color': feature['properties']['color'],
            'weight': 2,
            'fillOpacity': 0.5,
        }

    # Add GeoJSON layer to the map with the style function
    folium.GeoJson(geojson_data, name='geojson', style_function=style_function).add_to(m)

    # Add project locations (as example markers)
    for project in projects:
        folium.Marker(location=project["location"], popup=f'{project["name"]}: Peak demand added= {calculate_peak_demand(project["csv_file"])} kW').add_to(m)

    # Create a legend
    legend_html = '''
    <div style="position: fixed;
                bottom: 50px; left: 50px; width: 250px; height: auto;
                z-index:9999; font-size:14px;">
        <h4>Legend</h4>
        <div style="background:white; padding: 10px;">
    '''
    for item in legend_info:
        legend_html += f'''
        <i style="background:{item['color']};width:20px;height:20px;float:left;margin-right:8px;"></i>
        {item['name']} - Peak demand: {item['peak_demand']} kW<br>
        '''
    legend_html += '''
        </div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    # Save map to an HTML file
    m.save('templates/map.html')

    return render_template('map.html')

if __name__ == '__main__':
    app.run(debug=True)