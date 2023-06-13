# One-time script to rename "tube-7-10.jpg", "tube-7-11.jpg", etc. to "tube-7.10.jpg", "tube-7.11.jpg", etc.
# Path: imageManipulation\renameFilesTemp.py
import os

args_dict = {}
args_dict['image_dir'] = "D:\\Data\\MyRenders\\Jen\\Jen_story\\Scene_5_game_show\\ch19_round1\\tube-7"
args_dict['extension'] = "jpg"
for image_file in os.listdir(args_dict['image_dir']):
    if image_file.endswith("." + args_dict['extension']):
        img_name_full = image_file.split('.')[0]
        img_prefix = img_name_full.split('-')[:-1]
        img_num = img_name_full.split('-')[-1]
        img_name_new = '-'.join(img_prefix) + '.' + img_num + '.' + args_dict['extension']
        img_file_fullPath = os.path.join(args_dict['image_dir'], image_file)
        img_file_new_fullPath = os.path.join(args_dict['image_dir'], img_name_new)
        os.rename(img_file_fullPath, img_file_new_fullPath)