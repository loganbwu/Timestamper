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

1. Run `python app.py`
2. In the File menu (or hotkey Command/Ctrl + O) load one or more JPEGs or TIFFs from a folder
3. Preview photos in the file list (handy to match photos against your notes).
4. Enter the datetime, camera/lens, and exposure info.
5. (Optional) save your camera/lens as a preset, or select a preset.
6. Press Command/Ctrl+S to save EXIF to file. The tool auto-advances to the next photo (or previous if the next photo is 'ticked' and the previous photo is not). In general, the previous image's settings are retained in the input fields when moving to a new image with the assumption that the two images are taken consecutively, allowing for faster input.
7. With the file list selected, use the hotkeys Y-L to adjust the datetime.
8. If you need to amend a previously saved photo, re-selecting a 'ticked' photo will re-populate the previously saved EXIF. Checking 'amend' and selecting any photo will also load and populate EXIF. This can be used duplicate metadata by loading it from a photo in 'amend' mode, then selecting a new photo (missing values will not override field text in amend mode).

## Known issues

- When populating EXIF ('amend' mode or selecting a previously saved image), the preset pickers do not check if the image matches a preset. Workaround is they default to '(None)' while EXIF fields remain populated.
- When saving info, blank fields are not used, to avoid deleting existing information. However, this means there is currently no way to clear information.
- In general, the preset input fields (both data fields and preset selectors) might not work as expected because of how the presets are saved on the device. Have a suggestion? Create an *Issue* on Github.

## Development Plan

This section outlines the planned improvements for Timestamper, focusing on code quality, user interface (UI), user experience (UX), and testing.

### Proposed Changes

**A. Code Quality Improvements:**
1.  **Refactor datetime adjustment button connections:** Consolidate individual button connections into a more concise loop. [x]
2.  **Centralize constants:** Move hardcoded values (e.g., UI dimensions, magic strings) into a dedicated constants file or class for better maintainability. [x]
3.  **Improve error handling for Exiftool:** Implement more specific `try-except` blocks for `exiftool` operations and provide user-friendly error messages. [x]
4.  **Abstract preset management logic:** Create generic helper functions to reduce code duplication across camera and lens preset management. [x]
5.  **Implement proper logging:** Replace `print` statements with Python's `logging` module for controlled and flexible output. [x]
6.  **Fix typo in `on_wideaperturevalue_editingfinished`:** Correct a variable name typo to ensure proper function. [x]
7.  **Validate input for `save` function:** Add validation for numeric input fields before saving to EXIF. [x]

**B. UI/UX Enhancements:**
1.  **Visual feedback for save operations:** Display a temporary status message (e.g., in a status bar) after successful EXIF data saves. [x]
2.  **"Browse" button for Exiftool path:** Add a button next to the Exiftool path input field for easy executable selection. [x]
3.  **Clear fields functionality:** Implement a mechanism to clear all input fields, allowing users to explicitly remove EXIF data. [x]
4.  **Improve preset management UX:** Enhance feedback for saving/updating presets and address the default '(None)' issue in preset pickers. [x]
5.  **Dynamic image preview resizing:** Ensure the image preview area resizes dynamically with the window while maintaining aspect ratio. [x]
6.  **Tooltips for hotkeys:** Use tooltips to display hotkeys for datetime adjustment buttons for a cleaner UI. [x]
7.  **Refine "Amend mode" clarity:** Consider renaming "Amend mode" to a more intuitive label (e.g., "Load EXIF for Editing") and provide clearer visual cues. [x]

### Testing Strategy

To ensure continuous functionality, automated tests will be implemented using `pytest`.

**Initial Steps:**
1.  Add `pytest` to `requirements.txt`. [x]
2.  Create a `tests/` directory. [x]
3.  Create `tests/test_main.py` and `tests/test_offset_spin_box.py`. [x]
4.  Implement unit tests for utility functions (`float_to_shutterspeed`, `parse_lensinfo`, `textFromValue`, `valueFromText`). [x]
5.  Utilize `unittest.mock` to mock `exiftool` interactions for isolated testing of application logic. [x]
