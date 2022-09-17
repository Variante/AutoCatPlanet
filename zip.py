from zipfile import ZipFile
import os
import glob

file = 'AutoCatPlanet.zip'
prefix = './AutoCatPlanet/'

try:
    os.remove(file)
except:
    pass
    
# create a ZipFile object
with ZipFile(file, 'w') as zipObj:
    # Add multiple files to the zip
    zipObj.write('./dist/AutoCatPlanet.exe', prefix + 'AutoCatPlanet.exe')
    
    for i in ['config.json', 'README.md', 'LICENSE']:
        zipObj.write(i, prefix + i)
    
    for i in glob.glob('./img/*'):
        zipObj.write(i, prefix + i)
        
    for i in glob.glob('./db/*'):
        zipObj.write(i, prefix + i)