# Color Insert Script Generator || CISG
import logging
import psycopg2
import argparse
from pantone_numbers import color_names
from color_utis import insert_color_name_sql_command

logging.basicConfig(level=logging.INFO)


# Argument parsing
parser = argparse.ArgumentParser(description="Insert color data based on a specified color space.")
parser.add_argument('color_space', choices=['rgb', 'hsl', 'cmyk', 'pantone', 'lab'], help='Specify the color space.')
args = parser.parse_args()

# Insertion Loop for color names
logging.info('Starting to insert color names')
for pantone, color_info in color_names.items():
    insert_color_name_sql_command((color_info['hex'], color_info['name']), args.color_space, pantone)

logging.info('Finished inserting color names')
