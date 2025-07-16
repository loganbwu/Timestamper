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

1.  **Uncomment and Fix `on_wideaperturevalue_editingfinished`**: The function `on_wideaperturevalue_editingfinished` is currently commented out in `main.py`. It will be uncommented and its signal connection restored to ensure it works as intended.
2.  **Refactor Large Functions**: The `select_file_from_list` and `save` functions in `main.py` will be broken down into smaller, more focused functions to improve readability and maintainability.
3.  **Add Docstrings and Type Hinting**: The codebase will be updated with docstrings and type hints for functions and classes to improve clarity and robustness.
4.  **Improve `pyproject.toml`**: The `pyproject.toml` file will be updated to include more project metadata, such as the version, author, and description, to align with modern Python packaging standards.

**B. UI/UX Enhancements**

1.  **Improve Preset Matching on Load**: When a file is loaded, its EXIF data will be automatically matched to saved presets, selecting the correct camera and lens from the dropdowns.
2.  **Add Drag-and-Drop Support**: Users will be able to drag and drop image files directly onto the file list for quicker loading.
3.  **Visual Feedback for Preset Operations**: Clearer visual feedback will be added for saving or updating a preset.
4.  **Smarter File Dialog Start Path**: The file dialog will open in a more user-friendly location (e.g., the user's home or pictures folder) instead of the application's directory.
5.  **Folder Selection in File Dialog**: Users will be able to select a folder to load all supported image files within it.

**C. New Features**

1.  **Configuration File**: Support for a user-editable configuration file (e.g., `config.ini`) will be added for settings like the `exiftool` path.

### Testing Strategy

To ensure continuous functionality, automated tests will be implemented using `pytest`. The existing test suite provides a good foundation, and new tests will be added to cover the new features and improvements.
