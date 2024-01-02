# Timestamper

Timestamper is a Pyside6 app for adding timestamps and other routine EXIF data to your film scans or any other JPEG/TIFFs that lack valuable data for digital cataloguing. The user interface is designed to rapidly assign data when elements are often related in a roll such as the same camera and lens, or sequentially offset timestamps.

Select all images in a folder of scans then use the hotkeys and preset controls to rapidly save metadata.

## Installation

Current there is no standalone distribution and `requirements.txt` has not been tested.

1. Install Python
2. Install required packages (if `requirements.txt` doesn't work, inspect `main.py` and `app.py`)
3. Run `app.py`

## Usage

1. Install Exiftool (exiftool.org)
2. In the File menu (or hotkey Command/Ctrl + O) load one or more JPEGs or TIFFs from a folder
3. Preview photos in the file list (handy to match photos against your notes)
4. Enter the datetime, camera/lens, and exposure info
5. (Optional) save your camera/lens as a preset, or select a preset
6. Press Command/Ctrl+S to save EXIF to file. Auto-advances to the next photo (or previous if the next photo is 'ticked' and the previous photo is not)
7. With the file list selected, use the hotkeys Y-L to quickly adjust the datetime (useful if the files are named alphabetically and chronologically, either forwards or in reverse as provided by some labs)
8. If you need to amend a previously saved photo, re-selecting a 'ticked' photo will re-load the previously saved EXIF. Similarly, checking 'amend' and selecting any photo will also re-load the EXIF. This can be used copy/paste EXIF by loading it from a photo in 'amend' mode, then selecting a new photo with no EXIF (no EXIF will not overwrite field text in amend mode)
