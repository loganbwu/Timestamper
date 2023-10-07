import exiftool

files = ["/Users/wu.l/Desktop/2023-09-08/IMG_3697-Edit.jpg"]
with exiftool.ExifToolHelper(executable="/Users/wu.l/Pictures/Lightroom/Plugins/LensTagger-1.9.2.lrplugin/bin/exiftool") as et:
    d = et.get_metadata(files[0])[0]
    # for d in metadata:
    for k, v in d.items():
        if "EXIF" in k:
            print(f'{k}: {v}')