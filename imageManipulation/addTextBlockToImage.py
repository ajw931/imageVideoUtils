import argparse
import os
import subprocess
# Local methods
from convert_Windows_to_WSL_path import convert_Windows_to_WSL_path

def display_help():
    print("Usage: script_name image_dir text_dir output_dir extension")
    print("Concatenates each pair of images vertically from an image directory and a text directory")
    print("and places them in an output directory.")
    print("")
    print("Positional arguments:")
    print("  image_dir       Path to the image directory.")
    print("  text_dir        Path to the text directory.")
    print("  output_dir      Path to the output directory.")
    print("  extension       File extension for images and text files (e.g. png, jpg).")
    print("  mode            'exact' (default; requires one-to-one matching of filenames in image_dir and text_dir) or 'pattern' (a text_dir file containing the string '[any]' will be matched with each image_dir file matching that pattern")
    print("")
    print("Optional arguments:")
    print("  -h, --help      Show this help message and exit.")

def addTextBlockToImage(args_dict):

    # Check if the help flag is set
    if args_dict['extension'] == '-h' or args_dict['extension'] == '--help':
        display_help()
        exit(0)

    # Check that the correct number of arguments have been supplied
    if len([args_dict['image_dir'], args_dict['text_dir'], args_dict['output_dir'], args_dict['extension']]) != 4:
        print("Error: Incorrect number of arguments.")
        display_help()
        exit(1)

    # Create the output directory if it doesn't exist
    os.makedirs(args_dict['output_dir'], exist_ok=True)

    # Iterate over the files in the image directory
    for image_file in os.listdir(args_dict['image_dir']):
        # Check if the file is an image file with the specified extension
        if image_file.endswith("." + args_dict['extension']):
            # Get the corresponding file in the text directory
            if args_dict['mode'] == 'exact':
                text_file = os.path.splitext(image_file)[0] + ".text." + args_dict['extension']
            else:
                image_file_split = image_file.split('.')
                text_file = '.'.join(image_file_split[:-2]+['[any]','text',image_file_split[-1]])

            text_file_fullPath = os.path.join(args_dict['text_dir'], text_file)
            image_file_fullPath = os.path.join(args_dict['image_dir'], image_file)
            
            img_linux = convert_Windows_to_WSL_path(image_file_fullPath)
            txt_linux = convert_Windows_to_WSL_path(text_file_fullPath)

            # Check if the text file exists
            if os.path.isfile(text_file_fullPath):
                # Concatenate the image and text vertically using the montage command
                output_file_fullPath = os.path.join(args_dict['output_dir'], image_file)
                #out_singleSlash = output_file_fullPath.replace("\\","/")
                out_linux = convert_Windows_to_WSL_path(output_file_fullPath)
                cmd = ["wsl","montage", img_linux, txt_linux, "-geometry", "+0+0", "-tile", "1x2", out_linux]
                print(" ".join(cmd))
                subprocess.run(cmd)
            else:
                print(f"Warning: {txt_linux} not found")

if __name__ == '__main__':
    # Create a parser to parse command-line arguments
    parser = argparse.ArgumentParser(description='Concatenates images and text vertically.')
    parser.add_argument('image_dir', type=str, help='Path to the image directory.')
    parser.add_argument('text_dir', type=str, help='Path to the text directory.')
    parser.add_argument('output_dir', type=str, help='Path to the output directory.')
    parser.add_argument('extension', type=str, help='File extension for images and text files.')
    parser.add_argument('mode', type=str, default='exact', help='exact or pattern')
    args = parser.parse_args()

    args_dict = vars(args)

    addTextBlockToImage(args_dict)
