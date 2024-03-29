#!/usr/bin/env python
import logging
import os
import platform
import sys
from ctypes import cdll, c_char_p, c_bool, Structure

from get_resolve import get_bmd

__author__ = "Michael<https://github.com/fukco>"
__version__ = "0.5.0"
__license__ = "MIT"

fields_list = [
    ("IsSupportMedia", c_bool),
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
    # ("Shutter", c_char_p),
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
    ("ND Filter", c_char_p),
    ("Compression Ratio", c_char_p),
    ("Codec Bitrate", c_char_p),
    ("Sensor Area Captured", c_char_p),
    ("PAR Notes", c_char_p),
    ("Aspect Ratio Notes", c_char_p),
    ("Gamma Notes", c_char_p),
    ("Color Space Notes", c_char_p)]


class DRMetadata(Structure):
    _fields_ = fields_list

    def get_dict(self):
        return dict((f, getattr(self, f)) for f, _ in self._fields_)


def get_clips(folder, result):
    result.extend(folder.GetClipList())
    sub_folders = folder.GetSubFolders()
    for sub_folder in sub_folders.values():
        get_clips(sub_folder, result)


def get_cdll_lib():
    path = os.path.dirname(sys.argv[0])
    if sys.platform.startswith("win") or sys.platform.startswith("cygwin"):
        library = os.path.join(path, "resolve-metadata.dll")
    else:
        if platform.machine() == "x86_64":
            library = os.path.join(path, "resolve-metadata-amd64.dylib")
        else:
            library = os.path.join(path, "resolve-metadata-arm64.dylib")
    lib = cdll.LoadLibrary(library)
    lib.DRProcessMediaFile.argtypes = [c_char_p]
    lib.DRProcessMediaFile.restype = DRMetadata
    return lib


def success_message(num):
    bmd = get_bmd()
    fusion = bmd.scriptapp("Fusion")
    ui = fusion.UIManager
    disp = bmd.UIDispatcher(ui)
    win = disp.AddWindow({
        'ID': 'MyWin',
        'WindowTitle': 'Notification',
        'Spacing': 10, }, [

        ui.VGroup({'ID': 'root'}, [

            ui.HGroup([
                ui.Label({
                    'Text': f"{num} clips in media pool has been parsed.\nMore details in console.",
                    'Alignment': {'AlignHCenter': True, 'AlignVCenter': True},
                })
            ]),

            ui.HGroup({
                'Weight': 0,
            }, [
                ui.Button({
                    'ID': 'B',
                    'Text': 'OK',
                })
            ]),
        ]),
    ])
    win.Resize([400, 120])
    win.RecalcLayout()

    def close(ev):
        disp.ExitLoop()

    win.On['MyWin'].Close = close
    win.On['B'].Clicked = close

    win.Show()
    disp.RunLoop()
    win.Hide()


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

    logger.info("Processing...")
    resolve = get_bmd().scriptapp("Resolve")
    projectManager = resolve.GetProjectManager()
    project = projectManager.GetCurrentProject()
    mediaPool = project.GetMediaPool()
    rootFolder = mediaPool.GetRootFolder()

    clips = []
    get_clips(rootFolder, clips)

    lib = get_cdll_lib()
    n = 0
    for clip in clips:
        file_path = clip.GetClipProperty("File Path")
        if len(file_path) > 0:
            resolve_meta_dict = lib.DRProcessMediaFile(file_path.encode("utf-8")).get_dict()
            if resolve_meta_dict:
                if not resolve_meta_dict["IsSupportMedia"]:
                    logger.warning(f"{os.path.basename(file_path)} Not Supported.")
                    continue
                else:
                    del resolve_meta_dict["IsSupportMedia"]
                    meta = {k: v for k, v in resolve_meta_dict.items() if v}
                    if not meta:
                        logger.debug(f"Ignore clip {os.path.basename(file_path)}.")
                    else:
                        if clip.SetMetadata(meta):
                            logger.debug(f"Process {os.path.basename(file_path)} Successfully.")
                            n += 1
                        else:
                            logger.error(f"Failed to set {os.path.basename(file_path)} metadata!")
            else:
                logger.error(f"Failed to parse clip {clip.GetName()}")
    logger.info("Done.")
    success_message(n)
