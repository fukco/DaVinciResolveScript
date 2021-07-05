#!/usr/bin/env python
import collections
import logging
import sys

__author__ = "Michael<https://github.com/fukco>"
__version__ = "0.2.0"
__license__ = "MIT"

gui_mode = True  # True or False
# Option 0:All 1:Same Clip 2:Same Camera Type 3:Same Camera Serial # 4:Same Keywords
# 5:Same Color Space 6:Same Clip Color 7:Same Flags
default_option = 1
default_assign_color_version = True  # True or False
default_color_version_name = "Auto Generate Color Version"


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


options = ['All', 'Same Clip', 'Same Camera Type', 'Same Camera Serial #', 'Same Keywords', 'Same Input Color Space',
           'Same Clip Color', 'Same Flags']
color_version_name_placeholder = "Auto Generate Color Version"

# create logger
logger = logging.getLogger("color_grading_copy_tool")
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


def get_all_timeline_item():
    track_count = timeline.GetTrackCount("video")
    result = []
    for index in range(track_count):
        items = timeline.GetItemListInTrack("video", index)
        if items and len(items) > 0:
            result.extend(items)
    return result


def handle_color_version(timeline_items, assign_color_version, color_version_name):
    if assign_color_version:
        for item in timeline_items:
            if not item.LoadVersionByName(color_version_name, 0):
                item.AddVersion(color_version_name, 0)


def copy_grading(timeline_item, option, assign_color_version, color_version_name):
    logger.debug(
        "Current timelineItem is {}, Option is {}, Assign color version is {}, Color version name is {}".format(
            timeline_item.GetName(), option, assign_color_version, color_version_name))
    timeline_items = get_all_timeline_item()
    target_items = []
    if option == options[0]:  # All
        target_items = timeline_items
    elif option == options[1]:  # Same Clip
        for item in timeline_items:
            if item.GetMediaPoolItem().GetClipProperty(
                    "File Path") == timeline_item.GetMediaPoolItem().GetClipProperty("File Path"):
                target_items.append(item)
    elif option == options[5]:  # Same Input Color Space
        for item in timeline_items:
            if item.GetMediaPoolItem().GetClipProperty(
                    "Input Color Space") == timeline_item.GetMediaPoolItem().GetClipProperty(
                "Input Color Space"):
                target_items.append(item)
    elif option == options[6]:  # Clip Color
        for item in timeline_items:
            if item.GetClipColor() == timeline_item.GetClipColor():
                target_items.append(item)
    elif option == options[7]:  # Flags
        for item in timeline_items:
            if item.GetFlags() == timeline_item.GetFlags():
                target_items.append(item)
    else:
        param = option.lstrip("Same ")
        if param == "Keywords":
            for item in timeline_items:
                if collections.Counter(item.GetMediaPoolItem().GetMetadata(param).split(",")) == collections.Counter(
                        timeline_item.GetMediaPoolItem().GetMetadata(param).split(",")):
                    target_items.append(item)
        else:
            for item in timeline_items:
                if item.GetMediaPoolItem().GetMetadata(param) == timeline_item.GetMediaPoolItem().GetMetadata(
                        param):
                    target_items.append(item)
    handle_color_version(target_items, assign_color_version, color_version_name)
    if len(target_items) > 0 and not timeline_item.CopyGrades(target_items):
        logger.error("copy failed {}".format(target_items))
        return False
    logger.info("Copy Grading Execute finished.")
    return True


def main_window():
    win = dispatcher.AddWindow({
        "ID": 'MyWin',
        "WindowTitle": 'Color Grading Copy Tool',
        "Geometry": [600, 300, 500, 140]
    }, [
        ui.VGroup({"ID": 'root'}, [
            # Add your GUI elements here:
            ui.HGroup([
                ui.Label({
                    "Text": 'Copy To Timeline:',
                }),

                ui.ComboBox({
                    "ID": 'MyCombo'
                }),
            ]),

            ui.HGroup([
                ui.CheckBox({
                    "ID": 'MyCheckbox',
                    "Text": 'Assign Color Version'
                }),

                ui.LineEdit({
                    "ID": 'MyLineTxt',
                    "PlaceholderText": color_version_name_placeholder,
                }),
            ]),

            ui.HGroup([
                ui.Label({
                    "ID": "InfoLabel"
                })
            ]),

            ui.HGroup([
                ui.Button(
                    {
                        "Text": "Execute",
                        "ID": "Execute"
                    }

                )
            ]),
        ]),
    ])
    # Add your GUI element based event functions here:
    itm = win.GetItems()

    # Add the items to the ComboBox menu
    for option in options:
        itm["MyCombo"].AddItem(option)

    itm["MyCombo"]["CurrentIndex"] = 1

    # The window was closed
    def close_win(ev):
        dispatcher.ExitLoop()

    def execute(ev):
        current_timeline_item = timeline.GetCurrentVideoItem()
        if not current_timeline_item:
            show_message("Please open [Edit] or [Color] page to choose one timeline item!", 1)
            logger.warning("Please open [Edit] or [Color] page to choose one timeline item!")
            return
        option = itm["MyCombo"]["CurrentText"]
        assign_color_version = itm["MyCheckbox"]["Checked"]
        color_version_name = itm["MyLineTxt"]["Text"]
        if not color_version_name:
            color_version_name = color_version_name_placeholder
        if copy_grading(current_timeline_item, option, assign_color_version, color_version_name):
            show_message("Finished.")
        else:
            show_message("Some error occurred, Please check log details!")

    def show_message(message, t=0):
        if t == 0:
            itm["InfoLabel"]["Text"] = f"<font color='#39CA41'>{message}</font>"
        elif t == 1:
            itm["InfoLabel"]["Text"] = f"<font color='#922626'>{message}</font>"

    win.On.MyWin.Close = close_win
    win.On.Execute.Clicked = execute

    win.Show()
    dispatcher.RunLoop()
    win.Hide()


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
        current_timeline_item = timeline.GetCurrentVideoItem()
        if current_timeline_item:
            copy_grading(current_timeline_item, default_option, default_assign_color_version,
                         default_color_version_name)
        else:
            logger.warning("Please open [Edit] or [Color] page to choose one timeline item!")
