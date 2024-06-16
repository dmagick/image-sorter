import os.path, errno, sys
import pyexiv2
import hashlib
import time, datetime
import pprint

"""
Quick script to sort a lot of images into when they were taken, ala yyyy/mm/dd
based on exif data (when the pic was taken)

uses pyexiv2 (https://pypi.org/project/pyexiv2/)
"""

#origin_image_path="c:" + os.sep + "Data" + os.sep + "to_sort"
#sorted_path="c:" + os.sep + "Data" + os.sep + "Photos"
origin_image_path = os.path.normpath(os.path.join('c:\\', 'Data', 'to-sort'))
sorted_path       = os.path.normpath(os.path.join('c:\\', 'Data', 'Photos'))

origin_image_path = os.path.normpath(os.path.join('p:\\', 'photo-sort', 'to-sort'))
sorted_path       = os.path.normpath(os.path.join('p:\\', 'Photo Backup'))
duplicate_path    = os.path.normpath(os.path.join('p:\\', 'Photo-Duplicates'))

if sorted_path == "":
    print ("Must set a sorted path (base directory for where the images will be sorted to)")
    sys.exit(1)

if origin_image_path == "":
    print ("Must set an origin path (where the images are currently)")
    sys.exit(1)

def mkdir_p(path):
    if not os.path.isdir(path):
        os.makedirs(path, 0o755)

def get_duration(starttime, endtime):
    duration = endtime - starttime
    if duration.seconds < 60:
        return "%s seconds" % (duration.seconds)

    hours   = duration.seconds // 60 // 60
    minutes = (duration.seconds - (hours * 60 * 60)) // 60
    duration_time = ""
    if hours > 0:
        duration_time = "%s hours" % hours
        if minutes > 0:
            duration_time += ", "

    if minutes > 0:
        duration_time = "%s minutes" % minutes

    return duration_time

def get_max_str(lst):
    if len(lst) == 0:
        return ''
    return max(lst, key=len)

starttime = datetime.datetime.now()
print ("Finding images..")
filelist = []

dirlist = []

for root, dirs, files in os.walk(origin_image_path, topdown=True):
    for d in dirs:
        dirlist.append(os.path.join(root, d))

    for f in files:
        filelist.append(os.path.join(root, f))

print ("Finished finding images.".ljust(len(get_max_str(filelist)),' '))
print ()

total_files = len(filelist)

duplicates    = {}
stats         = {}
skip_files    = {}
skip_mdata    = {}
deleted_files = {}
renamed_files = {}

delete_extensions = ['.thm', '.ctg', '.scr', '.ds_store']
delete_files      = ['.DS_Store']
delete_fullfiles  = ['.picasa.ini', 'dji.gis'] # full filenames to delete.
rename_extensions = {'.lrv': {
                            'new-extension': 'mp4',
                            'filesuffix': 'small'
                        }
                    }

if total_files > 0:
    pyexiv2.enableBMFF()

c = 0
for file in filelist:
    c = c + 1
    if c % 10 == 0:
        print ("Processed %s/%s\r" % (str(c), str(total_files)),)

    if os.path.isfile(file):
        full_filename = os.path.basename(file)
        filename      = os.path.splitext(full_filename)[0]
        ext           = os.path.splitext(full_filename)[1]
        lext          = ext.lower()

        if filename in delete_files:
            if filename not in deleted_files:
                deleted_files[filename] = {}

            deleted_files[filename][file] = 1
            os.remove(file)
            continue

        if full_filename in delete_fullfiles:
            if full_filename not in deleted_files:
                deleted_files[full_filename] = {}

            deleted_files[full_filename][file] = 1
            os.remove(file)
            continue

        if lext in delete_extensions:
            if lext not in deleted_files:
                deleted_files[lext] = {}

            deleted_files[lext][file] = 1
            os.remove(file)
            continue

        if lext in rename_extensions:
            new_name  = "%s-%s.%s" % (filename, rename_extensions[lext]['filesuffix'], rename_extensions[lext]['new-extension'])
            curr_path = os.path.dirname(file)
            new_path  = os.path.join(curr_path, new_name)
            if lext not in renamed_files:
                renamed_files[lext] = {}
            renamed_files[lext][file] = 1
            os.rename(file, new_path)
            continue

        if lext not in [".jpg", ".crw", ".cr2", ".dng", ".gpr", ".cr3"]:
            if lext not in skip_files:
                skip_files[lext] = {}

            skip_files[lext][file] = 1
            continue

        try:
            img = pyexiv2.Image(file)
            metadata = img.read_exif()
            img.close()
        except:
            found = False
            os.sys.exit(1)
            continue

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

        tag = found
        if tag == "0000:00:00 00:00:00":
            if lext not in skip_mdata:
                skip_mdata[lext] = {}

            skip_mdata[lext][file] = 1
            continue

        taginfo = datetime.datetime.strptime(tag, "%Y:%m:%d %H:%M:%S")

        y = taginfo.strftime("%Y")
        m = taginfo.strftime("%m")
        d = taginfo.strftime("%d")

        stats_dmy = str(y) + os.sep + str(m) + os.sep + str(d)
        if stats_dmy in stats:
            stats[stats_dmy]+=1
        else:
            stats[stats_dmy]=1

        final_path = os.path.join(sorted_path, str(y), str(m), str(d))
