
def convertWindowsPathToWSL(path):
    # Check if the filename is a Windows path. If so, convert it to a WSL path.
    if path[1:3] == ':/':
        drive_letter = path[0]
        if drive_letter.isalpha():
            path = path.replace(drive_letter + ':', '/mnt/' + drive_letter.lower())
    return path

if __name__ == '__main__':
    convertWindowsPathToWSL()

    