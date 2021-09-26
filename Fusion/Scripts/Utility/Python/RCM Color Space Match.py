#!/usr/bin/env python
"""For DaVinci Resolve Color Grading"""
__author__ = "Michael<https://github.com/fukco>"
__version__ = "0.5.0"
__license__ = "MIT"

import logging
import os
import re

from get_resolve import get_bmd

metadata_parser = __import__("Metadata Parser")

gui_mode = 1


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

default_color_version_name = "Auto Generate Color Version"
color_space_match_list = [ColorSpaceMatchRule("Atomos", "CLog", "Cinema", "Canon Cinema Gamut/Canon Log"),
                          ColorSpaceMatchRule("Atomos", "CLog2", "Cinema", "Canon Cinema Gamut/Canon Log2"),
                          ColorSpaceMatchRule("Atomos", "CLog3", "Cinema", "Canon Cinema Gamut/Canon Log3"),
                          ColorSpaceMatchRule("Atomos", "F-Log", "F-Gamut", "FujiFilm F-Log"),
                          ColorSpaceMatchRule("Atomos", "V-Log", "V-Gamut", "Panasonic V-Gamut/V-Log"),
                          ColorSpaceMatchRule("Atomos", "SLog3", "SGamut3", "S-Gamut3/S-Log3"),
                          ColorSpaceMatchRule("Atomos", "SLog3", "SGamut3Cine", "S-Gamut3.Cine/S-Log3"),
                          ColorSpaceMatchRule("Atomos", "N-Log", "BT.2020", "Nikon N-Log"),
                          ColorSpaceMatchRule("Atomos", "HLG", "BT.2020", "Rec.2100 HLG"),

                          ColorSpaceMatchRule("Fujifilm", "F-log", "", "FujiFilm F-Log"),

                          ColorSpaceMatchRule("Panasonic", "V-Log", "V-Gamut", "Panasonic V-Gamut/V-Log"),

                          ColorSpaceMatchRule("Sony", "s-log2", "s-gamut", "S-Gamut/S-Log2"),
                          ColorSpaceMatchRule("Sony", "s-log3-cine", "s-gamut3-cine", "S-Gamut3.Cine/S-Log3"),
                          ColorSpaceMatchRule("Sony", "s-log3", "s-gamut3", "S-Gamut3/S-Log3"),
                          ]
