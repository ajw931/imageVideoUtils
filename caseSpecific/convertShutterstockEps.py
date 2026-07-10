import convertImage
import os

'''
Convert all EPS files in a directory to JPG files with a specified width.
'''

shutterDir = "D:/Data/My Resources/Shutterstock/BACKGROUNDS"
os.chdir(shutterDir)
extension = "eps"
num_converts = 0
for filename in os.listdir("."):
    if filename.endswith(extension):
        convertImage.convertImage(filepath=filename, outputFormat="jpg", width=5000)
        num_converts += 1