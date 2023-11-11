# Color Insert Script Generator || CISG
import logging
import psycopg2
import os
import argparse
from color_names import color_names, parent_colors
from color_utis import hex_to_rgb, hex_to_lab, hex_to_cmyk, closest_color_in_space

logging.basicConfig(level=logging.INFO)
# Function to establish a connection with the PostgreSQL database
def connect_to_db():
    try:
        connection = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        return connection
    except Exception as error:
        logging.error(f"Error while connecting to PostgreSQL: {error}")
        exit(1)

def insert_parent_color_sql_command(color_info, color_space, parent_id):  # Added parent_id argument
    hex, name = color_info
    r, g, b = hex_to_rgb(hex)
    lab_l, lab_a, lab_b = hex_to_lab(hex)
    c, m, y, k = hex_to_cmyk(hex)

    sql_command = f"""INSERT INTO parent_colors_{color_space} (id, color_name, hex, rgb, lab, cmyk)
    VALUES ({parent_id}, '{name}', '{hex}', CUBE(array[{r}, {g}, {b}]), CUBE(array[{lab_l}, {lab_a}, {lab_b}]), CUBE(array[{c}, {m}, {y}, {k}]));\n"""

    with open(f"insert_commands_{color_space}.sql", 'a') as f:
        f.write(sql_command)

def insert_color_name_sql_command(color_info, color_space, parent_ids, parent_colors):
    hex, name = color_info
    r, g, b = hex_to_rgb(hex)
    lab_l, lab_a, lab_b = hex_to_lab(hex)
    c, m, y, k = hex_to_cmyk(hex)

    closest_color = closest_color_in_space((r, g, b), parent_colors, color_space)
    logging.info(f"Closest color computed: {closest_color}")

    try:
        closest_parent_color_id = parent_ids[closest_color]
    except KeyError:
        logging.warning(parent_ids)
        logging.warning(f"Could not find closest color: {closest_color}. Skipping this entry.")
        return

    sql_command = f"""INSERT INTO color_names_{color_space} (color_name, hex, rgb, lab, cmyk, parent_color_id)
    VALUES ('{name}', '{hex}', CUBE(array[{r}, {g}, {b}]), CUBE(array[{lab_l}, {lab_a}, {lab_b}]), CUBE(array[{c}, {m}, {y}, {k}]), {closest_parent_color_id});\n"""

    with open(f"insert_commands_{color_space}.sql", 'a') as f:
        f.write(sql_command)

# Argument parsing
parser = argparse.ArgumentParser(description="Insert color data based on a specified color space.")
parser.add_argument('color_space', choices=['rgb', 'hsl', 'cmyk', 'pantone', 'lab'], help='Specify the color space.')
args = parser.parse_args()

parent_colors_dict = {hex: name for hex, name in parent_colors}

# ID Generation Loop for parent colors
logging.info('Generating IDs for parent colors')
parent_ids = {}
parent_id_counter = 1
for hex, name in parent_colors:
    parent_ids[name] = parent_id_counter
    parent_id_counter += 1

logging.warning("parent colors ids array")
logging.warning(parent_ids)

# Insertion Loop for parent colors
logging.info('Starting to insert parent colors')
for hex, name in parent_colors:
    # Use the new function for parent colors
    insert_parent_color_sql_command((hex, name), args.color_space, parent_ids[name])

# Insertion Loop for color names
logging.info('Starting to insert color names')
for hex, name in color_names:
    insert_color_name_sql_command((hex, name), args.color_space, parent_ids, parent_colors_dict)

logging.info('Finished inserting color names')



