import os.path, errno, sys
import exiftool
import hashlib
import time, datetime
import pprint

"""
Quick script to sort a lot of images into when they were taken, ala yyyy/mm/dd
based on exif data (when the pic was taken)
"""

keep_duplicate_images = False

current_dir = os.path.dirname(os.path.realpath(__file__))

exifToolPath = os.path.normpath(os.path.join(current_dir, 'Exiftool', 'Exiftool.exe'))

#origin_image_path="c:" + os.sep + "Data" + os.sep + "to_sort"
#sorted_path="c:" + os.sep + "Data" + os.sep + "Photos"
origin_image_path = os.path.normpath(os.path.join('c:\\', 'Data', 'to-sort'))
sorted_path       = os.path.normpath(os.path.join('c:\\', 'Data', 'Photos'))

origin_image_path = os.path.normpath(os.path.join('p:\\', 'photo-sort', 'to-sort'))
sorted_path       = os.path.normpath(os.path.join('p:\\', 'Photo Backup'))
duplicate_path    = os.path.normpath(os.path.join('p:\\', 'Photo-Duplicates'))

log_path = os.path.normpath(os.path.join('p:\\', 'Photo Backup', 'Logs'))
# can't use mkdir_p because it's defined after this is used by log_path_handle.
if not os.path.isdir(log_path):
    os.makedirs(log_path, 0o755)

# needed here to define the log path file name so it can define the log_path_handle.
starttime = datetime.datetime.now()

log_path_file   = os.path.join(log_path, 'backup-logs-' + starttime.strftime('%Y-%m-%d-%H-%M-%S') + '.log')
log_path_handle = open(log_path_file, 'a')

if sorted_path == "":
    print ("Must set a sorted path (base directory for where the images will be sorted to)")
    sys.exit(1)

if origin_image_path == "":
    print ("Must set an origin path (where the images are currently)")
    sys.exit(1)

if exifToolPath == "" or not os.path.isfile(exifToolPath):
    print ("Must set the correct path to exif tool. Currently set to '%s'" % (exifToolPath))
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

def printlog(msg = "", loghandle=log_path_handle):
    print (msg)
    loghandle.write(msg + "\n")

def gethash(filepath):
    f = open(filepath, 'rb')
    h = hashlib.sha1()
    h.update(f.read())
    hash = h.hexdigest()
    f.close()
    return hash

printlog ("Starting at %s" % (starttime.strftime('%Y-%m-%d %H:%M:%S')))
printlog ()
printlog ("Finding images..")
filelist = []

dirlist = []

for root, dirs, files in os.walk(origin_image_path, topdown=True):
    for d in dirs:
        dirlist.append(os.path.join(root, d))

    for f in files:
        filelist.append(os.path.join(root, f))

total_files = len(filelist)

printlog ("Finished finding images (found %d).".ljust(len(get_max_str(filelist)),' ') % (total_files))
printlog ()

duplicates      = {}
stats           = {}
skip_files      = {}
skip_mdata      = {}
deleted_files   = {}
renamed_files   = {}
processed_files = {}

delete_extensions = ['.thm', '.ctg', '.scr', '.ds_store']
delete_files      = ['.DS_Store']
delete_fullfiles  = ['.picasa.ini', 'dji.gis'] # full filenames to delete.
rename_extensions = {'.lrv': {
                            'new-extension': 'mp4',
                            'filesuffix': 'small'
                        }
                    }

# map of filetype -> metadata field name to get 'created date' from.
metadataFields = {
    'cr2' : 'EXIF:DateTimeOriginal',
    'cr3' : 'EXIF:CreateDate',
    'crw' : 'MakerNotes:DateTimeOriginal',
    'dng' : 'EXIF:DateTimeOriginal',
    'jpg' : 'EXIF:DateTimeOriginal',
    'mp4' : 'EXIF:CreateDate',
}

