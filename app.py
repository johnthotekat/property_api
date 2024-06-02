from datetime import datetime

from flask import Flask, request, jsonify
import json
import xml.etree.ElementTree as ET
import sqlite3
import requests

app = Flask(__name__)


# Function to create a database connection
def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        print(e)
    return conn


# Function to create table
def create_table(conn, table_name, columns):
    """ create a table from the columns dictionary """
    columns_def = ", ".join([f"{col} TEXT" for col in columns])
    create_table_sql = f"""CREATE TABLE IF NOT EXISTS {table_name} ({columns_def});"""
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except sqlite3.Error as e:
        print(e)


# Function to insert data into table
def insert_data(conn, table_name, columns, values):
    """ insert data into table """
    columns_str = ", ".join(columns)
    placeholders = ", ".join(["?" for _ in values])
    insert_sql = f"""INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders});"""
    try:
        c = conn.cursor()
        c.execute(insert_sql, values)
        conn.commit()
    except sqlite3.Error as e:
        print(e)


# Main function to parse XML and insert into database
def parse_xml_to_db(xml_content, db_file, table_name):
    # Parse the XML content
    root = ET.fromstring(xml_content)

    # Get all properties
    properties = root.findall("property")

    try:
        if properties:
            # Extract column names (element tags) from the first property
            columns = [elem.tag for elem in properties[0] if
                       elem.tag != 'Features' and elem.tag != 'Images' and elem.tag != 'geopoints']
            # Add Features, Images, Longitude, and Latitude columns separately
            columns += ['Features', 'Images', 'Longitude', 'Latitude']

            # Create a database connection
            conn = create_connection(db_file)

            if conn:
                # Create table
                create_table(conn, table_name, columns)

                # Iterate over each property and insert into the database
                for prop in properties:
                    values = []
                    for col in columns:
                        if col == 'Features':
                            features_elem = prop.find('Features')
                            features = [feature.text for feature in features_elem] if features_elem is not None else []
                            values.append(", ".join(features))
                        elif col == 'Images':
                            images_elem = prop.find('Images')
                            images = [image.text for image in images_elem] if images_elem is not None else []
                            values.append(", ".join(images))
                        elif col == 'Longitude':
                            longitude_elem = prop.find('geopoints/Longitude')
                            values.append(longitude_elem.text if longitude_elem is not None else None)
                        elif col == 'Latitude':
                            latitude_elem = prop.find('geopoints/Latitude')
                            values.append(latitude_elem.text if latitude_elem is not None else None)
                        else:
                            elem = prop.find(col)
                            values.append(elem.text if elem is not None else None)

                    insert_data(conn, table_name, columns, values)

                conn.close()
            else:
                print("Error! Cannot create the database connection.")
        else:
            print("No properties found in the XML file.")
    except Exception as e:
        raise e


# Function to parse XML to JSON
def parse_xml_to_json(xml_content):
    # Parse the XML content
    root = ET.fromstring(xml_content)

    properties_list = []

    # Get all properties
    properties = root.findall("property")

    for prop in properties:
        property_dict = {}
        for elem in prop:
            if elem.tag == 'Features':
                property_dict['Features'] = [feature.text for feature in elem]
            elif elem.tag == 'Images':
                property_dict['Images'] = [image.text for image in elem]
            elif elem.tag == 'geopoints':
                property_dict['Longitude'] = elem.find('Longitude').text
                property_dict['Latitude'] = elem.find('Latitude').text
            else:
                property_dict[elem.tag] = elem.text
        properties_list.append(property_dict)

    return json.dumps(properties_list, indent=4)


@app.route('/xml-to-json', methods=['POST'])
def xml_to_json():
    if 'xml' not in request.values:
        return jsonify({"error": "No XML path provided"}), 400

    xml_path = request.values['xml']
    xml_content = requests.get(xml_path).content
    json_data = parse_xml_to_json(xml_content)

    return jsonify(json.loads(json_data))


@app.route('/xml-to-db', methods=['POST'])
def xml_to_db():
    if 'xml' not in request.values:
        return jsonify({"error": "No XML path provided. Include 'post' in your request !"}), 400

    xml_path = request.values['xml']
    xml_content = requests.get(xml_path).content

    db_file = f"properties_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"  # You can make this configurable
    table_name = "properties"  # You can make this configurable

    try:
        parse_xml_to_db(xml_content, db_file, table_name)
        return jsonify({"message": "Sync completed from XML to database"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/get-properties', methods=['GET'])
def get_properties():
    db_file = "properties.db"
    table_name = "properties"

    conn = create_connection(db_file)
    if not conn:
        return jsonify({"error": "Cannot connect to database"}), 500

    try:
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM {table_name}")
        rows = cur.fetchall()

        columns = [description[0] for description in cur.description]
        properties = [dict(zip(columns, row)) for row in rows]

        return jsonify(properties), 200
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


if __name__ == '__main__':
    app.run(debug=True)
