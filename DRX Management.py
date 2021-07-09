#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""For DRX File Management"""
__author__ = "Michael<https://github.com/fukco>"
__version__ = "0.1.0"
__license__ = "MIT"

import json
import logging
import os
import pathlib
import sys
from json import JSONDecodeError

gui_mode = True


def get_bmd():
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

    return bmd


# create logger
logger = logging.getLogger("color_grading_tool")
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

pathname = os.path.dirname(sys.argv[0])
filename = "conf.json"
json_file = os.path.join(pathname, filename)
data = {}
folder = ""
lists = []

if pathlib.Path(json_file).is_file():
    try:
        f = open(json_file, mode="r", encoding="utf-8")
        logger.debug(f"Open Json File {json_file}")
        data = json.load(f)
        if data.get("DRX") and data.get("DRX").get("folder"):
            folder = data.get("DRX").get("folder")
        if data.get("DRX") and data.get("DRX").get("lists"):
            lists = data.get("DRX").get("lists")
        f.close()
    except JSONDecodeError:
        logger.error("Invalid json file!")


def main_window():
    win = dispatcher.AddWindow({
        "ID": 'MyWin',
        "WindowTitle": 'DRX Management',
        "Geometry": [600, 300, 800, 500]
    }, [
        ui.VGroup({"ID": 'root'}, [
            # Add your GUI elements here:
            ui.HGroup({"Weight": 0}, [
                ui.Label({"Text": "Folder:", "Weight": 0.25}),

                ui.Label(
                    {"ID": "fileLabelId", 'Text': folder if folder else "Please Select DRX Folder Location",
                     'Weight': 1.5,
                     'Font': ui.Font({'Family': "Times New Roman", 'PixelSize': 12})}),

                ui.Button({"Text": "Select a Folder", "ID": "SelectButton", "Weight": 0}),

                ui.Button({"Text": "Update Lists", "ID": "UpdateButton", "Weight": 0}),
            ]),

            ui.VGap(5),

            ui.HGroup([
                ui.Tree({"ID": "MyTree", "Weight": 1})
            ]),

        ]),
    ])
    # Add your GUI element based event functions here:
    itms = win.GetItems()
    # Add a header row.
    hdr = itms["MyTree"].NewItem()
    hdr["Text"][0] = "Name"
    hdr["Text"][1] = "Path"
    itms["MyTree"].SetHeaderItem(hdr)

    # Number of columns in the Tree list
    itms["MyTree"]["ColumnCount"] = 2

    # Resize the Columns
    itms["MyTree"]["ColumnWidth"][0] = 300
    itms["MyTree"]["ColumnWidth"][1] = 300

    def refresh_tree():
        itms["MyTree"].Clear()
        if lists:
            for item in lists:
                detail = itms["MyTree"].NewItem()
                detail["Text"][0] = item.get("name")
                detail["Text"][1] = item.get("path")
                itms["MyTree"].AddTopLevelItem(detail)

    def click_folder_button(ev):
        target_path = fusion.RequestDir()
        logger.info('[folder] ', target_path)
        itms["fileLabelId"]["Text"] = target_path
        global folder
        folder = target_path

    def close_win(ev):
        dispatcher.ExitLoop()

    def execute(ev):
        refresh_lists()
        refresh_tree()

    win.On.MyWin.Close = close_win
    win.On.SelectButton.Clicked = click_folder_button
    win.On.UpdateButton.Clicked = execute

    refresh_tree()
    win.Show()
    dispatcher.RunLoop()
    win.Hide()


def refresh_lists():
    if folder:
        lists.clear()
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.endswith(".drx"):
                    drx_path = os.path.join(root, file)
                    relative_path = os.path.relpath(drx_path, folder)
                    drx_name = os.path.splitext(relative_path)[0].replace(os.sep, "_")
                    lists.append({"name": drx_name, "path": drx_path})
        data.update({"DRX": {"lists": lists, "folder": folder}})
        write_file = open(json_file, mode="w", encoding="utf-8")
        json.dump(data, write_file, indent=2, ensure_ascii=False)
        write_file.close()
        logger.info("DRX file list saved!")


if __name__ == '__main__':
    bmd = get_bmd()
    resolve = bmd.scriptapp("Resolve")
    projectManager = resolve.GetProjectManager()
    project = projectManager.GetCurrentProject()
    mediaPool = project.GetMediaPool()
    rootFolder = mediaPool.GetRootFolder()
    timeline = project.GetCurrentTimeline()
    if "gui_mode" in locals().keys() and gui_mode:
        fusion = bmd.scriptapp("Fusion")
        ui = fusion.UIManager
        dispatcher = bmd.UIDispatcher(ui)
        main_window()
    else:
        refresh_lists()
