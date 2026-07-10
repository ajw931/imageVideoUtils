import argparse
import os
import subprocess
import shlex

import convertWindowsPathToWSL
from convert_Windows_to_WSL_path import convert_Windows_to_WSL_path

def convertImage(filepath, outputFormat, width):
    '''
    Convert an image file to a specified format using ImageMagick with a specified width.
    '''
    #filepath = convertWindowsPathToWSL.convertWindowsPathToWSL(filepath)
    filepath = convert_Windows_to_WSL_path(filepath)

    # Separate out the directory and filename
    directory = os.path.dirname(filepath)
    filename = os.path.basename(filepath)

    # Filename without the extension
    filename_noExt = os.path.splitext(filename)[0]

    # Change to this directory to avoid potential whitespace issues
    if directory != '':
        os.chdir(directory)

    # Create a directory for the output files if it doesn't exist
    if not os.path.exists(outputFormat):
        os.mkdir(outputFormat)

    command = ['wsl','convert', shlex.quote(f'{filename}'), '-strip', '-resize', f'{width}x', shlex.quote(f'{outputFormat}/{filename_noExt}.{outputFormat}')]
    print(' '.join(command))
    # Subprocess.run is giving an error with the wsl or convert command for some reason. But os.system works.
    os.system(" ".join(command))
    #subprocess.run(command)
    
if __name__ == '__main__':
    # Set up the command line argument parser
    parser = argparse.ArgumentParser(description='Convert an EPS file to a PNG file.')
    parser.add_argument('filename', help='Base filename with extension')
    parser.add_argument('outputFormat', help='Output image extension (e.g. jpg)')
    parser.add_argument('width', type=int, help='Image width')
    
    # Parse the command line arguments
    args = parser.parse_args()

    # Call the function with the input arguments
    convertImage(args.filename, args.outputFormat, args.width)
