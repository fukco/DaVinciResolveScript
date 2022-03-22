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

local function log_line(message)
    print(string.format("[%s] %s", os.date("%Y-%m-%d %X"), message))
end

local function processClip(clip)
    local filePath = clip:GetClipProperty("File Path")
    if filePath ~= "" then
        local c_str = ffi.new("char[?]", #filePath+1)
        ffi.copy(c_str, filePath)
        local res = lib.DRProcessMediaFile(c_str)
        if res == nil then
            log_line("Failed to parse clip" .. filePath)
            return
        end
        if not res.IsSupportMedia then
            log_line("Clip " .. filePath .. " Not Support.")
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
            log_line("Ignore Clip " .. filePath)
            return
        end
        if clip:SetMetadata(metadata) then
            log_line("Process clip " .. filePath .. " successfully.")
            return true
        else
            log_line("Failed to set clip " .. filePath .. " metadata")
        end
    end
end

local function processClips(folder)
    local clips = folder:GetClipList()
    for i = 1, #clips do
        if processClip(clips[i]) then
            n = n + 1
        end
    end
    local subFolders = folder:GetSubFolderList()
    for i = 1, #subFolders do
        processClips(subFolders[i])
    end
end

resolve = Resolve()
projectManager = resolve:GetProjectManager()
project = projectManager:GetCurrentProject()
mediaPool = project:GetMediaPool()
rootFolder = mediaPool:GetRootFolder()
n = 0
processClips(rootFolder)

local ui = fu.UIManager
local disp = bmd.UIDispatcher(ui)

win = disp:AddWindow({
    ID = 'MyWin',
    WindowTitle = 'Notification',
    Spacing = 10,

    ui:VGroup {
        ID = 'root',

        -- Add your GUI elements here:
        ui:HGroup {
            ui:Label {
                Text = n .. ' clips in media pool has been parsed.\nMore details in console.',
                Alignment = { AlignHCenter = true, AlignVCenter = true },
            },
        },

        ui:HGroup {
            Weight = 0,
            ui:Button {
                ID = 'B',
                Text = 'OK',
            },
        }
    },
})
win:Resize({ 400, 120 });
win:RecalcLayout();

-- The window was closed
function win.On.MyWin.Close(ev)
    disp:ExitLoop()
end

-- Add your GUI element based event functions here:
itm = win:GetItems()

function win.On.B.Clicked(ev)
    disp:ExitLoop()
end

win:Show()
disp:RunLoop()
win:Hide()
