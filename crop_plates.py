#!/usr/bin/python

import os
import sys
import json
import math
import cv2
import numpy as np
import copy
from numpy.core.numeric import full
import yaml
from argparse import ArgumentParser

parser = ArgumentParser(description='OpenALPR License Plate Cropper')

parser.add_argument( "--input_dir", dest="input_dir", action="store", type=str, required=True, 
                  help="Directory containing plate images and yaml metadata" )

parser.add_argument( "--out_dir", dest="out_dir", action="store", type=str, required=True, 
                  help="Directory to output cropped plates" )

parser.add_argument( "--zoom_out_percent", dest="zoom_out_percent", action="store", type=float, default=1.25, 
                  help="Percent multiplier to zoom out before cropping" )

parser.add_argument( "--plate_width", dest="plate_width", action="store", type=float, required=True, 
                  help="Desired aspect ratio width" )
parser.add_argument( "--plate_height", dest="plate_height", action="store", type=float, required=True, 
                  help="Desired aspect ratio height" )

options = parser.parse_args()

if not os.path.isdir(options.input_dir):
    print ("input_dir (%s) doesn't exist")
    sys.exit(1)

if not os.path.isdir(options.out_dir):
    os.makedirs(options.out_dir)

def get_box(x1, y1, x2, y2, x3, y3, x4, y4, full_image_path):
    height1 = int(round(math.sqrt((x1-x4)*(x1-x4) + (y1-y4)*(y1-y4))))
    height2 = int(round(math.sqrt((x3-x2)*(x3-x2) + (y3-y2)*(y3-y2))))

    height = height1
    if height2 > height:
        height = height2

    # add 25% to the height
    height *= options.zoom_out_percent

    points = [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]

    moment = cv2.moments(np.float32(points))
    centerx = int(round(moment["m10"] / moment["m00"]))
    centery = int(round(moment["m01"] / moment["m00"]))


    training_aspect = options.plate_width / options.plate_height
    width = int(round(training_aspect * height))

    top_left_x = int(round(centerx - (width / 2)))
    top_left_y = int(round(centery - (height / 2)))

    return (top_left_x, top_left_y, width, int(round(height)))

def crop_rect(big_image, x,y,width,height):

    (big_height, big_width, channels) = big_image.shape
    if x >= 0 and y >= 0 and (y+height) < big_height and (x+width) < big_width:
        crop_img = img[y:y+height, x:x+width]
    else:
        crop_img = np.zeros((height, width, 3), np.uint8)
        cv2.randu(crop_img, (0,0,0), (255,255,255))

        offset_x = 0
        offset_y = 0
        if x < 0:
            offset_x = -1 * x
            x = 0
            width -= offset_x
        if y < 0:
            offset_y = -1 * y
            y = 0
            height -= offset_y
        if (x+width) >= big_width:
            offset_x = 0
            width = big_width - x
        if (y+height) >= big_height:
            offset_y = 0
            height = big_height - y

        original_crop =  img[y:y+height-1, x:x+width-1]
        (small_image_height, small_image_width, channels) = original_crop.shape
        crop_img[offset_y:offset_y+small_image_height, offset_x:offset_x+small_image_width] = original_crop

    return crop_img

count = 1
yaml_files = []
for in_file in os.listdir(options.input_dir):
    if in_file.endswith('.yaml') or in_file.endswith('.yml'):
        yaml_files.append(in_file)


yaml_files.sort()

for yaml_file in yaml_files:


    print ("Processing: " + yaml_file + " (" + str(count) + "/" + str(len(yaml_files)) + ")")
    count += 1


    yaml_path = os.path.join(options.input_dir, yaml_file)
    yaml_without_ext = os.path.splitext(yaml_path)[0]
    with open(yaml_path, 'r') as yf:
        yaml_obj = yaml.load(yf)

    image = yaml_obj['image_file']

    # Skip missing images
    full_image_path = os.path.join(options.input_dir, image)
    if not os.path.isfile(full_image_path):
        print (f"Could not find image file {full_image_path}, skipping")
        continue

    plate_corners = yaml_obj['plate_corners_gt']
    cc = plate_corners.strip().split()
    for i in range(0, len(cc)):
        cc[i] = int(cc[i])

    box = get_box(cc[0], cc[1], cc[2], cc[3], cc[4], cc[5], cc[6], cc[7], full_image_path)

    img = cv2.imread(full_image_path)
    crop = crop_rect(img, box[0], box[1], box[2], box[3])

    out_crop_path = options.out_dir + '/' + yaml_file + ".jpg"
    print(f"Ruta output: {out_crop_path}")
    flag_out = cv2.imwrite(out_crop_path, crop )
    print(f"Resultado output: {flag_out}")

print (f"{count-1} Cropped images are located in {options.out_dir}")