with exiftool.ExifToolHelper(executable=exifToolPath) as et:
    c = 0
    for file in filelist:
        c = c + 1
        if c % 10 == 0:
            print ("Processed %s/%s" % (str(c), str(total_files)), end="\r")

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

            if lext not in [".mp4", ".jpg", ".crw", ".cr2", ".dng", ".gpr", ".cr3"]:
                if lext not in skip_files:
                    skip_files[lext] = {}

                skip_files[lext][file] = 1
                continue

            created = None
            for d in et.get_metadata(file):
                if not 'File:FileTypeExtension' in d:
                    print("Unable to find file extension info for '%s'" % file)
                    break

                filetype = d['File:FileTypeExtension'].lower()
                # if filetype in ['jpg']:
                #     pprint.pprint(d)
                #     os.sys.exit(1)
                #     print("skipping file '%s' for now" % (file))
                #     break

                if not filetype in metadataFields.keys():
                    print("For file '%s', unable to find file type '%s' in metadata fields list" % (file, filetype))
                    pprint.pprint(d)
                    os.sys.exit(1)
                    break

                mdata_field = metadataFields[filetype]
                if not mdata_field in d:
                    print("For file '%s', unable to find the metadata field '%s'" % (file, mdata_field))
                    pprint.pprint(d)
                    os.sys.exit(1)

                created = d[mdata_field]
                break

                print("file '%s' : unknown file type '%s'" % (file, filetype))
                pprint.pprint(d)
                os.sys.exit(1)

            if not created:
                print("Unable to get created info for file '%s'" % file)
                continue

            if created == "0000:00:00 00:00:00":
                if lext not in skip_mdata:
                    skip_mdata[lext] = {}

                skip_mdata[lext][file] = 1
                continue

            taginfo = datetime.datetime.strptime(created, "%Y:%m:%d %H:%M:%S")

            y = taginfo.strftime("%Y")
            m = taginfo.strftime("%m")
            d = taginfo.strftime("%d")

            stats_dmy = str(y) + os.sep + str(m) + os.sep + str(d)

            final_path = os.path.join(sorted_path, str(y), str(m), str(d))
    #        final_path=sorted_path + os.sep + str(y) + os.sep + str(m) + os.sep + str(d)

            keep_file = True

            mkdir_p(final_path)
            final_image_path = os.path.join(final_path, os.path.basename(file))
            if os.path.isfile(final_image_path):
                hash  = gethash(final_image_path)
                original_file_hash = gethash(file)

                if hash == original_file_hash:
                    if keep_duplicate_images == False:
                        printlog ()
                        printlog ("found image %s and it is already kept at %s, going to delete it" % (file, final_image_path))

                        if lext not in deleted_files:
                            deleted_files[lext] = {}

                        deleted_files[lext][file] = 1
                        os.remove(file)
                        continue

                    duplicates[file] = final_image_path
                    dupe_path = os.path.join(duplicate_path, str(y), str(m), str(d))
                    mkdir_p(dupe_path)
                    dupe_image_path = os.path.join(dupe_path, os.path.basename(file))
                    if os.path.isfile(dupe_image_path):
                        printlog ()
                        printlog ("found a duplicate file %s" % (file))
                        printlog ("already stored in %s and %s" % (final_image_path, dupe_image_path))
                        printlog ("don't need to keep it again, going to delete it instead")

                        if lext not in deleted_files:
                            deleted_files[lext] = {}

                        deleted_files[lext][file] = 1
                        os.remove(file)
                        continue
                    else:
                        if stats_dmy in stats:
                            stats[stats_dmy]+=1
                        else:
                            stats[stats_dmy]=1

                        try:
                            os.rename(file, dupe_image_path)
                        except:
                            printlog ()
                            printlog ("trying to put file %s into %s" % (file, dupe_image_path))
                            printlog ("Unexpected error:", sys.exc_info()[0])
                    continue

                prev_filename = None
                prev_filehash = None
                new_path      = None
                new_filehash  = None
                filecounter=0

                while True:
                    prev_filename = new_path
                    prev_filehash = new_filehash
                    filecounter = filecounter + 1
                    new_name = "%s-%d" % (filename, filecounter)
                    new_path = os.path.join(final_path, (new_name + ext))

                    printlog ("Trying to rename %s to %s" % (file, new_path))
                    if os.path.isfile(new_path) == False:
                        final_image_path = new_path
                        break

                    new_filehash = gethash(new_path)
                    # printlog ("new path = %s, hash = %s" % (new_path, new_filehash))
                    # printlog ("file = %s, hash = %s" % (file, original_file_hash))

                    if new_filehash == original_file_hash:
                        keep_file = False
                        printlog ("original file %s seems to be the same as new name %s, going to delete it." % (file, new_path))
                        if lext not in deleted_files:
                            deleted_files[lext] = {}

                        deleted_files[lext][file] = 1
                        os.remove(file)
                        break


                    # if prev_filehash == new_filehash:
                    #     printlog ("file %s (hash: %s) seems to be the same as file %s (hash: %s)" % (prev_filename, prev_filehash, new_path, new_filehash))
                    #     os.sys.exit(1)
                    #

                    if filecounter > 5:
                        printlog ("File counter is > 5")
                        os.sys.exit(1)
                        break


            if not keep_file:
                printlog ("not keeping file %s, skipping." % file)
                continue

            try:
                if stats_dmy in stats:
                    stats[stats_dmy]+=1
                else:
                    stats[stats_dmy]=1

                os.rename(file, final_image_path)

                if lext not in processed_files:
                    processed_files[lext] = {
                        'files' : [],
                    }
                processed_files[lext]['files'].append(file)

            except:
                printlog ()
                printlog ("trying to put file %s into %s" % (file, final_image_path))
                printlog ("Unexpected error:", sys.exc_info()[0])
                continue

