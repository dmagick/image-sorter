import os.path, errno, sys
import pyexiv2
import hashlib

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

duplicates = {}
stats = {}

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
		filename  = os.path.basename(os.path.splitext(file)[0])
		ext  = os.path.splitext(file)[1]
		lext = ext.lower()
		if lext != ".jpg" and lext != ".cr2" and lext != ".crw":
			os.remove(file)
			continue

		metadata = pyexiv2.ImageMetadata(file)
		metadata.read()
		
		if lext == ".crw":
			key_to_find = "Exif.Photo.DateTimeOriginal"
		else:
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
		stats_dmy = str(y) + os.sep + str(m) + os.sep + str(d)
		if stats_dmy in stats:
			stats[stats_dmy]+=1
		else:
			stats[stats_dmy]=1
		
		final_path=sorted_path + os.sep + str(y) + os.sep + str(m) + os.sep + str(d)

		mkdir_p(final_path)
		final_image_path = final_path + os.sep + os.path.basename(file)
		if os.path.isfile(final_image_path):
			f = open(final_image_path, 'rb')
			h = hashlib.sha1()
			h.update(f.read())
			hash = h.hexdigest()
			f.close()

			f = open(file, 'rb')
			h2 = hashlib.sha1()
			h2.update(f.read())
			hash2 = h2.hexdigest()
			f.close()

			if hash == hash2:
				 duplicates[file] = final_image_path
				 continue

			filecounter=0
			while True:
				filecounter = filecounter + 1
				new_name = filename + "-%d" % filecounter
				new_path = final_path + os.sep + new_name + ext
				if os.path.isfile(new_path) == False:
					final_image_path = new_path
					break

		try:
			os.rename(file, final_image_path)
		except:
			print
			print "trying to put file " + file + " into " + final_image_path
			print "Unexpected error:", sys.exc_info()[0]
			continue

print "Processed " + str(c) + "/" + str(total_files)
print "========"
for k, v in stats.iteritems():
	print str(v) + " images were put in " + k

for k, v in duplicates.iteritems():
	print "Found duplicate image: " + k + " (already found at " + v + "), sha1 hashes are the same."

print
print "========"
pause = raw_input('press enter to exit.')
