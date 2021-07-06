#!/usr/bin/env python
"""For DaVinci Resolve Color Grading"""
__author__ = "Michael<https://github.com/fukco>"
__version__ = "0.2.0"
__license__ = "MIT"

import json
import logging
import os
import pathlib
import sys

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


class ColorSpaceMatchRule:
    def __init__(self, manufacturer, gamma_notes, color_space_notes, input_color_space):
        self.manufacturer = manufacturer
        self.gamma_notes = gamma_notes
        self.color_space_notes = color_space_notes
        self.input_color_space = input_color_space


# create logger
logger = logging.getLogger("RCM_Color_Space_Match")
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

color_space_match_rules = "Color Space Match Rules"
custom_rules = "Custom Rules"
default_color_version_name = "Auto Generate Color Version"
color_space_match_list = [ColorSpaceMatchRule("Atomos", "CLog", "Cinema", "Canon Cinema Gamut/Canon Log"),
                          ColorSpaceMatchRule("Atomos", "CLog2", "Cinema", "Canon Cinema Gamut/Canon Log2"),
                          ColorSpaceMatchRule("Atomos", "CLog3", "Cinema", "Canon Cinema Gamut/Canon Log3"),
                          ColorSpaceMatchRule("Atomos", "F-Log", "F-Gamut", "FujiFilm F-Log"),
                          ColorSpaceMatchRule("Atomos", "V-Log", "V-Gamut", "Panasonic V-Gamut/V-Log"),
                          ColorSpaceMatchRule("Atomos", "SLog3", "SGamut3.cine", "S-Gamut3.Cine/S-Log3"),
                          ColorSpaceMatchRule("Atomos", "SLog3", "SGamut3", "S-Gamut3/S-Log3"),
                          ColorSpaceMatchRule("Atomos", "N-Log", "BT.2020", "Nikon N-Log"),
                          ColorSpaceMatchRule("Atomos", "HLG", "BT.2020", "Rec.2100 HLG"),

                          ColorSpaceMatchRule("Fujifilm", "F-log", "", "FujiFilm F-Log"),

                          ColorSpaceMatchRule("Panasonic", "V-Log", "V-Gamut", "Panasonic V-Gamut/V-Log"),

                          ColorSpaceMatchRule("Sony", "s-log3-cine", "s-gamut3-cine", "S-Gamut3.Cine/S-Log3"),
                          ColorSpaceMatchRule("Sony", "s-log3", "s-gamut3", "S-Gamut3/S-Log3"),
                          ]
color_space_match_map = {}
input_color_space_list = []
for item in color_space_match_list:
    color_space_match_map[(item.gamma_notes, item.color_space_notes)] = item.input_color_space
    if item.input_color_space not in input_color_space_list:
        input_color_space_list.append(item.input_color_space)

data = {}
if pathlib.Path(json_file).is_file():
    f = open(json_file, mode="r", encoding="utf-8")
    logger.debug(f"Open Json File {json_file}")
    data = json.load(f)
    f.close()

if not data.get(color_space_match_rules):
    data.update({color_space_match_rules: {"_comments": "this is for RCM only!"}})
if not data.get(color_space_match_rules).get("rules"):
    match_rules = {"rules": []}
    manufacturers = []
    for item in color_space_match_list:
        if item.manufacturer in manufacturers:
            index = manufacturers.index(item.manufacturer)
            match_rules["rules"][index]["details"].append(
                {"Gamma Notes": item.gamma_notes, "Color Space Notes": item.color_space_notes,
                 "Input Color Space": item.input_color_space})
        else:
            manufacturers.append(item.manufacturer)
            match_rules["rules"].append({"manufacturer": item.manufacturer, "details": [
                {"Gamma Notes": item.gamma_notes, "Color Space Notes": item.color_space_notes,
                 "Input Color Space": item.input_color_space}]})
    data[color_space_match_rules].update(match_rules)
    f = open(json_file, mode="w", encoding="utf-8")
    json.dump(data, f, indent=2, ensure_ascii=False)
    logger.debug(f"Color Match Rules Not Found, Write Json File {json_file}")
    f.close()


