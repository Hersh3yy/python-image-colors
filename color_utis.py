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
def closest_color_in_space(requested_color, colors, color_space):
    min_distances = {}
    color_space_fn = color_space_functions.get(color_space, hex_to_rgb)

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