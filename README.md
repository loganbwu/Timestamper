# Timestamper

Timestamper is a desktop application built with PySide6 for adding and editing EXIF metadata to your images. It's designed for a fast, efficient workflow, especially when processing batches of photos like film scans that often lack the valuable data needed for digital cataloging.

This application should work on macOS, Windows, and Linux, provided the dependencies are met. It has been primarily tested on macOS.

![Screenshot of main screen](https://github.com/loganbwu/Timestamper/blob/main/screenshots/main_screen.png?raw=true)

## Who is this for?

Timestamper is ideal for:

-   **Film Photographers:** Easily add camera, lens, and exposure details to your scanned negatives or positives.
-   **Digital Archivists:** Add or correct timestamps and other metadata on batches of images for better organization in software like Adobe Lightroom, PhotoPrism, or Immich.
-   **Anyone needing to fix metadata:** Correct or add missing EXIF data on any JPEG or TIFF image.

## Why use Timestamper?

-   **Rapid Batch Editing:** The UI is designed for speed. After saving data for one image, the application automatically advances to the next, retaining relevant data to minimize repetitive typing.
-   **Powerful Presets:** Save and load entire camera and lens profiles. If you shoot a whole roll with the same gear, you only need to enter it once.
-   **Efficient Workflow:** Use drag-and-drop to load files and folders, and keyboard shortcuts to make quick datetime adjustments.
-   **Data Integrity:** The app uses the industry-standard `exiftool` to handle metadata, ensuring your files are modified safely.

## Features

-   **Comprehensive EXIF Editing:** Add or edit a wide range of tags, including:
    -   Date and Time (with timezone offset)
    -   Camera Make and Model
    -   Lens Make, Model, Serial Number, and Optical Characteristics (focal length, aperture)
    -   Exposure Details (ISO, F-Number, Exposure Time)
-   **Batch Processing:** Load multiple files or entire folders at once and efficiently work through them.
-   **Camera & Lens Presets:** Create, save, and manage presets for your most-used camera and lens combinations.
-   **Drag-and-Drop:** Quickly load files by dragging them directly onto the file list.
-   **Image Preview & EXIF Viewer:** See a preview of the selected image and inspect all its existing EXIF data in a clear, organized tree view.
-   **Hotkeys for Rapid Adjustments:** Use keyboard shortcuts to quickly adjust the date and time by days, hours, or minutes.
-   **Amend Mode:** Easily load, modify, and re-save the EXIF data of previously processed images.
-   **Configurable `exiftool` Path:** Set the path to your `exiftool` executable through a simple settings dialog.

## Development Plan

Here are some of the features and improvements planned for future releases:

-   **Apply to Selected:** Apply the current metadata to all selected files in the list simultaneously.
-   **Thumbnail View:** Implement a thumbnail grid view for easier visual identification of images.
-   **Undo Last Save:** Add a mechanism to revert the most recent EXIF save operation.
-   **Centralized Settings:** Expand the settings dialog to manage more application preferences.
-   **Reactive Preset Fields:** Make presets more intelligent. For example:
    -   When selecting a lens preset with a specific aperture range (e.g., f/2.8-f/22), the aperture field will automatically adjust if its current value is outside that range.
    -   When selecting a zoom lens preset (e.g., 24-70mm), the focal length field might be cleared or constrained to that range.

## Installation

This project is managed using [Rye](https://rye-up.com/), which handles Python version management and package installation.

**Prerequisites:**

1.  **Rye:** Follow the official instructions to [install Rye](https://rye-up.com/guide/installation/).
2.  **ExifTool:** Download and install `exiftool` from the [official website](https://exiftool.org/). Make a note of the path to the executable.

**Steps:**

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/loganbwu/Timestamper.git
    cd Timestamper
    ```

2.  **Install dependencies:**
    This command will automatically download the correct Python version and install all required packages into a virtual environment.
    ```bash
    rye sync
    ```

## Usage

1.  **Run the application:**
    ```bash
    rye run timestamper
    ```

2.  **Configure ExifTool:**
    The first time you run the app, go to `File -> Settings` and set the path to your `exiftool` executable. This is a one-time setup.

3.  **Load Images:**
    -   Use `File -> Open...` (or `Cmd/Ctrl+O`) to select one or more image files (JPEG, TIFF). You can also select a folder to load all supported images within it.
    -   Alternatively, drag and drop files or folders onto the file list.

4.  **Enter EXIF Data:**
    -   Select a file from the list on the left. A preview and its existing EXIF data will appear on the right.
    -   Fill in the fields with the desired information.
    -   To speed things up, save your camera and lens information as presets using the `+` button. You can then select them from the dropdown menu.

5.  **Save Data:**
    -   Press `Cmd/Ctrl+S` to save the EXIF data to the current file.
    -   The application will mark the file as "done" (✓) and automatically select the next unprocessed image in the list.

6.  **Amend Data (Optional):**
    -   If you need to correct a previously saved image, simply select it from the list. The saved data will populate the fields.
    -   Alternatively, check the "Amend Mode" box to load EXIF data from any selected image without auto-advancing. This is useful for copying metadata from one file to another.

# Current issues
- If the exiftool path is not specified (or not found), the program gives an error but does not help the user fix the issue. You can't guarantee people will read the README so the GUI should guide people to install exiftool if not available.
- There is no GUI indication of how to access the settings dialog (either through the Files dropdown, which would also display the shortcut Command+, , or as a GUI button in the window).
- There is no visual indication in the files list pane for which files have had their EXIF data modified and saved in the current session, like there used to be before switching to the thumbnail display. (I used to put a tick in front of the filename)
- The thumbnail display in the files list pane has too much padding between the thumbnail and the filename. It could be more compact.
- Manually editing the timezone input using the keyboard gets reverted when focusing off the input. Only clicking the +/- buttons successfully modifies the timezone.
