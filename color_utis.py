import webcolors
from colormath.color_objects import sRGBColor, LabColor, CMYKColor, XYZColor
from colormath.color_conversions import convert_color
import logging
import os
from color_names import parent_colors

# Function to calculate Euclidean distance in any color space
def calculate_euclidean_distance(color1, color2):
    return sum((a - b)**2 for a, b in zip(color1, color2)) ** 0.5

# Existing helper functions
def hex_to_rgb(hex):
    return webcolors.hex_to_rgb("#" + hex)

def hex_to_lab(hex):
    rgb = webcolors.hex_to_rgb("#" + hex)
    srgb = sRGBColor(rgb[0], rgb[1], rgb[2], is_upscaled=True)
    lab = convert_color(srgb, LabColor)
    return lab.lab_l, lab.lab_a, lab.lab_b

def hex_to_cmyk(hex):
    rgb = hex_to_rgb(hex)
    srgb = sRGBColor(rgb[0], rgb[1], rgb[2], is_upscaled=True)
    cmyk = convert_color(srgb, CMYKColor)
    return cmyk.cmyk_c, cmyk.cmyk_m, cmyk.cmyk_y, cmyk.cmyk_k


def hex_to_xyz(hex):
    rgb = webcolors.hex_to_rgb("#" + hex)
    srgb = sRGBColor(rgb[0], rgb[1], rgb[2], is_upscaled=True)
    xyz = convert_color(srgb, XYZColor)
    return xyz.xyz_x, xyz.xyz_y, xyz.xyz_z

# Color space selection
color_space_functions = {
    'rgb': lambda hex: hex_to_rgb(hex),
    'lab': lambda hex: hex_to_lab(hex),
    'cmyk': lambda hex: hex_to_cmyk(hex),
}

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

# Function to find the closest color given a requested color and color space
def closest_color_in_space(requested_color, parent_colors, color_space):

    requestedHex, name = requested_color
    min_distances = {}
    color_space_fn = color_space_functions.get(color_space, hex_to_lab)

    for hex, name in parent_colors.items():
        distance = calculate_euclidean_distance(
            color_space_fn(requestedHex),
            color_space_fn(hex)
        )
        min_distances[distance] = hex, name

    # Sort and get closest color
    closest_color = min(min_distances.items())
    distance = closest_color[0]
    hex, name = closest_color[1]


    logging.info(f"Closest found {color_space} color for {name}: {closest_color}")
    return hex, name, distance

parent_colors_dict = {hex: name for hex, name in parent_colors}

def insert_color_name_sql_command(color_info, color_space, pantone = 0):
    hex, name = color_info
    r, g, b = hex_to_rgb(hex)
    lab_l, lab_a, lab_b = hex_to_lab(hex)
    c, m, y, k = hex_to_cmyk(hex)

    closest_color_hex, closest_color_name, closest_color_distance = closest_color_in_space((hex, name), parent_colors_dict, color_space)
    logging.info(f"Closest color computed: {closest_color_name} - {closest_color_hex}")

    sql_command = f"""INSERT INTO color_names_{color_space} (color_name, hex, rgb, lab, cmyk, parent_color_name, parent_color_hex, parent_color_distance)
    VALUES ('{name}', '{hex}', CUBE(array[{r}, {g}, {b}]), CUBE(array[{lab_l}, {lab_a}, {lab_b}]), CUBE(array[{c}, {m}, {y}, {k}]), '{closest_color_name}', '{closest_color_hex}', '{closest_color_distance}');\n"""
    # logging.info(f"Sql command: {sql_command}")
    with open(f"insert_commands_{color_space}.sql", 'a') as f:
        f.write(sql_command)
