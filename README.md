# Timestamper

Timestamper is a Pyside6 app for adding timestamps and other routine EXIF data to your film scans or any other JPEG/TIFFs that lack valuable data for digital cataloguing. The user interface is designed to rapidly assign data when elements are often related in a roll such as the same camera and lens, or sequentially offset timestamps.

Select all images in a folder of scans then use the hotkeys and preset controls to rapidly save metadata.

## Installation

Currently there is no standalone distribution as this is developed for personal use.

1. Clone or download this repository
2. Install Exiftool (exiftool.org)
3. Install Python
4. (Optional) make a new virtual environment: `python -m venv timestamperenv` `source timestamperenv/bin/activate`
5. Install required packages: `pip install -r requirements.txt`

## Usage

1. Run `python app.py`
2. In the File menu (or hotkey Command/Ctrl + O) load one or more JPEGs or TIFFs from a folder
3. Preview photos in the file list (handy to match photos against your notes).
4. Enter the datetime, camera/lens, and exposure info.
5. (Optional) save your camera/lens as a preset, or select a preset.
6. Press Command/Ctrl+S to save EXIF to file. The tool auto-advances to the next photo (or previous if the next photo is 'ticked' and the previous photo is not).
7. With the file list selected, use the hotkeys Y-L to adjust the datetime.
8. If you need to amend a previously saved photo, re-selecting a 'ticked' photo will re-load the previously saved EXIF. Similarly, checking 'amend' and selecting any photo will also re-load the EXIF. This can be used duplicate EXIF by loading it from a photo in 'amend' mode, then selecting a new photo (missing EXIF will not override field text in amend mode).