color_space_match_map = {}
input_color_space_list = []
for item in color_space_match_list:
    color_space_match_map[(item.gamma_notes, item.color_space_notes)] = item.input_color_space
    if item.input_color_space not in input_color_space_list:
        input_color_space_list.append(item.input_color_space)

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
        'Geometry': [300, 180, 800, 460],
        'WindowTitle': "RCM Color Space Match",
    },
        ui.VGroup([
            # color space match rule
            ui.Tree({"ID": tree_id}),

            ui.HGroup({"Weight": 0}, [
                ui.CheckBox(
                    {"ID": "EnableMetadataParser", "Text": "Enable Metadata Parser", "Weight": 0, "Checked": True}),
                ui.HGap(10),
                ui.CheckBox(
                    {"ID": "EnableDataLevelAdjustment", "Text": "Enable Assign Atomos Clips' Data Level", "Weight": 0}),
                ui.ComboBox({"ID": "DataLevelAdjustmentType", "Weight": 1})
            ]),

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

    def init_combo():
        items = win.GetItems()

        items["DataLevelAdjustmentType"].AddItem('For Log and Legal Clips')
        items["DataLevelAdjustmentType"].AddItem('For All Clips')

    def show_message(message, t=0):
        if t == 0:
            win.GetItems()["InfoLabel"]["Text"] = f"<font color='#39CA41'>{message}</font>"
        elif t == 1:
            win.GetItems()["InfoLabel"]["Text"] = f"<font color='#922626'>{message}</font>"

    def load_color_space_match_rule():
        for manufacturerRule in match_rules["rules"]:
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
            item["Expanded"] = True

    def click_execute_button(ev):
        logger.info("Start Processing.")
        show_message("Processing...")
        items = win.GetItems()
        if execute(assign_data_level_enabled=items["EnableDataLevelAdjustment"]["Checked"],
                   assign_type=items["DataLevelAdjustmentType"]["CurrentIndex"],
                   parse_metadata_enabled=items["EnableMetadataParser"]["Checked"]):
            show_message("All Down. Have Fun!")
        else:
            show_message("Some process failed, please check console log details.", 1)

    def close(ev):
        dispatcher.ExitLoop()

    init_tree()
    init_combo()
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


def assign_data_level(clip, metadata, assign_type):
    if metadata.get("Camera Manufacturer") == "Atomos":
        gamma_notes = metadata.get("Gamma Notes") if metadata.get("Gamma Notes") else ""
        camera_notes = metadata.get("Camera Notes") if metadata.get("Camera Notes") else ""
        if assign_type == 0 and (
                re.search("LOG", gamma_notes, re.IGNORECASE) or "Range: Legal" in camera_notes) or assign_type == 1:
            if clip.SetClipProperty("Data Level", "Full"):
                logger.debug(f"Assign {clip.GetName()} data level full successfully.")
            else:
                logger.error(f"Assign {clip.GetName()} data level full failed.")
                return False
    return True


def parse_metadata(clip, lib):
    file_path = clip.GetClipProperty("File Path")
    if len(file_path) > 0:
        resolve_meta_dict = lib.DRProcessMediaFile(file_path.encode("utf-8")).get_dict()
        if resolve_meta_dict:
            if not resolve_meta_dict["IsSupportMedia"]:
                logger.warning(f"{os.path.basename(file_path)} Not Supported.")
            else:
                del resolve_meta_dict["IsSupportMedia"]
                meta = {k: v.decode("utf-8") for k, v in resolve_meta_dict.items() if v}
                if not meta:
                    logger.debug(f"Ignore clip {os.path.basename(file_path)}.")
                else:
                    if clip.SetMetadata(meta):
                        logger.debug(f"Process {os.path.basename(file_path)} Successfully.")
                        return meta
                    else:
                        logger.error(f"Failed to set {os.path.basename(file_path)} metadata!")
        else:
            logger.error(f"Failed to parse clip {clip.GetName()}")
    return None


def execute(assign_data_level_enabled=True, assign_type=0, parse_metadata_enabled=True):
    logger.info("Start match input color space and apply custom grading rules.")
    resolve = bmd.scriptapp("Resolve")
    project_manager = resolve.GetProjectManager()
    project = project_manager.GetCurrentProject()
    media_pool = project.GetMediaPool()
    root_folder = media_pool.GetRootFolder()
    success = True
    is_rcm = "davinciYRGBColorManaged" in project.GetSetting("colorScienceMode")
    clips = []

    get_clips(root_folder, clips)
    lib = {}
    if parse_metadata_enabled:
        lib = metadata_parser.get_cdll_lib()
    for clip in clips:
        metadata = parse_metadata(clip, lib) if parse_metadata_enabled else clip.GetMetadata()
        if not metadata:
            continue
        if is_rcm:
            gamma_notes = metadata.get("Gamma Notes") if metadata.get("Gamma Notes") else ""
            color_space_rotes = metadata.get("Color Space Notes") if metadata.get("Color Space Notes") else ""
            input_color_space = color_space_match_map.get((gamma_notes, color_space_rotes))
            if input_color_space:
                if clip.SetClipProperty("Input Color Space", input_color_space):
                    logger.debug(f"{clip.GetName()} Set Input Color Space {input_color_space} Successfully.")
                else:
                    success = False
                    logger.error(f"{clip.GetName()} Set Input Color Space {input_color_space} Failed!")
            else:
                logger.warning(f"{clip.GetName()} Does Not Found Input Color Space Match Rule!")
        if assign_data_level_enabled:
            if not assign_data_level(clip, metadata, assign_type):
                success = False
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
