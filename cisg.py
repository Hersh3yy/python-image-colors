# Color Insert Script Generator || CISG
import logging
import psycopg2
import os
import argparse
from color_names import parent_colors
from pantone_numbers import color_names
from color_utis import insert_parent_color_sql_command, insert_color_name_sql_command

logging.basicConfig(level=logging.INFO)


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
for pantone, color_info in color_names.items():
    insert_color_name_sql_command((color_info['hex'], color_info['name']), args.color_space, parent_ids, parent_colors_dict, pantone)

logging.info('Finished inserting color names')

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
