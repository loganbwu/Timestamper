"""EXIF data management for the Timestamper application."""

import logging
from typing import Dict, Any, Optional
import exiftool
from PySide6.QtCore import QDateTime, Qt

from .constants import (
    EXIF_DATE_TIME_ORIGINAL,
    EXIF_EXPOSURE_TIME,
    EXIF_LENS_INFO,
    EXIF_MAKE,
    EXIF_MODEL,
    EXIF_OFFSET_TIME,
    EXIF_OFFSET_TIME_ORIGINAL,
    EXIF_SHUTTER_SPEED
)
from .utils import float_to_shutterspeed, parse_lensinfo

logger = logging.getLogger(__name__)


class ExifManager:
    """Manages EXIF data operations for image files."""
    
    def __init__(self, exiftool_path: str):
        """Initialize the EXIF manager with the path to exiftool."""
        self.exiftool_path = exiftool_path
    
    def load_exif_data(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load EXIF data from a file."""
        try:
            with exiftool.ExifToolHelper(executable=self.exiftool_path) as et:
                exif_data = et.get_metadata(file_path)[0]
                logger.info(f'Loaded EXIF for "{file_path}"')
                return exif_data
        except Exception as e:
            logger.error(f'Error loading EXIF for "{file_path}": {e}')
            return None
    
    def save_exif_data(self, file_path: str, tags: Dict[str, str]) -> bool:
        """Save EXIF data to a file."""
        try:
            with exiftool.ExifToolHelper(executable=self.exiftool_path) as et:
                et.set_tags(file_path, tags=tags, params=["-overwrite_original"])
            logger.info(f'Saved EXIF to file: {tags}')
            return True
        except Exception as e:
            logger.error(f'Error saving EXIF to "{file_path}": {e}')
            return False
    
    def format_exif_for_display(self, exif_data: Dict[str, Any]) -> Dict[str, list]:
        """Format EXIF data for display in the tree widget."""
        data = {}
        for k, v in sorted(exif_data.items()):
            if ":" in k:
                prefix, name = k.split(":")
                if name in ["ShutterSpeedValue", "ExposureTime"]:
                    v = f"{float_to_shutterspeed(v)}s"
                if prefix in data:
                    data[prefix].append([name, v])
                else:
                    data[prefix] = [[name, v]]
        
        # Move EXIF to the front if it exists
        if "EXIF" in data:
            data = {"EXIF": data.pop("EXIF"), **data}
        
        return data
    
    def extract_datetime_from_exif(self, exif_data: Dict[str, Any]) -> Optional[QDateTime]:
        """Extract datetime from EXIF data and return as QDateTime."""
        if EXIF_DATE_TIME_ORIGINAL in exif_data:
            iso_dt = exif_data[EXIF_DATE_TIME_ORIGINAL].replace(":", "-", 2)
            return QDateTime.fromString(iso_dt, format=Qt.DateFormat.ISODate)
        return None
    
    def extract_offset_time_from_exif(self, exif_data: Dict[str, Any]) -> Optional[str]:
        """Extract offset time from EXIF data."""
        offsettime_keys = [EXIF_OFFSET_TIME_ORIGINAL, EXIF_OFFSET_TIME]
        for k in offsettime_keys:
            if k in exif_data:
                return exif_data[k]
        return None
    
    def extract_shutter_speed_from_exif(self, exif_data: Dict[str, Any]) -> Optional[str]:
        """Extract shutter speed from EXIF data."""
        shutter_keys = [EXIF_EXPOSURE_TIME, EXIF_SHUTTER_SPEED]
        for k in shutter_keys:
            if k in exif_data:
                return float_to_shutterspeed(exif_data[k])
        return None
    
    def extract_lens_info_from_exif(self, exif_data: Dict[str, Any]) -> Optional[list]:
        """Extract lens info from EXIF data and parse it."""
        if EXIF_LENS_INFO in exif_data:
            return parse_lensinfo(exif_data[EXIF_LENS_INFO])
        return None
    
    def prepare_tags_for_save(self, form_data: Dict[str, str]) -> Dict[str, str]:
        """Prepare EXIF tags from form data for saving."""
        # Handle lens info construction
        a = form_data.get('widefocallength', '')
        b = form_data.get('longfocallength', '')
        if a and not b:
            b = a
        c = form_data.get('wideaperturevalue', '')
        d = form_data.get('longaperturevalue', '')
        if c and not d:
            d = c
        lensinfo = f"{a} {b} {c} {d}"
        logger.info(f"LensInfo: {lensinfo}")
        
        tags = {
            "DateTimeOriginal": form_data.get('datetime_original', ''),
            "OffsetTimeOriginal": form_data.get('offset_time_original', ''),
            "OffsetTime": form_data.get('offset_time', ''),
            "Make": form_data.get('make', ''),
            "Model": form_data.get('model', ''),
            "MaxApertureValue": form_data.get('wideaperturevalue', ''),
            "ISO": form_data.get('iso', ''),
            "LensMake": form_data.get('lensmake', ''),
            "LensModel": form_data.get('lensmodel', ''),
            "LensInfo": lensinfo,
            "LensSerialNumber": form_data.get('lensserialnumber', ''),
            "FocalLength": form_data.get('focallength', '').removesuffix("mm"),
            "FNumber": form_data.get('fnumber', ''),
            "ExposureTime": form_data.get('exposuretime', ''),
            "ShutterSpeedValue": form_data.get('exposuretime', '')
        }
        
        # Return only non-empty tags
        return {k: v for k, v in tags.items() if v}