printlog ("Checking for empty directories..")
dirlist.reverse()
c = 0
total_dirs = len(dirlist)
for dir in dirlist:
    print(dir)
    c = c + 1
    if c % 10 == 0:
        print ("Processed %s/%s" % (str(c), str(total_dirs)), end="\r")

    if os.path.isdir(dir):
        if not os.listdir(dir):
            printlog ("Directory %s appears to be empty, removing it." % dir)
            os.rmdir(dir)
        else:
            printlog ("Directory %s appears to have something in it, skipping." % dir)

endtime = datetime.datetime.now()
duration_time = get_duration(starttime, endtime)
printlog ("")
printlog ("Finished at %s (it took %s)" % (endtime.strftime('%Y-%m-%d %H:%M:%S'), duration_time))
printlog ("Processed %s/%s directories" % (str(c), str(total_dirs)))
printlog ("========")
for k, v in sorted(stats.items()):
    printlog ("%s images were put in %s" % (str(v), k))

for k, v in sorted(duplicates.items()):
    printlog ("Found duplicate image: %s (already found at %s), sha1 hashes are the same." % (k, v))

if renamed_files:
    printlog ("Renamed these files:")
    for ftype, vtype in sorted(renamed_files.items()):
        printlog ("\t%s" % (str(ftype)))
        for f, v in sorted(vtype.items()):
            printlog ("\t\t%s" % (str(f)))
        printlog ()
printlog ()

if deleted_files:
    printlog ("Deleted these file types:")
    for ftype, vtype in sorted(deleted_files.items()):
        printlog ("\t%s" % (str(ftype)))
        for f, v in sorted(vtype.items()):
            printlog ("\t\t%s" % (str(f)))
        printlog ()
printlog ()

if skip_files:
    printlog ("Skipping these unknown file types:")

    for ftype, vtype in sorted(skip_files.items()):
        printlog ("\t%s" % (str(ftype)))
        for f, v in sorted(vtype.items()):
            printlog ("\t\t%s" % (str(f)))
        printlog ()

if skip_mdata:
    printlog ("Skipping these files that have no proper metadata:")

    for ftype, vtype in sorted(skip_mdata.items()):
        printlog ("\t%s" % (str(ftype)))
        for f, v in sorted(vtype.items()):
            printlog ("\t\t%s" % (str(f)))
        printlog ()

if processed_files:
    printlog ("Processed these filetypes:")
    for ftype, vtype in sorted(processed_files.items()):
        c = len(vtype['files'])
        printlog("\t%s (%s)" % (str(ftype), c))
        if c < 100:
            log_path_handle.write("Files:\n")
            log_path_handle.write("\t- " + "\n\t- ".join(files))

printlog ()
printlog ("========")
print ()
print ("You can check the log at " + log_path_file)
print ()
pause = input('press enter to exit.')
