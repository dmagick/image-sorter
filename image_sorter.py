import os.path, errno, sys
import pyexiv2

"""
Quick script to sort a lot of images into when they were taken, ala yyyy/mm/dd
based on exif data (when the pic was taken)
"""

origin_image_path="y:" + os.sep + "to_sort"
sorted_path="y:" + os.sep + "Photos"

if sorted_path == "":
	print "Must set a sorted path (base directory for where the images will be sorted to)"
	sys.exit(1)

if origin_image_path == "":
	print "Must set an origin path (where the images are currently)"
	sys.exit(1)

def mkdir_p(path):
	if not os.path.isdir(path):
		os.makedirs(path, 0755)

# os.path.walk can be used to traverse directories recursively
# to apply changes to a whole tree of files.
def find_images( arg, dirname, fnames ):
	for file in fnames:
		arg.append(dirname + os.sep + file)

print "Finding images.."
arglist = []
os.path.walk(origin_image_path,find_images,arglist)

total_files = len(arglist)

c = 0
for file in arglist:
	c = c + 1
	if c % 10 == 0:
		print "Processed " + str(c) + "/" + str(total_files) + "\r",
	
	if os.path.isdir(file):
		if not os.listdir(file):
			os.rmdir(file)
			continue


	if os.path.isfile(file):
		extension = os.path.splitext(file)[1].lower()
		if extension != ".jpg" and extension != ".cr2" and extension != ".crw":
			os.remove(file)
			continue

		metadata = pyexiv2.ImageMetadata(file)
		metadata.read()
		key_to_find = "Exif.Image.DateTime"
		try:
			found = metadata[key_to_find]
		except KeyError:
			found = False
		
		if not found:
			continue

		tag = metadata[key_to_find].value
		if tag == "0000:00:00 00:00:00":
			print
			print "Skipping file " + file
			continue

		y = tag.year
		m = tag.strftime("%m")
		d = tag.strftime("%d")
		final_path=sorted_path + os.sep + str(y) + os.sep + str(m) + os.sep + str(d)
		mkdir_p(final_path)
		final_image_path = final_path + os.sep + os.path.basename(file)
		if os.path.isfile(final_image_path):
			os.remove(final_image_path)
			continue

		try:
			os.rename(file, final_image_path)
		except:
			print
			print "trying to put file " + file + " into " + final_image_path
			print "Unexpected error:", sys.exc_info()[0]
			continue

print "Processed " + str(c) + "/" + str(total_files)
