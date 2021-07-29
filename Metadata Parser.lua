local script_path = arg[0]

local getPath=function(str,sep)
    sep=sep or'/'
    return str:match("(.*"..sep..")")
end

local lib = ffi.load(ffi.os == "Windows" and getPath(arg[0], "\\").."resolve-metadata.dll" or getPath(arg[0]).."resolve-metadata.so")
ffi.cdef[[
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
		char *NdFilter;
		char *CompressionRatio;
		char *CodecBitrate;
		char *AspectRatioNotes;
		char *GammaNotes;
		char *ColorSpaceNotes;
	}DRMetadata ;
	extern __declspec(dllexport) DRMetadata DRProcessMediaFile(char* absPath);
]]

local function processClip( clip )
	local filePath = clip:GetClipProperty("File Path")
	if filePath ~= "" then
		local c_str = ffi.new("char[?]", #filePath)
		ffi.copy(c_str, filePath)
		local res = lib.DRProcessMediaFile(c_str)
		if res == nil then
			print("Failed to parse clip"..filePath)
			return
		end
		if not res.IsSupportMedia then
			print("Clip "..filePath.." Not Support.")
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
		returnVal["ND Filter"] = ffi.string(res.NdFilter)
		returnVal["Compression Ratio"] = ffi.string(res.CompressionRatio)
		returnVal["Codec Bitrate"] = ffi.string(res.CodecBitrate)
		returnVal["Aspect Ratio Notes"] = ffi.string(res.AspectRatioNotes)
		returnVal["Gamma Notes"] = ffi.string(res.GammaNotes)
		returnVal["Color Space Notes"] = ffi.string(res.ColorSpaceNotes)
		for key, value in pairs(returnVal) do
			if value ~= "" then
				metadata[key] = value
			end
		end
		if next(metadata) == nil then
			print("Ignore Clip "..filePath)
			return
		end
		if clip:SetMetadata(metadata) then
			print("Process clip "..filePath.." successfully.")
		else
			print("Failed to set clip "..filePath.." metadata")
		end
	end
end

local function processClips( folder )
	local clips = folder:GetClipList()
	for i=1, #clips do
		processClip(clips[i])
	end
	local subFolders = folder:GetSubFolderList()
	for i=1, #subFolders do
		processClips(subFolders[i])
	end
end

resolve = Resolve()
projectManager = resolve:GetProjectManager()
project = projectManager:GetCurrentProject()
mediaPool = project:GetMediaPool()
rootFolder = mediaPool:GetRootFolder()
processClips(rootFolder)

print("All Done!")