def main_window():
    # some element IDs
    win_id = "com.xiaoli.RCMColorSpaceMatch"  # should be unique for single instancing
    tree_id = "MatchTree"
    gamma_notes = "Gamma Notes"
    color_space_notes = "Color Space Notes"
    input_color_space = "Input Color Space"

    # check for existing instance
    win = ui.FindWindow(win_id)
    if win:
        win.Show()
        win.Raise()
        exit()

    # define the window UI layout
    win = dispatcher.AddWindow({
        'ID': win_id,
        'Geometry': [600, 100, 800, 400],
        'WindowTitle': "RCM Color Space Match",
    },
        ui.VGroup([
            # color space match rule
            ui.Tree({"ID": tree_id}),

            ui.HGroup({"Weight": 0}, [
                ui.Button({"Text": "Match", "ID": "ExecuteButton", "Weight": 0}),
                ui.HGap(5),
                ui.Label({'Font': ui.Font({'Family': "Times New Roman"}), "ID": "InfoLabel"})
            ]),
        ])
    )

    def init_tree():
        items = win.GetItems()

        # Add a header row.
        hdr = items[tree_id].NewItem()
        hdr["Text"][0] = gamma_notes
        hdr["Text"][1] = color_space_notes
        hdr["Text"][2] = input_color_space
        items[tree_id].SetHeaderItem(hdr)

        # Number of columns in the Tree list
        items[tree_id]["ColumnCount"] = 3

        # Resize the Columns
        items[tree_id]["ColumnWidth"][0] = 200
        items[tree_id]["ColumnWidth"][1] = 200
        items[tree_id]["ColumnWidth"][2] = 360

    def show_message(message, t=0):
        if t == 0:
            win.GetItems()["InfoLabel"]["Text"] = f"<font color='#39CA41'>{message}</font>"
        elif t == 1:
            win.GetItems()["InfoLabel"]["Text"] = f"<font color='#922626'>{message}</font>"

    def load_color_space_match_rule():
        for manufacturerRule in data[color_space_match_rules]["rules"]:
            items = win.GetItems()
            item = items[tree_id].NewItem()
            item["Text"][0] = manufacturerRule["manufacturer"]
            items[tree_id].AddTopLevelItem(item)
            for rule in manufacturerRule["details"]:
                item_child = items[tree_id].NewItem()
                item_child["Text"][0] = rule[gamma_notes]
                item_child["Text"][1] = rule[color_space_notes]
                item_child["Text"][2] = rule[input_color_space]
                item.AddChild(item_child)

    def click_execute_button(ev):
        logger.info("Start Processing.")
        show_message("Processing...")
        if execute():
            show_message("All Down. Have Fun!")
        else:
            show_message("Some process failed, please check console log details.", 1)

    def close(ev):
        dispatcher.ExitLoop()

    init_tree()
    load_color_space_match_rule()

    # assign event handlers
    win.On[win_id].Close = close
    win.On["ExecuteButton"].Clicked = click_execute_button
    win.Show()
    dispatcher.RunLoop()
    win.Hide()


def get_clips(folder, result):
    result.extend(folder.GetClipList())
    sub_folders = folder.GetSubFolders()
    for sub_folder in sub_folders.values():
        get_clips(sub_folder, result)


def execute():
    logger.info("Start match input color space and apply custom grading rules.")
    resolve = bmd.scriptapp("Resolve")
    project_manager = resolve.GetProjectManager()
    project = project_manager.GetCurrentProject()
    media_pool = project.GetMediaPool()
    root_folder = media_pool.GetRootFolder()
    success = True
    if "davinciYRGBColorManaged" in project.GetSetting("colorScienceMode"):
        logger.debug("Match input color space begin")
        clips = []
        get_clips(root_folder, clips)
        for clip in clips:
            metadata = clip.GetMetadata()
            input_color_space = color_space_match_map.get(
                (metadata.get("Gamma Notes"), metadata.get("Color Space Notes")))
            if input_color_space:
                if clip.SetClipProperty("Input Color Space", input_color_space):
                    logger.debug(f"{clip.GetName()} Set Input Color Space {input_color_space} Successfully.")
                else:
                    success = False
                    logger.error(f"{clip.GetName()} Set Input Color Space {input_color_space} Failed!")

    if success:
        logger.info("All Done, Have Fun!")
        return True
    else:
        logger.warning("Some error happened, please check console details.")
        return False


if __name__ == '__main__':
    bmd = get_bmd()
    if "gui_mode" in locals().keys() and gui_mode:
        fusion = bmd.scriptapp("Fusion")
        ui = fusion.UIManager
        dispatcher = bmd.UIDispatcher(ui)
        main_window()
    else:
        execute()
