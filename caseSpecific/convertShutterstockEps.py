import convertImage
import os

#shutterDir = "/mnt/d/Data/My Resources/Shutterstock/TEXTURES"
#imageName = "shutterstock_252115858"
#path = shutterDir+"/"+imageName
#convertImage.convertImage(path, "eps", "jpg", 500)

shutterDir = "D:/Data/My Resources/Shutterstock/TEXTURES"
os.chdir(shutterDir)
extension = "eps"
num_converts = 0
for filename in os.listdir("."):
    if filename.endswith(extension):
        convertImage.convertImage(filename, "jpg", 500)
        num_converts += 1