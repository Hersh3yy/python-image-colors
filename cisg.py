# Color Insert Script Generator || CISG
import logging
import psycopg2
import os
import argparse
import webcolors
from colormath.color_objects import sRGBColor, LabColor, CMYKColor
from colormath.color_conversions import convert_color
from color_names import color_names, parent_colors

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

# Function to calculate Euclidean distance in any color space
def calculate_euclidean_distance(color1, color2):
    return sum((a - b)**2 for a, b in zip(color1, color2)) ** 0.5

# Function to find the closest color given a requested color and color space
def closest_color_in_space(requested_color, colors, color_space_fn, color_space):
    min_distances = {}

    for hex, name in colors.items():
        distance = calculate_euclidean_distance(
            requested_color,
            color_space_fn(hex)
        )
        min_distances[distance] = name

    # Sort and get closest color
    closest_color = min(min_distances.items())[1]

    logging.info(f"Closest found {color_space} color: {closest_color}")
    return closest_color


def insert_parent_color_sql_command(color_info, color_space, parent_id):  # Added parent_id argument
    hex, name = color_info
    r, g, b = hex_to_rgb(hex)
    lab_l, lab_a, lab_b = hex_to_lab(hex)
    c, m, y, k = hex_to_cmyk(hex)

    sql_command = f"""INSERT INTO parent_colors_{color_space} (id, color_name, hex, rgb, lab, cmyk)
    VALUES ({parent_id}, '{name}', '{hex}', CUBE(array[{r}, {g}, {b}]), CUBE(array[{lab_l}, {lab_a}, {lab_b}]), CUBE(array[{c}, {m}, {y}, {k}]));\n"""

    with open(f"insert_commands_{color_space}.sql", 'a') as f:
        f.write(sql_command)

def insert_color_name_sql_command(color_info, color_space, closest_function, parent_ids, parent_colors, color_space_fn):
    hex, name = color_info
    r, g, b = hex_to_rgb(hex)
    lab_l, lab_a, lab_b = hex_to_lab(hex)
    c, m, y, k = hex_to_cmyk(hex)

    closest_color = closest_function((r, g, b), parent_colors, color_space_fn, color_space)
    logging.info(f"Closest color computed: {closest_color}")

    try:
        closest_color_id = parent_ids[closest_color]
    except KeyError:
        logging.warning(parent_ids)
        logging.warning(f"Could not find closest color: {closest_color}. Skipping this entry.")
        return

    sql_command = f"""INSERT INTO color_names_{color_space} (color_name, hex, rgb, lab, cmyk, parent_color_id)
    VALUES ('{name}', '{hex}', CUBE(array[{r}, {g}, {b}]), CUBE(array[{lab_l}, {lab_a}, {lab_b}]), CUBE(array[{c}, {m}, {y}, {k}]), {closest_color_id});\n"""

    with open(f"insert_commands_{color_space}.sql", 'a') as f:
        f.write(sql_command)


# Existing helper functions
def hex_to_rgb(hex):
    return webcolors.hex_to_rgb("#" + hex)

def hex_to_lab(hex):
    rgb = webcolors.hex_to_rgb("#" + hex)
    srgb = sRGBColor(rgb[0], rgb[1], rgb[2], is_upscaled=True)
    lab = convert_color(srgb, LabColor)
    return lab.lab_l, lab.lab_a, lab.lab_b

def hex_to_cmyk(hex):
    rgb = webcolors.hex_to_rgb("#" + hex)
    #srgb = sRGBColor(rgb[0], rgb[1], rgb[2], is_upscaled=True)
    #cmyk = convert_color(srgb, CMYKColor)
    return rgb_to_cmyk(rgb[0], rgb[1], rgb[2]) #cmyk.cmyk_c, cmyk.cmyk_m, cmyk.cmyk_y, cmyk.cmyk_k

# Function to convert RGB to CMYK
def rgb_to_cmyk(r, g, b):
    c = 1 - r / 255.
    m = 1 - g / 255.
    y = 1 - b / 255.
    k = min(c, m, y)
    if k < 1:
        c = (c - k) / (1 - k)
        m = (m - k) / (1 - k)
        y = (y - k) / (1 - k)
    return c, m, y, k

# Argument parsing
parser = argparse.ArgumentParser(description="Insert color data based on a specified color space.")
parser.add_argument('color_space', choices=['rgb', 'hsl', 'cmyk', 'pantone', 'lab'], help='Specify the color space.')
args = parser.parse_args()

# Color space selection
color_space_functions = {
    'rgb': lambda hex: hex_to_rgb(hex),
    'lab': lambda hex: hex_to_lab(hex),
    'cmyk': lambda hex: hex_to_cmyk(hex),
}

closest_function = closest_color_in_space

parent_colors_dict = {hex: name for hex, name in parent_colors}

# ID Generation Loop for parent colors
logging.info('Generating IDs for parent colors')
parent_ids = {}
parent_id_counter = 1
for hex, name in parent_colors:
    parent_ids[name] = parent_id_counter
    parent_id_counter += 1

logging.warning("parent colors array")
logging.warning(parent_ids)

# Insertion Loop for parent colors
logging.info('Starting to insert parent colors')
for hex, name in parent_colors:
    # Use the new function for parent colors
    insert_parent_color_sql_command((hex, name), args.color_space, parent_ids[name])

# Insertion Loop for color names
logging.info('Starting to insert color names')
for hex, name in color_names:
    insert_color_name_sql_command((hex, name), args.color_space, closest_function, parent_ids, parent_colors_dict, color_space_functions.get(args.color_space, hex_to_rgb))

logging.info('Finished inserting color names')



