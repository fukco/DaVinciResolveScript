gui_mode = 1

local color_space_match_list = {
    { manufacturer = "Atomos", details = {
        { gamma_notes = "CLog", color_science_mode = "Cinema", input_color_space = "Canon Cinema Gamut/Canon Log" },
        { gamma_notes = "CLog2", color_science_mode = "Cinema", input_color_space = "Canon Cinema Gamut/Canon Log2" },
        { gamma_notes = "CLog3", color_science_mode = "Cinema", input_color_space = "Canon Cinema Gamut/Canon Log3" },
        { gamma_notes = "F-Log", color_science_mode = "F-Gamut", input_color_space = "FujiFilm F-Log" },
        { gamma_notes = "V-Log", color_science_mode = "V-Gamut", input_color_space = "Panasonic V-Gamut/V-Log" },
        { gamma_notes = "SLog3", color_science_mode = "SGamut3", input_color_space = "S-Gamut3/S-Log3" },
        { gamma_notes = "SLog3", color_science_mode = "SGamut3Cine", input_color_space = "S-Gamut3.Cine/S-Log3" },
        { gamma_notes = "N-Log", color_science_mode = "BT.2020", input_color_space = "Nikon N-Log" },
        { gamma_notes = "HLG", color_science_mode = "BT.2020", input_color_space = "Rec.2100 HLG" }
    } },
    { manufacturer = "Fujifilm", details = {
        { gamma_notes = "F-log", color_science_mode = "", input_color_space = "FujiFilm F-Log" }
    } },
    { manufacturer = "Panasonic", details = {
        { gamma_notes = "V-Log", color_science_mode = "V-Gamut", input_color_space = "Panasonic V-Gamut/V-Log" }
    } },
    { manufacturer = "Sony", details = {
        { gamma_notes = "s-log2", color_science_mode = "s-gamut", input_color_space = "S-Gamut/S-Log2" },
        { gamma_notes = "s-log3-cine", color_science_mode = "s-gamut3-cine", input_color_space = "S-Gamut3.Cine/S-Log3" },
        { gamma_notes = "s-log3", color_science_mode = "s-gamut3", input_color_space = "S-Gamut3/S-Log3" },
        { gamma_notes = "rec2100-hlg", color_science_mode = "rec2020", input_color_space = "Rec.2100 HLG" },
    }
    }
}

local color_space_match_map = {}

for _, value in ipairs(color_space_match_list) do
    for _, detail in ipairs(value["details"]) do
        if color_space_match_map[detail["gamma_notes"]] then
            local exist = color_space_match_map[detail["gamma_notes"]]
            if exist[detail["color_science_mode"]] == nil then
                exist[detail["color_science_mode"]] = detail["input_color_space"]
            end
        else
            local child = {}
            child[detail["color_science_mode"]] = detail["input_color_space"]
            color_space_match_map[detail["gamma_notes"]] = child
        end
    end
end

local lib
if ffi.os == "Windows" then
    lib = ffi.load(fusion:MapPath('LuaModules:/resolve-metadata.dll'))
elseif ffi.os == "OSX" then
    if ffi.arch == "x64" then
        lib = ffi.load(fusion:MapPath('LuaModules:/resolve-metadata-amd64.dylib'))
    elseif ffi.arch == "arm64" then
        lib = ffi.load(fusion:MapPath('LuaModules:/resolve-metadata-arm64.dylib'))
    end
end

