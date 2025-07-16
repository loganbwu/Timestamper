# Timestamper

Timestamper is a Pyside6 app for adding timestamps and other routine EXIF data to your film scans or any other JPEG/TIFFs that lack valuable data for digital cataloguing. The user interface is designed to rapidly assign data when elements are often related in a roll such as the same camera and lens, or sequentially offset timestamps.

This *should* work on Mac, Windows, or Linux, but I have only test it on Mac.

![Screenshot of main screen](https://github.com/loganbwu/Timestamper/blob/main/screenshots/main_screen.png?raw=true)

## Installation

Currently there is no standalone distribution as this is developed for personal use.

1. Clone or download this repository
2. Install Exiftool (exiftool.org)
3. Install Python
4. (Optional) make a new virtual environment: `python -m venv timestamperenv` `source timestamperenv/bin/activate`
5. Install required packages: `pip install -r requirements.txt`

In theory, running `build.sh` with nuitka installed should create a standalone. I've gotten it to work before, but personal circumstances stop me from being able to offer it at the moment.

## Usage

1. Run the application with `python app.py`.
2. In the File menu (or hotkey Command/Ctrl + O) load one or more JPEGs or TIFFs from a folder
3. Preview photos in the file list (handy to match photos against your notes).
4. Enter the datetime, camera/lens, and exposure info.
5. (Optional) save your camera/lens as a preset, or select a preset.
6. Press Command/Ctrl+S to save EXIF to file. The tool auto-advances to the next photo (or previous if the next photo is 'ticked' and the previous photo is not). In general, the previous image's settings are retained in the input fields when moving to a new image with the assumption that the two images are taken consecutively, allowing for faster input.
7. With the file list selected, use the hotkeys Y-L to adjust the datetime.
8. If you need to amend a previously saved photo, re-selecting a 'ticked' photo will re-populate the previously saved EXIF. Checking 'amend' and selecting any photo will also load and populate EXIF. This can be used duplicate metadata by loading it from a photo in 'amend' mode, then selecting a new photo (missing values will not override field text in amend mode).

## Known issues

- When populating EXIF ('amend' mode or selecting a previously saved image), the preset pickers do not check if the image matches a preset. Workaround is they default to '(None)' while EXIF fields remain populated.
- When saving info, blank fields will now clear existing information, allowing for explicit removal of EXIF data.
- In general, the preset input fields (both data fields and preset selectors) might not work as expected because of how the presets are saved on the device. Have a suggestion? Create an *Issue* on Github.

## Development Plan

This section outlines the planned improvements for Timestamper, focusing on code quality, user interface (UI), user experience (UX), and new features.

### Proposed Changes

**A. Code Quality & Maintainability**

1.  **Add Docstrings and Type Hinting**: The codebase will be updated with docstrings and type hints for functions and classes to improve clarity and robustness.

**B. UI/UX Enhancements**

1.  **Add Drag-and-Drop Support**: Implement drag-and-drop functionality for image files onto the file list. The `src/timestamper/drag_drop_list_widget.py` already exists, suggesting this is a planned feature. This will need to be integrated into `main.py`.
2.  **Visual Feedback for Preset Operations**: Add visual cues (e.g., status bar messages, temporary highlights) when presets are saved or updated.
3.  **Smarter File Dialog Start Path**: Modify the file dialog to open in a more user-friendly default location.
4.  **Folder Selection in File Dialog**: Enhance the file loading mechanism to allow selecting an entire folder.

**C. New Features**

1.  **`exiftool` Path Configuration via GUI (using QSettings)**: Implement a settings dialog or menu option where users can browse for and save the path to their `exiftool` executable. This will use `QSettings` for persistence, aligning with existing preset management.

### Testing Strategy

To ensure continuous functionality, automated tests will be implemented using `pytest`. The existing test suite provides a good foundation, and new tests will be added to cover the new features and improvements.

### Developer Notes

- **Keep the test suite up to date:** Whenever you add or modify a feature, please update the tests accordingly.
- **Run tests frequently:** Run the test suite often to catch regressions early.
- **Commit discrete changes:** Make small, atomic commits with clear messages. This helps in tracking changes and debugging.
