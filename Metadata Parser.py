#!/usr/bin/env python
import logging
import os
import sys
from ctypes import cdll, c_char_p, Structure

__author__ = "Michael<https://github.com/fukco>"
__version__ = "0.1.0"
__license__ = "MIT"

fields_list = [
    ("Camera Type", c_char_p),
    ("Camera Manufacturer", c_char_p),
    ("Camera Serial #", c_char_p),
    ("Camera ID", c_char_p),
    ("Camera Notes", c_char_p),
    ("Camera Format", c_char_p),
    ("Media Type", c_char_p),
    ("Time-Lapse Interval", c_char_p),
    ("Camera FPS", c_char_p),
    ("Shutter Type", c_char_p),
    ("Shutter", c_char_p),
    ("ISO", c_char_p),
    ("White Point (Kelvin)", c_char_p),
    ("White Balance Tint", c_char_p),
    ("Camera Firmware", c_char_p),
    ("Lens Type", c_char_p),
    ("Lens Number", c_char_p),
    ("Lens Notes", c_char_p),
    ("Camera Aperture Type", c_char_p),
    ("Camera Aperture", c_char_p),
    ("Focal Point (mm)", c_char_p),
    ("Distance", c_char_p),
    ("Filter", c_char_p),
    ("Nd Filter", c_char_p),
    ("Compression Ratio", c_char_p),
    ("Codec Bitrate", c_char_p),
    ("Aspect Ratio Notes", c_char_p),
    ("Gamma Notes", c_char_p),
    ("Color Space Notes", c_char_p)]


class DRMetadata(Structure):
    _fields_ = fields_list

    def get_dict(self):
        return dict((f, getattr(self, f)) for f, _ in self._fields_)


def GetResolve():
    try:
        # The PYTHONPATH needs to be set correctly for this import statement to work.
        # An alternative is to import the DaVinciResolveScript by specifying absolute path (see ExceptionHandler logic)
        import DaVinciResolveScript as bmd
    except ImportError:
        if sys.platform.startswith("darwin"):
            expectedPath = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules/"
        elif sys.platform.startswith("win") or sys.platform.startswith("cygwin"):
            import os
            expectedPath = os.getenv(
                'PROGRAMDATA') + "\\Blackmagic Design\\DaVinci Resolve\\Support\\Developer\\Scripting\\Modules\\"
        elif sys.platform.startswith("linux"):
            expectedPath = "/opt/resolve/libs/Fusion/Modules/"

        # check if the default path has it...
        # print("Unable to find module DaVinciResolveScript from $PYTHONPATH - trying default locations")
        try:
            import imp
            bmd = imp.load_source('DaVinciResolveScript', expectedPath + "DaVinciResolveScript.py")
        except ImportError:
            # No fallbacks ... report error:
            print(
                "Unable to find module DaVinciResolveScript - please ensure that the module DaVinciResolveScript is discoverable by python")
            print(
                "For a default DaVinci Resolve installation, the module is expected to be located in: " + expectedPath)
            sys.exit()

    return bmd.scriptapp("Resolve")


def get_clips(folder, result):
    result.extend(folder.GetClipList())
    sub_folders = folder.GetSubFolders()
    for sub_folder in sub_folders.values():
        get_clips(sub_folder, result)


if __name__ == "__main__":
    # create logger
    logger = logging.getLogger("metadata_parser")
    logger.setLevel(logging.DEBUG)
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)

    resolve = GetResolve()
    projectManager = resolve.GetProjectManager()
    project = projectManager.GetCurrentProject()
    mediaPool = project.GetMediaPool()
    rootFolder = mediaPool.GetRootFolder()

    clips = []
    get_clips(rootFolder, clips)

    result = {}
    ext = ".so"
    path = os.path.dirname(sys.argv[0])
    if sys.platform.startswith("win") or sys.platform.startswith("cygwin"):
        ext = ".dll"
    library = os.path.join(path, f"resolve-metadata{ext}")
    lib = cdll.LoadLibrary(library)
    lib.DRProcessMediaFile.argtypes = [c_char_p]
    lib.DRProcessMediaFile.restype = DRMetadata
    for clip in clips:
        file_path = clip.GetClipProperty("File Path")
        if len(file_path) > 0:
            resolve_meta_dict = result.get(file_path)
            if not resolve_meta_dict:
                resolve_meta_dict = lib.DRProcessMediaFile(file_path.encode("utf-8")).get_dict()
                result[file_path] = resolve_meta_dict
            meta = {k: v for k, v in resolve_meta_dict.items() if v}
            if clip.SetMetadata(meta):
                logger.debug(f"Processed {os.path.basename(file_path)} Successfully.")
            else:
                logger.error(f"Processed {os.path.basename(file_path)} Unsuccessfully!")
    logger.info("Done.")