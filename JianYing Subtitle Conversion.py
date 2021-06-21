#!/usr/bin/env python
__author__ = "Michael<https://github.com/fukco>"
__version__ = "0.1.0"
__license__ = "MIT"

import datetime
import json
import os
import sys


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


bmd = get_bmd()
fusion = bmd.scriptapp("Fusion")
ui = fusion.UIManager
dispatcher = bmd.UIDispatcher(ui)

# some element IDs
winID = "com.xiaoli.JianYingSubtitleConversion"  # should be unique for single instancing
tabsID = "MyTabs"
exec1ID = "Step1ExecuteButton"
exec2ID = "Step2ExecuteButton"
stackID = "MyStack"
fileLabelId = "FileText"
fileButtonId = "FileButton"
folderLabelId = "FolderText"
folderButtonId = "FolderButton"

# check for existing instance
win = ui.FindWindow(winID)
if win:
    win.Show()
    win.Raise()
    exit()

# define the window UI layout
win = dispatcher.AddWindow({
    'ID': winID,
    'Geometry': [600, 300, 600, 200],
    'WindowTitle': "JianYing Subtitle Conversion",
},
    ui.VGroup([
        ui.TabBar({
            'CurrentIndex': 0,
            'ID': 'MyTabs',
        }),

        ui.Stack({"Weight": 10, "ID": stackID, }, [
            ui.VGroup([
                ui.VGap(0, 5),
                ui.Label({"Text": "In Developing!", 'Font': ui.Font({'Family': "Times New Roman"}),
                          "Alignment": {"AlignHCenter": True}, "Weight": 0}),
                ui.VGap(0, 5)
            ]),

            ui.VGroup([
                ui.VGap(0, 10),

                ui.HGroup([
                    ui.Label({"Text": 'File:', "Weight": 0.25,
                              'Font': ui.Font({'Family': "Times New Roman"})}),
                    ui.Label(
                        {"ID": fileLabelId, 'Text': "Please Select JianYing Subtitle Json File Location", 'Weight': 1.5,
                         'Font': ui.Font({'Family': "Times New Roman", 'PixelSize': 12})}),
                    ui.Button({"Text": "Select a File", "ID": fileButtonId, "Weight": 0.25}),
                ]),

                ui.HGroup([
                    ui.Label({"Text": 'Folder:', "Weight": 0.25,
                              'Font': ui.Font({'Family': "Times New Roman"})}),
                    ui.Label(
                        {"ID": folderLabelId, 'Text': "Please Select Output Subtitle File Path", 'Weight': 1.5,
                         'Font': ui.Font({'Family': "Times New Roman", 'PixelSize': 12})}),
                    ui.Button({"Text": "Select a Folder", "ID": folderButtonId, "Weight": 0.25}),
                ]),

                ui.VGap(0, 10),

                ui.HGroup([
                    ui.Button({"Text": "Execute", "ID": "Step2ExecuteButton", "Weight": 0.25}),
                ]),
            ]),
        ]),

    ])
)

# Add your GUI element based event functions here:
items = win.GetItems()

items[stackID].CurrentIndex = 0

# Add the items to the ComboBox menu
items[tabsID].AddTab('Export Media')
items[tabsID].AddTab('Generate SRT')


# items[]

# Event handlers
def close(ev):
    dispatcher.ExitLoop()


def change_tab(ev):
    items[stackID].CurrentIndex = ev["Index"]


def click_file_button(ev):
    selected_path = fusion.RequestFile('')

    print('[File] ', selected_path)
    items[fileLabelId]["Text"] = selected_path


def click_folder_button(ev):
    target_path = fusion.RequestDir()

    print('[folder] ', target_path)
    items[folderLabelId]["Text"] = target_path


def resolve_handle_subtitle(srt_file):
    resolve = bmd.scriptapp("Resolve")
    projectManager = resolve.GetProjectManager()
    project = projectManager.GetCurrentProject()
    mediaPool = project.GetMediaPool()
    rootFolder = mediaPool.GetRootFolder()
    subFolders = rootFolder.GetSubFolderList()
    subtitleFolder = ""
    for subFolder in subFolders:
        if subFolder.GetName() == "SubTitles":
            subtitleFolder = subFolder
    if not subtitleFolder:
        subtitleFolder = mediaPool.AddSubFolder(rootFolder, "SubTitles")
    # mediaPool.SetCurrentFolder(subtitleFolder)
    # mediaPoolItem = mediaPool.ImportFile([{"FilePath": srt_file}])
    timeline = project.GetCurrentTimeline()
    if timeline.GetTrackCount("subtitle") <= 0:
        timeline.AddTrack("subtitle")


def convert_jianying_json_to_srt(json_file, srt_folder):
    f = open(json_file, mode="r", encoding="utf-8")
    data = json.load(f)
    time_dict = {}
    for track in data["tracks"]:
        if track["type"] == "text":
            for segment in track["segments"]:
                time_dict[segment["material_id"]] = segment["target_timerange"]
    f.close()
    project = bmd.scriptapp("Resolve").GetProjectManager().GetCurrentProject()
    project_name = project.GetName()
    time_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    srt_file = os.path.join(srt_folder, f"{project_name}_{time_str}.srt")
    f = open(srt_file, "w+", encoding="utf-8")
    i = 0
    for text in data["materials"]["texts"]:
        start_and_duration = time_dict[text["id"]]
        start_time = str(datetime.timedelta(microseconds=start_and_duration["start"]))[:-3].replace(".", ",")
        end_time = str(datetime.timedelta(microseconds=start_and_duration["start"] + start_and_duration["duration"]))[
                   :-3].replace(".", ",")
        f.writelines([str(i) + "\n", f"{start_time} --> {end_time}\n", text["content"] + "\n", "\n"])
        i += 1
    f.close()
    # mediaPool ImportFile can not import srt file
    resolve_handle_subtitle(srt_file)
    dispatcher.ExitLoop()


def process_srt(ev):
    source_json = items[fileLabelId]["Text"]
    target_path = items[folderLabelId]["Text"]
    if os.path.exists(source_json) and os.path.exists(target_path):
        convert_jianying_json_to_srt(source_json, target_path)
    else:
        if not source_json:
            print('[File] is Empty!')
            items[fileLabelId]["Text"] = "Please set File Path!"
        if not target_path:
            print('[Folder] is Empty!')
            items[folderLabelId]["Text"] = "Please set Folder Path!"
        return


# assign event handlers
win.On[winID].Close = close
win.On[tabsID].CurrentChanged = change_tab
win.On[exec2ID].Clicked = process_srt
win.On[fileButtonId].Clicked = click_file_button
win.On[folderButtonId].Clicked = click_folder_button

# Main dispatcher loop
if __name__ == '__main__':
    win.Show()
    dispatcher.RunLoop()
    win.Hide()
