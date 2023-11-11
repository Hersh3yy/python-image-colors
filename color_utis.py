import webcolors
from colormath.color_objects import sRGBColor, LabColor, CMYKColor, XYZColor
from colormath.color_conversions import convert_color
import logging

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

# Function to find the closest color given a requested color and color space
def closest_color_in_space(requested_color, parent_colors, color_space):

    requestedHex, name = requested_color
    min_distances = {}
    color_space_fn = color_space_functions.get(color_space, hex_to_rgb)

    for hex, name in parent_colors.items():
        distance = calculate_euclidean_distance(
            color_space_fn(requestedHex),
            color_space_fn(hex)
        )
        min_distances[distance] = name

    # Sort and get closest color
    closest_color = min(min_distances.items())[1]

    logging.info(f"Closest found {color_space} color for {name}: {closest_color}")
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

def insert_color_name_sql_command(color_info, color_space, parent_ids, parent_colors, pantone):
    hex, name = color_info
    r, g, b = hex_to_rgb(hex)
    lab_l, lab_a, lab_b = hex_to_lab(hex)
    c, m, y, k = hex_to_cmyk(hex)

    closest_color = closest_color_in_space((hex, name), parent_colors, color_space)
    logging.info(f"Closest color computed: {closest_color}")

    try:
        closest_parent_color_id = parent_ids[closest_color]
    except KeyError:
        logging.warning(parent_ids)
        logging.warning(f"Could not find closest color: {closest_color}. Skipping this entry.")
        return

    sql_command = f"""INSERT INTO color_names_{color_space} (color_name, hex, pantone, rgb, lab, cmyk, parent_color_id)
    VALUES ('{name}', '{hex}', '{pantone}', CUBE(array[{r}, {g}, {b}]), CUBE(array[{lab_l}, {lab_a}, {lab_b}]), CUBE(array[{c}, {m}, {y}, {k}]), {closest_parent_color_id});\n"""

    with open(f"insert_commands_{color_space}.sql", 'a') as f:
        f.write(sql_command)
