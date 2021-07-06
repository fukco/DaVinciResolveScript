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
from datetime import datetime

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

color_space_match_rules = "Color Space Match Rules"
custom_rules = "Custom Rules"
enabled = "enabled"
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
    data.update({color_space_match_rules: {enabled: True, "_comments": "this is for RCM only!"},
                 custom_rules: {enabled: False}})
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
drx_lists = []
if data.get("DRX") and data.get("DRX").get("lists"):
    drx_lists = data.get("DRX").get("lists")
drx_map = dict((x.get("name"), x.get("path")) for x in drx_lists) if drx_lists else {}


def main_window():
    # some element IDs
    win_id = "com.xiaoli.ColorGradingTool"  # should be unique for single instancing
    tree_id = "MatchTree"
    option_combo = "OptionCombo"
    save_button_id = "SaveButton"
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
        'Geometry': [600, 100, 800, 800],
        'WindowTitle': "Color Grading Tool",
        'fixedSize': {800, 800}
    },
        ui.VGroup([
            # checkbox
            ui.HGroup({"Weight": 0}, [
                ui.HGap(0, 10),
                ui.CheckBox({"Text": 'RCM Color Space Match', "ID": "ColorScienceCheckBox"}),
                ui.CheckBox({"Text": 'Custom Grading', "ID": "CustomGradingCheckBox"}),
                ui.HGap(0, 10)]),

            # color space match rule
            ui.HGroup({"Weight": 0.05}, [
                ui.Label({"Text": 'RCM Color Space Match Rules:', 'Font': ui.Font({'Family': "Times New Roman"}),
                          "Alignment": {"AlignHCenter": True, "AlignTop": True}})]),
            ui.VGroup({"Weight": 2}, [ui.Tree({"ID": tree_id})]),

            # custom rule
            ui.VGroup({"ID": "CustomRuleId", "Weight": 5}, [
                # option
                ui.HGroup({"Weight": 0}, [
                    ui.Label({"Text": 'Custom Grading Rules:', 'Font': ui.Font({'Family': "Times New Roman"}),
                              "Alignment": {"AlignHCenter": True, "AlignTop": True}})]),

                ui.HGroup({"Weight": 0}, [
                    ui.Label({"Text": 'Option:', 'Font': ui.Font({'Family': "Times New Roman"}), "Weight": 0}),
                    ui.ComboBox({"ID": option_combo, "Weight": 1.5}),
                    ui.Button({"ID": "OptionAddButton", "Text": "Add", "Weight": 0}),
                    ui.Button({"ID": "OptionDeleteButton", "Text": "Delete", "Weight": 0})]),

                # details
                ui.HGroup({"Weight": 0}, [
                    ui.Button({"ID": "EntryAddButton", "Text": "Add Entry", "Weight": 0.25}),
                    ui.HGap(0, 10)
                ]),

                ui.VGroup({"ID": "CustomRuleEntriesContainer", "Weight": 10}, [
                    ui.VGroup({"ID": "CustomRules"}),
                ]),
            ]),

            ui.HGroup({"Weight": 0}, [
                ui.Button({"Text": "Execute", "ID": "ExecuteButton", "Weight": 0}),
                ui.HGap(2),
                ui.Button({"Text": "Save Config", "ID": save_button_id, "Weight": 0}),
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

    def init_checkbox():
        items = win.GetItems()
        if data[color_space_match_rules].get(enabled):
            items["ColorScienceCheckBox"]["Checked"] = True
        if data[custom_rules].get(enabled):
            items["CustomGradingCheckBox"]["Checked"] = True

    def add_custom_rules_table(options):
        if len(options) <= 0:
            return
        entries = []
        option_selected = {}
        for option in options:
            if option["selected"]:
                option_selected = option
                if "entries" in option:
                    entries = option["entries"]
        # assign color version name
        win.GetItems()["CustomRules"].AddChild(ui.HGroup({"Weight": 0}, [
            ui.CheckBox(
                {"Text": 'Assign Color Version Name', "Checked": option_selected.get("Assign Color Version Name"),
                 "ID": "AssignColorVersionNameCheckBox", "Weight": 0}),
            ui.LineEdit({"ID": "ColorVersionName", "Weight": 5, "Text": option_selected.get("Color Version Name"),
                         "PlaceholderText": default_color_version_name})
        ]))
        win.GetItems()["CustomRules"].AddChild(ui.VGap(0, 10))
        for index in range(len(entries) - 1, -1, -1):
            entry = entries[index]
            conditions = []
            if "conditions" in entry:
                conditions = entry["conditions"]
            condition_tables = []
            for j in range(len(conditions)):
                # condition = conditions[j]
                # key = condition["key"]
                # value = condition["value"]
                condition_row = [ui.ComboBox({"ID": f"ConditionKeyCombo_{index}_{j}", "Weight": 0.5}),
                                 ui.HGroup({"ID": f"ConditionContainer_{index}_{j}", "Weight": 1}),
                                 ui.Button({"ID": f"DeleteConditionButton_{index}_{j}", "Text": "Delete", "Weight": 0})]
                condition_tables.append(ui.HGroup(condition_row))

            # drx = entry["drx"]
            if drx_lists:
                # drx_element = ui.Label({"Text": drx, 'Font': ui.Font({'Family': "Times New Roman"}),
                #                         "Weight": 1.5, "ID": f"drxFile_{index}"})
                drx_element = ui.ComboBox({"ID": f"drxFile_{index}"})
            else:
                drx_element = ui.Label({"Text": "<font color='#922626'>Please update DRX file lists first!</font>",
                                        'Font': ui.Font({'Family': "Times New Roman"}), "Weight": 2})

            option_element = ui.HGroup([
                ui.VGroup([
                    ui.HGroup([
                        ui.HGap(2),
                        ui.Label(
                            {"Text": f"Entry # {index + 1}", 'Font': ui.Font({'Family': "Times New Roman"}),
                             "Weight": 0}),
                        ui.HGap(140),
                        drx_element,
                        ui.HGap(100),
                        ui.Button({"ID": f"EntryDeleteButton_{index}", "Text": "Delete Entry", "Weight": 0}),
                    ]),
                    ui.HGroup({"Weight": 0}, [
                        ui.VGroup({"Weight": 0}, [
                            ui.Button(
                                {"ID": f"ConditionAddButton_{index}", "Text": "Add Condition", "Weight": 0})]),
                        ui.VGroup({"ID": f"conditionRows_{index}"}, condition_tables)
                    ])
                ]),
            ])
            win.GetItems()["CustomRules"].AddChild(option_element)

        def delete_entry(ev):
            index = int(ev["who"].split("_")[-1])
            option_selected_index = win.GetItems()[option_combo]["CurrentIndex"]
            del data[custom_rules]["options"][option_selected_index]["entries"][index]
            repaint_custom_rules_table()

        def update_drx(ev):
            index = int(ev["who"].split("_")[-1])
            option_selected_index = win.GetItems()[option_combo]["CurrentIndex"]
            entries = data[custom_rules]["options"][option_selected_index]["entries"]
            entries[index]["drx"] = win.GetItems()[f"drxFile_{index}"]["CurrentText"]

        def add_condition(ev):
            index = int(ev["who"].split("_")[-1])
            option_selected_index = win.GetItems()[option_combo]["CurrentIndex"]
            data[custom_rules]["options"][option_selected_index]["entries"][index]["conditions"].append(
                {"key": "", "value": ""})
            repaint_custom_rules_table()

        def delete_condition(ev):
            i = int(ev["who"].split("_")[-2])
            j = int(ev["who"].split("_")[-1])
            option_selected_index = win.GetItems()[option_combo]["CurrentIndex"]
            del data[custom_rules]["options"][option_selected_index]["entries"][i]["conditions"][j]
            repaint_custom_rules_table()

        def change_condition_key(ev):
            i = int(ev["who"].split("_")[-2])
            j = int(ev["who"].split("_")[-1])
            items = win.GetItems()
            option_selected_index = win.GetItems()[option_combo]["CurrentIndex"]
            value = data[custom_rules]["options"][option_selected_index]["entries"][i]["conditions"][j]["value"]
            data[custom_rules]["options"][option_selected_index]["entries"][i]["conditions"][j]["key"] = \
                items[f"ConditionKeyCombo_{i}_{j}"]["CurrentText"]
            items[f"ConditionContainer_{i}_{j}"].RemoveChild(f"ConditionValue_{i}_{j}")
            items[f"ConditionContainer_{i}_{j}"].RemoveChild(f"ConditionValueColor_{i}_{j}")
            if items[f"ConditionKeyCombo_{i}_{j}"]["CurrentText"] == "Clip Color":
                items[f"ConditionContainer_{i}_{j}"].AddChild(ui.ComboBox({"ID": f"ConditionValue_{i}_{j}"}))
                items[f"ConditionContainer_{i}_{j}"].AddChild(
                    ui.LineEdit({"ID": f"ConditionValueColor_{i}_{j}", "ReadOnly": True, "Weight": 0.2}))
                clip_colors = ["Orange", "Apricot", "Yellow", "Lime", "Olive", "Green", "Teal", "Navy", "Blue",
                               "Purple", "Violet", "Pink", "Tan", "Beige", "Brown", "Chocolate"]
                for color in clip_colors:
                    win.GetItems()[f"ConditionValue_{i}_{j}"].AddItem(color)
                if value and value in clip_colors:
                    win.GetItems()[f"ConditionValue_{i}_{j}"]["CurrentIndex"] = clip_colors.index(value)
                win.On[f"ConditionValue_{i}_{j}"].CurrentIndexChanged = change_clip_color
            elif items[f"ConditionKeyCombo_{i}_{j}"]["CurrentText"] == "Flag":
                items[f"ConditionContainer_{i}_{j}"].AddChild(ui.ComboBox({"ID": f"ConditionValue_{i}_{j}"}))
                items[f"ConditionContainer_{i}_{j}"].AddChild(
                    ui.LineEdit({"ID": f"ConditionValueColor_{i}_{j}", "ReadOnly": True, "Weight": 0.2}))
                flag_colors = ["Blue", "Cyan", "Green", "Yellow", "Red", "Pink", "Purple", "Fuchsia", "Rose",
                               "Lavender", "Sky", "Mint", "Lemon", "Sand", "Cocoa", "Cream"]
                for color in flag_colors:
                    win.GetItems()[f"ConditionValue_{i}_{j}"].AddItem(color)
                if value and value in flag_colors:
                    win.GetItems()[f"ConditionValue_{i}_{j}"]["CurrentIndex"] = flag_colors.index(value)
                win.On[f"ConditionValue_{i}_{j}"].CurrentIndexChanged = change_flag
            elif items[f"ConditionKeyCombo_{i}_{j}"]["CurrentText"] == "Input Color Space":
                items[f"ConditionContainer_{i}_{j}"].AddChild(ui.ComboBox({"ID": f"ConditionValue_{i}_{j}"}))
                for input_color_space in input_color_space_list:
                    win.GetItems()[f"ConditionValue_{i}_{j}"].AddItem(input_color_space)
                win.On[f"ConditionValue_{i}_{j}"].CurrentIndexChanged = change_input_color_space
            elif items[f"ConditionKeyCombo_{i}_{j}"]["CurrentText"] == "All":
                items[f"ConditionContainer_{i}_{j}"].AddChild(
                    ui.LineEdit({"ID": f"ConditionValue_{i}_{j}", "Weight": 1, "ReadOnly": True,
                                 "PlaceholderText": "No need to input anything."}))
            else:
                items[f"ConditionContainer_{i}_{j}"].AddChild(
                    ui.LineEdit({"ID": f"ConditionValue_{i}_{j}", "Weight": 1, "Text": value,
                                 "PlaceholderText": "Please Enter Condition Value."}))
                win.On[f"ConditionValue_{i}_{j}"].TextChanged = update_condition_value_text
            win.RecalcLayout()

        def update_condition_value_text(ev):
            i = int(ev["who"].split("_")[-2])
            j = int(ev["who"].split("_")[-1])
            items = win.GetItems()
            option_selected_index = items[option_combo]["CurrentIndex"]
            data[custom_rules]["options"][option_selected_index]["entries"][i]["conditions"][j]["value"] = \
                items[f"ConditionValue_{i}_{j}"]["Text"]

        def change_clip_color(ev):
            condition_item = ev["who"].replace("ConditionValue_", "ConditionValueColor_")
            clip_colors = [{"R": 0.9215, "G": 0.4313, "B": 0.0039, "A": 1}, {"R": 1, "G": 0.6588, "B": 0.2, "A": 1},
                           {"R": 0.8313, "G": 0.6784, "B": 0.1215, "A": 1},
                           {"R": 0.6235, "G": 0.7764, "B": 0.0823, "A": 1},
                           {"R": 0.3725, "G": 0.6, "B": 0.1294, "A": 1}, {"R": 0.2666, "G": 0.5607, "B": 0.396, "A": 1},
                           {"R": 0.039, "G": 0.596, "B": 0.6, "A": 1}, {"R": 0, "G": 0.3215, "B": 0.4705, "A": 1},
                           {"R": 0.2627, "G": 0.4627, "B": 0.6313, "A": 1}, {"R": 0.6, "G": 0.447, "B": 0.6274, "A": 1},
                           {"R": 0.8156, "G": 0.3372, "B": 0.5529, "A": 1},
                           {"R": 0.9137, "G": 0.549, "B": 0.7098, "A": 1},
                           {"R": 0.7254, "G": 0.6862, "B": 0.5921, "A": 1},
                           {"R": 0.7686, "G": 0.6274, "B": 0.0039, "A": 1},
                           {"R": 0.6, "G": 0.4, "B": 0.0039, "A": 1}, {"R": 0.549, "G": 0.3529, "B": 0.247, "A": 1}]
            items = win.GetItems()
            current_index = items[ev["who"]]["CurrentIndex"]
            items[condition_item].SetPaletteColor('All', 'Base', clip_colors[current_index])
            i = int(ev["who"].split("_")[-2])
            j = int(ev["who"].split("_")[-1])
            option_selected_index = win.GetItems()[option_combo]["CurrentIndex"]
            data[custom_rules]["options"][option_selected_index]["entries"][i]["conditions"][j]["value"] = \
                items[f"ConditionValue_{i}_{j}"]["CurrentText"]

        def change_flag(ev):
            condition_item = ev["who"].replace("ConditionValue_", "ConditionValueColor_")
            flag_colors = [{"R": 0, "G": 0.498, "B": 0.8901, "A": 1}, {"R": 0, "G": 0.8078, "B": 0.8156, "A": 1},
                           {"R": 0, "G": 0.6784, "B": 0, "A": 1}, {"R": 0.9411, "G": 0.6156, "B": 0, "A": 1},
                           {"R": 0.8823, "G": 0.1411, "B": 0.0039, "A": 1}, {"R": 1, "G": 0.2666, "B": 0.7843, "A": 1},
                           {"R": 0.5647, "G": 0.0745, "B": 0.6, "A": 1},
                           {"R": 0.7529, "G": 0.1803, "B": 0.4352, "A": 1},
                           {"R": 1, "G": 0.6313, "B": 0.7254, "A": 1}, {"R": 0.6313, "G": 0.5764, "B": 0.7843, "A": 1},
                           {"R": 0.5725, "G": 0.8862, "B": 0.9921, "A": 1}, {"R": 0.447, "G": 0.8588, "B": 0, "A": 1},
                           {"R": 0.8627, "G": 0.9137, "B": 0.3529, "A": 1},
                           {"R": 0.745, "G": 0.5686, "B": 0.3686, "A": 1},
                           {"R": 0.4313, "G": 0.3176, "B": 0.2627, "A": 1},
                           {"R": 0.9607, "G": 0.9615, "B": 0.8823, "A": 1}]
            items = win.GetItems()
            current_index = items[ev["who"]]["CurrentIndex"]
            items[condition_item].SetPaletteColor('All', 'Base', flag_colors[current_index])
            i = int(ev["who"].split("_")[-2])
            j = int(ev["who"].split("_")[-1])
            option_selected_index = win.GetItems()[option_combo]["CurrentIndex"]
            data[custom_rules]["options"][option_selected_index]["entries"][i]["conditions"][j]["value"] = \
                items[f"ConditionValue_{i}_{j}"]["CurrentText"]

        def change_input_color_space(ev):
            i = int(ev["who"].split("_")[-2])
            j = int(ev["who"].split("_")[-1])
            items = win.GetItems()
            option_selected_index = win.GetItems()[option_combo]["CurrentIndex"]
            data[custom_rules]["options"][option_selected_index]["entries"][i]["conditions"][j]["value"] = \
                items[f"ConditionValue_{i}_{j}"]["CurrentText"]

        def click_assign_color_version_name_check_box(ev):
            option_selected = get_selected_option()
            if win.GetItems()["AssignColorVersionNameCheckBox"]["Checked"]:
                option_selected["Assign Color Version Name"] = True
            else:
                option_selected["Assign Color Version Name"] = False

        def update_color_version_name(ev):
            option_selected = get_selected_option()
            if option_selected:
                option_selected.update({"Color Version Name": win.GetItems()["ColorVersionName"]["Text"]})

        win.On["AssignColorVersionNameCheckBox"].Clicked = click_assign_color_version_name_check_box
        win.On["ColorVersionName"].TextChanged = update_color_version_name
        condition_keys = ["All", "Camera Type", "Camera Serial #", "Keyword", "Input Color Space", "Clip Color", "Flag"]
        for index in range(len(entries)):
            entry = entries[index]
            if win.GetItems().get(f"drxFile_{index}"):
                i = 0
                for drx_element in drx_lists:
                    win.GetItems().get(f"drxFile_{index}").AddItem(drx_element.get("name"))
                    if drx_element.get("name") == entry.get("drx"):
                        win.GetItems().get(f"drxFile_{index}")["CurrentIndex"] = i
                    i = i + 1
            win.On[f"drxFile_{index}"].CurrentIndexChanged = update_drx
            conditions = []
            if "conditions" in entry:
                conditions = entry["conditions"]
            win.On[f"ConditionAddButton_{index}"].Clicked = add_condition
            win.On[f"EntryDeleteButton_{index}"].Clicked = delete_entry
            for j in range(len(conditions)):
                key = conditions[j]["key"]
                win.On[f"DeleteConditionButton_{index}_{j}"].Clicked = delete_condition
                win.On[f"ConditionKeyCombo_{index}_{j}"].CurrentIndexChanged = change_condition_key
                for i in range(len(condition_keys)):
                    win.GetItems()[f"ConditionKeyCombo_{index}_{j}"].AddItem(condition_keys[i])
                    if condition_keys[i] == key:
                        win.GetItems()[f"ConditionKeyCombo_{index}_{j}"]["CurrentIndex"] = i

    def show_message(message, t=0):
        if t == 0:
            win.GetItems()["InfoLabel"]["Text"] = f"<font color='#39CA41'>{message}</font>"
        elif t == 1:
            win.GetItems()["InfoLabel"]["Text"] = f"<font color='#922626'>{message}</font>"

    def add_entry(ev):
        selected_option = get_selected_option()
        if selected_option:
            if "entries" not in selected_option:
                selected_option["entries"] = []
            if len(selected_option["entries"]) < 10:
                selected_option["entries"].append({"drx": "", "conditions": []})
                repaint_custom_rules_table()
                show_message("")
            else:
                show_message("Do Not Add Entry More Than 10!", 1)
        else:
            show_message("Please Add Option First!", 1)

    def repaint_custom_rules_table():
        if "options" in data[custom_rules]:
            items = win.GetItems()
            items["CustomRuleEntriesContainer"].RemoveChild("CustomRules")
            items["CustomRuleEntriesContainer"].AddChild(ui.VGroup({"ID": "CustomRules"}))
            add_custom_rules_table(data[custom_rules]["options"])
        else:
            add_custom_rules_table([])
        win.RecalcLayout()

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

    def new_option_win(ev):
        new_option_win = dispatcher.AddWindow({
            'ID': "new_option_win",
            "WindowFlags": {"Window": True, "WindowStaysOnTopHint": True},
            'Geometry': [850, 450, 300, 100],
            'WindowTitle': "Color Grading Tool",
        },
            ui.VGroup([
                ui.Label({"Text": "Please input new option name.", 'Font': ui.Font({'Family': "Times New Roman"}),
                          "ID": "NewOptionLabelId", "Alignment": {"AlignHCenter": True, "AlignTop": True},
                          "Weight": 0}),

                ui.HGroup([ui.LineEdit(
                    {"ID": "MyLineTxt", "Text": "My Option", "PlaceholderText": "Please Enter a option name."}), ]),

                # execute button
                ui.HGroup({"Weight": 0}, [
                    ui.Button({"Text": "Add", "ID": "OptionAddExecuteButton", "Weight": 0.25})
                ]),
            ])
        )

        new_option_items = new_option_win.GetItems()

        def close_new_option_win(ev):
            dispatcher.ExitLoop()

        def add_option_to_config(option_name):
            if custom_rules not in data or "options" not in data[custom_rules]:
                if not data[custom_rules]:
                    data[custom_rules][enabled] = False
                data[custom_rules]["options"] = [{"name": option_name, "selected": True}]
            else:
                if len(data[custom_rules]["options"]) >= 20:
                    new_option_items["NewOptionLabelId"][
                        "Text"] = "<font color='#ff0000'>Your Options is more than 20!</font>"
                    return False
                for option in data[custom_rules]["options"]:
                    if option["name"] == option_name:
                        new_option_items["NewOptionLabelId"][
                            "Text"] = "<font color='#ff0000'>Your option name is exist! Please use another one!</font>"
                        new_option_items["MyLineTxt"].SetPaletteColor('All', 'Base',
                                                                      {"R": 1, "G": 0.125, "B": 0.125,
                                                                       "A": 1})
                        return False
                for option in data[custom_rules]["options"]:
                    option["selected"] = False
                data[custom_rules]["options"].append({"name": option_name, "selected": True})
            return True

        def new_option_execute(ev):
            if add_option_to_config(new_option_items["MyLineTxt"]["Text"]):
                combo_add_option(new_option_items["MyLineTxt"]["Text"])
                dispatcher.ExitLoop()

        # assign event handlers
        new_option_win.On["new_option_win"].Close = close_new_option_win
        new_option_win.On["OptionAddExecuteButton"].Clicked = new_option_execute

        new_option_win.Show()
        dispatcher.RunLoop()
        new_option_win.Hide()
        return new_option_win, new_option_items

    def load_option_combo():
        if data[custom_rules] and "options" in data[custom_rules] and data[custom_rules]["options"]:
            i = 0
            items = win.GetItems()
            for option in data[custom_rules]["options"]:
                items[option_combo].AddItem(option["name"])
                if option["selected"]:
                    items[option_combo]["CurrentIndex"] = i
                i += 1

    def combo_add_option(option):
        items = win.GetItems()
        items[option_combo].AddItem(option)
        items[option_combo]["CurrentIndex"] = items[option_combo].Count() - 1

    def combo_delete_option(index):
        win.GetItems()[option_combo].RemoveItem(index)

    def delete_option(ev):
        if win.GetItems()[option_combo]["CurrentText"]:
            i = 0
            for option in data[custom_rules]["options"]:
                if option["name"] == win.GetItems()[option_combo]["CurrentText"]:
                    data[custom_rules]["options"].remove(option)
                    combo_delete_option(i)
                    break
                i += 1

    def combo_change(ev):
        options = data[custom_rules]["options"]
        for index in range(len(options)):
            if index == win.GetItems()[option_combo]["CurrentIndex"]:
                options[index]["selected"] = True
            else:
                options[index]["selected"] = False
        repaint_custom_rules_table()

    def save_config():
        write_file = open(json_file, mode="w", encoding="utf-8")
        json.dump(data, write_file, indent=2, ensure_ascii=False)
        write_file.close()

    def click_save_button(ev):
        save_config()
        show_message(f"Config Updated At {datetime.now().strftime('%H:%M:%S.%f')[:-3]}.")

    def click_execute_button(ev):
        logger.info("Start Processing.")
        show_message("Processing...")
        save_config()
        if execute():
            show_message("All Down. Have Fun!")
        else:
            show_message("Some process failed, please check console log details.", 1)

    def click_color_science_check_box(ev):
        if win.GetItems()["ColorScienceCheckBox"]["Checked"]:
            data[color_space_match_rules][enabled] = True
        else:
            data[color_space_match_rules][enabled] = False

    def click_custom_grading_check_box(ev):
        if win.GetItems()["CustomGradingCheckBox"]["Checked"]:
            data[custom_rules][enabled] = True
        else:
            data[custom_rules][enabled] = False

    def close(ev):
        dispatcher.ExitLoop()

    init_tree()
    init_checkbox()
    load_option_combo()
    load_color_space_match_rule()

    # assign event handlers
    win.On[win_id].Close = close
    win.On["OptionDeleteButton"].Clicked = delete_option
    win.On["OptionAddButton"].Clicked = new_option_win
    win.On[option_combo].CurrentIndexChanged = combo_change
    win.On["ExecuteButton"].Clicked = click_execute_button
    win.On[save_button_id].Clicked = click_save_button
    win.On["EntryAddButton"].Clicked = add_entry
    win.On["ColorScienceCheckBox"].Clicked = click_color_science_check_box
    win.On["CustomGradingCheckBox"].Clicked = click_custom_grading_check_box
    win.Show()
    dispatcher.RunLoop()
    win.Hide()


def get_selected_option():
    if custom_rules in data and "options" in data[custom_rules]:
        for option in data[custom_rules]["options"]:
            if option["selected"]:
                return option
        return data[custom_rules]["options"][0]
    return None


def get_clips(folder, result):
    result.extend(folder.GetClipList())
    sub_folders = folder.GetSubFolders()
    for sub_folder in sub_folders.values():
        get_clips(sub_folder, result)


def is_timeline_item_match_conditions(timeline_item, conditions):
    for condition in list(conditions):
        if condition.get("key") == "All":
            return True
        if not condition.get("key") or not condition.get("value"):
            conditions.remove(condition)
    if len(conditions) <= 0:
        return False
    clip = timeline_item.GetMediaPoolItem()
    metadata = clip.GetMetadata()
    for condition in conditions:
        key = condition.get("key")
        value = condition.get("value")
        if key == "keyword":
            if value in metadata.get("Keywords"):
                return True
            else:
                return False
        elif key == "Input Color Space":
            if clip.GetClipProperty("Input Color Space") == value:
                return True
            else:
                return False
        elif key == "Clip Color":
            if timeline_item.GetClipColor() == value:
                return True
            else:
                return False
        elif key == "Flag":
            flag_dict = clip.GetFlags()
            if flag_dict and value in flag_dict.values():
                return True
            else:
                return False
        else:
            if not metadata.get(key) == value:
                return False
    return True


def execute():
    logger.info("Start match input color space and apply custom grading rules.")
    resolve = bmd.scriptapp("Resolve")
    project_manager = resolve.GetProjectManager()
    project = project_manager.GetCurrentProject()
    media_pool = project.GetMediaPool()
    root_folder = media_pool.GetRootFolder()
    success = True
    if data[color_space_match_rules][enabled] and "davinciYRGBColorManaged" in project.GetSetting("colorScienceMode"):
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

    if data[custom_rules][enabled]:
        logger.debug("Apply custom color grading rules begin")
        option_selected = get_selected_option()
        if option_selected:
            entries = option_selected.get("entries") if option_selected else []
            timeline = project.GetCurrentTimeline()
            track_count = timeline.GetTrackCount("video")
            logger.debug(f"Total track count: {track_count}")
            if len(entries) > 0:
                version_name = option_selected.get("Color Version Name") if option_selected.get(
                    "Color Version Name") else default_color_version_name
                for index in range(1, int(track_count) + 1):
                    timeline_items = timeline.GetItemListInTrack("video", index)
                    for entry in entries:
                        conditions = entry.get("conditions")
                        drx_name = entry.get("drx")
                        drx_path = drx_map.get(drx_name)
                        target_items = []
                        for item in timeline_items:
                            if is_timeline_item_match_conditions(item, conditions):
                                if option_selected.get("Assign Color Version Name"):
                                    if not item.LoadVersionByName(version_name, 0):
                                        item.AddVersion(version_name, 0)
                                target_items.append(item)
                        if len(target_items) and not timeline.ApplyGradeFromDRX(drx_path, 0, target_items):
                            success = False
                            logger.error(f"Unable to apply a still from {drx_path} to target items.")
    if success:
        logger.info("All Done, Have Fun!")
        return True
    else:
        logger.warning("Some error happened, please check console details.")
        return False


if __name__ == '__main__':
    bmd = get_bmd()
    fusion = bmd.scriptapp("Fusion")
    ui = fusion.UIManager
    dispatcher = bmd.UIDispatcher(ui)
    if "gui_mode" in locals().keys() and gui_mode:
        main_window()
    else:
        execute()