#        final_path=sorted_path + os.sep + str(y) + os.sep + str(m) + os.sep + str(d)

        mkdir_p(final_path)
        final_image_path = os.path.join(final_path, os.path.basename(file))
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
                dupe_path = os.path.join(duplicate_path, str(y), str(m), str(d))
                mkdir_p(dupe_path)
                dupe_image_path = os.path.join(dupe_path, os.path.basename(file))
                if os.path.isfile(dupe_image_path):
                    print
                    print ("found a duplicate file %s" % (file))
                    print ("already stored in %s and %s" % (final_image_path, dupe_image_path))
                    print ("don't need to keep it again, going to delete it instead")

                    if filename not in deleted_files:
                        deleted_files[filename] = {}

                    deleted_files[filename][file] = 1
                    os.remove(file)
                    continue

                else:
                    try:
                        os.rename(file, dupe_image_path)
                    except:
                        print ()
                        print ("trying to put file %s into %s" % (file, dupe_image_path))
                        print ("Unexpected error:", sys.exc_info()[0])
                continue

            filecounter=0
            while True:
                filecounter = filecounter + 1
                new_name = "%s-%d" % (filename, filecounter)
                new_path = os.path.join(final_path, (new_name + ext))
                print("Trying to rename it to %s" % (new_path))
                if os.path.isfile(new_path) == False:
                    final_image_path = new_path
                    break

                if filecounter > 2:
                    print("File counter is > 2")
                    os.sys.exit(1)
                    break

        try:
            os.rename(file, final_image_path)
        except:
            print
            print ("trying to put file %s into %s" % (file, final_image_path))
            print ("Unexpected error:", sys.exc_info()[0])
            continue

print ("Checking for empty directories..")
dirlist.reverse()
c = 0
total_dirs = len(dirlist)
for dir in dirlist:
    print(dir)
    c = c + 1
    if c % 10 == 0:
        print ("Processed %s/%s\r" % (str(c), str(total_dirs)),)

    if os.path.isdir(dir):
        if not os.listdir(dir):
            os.rmdir(dir)
            continue

endtime = datetime.datetime.now()
duration_time = get_duration(starttime, endtime)
print ("Finished at %s (it took %s)" % (endtime.strftime('%Y-%m-%d %H:%M:%S'), duration_time))
print ("Processed %s/%s" % (str(c), str(total_dirs)))
print ("========")
for k, v in sorted(stats.items()):
    print ("%s images were put in %s" % (str(v), k))

for k, v in sorted(duplicates.items()):
    print ("Found duplicate image: %s (already found at %s), sha1 hashes are the same." % (k, v))

if renamed_files:
    print ("Renamed these files:")
    for ftype, vtype in sorted(renamed_files.items()):
        print ("\t%s" % (str(ftype)))
        for f, v in sorted(vtype.items()):
            print ("\t\t%s" % (str(f)))
        print ()
print ()

if deleted_files:
    print ("Deleted these file types:")
    for ftype, vtype in sorted(deleted_files.items()):
        print ("\t%s" % (str(ftype)))
        for f, v in sorted(vtype.items()):
            print ("\t\t%s" % (str(f)))
        print ()
print ()

if skip_files:
    print ("Skipping these unknown file types:")

    for ftype, vtype in sorted(skip_files.items()):
        print ("\t%s" % (str(ftype)))
        for f, v in sorted(vtype.items()):
            print ("\t\t%s" % (str(f)))
        print ()

if skip_mdata:
    print ("Skipping these files that have no proper metadata:")

    for ftype, vtype in sorted(skip_mdata.items()):
        print ("\t%s" % (str(ftype)))
        for f, v in sorted(vtype.items()):
            print ("\t\t%s" % (str(f)))
        print ()

print ()
print ("========")
pause = input('press enter to exit.')
