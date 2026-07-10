import os
import subprocess

from convert_Windows_to_WSL_path import convert_Windows_to_WSL_path

def tileImages(fileDir, imgBaseName, tileDirection='horizontal'):
    '''
    Tile images using the linux 'montage' command
    
    Parameters
    ----------
    fileDir : str
        Path to the directory containing the images to be tiled
    imgBaseName : str
        Base name of the image to be tiled. For example, imgBaseName='Jen' will
        search for 'Jen.Daz.jpg' or 'Jen.Daz.png' and 'Jen.AI.jpg' or 'Jen.AI.png',
        and tile them accordingly, creating 'Jen.tiled.jpg' in the same directory.
    tileDirection : str
        'horizontal' (default) or 'vertical'
    '''

    extensions = ['.jpg', '.png']
    baseImgPath = None
    aiImgPath = None

    # Check existence of both images with either .jpg or .png extensions
    for ext in extensions:
        if os.path.exists(os.path.join(fileDir, imgBaseName + ".Daz" + ext)):
            baseImgPath = os.path.join(fileDir, imgBaseName + ".Daz" + ext)
        if os.path.exists(os.path.join(fileDir, imgBaseName + ".AI" + ext)):
            aiImgPath = os.path.join(fileDir, imgBaseName + ".AI" + ext)

    if not baseImgPath or not aiImgPath:
        print(f"Matching image files for '{imgBaseName}' and '{imgBaseName}.AI' with extensions .jpg or .png must exist in the directory.")
        return

    outputPath = os.path.join(fileDir, imgBaseName + '.tiled.jpg')

    # Convert the paths to WSL paths
    baseImgPath = convert_Windows_to_WSL_path(baseImgPath)
    aiImgPath = convert_Windows_to_WSL_path(aiImgPath)
    outputPath = convert_Windows_to_WSL_path(outputPath)

    # Set up the montage command based on the tile direction
    if tileDirection == 'horizontal':
        cmd = ["wsl", "montage", baseImgPath, aiImgPath, "-geometry", "+0+0", "-tile", "2x1", outputPath]
    elif tileDirection == 'vertical':
        cmd = ["wsl", "montage", baseImgPath, aiImgPath, "-geometry", "+0+0", "-tile", "1x2", outputPath]
    else:
        print("Invalid tile direction. Use 'horizontal' or 'vertical'.")
        return

    # Run the command
    subprocess.run(cmd, check=True)
    print(f"Images tiled. Output saved as '{outputPath}'.")

def tileAllImages(fileDir, tileDirection):
    '''
    Tile all images in a directory matching the pattern '*.Daz.jpg' or '*.Daz.png'
    with the corresponding '*.AI.jpg' or '*.AI.png' image.
    '''
    for filename in os.listdir(fileDir):
        if filename.endswith(".Daz.jpg"):
            imgBaseName = filename.replace(".Daz.jpg", "")
            tileImages(fileDir=fileDir, imgBaseName=imgBaseName, tileDirection=tileDirection)
        elif filename.endswith(".Daz.png"):
            imgBaseName = filename.replace(".Daz.png", "")
            tileImages(fileDir=fileDir, imgBaseName=imgBaseName, tileDirection=tileDirection)

if __name__ == '__main__':
    tileAllImages(fileDir="D:/Data/MyAI/POSTED/MightiestMouse",
                  tileDirection='horizontal')
    
    # tileImages(fileDir="D:/Data/MyAI/POSTED/MightiestMouse",
    #            imgBaseName="MightyJen-1",
               # tileDirection='horizontal')