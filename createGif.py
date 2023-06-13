import argparse
import os
import subprocess

def create_animated_gif(baseDir, baseName, delay, extension):
    os.chdir(baseDir)
    # Build the command string
    command = f"wsl convert -delay {delay} -loop 0 {baseName}*.{extension} {baseName}_delay{delay}.gif"

    # Execute the command using subprocess
    subprocess.run(command, shell=True)

if __name__ == '__main__':
    # Set up the command line argument parser
    parser = argparse.ArgumentParser(description='Convert a sequence of images to an animated GIF.')
    parser.add_argument('filename', help='Base filename without the numbers or extension')
    parser.add_argument('delay', type=int, help='Delay between frames in centiseconds')
    parser.add_argument('extension', help='Image extension (e.g. jpg)')

    # Parse the command line arguments
    args = parser.parse_args()

    # Call the function with the input arguments
    create_animated_gif(args.filename, args.delay, args.extension)