ffi.cdef [[
	typedef struct
	{
		bool IsSupportMedia;
		char *CameraType;
		char *CameraManufacturer;
		char *CameraSerial;
		char *CameraId;
		char *CameraNotes;
		char *CameraFormat;
		char *MediaType;
		char *TimeLapseInterval;
		char *CameraFps;
		char *ShutterType;
		char *Shutter;
		char *ISO;
		char *WhitePoint;
		char *WhiteBalanceTint;
		char *CameraFirmware;
		char *LensType;
		char *LensNumber;
		char *LensNotes;
		char *CameraApertureType;
		char *CameraAperture;
		char *FocalPoint;
		char *Distance;
		char *Filter;
		char *NDFilter;
		char *CompressionRatio;
		char *CodecBitrate;
		char *SensorAreaCaptured;
		char *PARNotes;
		char *AspectRatioNotes;
		char *GammaNotes;
		char *ColorSpaceNotes;
	} DRMetadata;
	extern __declspec(dllexport) DRMetadata DRProcessMediaFile(char* absPath);
]]

local function LogLine(message)
    print(string.format("[%s] %s", os.date("%Y-%m-%d %X"), message))
end

local function ProcessClip(clip)
    local filePath = clip:GetClipProperty("File Path")
    if filePath ~= "" then
        local c_str = ffi.new("char[?]", #filePath+1)
        ffi.copy(c_str, filePath)
        local res = lib.DRProcessMediaFile(c_str)
        if res == nil then
            LogLine("Failed to parse clip" .. filePath)
            return
        end
        if not res.IsSupportMedia then
            LogLine("Clip " .. filePath .. " Not Support.")
            return
        end
        local metadata = {}
        local returnVal = {}
        returnVal["Camera Type"] = ffi.string(res.CameraType)
        returnVal["Camera Manufacturer"] = ffi.string(res.CameraManufacturer)
        returnVal["Camera Serial #"] = ffi.string(res.CameraSerial)
        returnVal["Camera ID"] = ffi.string(res.CameraId)
        returnVal["Camera Notes"] = ffi.string(res.CameraNotes)
        returnVal["Camera Format"] = ffi.string(res.CameraFormat)
        returnVal["Media Type"] = ffi.string(res.MediaType)
        returnVal["Time-Lapse Interval"] = ffi.string(res.TimeLapseInterval)
        returnVal["Camera FPS"] = ffi.string(res.CameraFps)
        returnVal["Shutter Type"] = ffi.string(res.ShutterType)
        returnVal["Shutter"] = ffi.string(res.Shutter)
        returnVal["ISO"] = ffi.string(res.ISO)
        returnVal["White Point (Kelvin)"] = ffi.string(res.WhitePoint)
        returnVal["White Balance Tint"] = ffi.string(res.WhiteBalanceTint)
        returnVal["Camera Firmware"] = ffi.string(res.CameraFirmware)
        returnVal["Lens Type"] = ffi.string(res.LensType)
        returnVal["Lens Number"] = ffi.string(res.LensNumber)
        returnVal["Lens Notes"] = ffi.string(res.LensNotes)
        returnVal["Camera Aperture Type"] = ffi.string(res.CameraApertureType)
        returnVal["Camera Aperture"] = ffi.string(res.CameraAperture)
        returnVal["Focal Point (mm)"] = ffi.string(res.FocalPoint)
        returnVal["Distance"] = ffi.string(res.Distance)
        returnVal["Filter"] = ffi.string(res.Filter)
        returnVal["ND Filter"] = ffi.string(res.NDFilter)
        returnVal["Compression Ratio"] = ffi.string(res.CompressionRatio)
        returnVal["Codec Bitrate"] = ffi.string(res.CodecBitrate)
        returnVal["Sensor Area Captured"] = ffi.string(res.SensorAreaCaptured)
        returnVal["PAR Notes"] = ffi.string(res.PARNotes)
        returnVal["Aspect Ratio Notes"] = ffi.string(res.AspectRatioNotes)
        returnVal["Gamma Notes"] = ffi.string(res.GammaNotes)
        returnVal["Color Space Notes"] = ffi.string(res.ColorSpaceNotes)
        for key, value in pairs(returnVal) do
            if value ~= "" then
                metadata[key] = value
            end
        end
        if next(metadata) == nil then
            LogLine("Ignore Clip " .. filePath)
            return
        end
        if clip:SetMetadata(metadata) then
            LogLine("Process clip " .. filePath .. " successfully.")
            return true, metadata
        else
            LogLine("Failed to set clip " .. filePath .. " metadata")
        end
    end
end

local tree_id = "MatchTree"

local function GetClips(folder, result)
    for _, v in ipairs(folder:GetClipList()) do
        table.insert(result, v)
    end
    sub_folders = folder:GetSubFolders()
    for _, sub_folder in ipairs(sub_folders) do
        GetClips(sub_folder, result)
    end
end

local function AssignDataLevel(clip, metadata, assign_type)
    if metadata and metadata["Camera Manufacturer"] == "Atomos" then
        gamma_notes = metadata["Gamma Notes"] ~= nil and metadata["Gamma Notes"] or ""
        camera_notes = metadata["Camera Notes"] ~= nil and metadata["Camera Notes"] or ""
        if assign_type == 0 and (string.find(string.upper(gamma_notes), "LOG") or string.find(camera_notes, "Range: Legal")) or assign_type == 1 then
            if clip:SetClipProperty("Data Level", "Full") then
                LogLine(string.format("Assign %s data level full successfully.", clip:GetName()))
            else
                LogLine(string.format("Assign %s data level full failed.", clip:GetName()))
                return False
            end
        end
    end
    return true
end

local function ParseMetadata(clip)
    local result, metadata = ProcessClip(clip)
    if result then
        return metadata
    else
        return nil
    end
end

local function Execute(assign_data_level_enabled, assign_type, parse_metadata_enabled)
    if assign_data_level_enabled == nil then
        assign_data_level_enabled = true
    end
    if assign_type == nil then
        assign_type = 0
    end
    if parse_metadata_enabled == nil then
        parse_metadata_enabled = true
    end
    LogLine("Start match input color space and apply custom grading rules.")
    resolve = bmd.scriptapp("Resolve")
    project_manager = resolve:GetProjectManager()
    project = project_manager:GetCurrentProject()
    media_pool = project:GetMediaPool()
    root_folder = media_pool:GetRootFolder()
    local success = true
    is_rcm = string.find(project:GetSetting("colorScienceMode"), "davinciYRGBColorManaged")

    if not is_rcm then
        LogLine("RCM Not Enabled!")
        return false, "RCM Not Enabled!"
    end

    clips = {}

    GetClips(root_folder, clips)
    for _, clip in ipairs(clips) do
        metadata = parse_metadata_enabled and ParseMetadata(clip) or clip:GetMetadata()
        codec = clip:GetClipProperty('Video Codec')
        if not metadata or 'RED' == string.upper(codec) or string.find(string.upper(codec), 'RAW') then
            goto continue
        end
        if is_rcm then
            gamma_notes = metadata["Gamma Notes"]
            color_space_rotes = metadata["Color Space Notes"]
            if gamma_notes == nil then
                gamma_notes = ""
            end
            if not color_space_rotes then
                color_space_rotes = ""
            end
            if gamma_notes == "" and color_space_rotes == "" then
                goto continue
            end
            input_color_space = ""
            if color_space_match_map[gamma_notes] then
                input_color_space = color_space_match_map[gamma_notes][color_space_rotes]
            end
            if input_color_space ~= "" then
                if clip:GetClipProperty("Input Color Space") == input_color_space then
                    LogLine(string.format("%s Input Color Space is already set", clip:GetName()))
                    goto continue
                end
                if clip:SetClipProperty("Input Color Space", input_color_space) then
                    LogLine(string.format("%s Set Input Color Space %s Successfully.", clip:GetName(), input_color_space))
                else
                    LogLine(string.format("%s Set Input Color Space %s Failed!", clip:GetName(), input_color_space))
                end
            else
                success = false
                LogLine(string.format("%s Does Not Found Input Color Space Match Rule!", clip:GetName()))
            end
        end
        ::continue::
        if assign_data_level_enabled then
            if not AssignDataLevel(clip, metadata, assign_type) then
                success = false
            end
        end
    end
    if success then
        LogLine("All Done, Have Fun!")
        return true
    else
        LogLine("Some error happened, please check console details.")
        return false
    end
end

local function MainWindow()
    local ui = fu.UIManager
    local disp = bmd.UIDispatcher(ui)

    --define the window UI layout
    win = disp:AddWindow({
        ID = "RCMColorSpaceMatchWin",
        WindowTitle = "RCM Color Space Match",
        Spacing = 0,

        ui:VGroup {
            --color space match rule
            ui:Tree { ID = tree_id },

            ui:VGap(2),

            ui:HGroup {
                Weight = 0,
                ui:CheckBox { ID = "EnableMetadataParser", Text = "Enable Metadata Parser", Weight = 0, Checked = true },
                ui:CheckBox { ID = "EnableDataLevelAdjustment", Text = "Enable Assign Atomos Clips' Data Level", Weight = 0 },
                ui:ComboBox { ID = "DataLevelAdjustmentType", Weight = 1 }
            },

            ui:VGap(2),

            ui:HGroup {
                Weight = 0,
                ui:Button { Text = "Match", ID = "ExecuteButton", Weight = 0 },
                ui:HGap(5),
                ui:Label { Font = ui:Font { Family = "Times New Roman" }, ID = "InfoLabel" }
            }
        }
    })

    items = win:GetItems()

    --Add a header row.
    hdr = items[tree_id]:NewItem()
    hdr.Text[0] = "Gamma Notes"
    hdr.Text[1] = "Color Space Notes"
    hdr.Text[2] = "Input Color Space"
    items[tree_id]:SetHeaderItem(hdr)

    --Number of columns in the Tree list
    items[tree_id].ColumnCount = 3

    --Resize the Columns
    items[tree_id].ColumnWidth[0] = 200
    items[tree_id].ColumnWidth[1] = 200
    items[tree_id].ColumnWidth[2] = 260

    items.DataLevelAdjustmentType:AddItem('For Log and Legal Clips')
    items.DataLevelAdjustmentType:AddItem('For All Clips')

    for _, value in ipairs(color_space_match_list) do
        item = items[tree_id]:NewItem()
        item.Text[0] = value["manufacturer"]
        items[tree_id]:AddTopLevelItem(item)
        for _, detail in ipairs(value["details"]) do
            item_child = items[tree_id]:NewItem()
            item_child.Text[0] = detail["gamma_notes"]
            item_child.Text[1] = detail["color_science_mode"]
            item_child.Text[2] = detail["input_color_space"]
            item:AddChild(item_child)
        end
        item.Expanded = true
    end

    win:Resize({ 700, 480 });
    win:RecalcLayout();

    local function ShowMessage(message, t)
        t = t or 0
        if t == 0 then
            items.InfoLabel.Text = string.format("<font color='#39CA41'>%s</font>", message)
        elseif t == 1 then
            items.InfoLabel.Text = string.format("<font color='#922626'>%s</font>", message)
        end
    end

    function win.On.ExecuteButton.Clicked(ev)
        LogLine("Start Processing.")
        ShowMessage("Processing...")
        local success, message = Execute(items["EnableDataLevelAdjustment"]["Checked"],
                items["DataLevelAdjustmentType"]["CurrentIndex"],
                items["EnableMetadataParser"]["Checked"])
        if success then
            ShowMessage("All Down. Have Fun!")
        else
            if message then
                ShowMessage(message, 1)
            else
                ShowMessage("Some processes failed, please check console details.", 1)
            end
        end
    end

    -- The window was closed
    function win.On.RCMColorSpaceMatchWin.Close(ev)
        disp:ExitLoop()
    end

    win:Show()
    disp:RunLoop()
    win:Hide()
end

if gui_mode == 1 then
    MainWindow()
else
    Execute()
end