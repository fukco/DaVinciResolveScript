#!/usr/bin/env python
"""For DaVinci Resolve Color Grading"""
__author__ = "Michael<https://github.com/fukco>"
__version__ = "0.2.0"
__license__ = "MIT"

import collections
import json
import logging
import os
import pathlib
import sys
from datetime import datetime

from get_resolve import get_bmd

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

custom_rules = "Custom Rules"
default_color_version_name = "Auto Generate Color Version"

data = {}
if pathlib.Path(json_file).is_file():
    f = open(json_file, mode="r", encoding="utf-8")
    logger.debug(f"Open Json File {json_file}")
    data = json.load(f)
    f.close()

input_color_space_list = []
if data.get("Color Space Match Rules") and data.get("Color Space Match Rules").get("rules"):
    for item in data.get("Color Space Match Rules").get("rules"):
        for detail in item.get("details"):
            if detail.get("Input Color Space") not in input_color_space_list:
                input_color_space_list.append(detail.get("Input Color Space"))
drx_lists = []
if data.get("DRX") and data.get("DRX").get("lists"):
    drx_lists = data.get("DRX").get("lists")
drx_map = dict((x.get("name"), x.get("path")) for x in drx_lists) if drx_lists else {}
copyTypeOptions = ['All', 'Same Clip', 'Same Camera Type', 'Same Camera Serial #', 'Same Keywords',
                   'Same Input Color Space',
                   'Same Clip Color', 'Same Flags']


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
    if option == copyTypeOptions[0]:  # All
        target_items = timeline_items
    elif option == copyTypeOptions[1]:  # Same Clip
        for item in timeline_items:
            if item.GetMediaPoolItem().GetClipProperty(
                    "File Path") == timeline_item.GetMediaPoolItem().GetClipProperty("File Path"):
                target_items.append(item)
    elif option == copyTypeOptions[5]:  # Same Input Color Space
        for item in timeline_items:
            if item.GetMediaPoolItem().GetClipProperty(
                    "Input Color Space") == timeline_item.GetMediaPoolItem().GetClipProperty(
                "Input Color Space"):
                target_items.append(item)
    elif option == copyTypeOptions[6]:  # Clip Color
        for item in timeline_items:
            if item.GetClipColor() == timeline_item.GetClipColor():
                target_items.append(item)
    elif option == copyTypeOptions[7]:  # Flags
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
    # some element IDs
    win_id = "com.xiaoli.ColorGradingTool"  # should be unique for single instancing
    option_combo = "OptionCombo"
    save_button_id = "SaveButton"
    copy_button_id = "CopyButton"

    # check for existing instance
    win = ui.FindWindow(win_id)
    if win:
        win.Show()
        win.Raise()
        exit()

    # define the window UI layout
    win = dispatcher.AddWindow({
        'ID': win_id,
        'Geometry': [600, 100, 700, 800],
        'WindowTitle': "Color Grading Tool"
    },
        ui.VGroup([
            # timeline color grading copy
            ui.HGroup({"Weight": 0.05}, [
                ui.Label({"Text": 'Timeline Color Grading Copy:', 'Font': ui.Font({'Family': "Times New Roman"}),
                          "Alignment": {"AlignHCenter": True, "AlignTop": True}})]),
            ui.HGroup({"Weight": 0}, [
                ui.HGap(70),

                ui.Label({
                    "Text": 'Copy To Timeline:',
                    "Weight": 0
                }),

                ui.ComboBox({
                    "ID": 'CopyTypesCombo'
                }),

            ]),
            ui.HGroup({"Weight": 0}, [
                ui.CheckBox({
                    "ID": 'CopyToAssignColorVersionCheckBox',
                    "Weight": 0,
                    "Text": 'Assign Color Version Name'
                }),

                ui.LineEdit({
                    "ID": 'CopyToColorVersionTxt',
                    "PlaceholderText": default_color_version_name,
                }),
            ]),

            ui.VGap(15),

            # custom rule
            ui.VGroup({"ID": "CustomRuleId", "Weight": 5}, [
                # option
                ui.HGroup({"Weight": 0}, [
                    ui.Label({"Text": 'Custom Grading Rules:', 'Font': ui.Font({'Family': "Times New Roman"}),
                              "Alignment": {"AlignHCenter": True, "AlignTop": True}})]),

                ui.HGroup({"Weight": 0}, [
                    ui.Label({"Text": 'Option:', 'Font': ui.Font({'Family': "Times New Roman"}), "Weight": 0}),
                    ui.HGap(5),
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
                ui.Button({"Text": "Copy Grades", "ID": copy_button_id, "Weight": 0}),
                ui.HGap(2),
                ui.Button({"Text": "Custom Grading", "ID": "ExecuteButton", "Weight": 0}),
                ui.HGap(2),
                ui.Button({"Text": "Save Rules", "ID": save_button_id, "Weight": 0}),
                ui.HGap(5),
                ui.Label({'Font': ui.Font({'Family': "Times New Roman"}), "ID": "InfoLabel"})
            ]),
        ])
    )
    items = win.GetItems()

    # Add the items to the ComboBox menu
    for option in copyTypeOptions:
        items["CopyTypesCombo"].AddItem(option)

    items["CopyTypesCombo"]["CurrentIndex"] = 1

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
                condition_row = [ui.ComboBox({"ID": f"ConditionKeyCombo_{index}_{j}", "Weight": 0.5}),
                                 ui.HGroup({"ID": f"ConditionContainer_{index}_{j}", "Weight": 1}),
                                 ui.Button({"ID": f"DeleteConditionButton_{index}_{j}", "Text": "Delete", "Weight": 0})]
                condition_tables.append(ui.HGroup(condition_row))

            if drx_lists:
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
            del data.get(custom_rules)["options"][option_selected_index]["entries"][index]
            repaint_custom_rules_table()

        def update_drx(ev):
            index = int(ev["who"].split("_")[-1])
            option_selected_index = win.GetItems()[option_combo]["CurrentIndex"]
            entries = data.get(custom_rules)["options"][option_selected_index]["entries"]
            entries[index]["drx"] = win.GetItems()[f"drxFile_{index}"]["CurrentText"]

        def add_condition(ev):
            index = int(ev["who"].split("_")[-1])
            option_selected_index = win.GetItems()[option_combo]["CurrentIndex"]
            data.get(custom_rules)["options"][option_selected_index]["entries"][index]["conditions"].append(
                {"key": "", "value": ""})
            repaint_custom_rules_table()

        def delete_condition(ev):
            i = int(ev["who"].split("_")[-2])
            j = int(ev["who"].split("_")[-1])
            option_selected_index = win.GetItems()[option_combo]["CurrentIndex"]
            del data.get(custom_rules)["options"][option_selected_index]["entries"][i]["conditions"][j]
            repaint_custom_rules_table()

        def change_condition_key(ev):
            i = int(ev["who"].split("_")[-2])
            j = int(ev["who"].split("_")[-1])
            items = win.GetItems()
            option_selected_index = win.GetItems()[option_combo]["CurrentIndex"]
            value = data.get(custom_rules)["options"][option_selected_index]["entries"][i]["conditions"][j]["value"]
            data.get(custom_rules)["options"][option_selected_index]["entries"][i]["conditions"][j]["key"] = \
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
            data.get(custom_rules)["options"][option_selected_index]["entries"][i]["conditions"][j]["value"] = \
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
            data.get(custom_rules)["options"][option_selected_index]["entries"][i]["conditions"][j]["value"] = \
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
            data.get(custom_rules)["options"][option_selected_index]["entries"][i]["conditions"][j]["value"] = \
                items[f"ConditionValue_{i}_{j}"]["CurrentText"]

        def change_input_color_space(ev):
            i = int(ev["who"].split("_")[-2])
            j = int(ev["who"].split("_")[-1])
            items = win.GetItems()
            option_selected_index = win.GetItems()[option_combo]["CurrentIndex"]
            data.get(custom_rules)["options"][option_selected_index]["entries"][i]["conditions"][j]["value"] = \
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
        if "options" in data.get(custom_rules):
            items = win.GetItems()
            items["CustomRuleEntriesContainer"].RemoveChild("CustomRules")
            items["CustomRuleEntriesContainer"].AddChild(ui.VGroup({"ID": "CustomRules"}))
            add_custom_rules_table(data[custom_rules]["options"])
        else:
            add_custom_rules_table([])
        win.RecalcLayout()

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
            if custom_rules not in data or "options" not in data.get(custom_rules):
                data.update({custom_rules: {"options": [{"name": option_name, "selected": True}]}})
            else:
                if len(data[custom_rules]["options"]) >= 20:
                    new_option_items["NewOptionLabelId"][
                        "Text"] = "<font color='#ff0000'>Your Options is more than 20!</font>"
                    return False
                for option in data.get(custom_rules)["options"]:
                    if option["name"] == option_name:
                        new_option_items["NewOptionLabelId"][
                            "Text"] = "<font color='#ff0000'>Your option name is exist! Please use another one!</font>"
                        new_option_items["MyLineTxt"].SetPaletteColor('All', 'Base',
                                                                      {"R": 1, "G": 0.125, "B": 0.125,
                                                                       "A": 1})
                        return False
                for option in data.get(custom_rules)["options"]:
                    option["selected"] = False
                data.get(custom_rules)["options"].append({"name": option_name, "selected": True})
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
        if data.get(custom_rules) and "options" in data.get(custom_rules) and data.get(custom_rules)["options"]:
            i = 0
            items = win.GetItems()
            for option in data.get(custom_rules)["options"]:
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
            for option in data.get(custom_rules)["options"]:
                if option["name"] == win.GetItems()[option_combo]["CurrentText"]:
                    data.get(custom_rules)["options"].remove(option)
                    combo_delete_option(i)
                    break
                i += 1

    def combo_change(ev):
        options = data.get(custom_rules)["options"]
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

    def click_copy_button(ev):
        current_timeline_item = timeline.GetCurrentVideoItem()
        if not current_timeline_item:
            show_message("Please open [Edit] or [Color] page to choose one timeline item!", 1)
            logger.warning("Please open [Edit] or [Color] page to choose one timeline item!")
            return
        option = items["CopyTypesCombo"]["CurrentText"]
        assign_color_version = items["CopyToAssignColorVersionCheckBox"]["Checked"]
        color_version_name = items["CopyToColorVersionTxt"]["Text"]
        if not color_version_name:
            color_version_name = default_color_version_name
        if copy_grading(current_timeline_item, option, assign_color_version, color_version_name):
            show_message("Finished.")
        else:
            show_message("Some error occurred, Please check log details!")

    def click_execute_button(ev):
        logger.info("Start Processing.")
        show_message("Processing...")
        save_config()
        if quick_grading_execute():
            show_message("All Down. Have Fun!")
        else:
            show_message("Some process failed, please check console log details.", 1)

    def close(ev):
        dispatcher.ExitLoop()

    load_option_combo()

    # assign event handlers
    win.On[win_id].Close = close
    win.On["OptionDeleteButton"].Clicked = delete_option
    win.On["OptionAddButton"].Clicked = new_option_win
    win.On[option_combo].CurrentIndexChanged = combo_change
    win.On["ExecuteButton"].Clicked = click_execute_button
    win.On[save_button_id].Clicked = click_save_button
    win.On[copy_button_id].Clicked = click_copy_button
    win.On["EntryAddButton"].Clicked = add_entry
    win.Show()
    dispatcher.RunLoop()
    win.Hide()


def get_selected_option():
    if custom_rules in data and "options" in data.get(custom_rules):
        for option in data.get(custom_rules)["options"]:
            if option["selected"]:
                return option
        return data.get(custom_rules)["options"][0]
    return None


def get_clips(folder, result):
    result.extend(folder.GetClipList())
    sub_folders = folder.GetSubFolders()
    for sub_folder in sub_folders.values():
        get_clips(sub_folder, result)


def is_timeline_item_match_conditions(timeline_item, conditions):
    for condition in conditions:
        if not condition.get("key") or not condition.get("value"):
            conditions.remove(condition)
    if len(conditions) <= 0:
        return False
    clip = timeline_item.GetMediaPoolItem()
    metadata = clip.GetMetadata()
    for condition in conditions:
        key = condition.get("key")
        value = condition.get("value")
        if key == "All":
            continue
        elif key == "keyword":
            if value not in metadata.get("Keywords"):
                return False
        elif key == "Input Color Space":
            if clip.GetClipProperty("Input Color Space") != value:
                return False
        elif key == "Clip Color":
            if timeline_item.GetClipColor() != value:
                return False
        elif key == "Flag":
            flag_dict = clip.GetFlags()
            if flag_dict and value not in flag_dict.values():
                return False
        else:
            if metadata.get(key) != value:
                return False
    return True


def quick_grading_execute():
    logger.info("Start match input color space and apply custom grading rules.")
    success = True

    logger.debug("Apply custom color grading rules begin")
    option_selected = get_selected_option()
    if option_selected:
        entries = option_selected.get("entries") if option_selected else []
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
                                logger.debug(
                                    f"{item.GetName()} apply drx [{drx_name}] to color version [{version_name}].")
                            else:
                                logger.debug(f"{item.GetName()} apply drx [{drx_name}] to current color version.")
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
    resolve = bmd.scriptapp("Resolve")
    project_manager = resolve.GetProjectManager()
    project = project_manager.GetCurrentProject()
    mediaPool = project.GetMediaPool()
    rootFolder = mediaPool.GetRootFolder()
    timeline = project.GetCurrentTimeline()
    main_window()
