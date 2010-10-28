import os.path, errno, sys
import pyexiv2

"""
Quick script to sort a lot of images into when they were taken, ala yyyy/mm/dd
based on exif data (when the pic was taken)
"""

sorted_path=""
origin_image_path=""

if sorted_path == "":
    print "Must set a sorted path (base directory for where the images will be sorted to)"
    sys.exit(1)

if origin_image_path == "":
    print "Must set an origin path (where the images are currently)"
    sys.exit(1)

def mkdir_p(path):
    try:
        os.makedirs(path, 0755)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST:
            pass
        else: raise

# os.path.walk can be used to traverse directories recursively
# to apply changes to a whole tree of files.
def callback( arg, dirname, fnames ):
    for file in fnames:
        arg.append(dirname + "/" + file)

arglist = []
os.path.walk(origin_image_path,callback,arglist)

for file in arglist:
    if os.path.isfile(file):
        exiv_image = pyexiv2.Image(file)
        exiv_image.readMetadata()
        exif_keys = exiv_image.exifKeys()
        image_date = exiv_image["Exif.Image.DateTime"]
        y = image_date.year
        m = image_date.strftime("%m")
        d = image_date.strftime("%d")
        final_path=sorted_path + "/" + str(y) + "/" + str(m) + "/" + str(d)
        mkdir_p(final_path)
        final_image_path = final_path + "/" + os.path.basename(file)
        try:
            os.rename(file, final_image_path)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            raise

        sys.exit(1)

