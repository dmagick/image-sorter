import os.path, errno, sys
import pyexiv2
import hashlib

"""
Quick script to sort a lot of images into when they were taken, ala yyyy/mm/dd
based on exif data (when the pic was taken)
"""

origin_image_path="p:" + os.sep + "Photos"

extract_image_path="e:" + os.sep + "Photos_Extracted"

if origin_image_path == "":
	print "Must set an origin path (where the images are currently)"
	sys.exit(1)

def mkdir_p(path):
	if not os.path.isdir(path):
		os.makedirs(path, 0755)

mkdir_p(extract_image_path)

# os.path.walk can be used to traverse directories recursively
# to apply changes to a whole tree of files.
def find_images( arg, dirname, fnames ):
	for file in fnames:
		arg.append(dirname + os.sep + file)

print "Finding images.."
arglist = []
os.path.walk(origin_image_path,find_images,arglist)

total_files = len(arglist)

duplicates = {}
stats = {}

c = 0
for file in arglist:
	c = c + 1
	if c % 10 == 0:
		print "Processed " + str(c) + "/" + str(total_files) + "\r",

	newpath = file.replace(origin_image_path, extract_image_path)

	if os.path.isdir(file):
		if not os.path.isdir(newpath):
			mkdir_p(newpath)
		continue

	ext  = os.path.splitext(file)[1]
	lext = ext.lower()
	if lext != ".jpg" and lext != ".cr2" and lext != ".crw":
		continue

	fname = os.path.splitext(newpath)[0]

	if os.path.isfile(fname):
		continue

	metadata = pyexiv2.ImageMetadata(file)
	metadata.read()

	thumb = metadata.exif_thumbnail
	thumb.write_to_file(fname)

print "Processed " + str(c) + "/" + str(total_files)
print "========"
pause = raw_input('press enter to exit.')
