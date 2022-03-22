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
        char *Manufacturer;
        char *FileFormatAndRecFrameRate;
        char *ModelName;
        char *FormatFPS;
        char *CaptureFPS;
        char *VideoBitrate;
        char *Profile;
        char *RecordingMode;
        bool IsProxyOn;
        long long int CreationTimestamp;
        int TimecodeSecs;
        int TimecodeFrame;
    } DRSonyNrtmd;

    typedef struct
    {
        int Frame;
        char *Data;
    } DRFrameData;

    typedef struct
    {
        DRFrameData array[1000];
        int len;
    } DRFrameDataArray;

    typedef struct
    {
        DRFrameDataArray WhiteBalanceModeArray;
        DRFrameDataArray ExposureModeArray;
        DRFrameDataArray AutoFocusSensingAreaArray;
        DRFrameDataArray ShutterSpeedArray;
        DRFrameDataArray ApertureArray;
        DRFrameDataArray ISOArray;
        DRFrameDataArray FocalLengthArray;
        DRFrameDataArray FocalLength35mmArray;
        DRFrameDataArray FocusPositionArray;
        DRFrameDataArray CaptureGammaEquationArray;
	    DRFrameDataArray CameraMasterGainAdjustmentArray;
        long long int Offset;
    } DRSonyRtmdDisp;

	extern __declspec(dllexport) DRSonyNrtmd DRSonyNrtmdDisp(char* absPath);
	extern __declspec(dllexport) DRSonyRtmdDisp DrSonyRtmdDisp(char* absPath, int start, int count, long long int offset);
]]

local function log_line(message)
    print(string.format("[%s] %s", os.date("%Y-%m-%d %X"), message))
end

local function isSonyXAVC()
    local filePath = mediaIn:GetData("MediaProps.MEDIA_PATH")
    if filePath ~= "" then
        local c_str = ffi.new("char[?]", #filePath + 1)
        ffi.copy(c_str, filePath)
        local res = lib.DRSonyNrtmdDisp(c_str)
        if res == nil or not res.IsSupportMedia then
            MyWindow("未找到媒体文件，或非SONY XAVC格式媒体文件")
            return false
        else
            return true
        end
    else
        MyWindow("无法找到媒体路径！")
        return false
    end
end

local function getSonyNrtmd(filePath)
    if filePath ~= "" then
        local c_str = ffi.new("char[?]", #filePath + 1)
        ffi.copy(c_str, filePath)
        local res = lib.DRSonyNrtmdDisp(c_str)
        if res == nil then
            log_line("Failed to parse clip" .. filePath)
            return
        end
        comp.FileFormatAndFrameRate.StyledText = ffi.string(res.FileFormatAndRecFrameRate)
        comp.BitrateText.StyledText = string.gsub(ffi.string(res.VideoBitrate), "Mbps", "")
        comp.Profile.StyledText = ffi.string(res.Profile)
        comp.ModelName.StyledText = ffi.string(res.ModelName)
        comp.CaptureFramerate.StyledText = string.gsub(ffi.string(res.CaptureFPS), "p", "fps")
        comp.ModelName.StyledText = ffi.string(res.ModelName)
        comp.DateTime.Timestamp = tonumber(res.CreationTimestamp)
        comp.Timecode.FirstFrameTimeInSec = res.TimecodeSecs
        comp.Timecode.FirstFrameFrameNum = res.TimecodeFrame
        local fps = ffi.string(res.FormatFPS):gsub("p", "")
        comp.Timecode.RecFrameRate = tonumber(fps)

        if ffi.string(res.RecordingMode) == "normal" then
            comp.RecordModeTransform.RecordMode = 0
        elseif ffi.string(res.RecordingMode) == "S&Q" then
            comp.RecordModeTransform.RecordMode = 1
        end
        if res.IsProxyOn then
            comp.ProxyIconTx.ProxyOn = 1
        else
            comp.ProxyIconTx.ProxyOn = 0
        end
    end
end

function MyWindow(text)
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
                    Text = text,
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
end

function handleRtmdByFrame(res)
    local whiteBalanceLen = res.WhiteBalanceModeArray.len
    for i = 0, whiteBalanceLen - 1 do
        if ffi.string(res.WhiteBalanceModeArray.array[i].Data) == lastWhiteBalance then
            goto continue
        end
        lastWhiteBalance = ffi.string(res.WhiteBalanceModeArray.array[i].Data)
        if lastWhiteBalance == "Auto" then
            comp.WBTransform.WBSelector[res.WhiteBalanceModeArray.array[i].Frame] = 0
        elseif lastWhiteBalance == "SunLight" then
            comp.WBTransform.WBSelector[res.WhiteBalanceModeArray.array[i].Frame] = 1
        elseif lastWhiteBalance == "Cloudy" then
            comp.WBTransform.WBSelector[res.WhiteBalanceModeArray.array[i].Frame] = 2
        elseif lastWhiteBalance == "Incandescent" then
            comp.WBTransform.WBSelector[res.WhiteBalanceModeArray.array[i].Frame] = 3
        elseif lastWhiteBalance == "Fluorescent" then
            comp.WBTransform.WBSelector[res.WhiteBalanceModeArray.array[i].Frame] = 4
        elseif lastWhiteBalance == "Other" then
            comp.WBTransform.WBSelector[res.WhiteBalanceModeArray.array[i].Frame] = 5
        elseif lastWhiteBalance == "Custom" then
            comp.WBTransform.WBSelector[res.WhiteBalanceModeArray.array[i].Frame] = 6
        elseif lastWhiteBalance == "Unknown" then
            comp.WBTransform.WBSelector[res.WhiteBalanceModeArray.array[i].Frame] = 7
        end
        :: continue ::
    end
    local shutterSpeedLen = res.ShutterSpeedArray.len
    for i = 0, shutterSpeedLen - 1 do
        if ffi.string(res.ShutterSpeedArray.array[i].Data) == lastShutterSpeed then
            goto continue
        end
        lastShutterSpeed = ffi.string(res.ShutterSpeedArray.array[i].Data)
        comp.ShutterSpeed.StyledText[res.ShutterSpeedArray.array[i].Frame] = lastShutterSpeed
        :: continue ::
    end
    local exposureModeLen = res.ExposureModeArray.len
    for i = 0, exposureModeLen - 1 do
        if ffi.string(res.ExposureModeArray.array[i].Data) == lastExposureMode then
            goto continue
        end
        lastExposureMode = ffi.string(res.ExposureModeArray.array[i].Data)
        --P档也是Manual
        if lastExposureMode == "Manual" then
            comp.ExposureMode.StyledText[res.ExposureModeArray.array[i].Frame] = "M"
        elseif lastExposureMode == "A Mode" then
            comp.ExposureMode.StyledText[res.ExposureModeArray.array[i].Frame] = "A"
        elseif lastExposureMode == "S Mode" then
            comp.ExposureMode.StyledText[res.ExposureModeArray.array[i].Frame] = "S"
        else
            comp.ExposureMode.StyledText[res.ExposureModeArray.array[i].Frame] = ""
        end
        :: continue ::
    end
    local autoFocusSensingAreaLen = res.AutoFocusSensingAreaArray.len
    for i = 0, autoFocusSensingAreaLen - 1 do
        if ffi.string(res.AutoFocusSensingAreaArray.array[i].Data) == lastAutoFocusSensingArea then
            goto continue
        end
        lastAutoFocusSensingArea = ffi.string(res.AutoFocusSensingAreaArray.array[i].Data)
        if lastAutoFocusSensingArea == "AF Whole" then
            comp.FocusAreaTransform.FocusAreaSelector[res.AutoFocusSensingAreaArray.array[i].Frame] = 0
        elseif lastAutoFocusSensingArea == "AF Multi" then
            comp.FocusAreaTransform.FocusAreaSelector[res.AutoFocusSensingAreaArray.array[i].Frame] = 1
        elseif lastAutoFocusSensingArea == "AF Center" then
            comp.FocusAreaTransform.FocusAreaSelector[res.AutoFocusSensingAreaArray.array[i].Frame] = 2
        elseif lastAutoFocusSensingArea == "AF Spot" then
            comp.FocusAreaTransform.FocusAreaSelector[res.AutoFocusSensingAreaArray.array[i].Frame] = 3
        elseif lastAutoFocusSensingArea == "MF" then
            comp.FocusAreaTransform.FocusAreaSelector[res.AutoFocusSensingAreaArray.array[i].Frame] = 4
        end
        :: continue ::
    end
    local apertureLen = res.ApertureArray.len
    for i = 0, apertureLen - 1 do
        if ffi.string(res.ApertureArray.array[i].Data) == lastAperture then
            goto continue
        end
        lastAperture = ffi.string(res.ApertureArray.array[i].Data)
        comp.Aperture.StyledText[res.ApertureArray.array[i].Frame] = lastAperture
        :: continue ::
    end
    local isoLen = res.ISOArray.len
    for i = 0, isoLen - 1 do
        if ffi.string(res.ISOArray.array[i].Data) == lastISO then
            goto continue
        end
        lastISO = ffi.string(res.ISOArray.array[i].Data)
        comp.ISO.StyledText[res.ISOArray.array[i].Frame] = lastISO
        :: continue ::
    end
    local focalLengthLen = res.FocalLengthArray.len
    for i = 0, focalLengthLen - 1 do
        if ffi.string(res.FocalLengthArray.array[i].Data) == lastFocalLength then
            goto continue
        end
        lastFocalLength = ffi.string(res.FocalLengthArray.array[i].Data)
        comp.FocalLength.StyledText[res.FocalLengthArray.array[i].Frame] = lastFocalLength
        :: continue ::
    end
    local focalLength35mmLen = res.FocalLength35mmArray.len
    for i = 0, focalLength35mmLen - 1 do
        if ffi.string(res.FocalLength35mmArray.array[i].Data) == lastFocalLength35mm then
            goto continue
        end
        lastFocalLength35mm = ffi.string(res.FocalLength35mmArray.array[i].Data)
        comp.FocalLength_35mm.StyledText[res.FocalLength35mmArray.array[i].Frame] = lastFocalLength35mm
        :: continue ::
    end
    local focusPositionLen = res.FocusPositionArray.len
    for i = 0, focusPositionLen - 1 do
        if ffi.string(res.FocusPositionArray.array[i].Data) == lastFocusPosition then
            goto continue
        end
        lastFocusPosition = ffi.string(res.FocusPositionArray.array[i].Data)
        comp.FocusPosition.StyledText[res.FocusPositionArray.array[i].Frame] = lastFocusPosition
        :: continue ::
    end
    local gammaEquationLen = res.CaptureGammaEquationArray.len
    for i = 0, gammaEquationLen - 1 do
        if ffi.string(res.CaptureGammaEquationArray.array[i].Data) == lastGammaEquation then
            goto continue
        end
        lastGammaEquation = ffi.string(res.CaptureGammaEquationArray.array[i].Data)
        comp.GammaEquation.StyledText[res.CaptureGammaEquationArray.array[i].Frame] = lastGammaEquation
        if lastGammaEquation == "rec709/Still" then
            comp.PPTransform.PPSelector[res.CaptureGammaEquationArray.array[i].Frame] = 2
        elseif lastGammaEquation == "rec709/Cine1" then
            comp.PPTransform.PPSelector[res.CaptureGammaEquationArray.array[i].Frame] = 5
        elseif lastGammaEquation == "rec709/Cine2" then
            comp.PPTransform.PPSelector[res.CaptureGammaEquationArray.array[i].Frame] = 6
        elseif lastGammaEquation == "S-Gamut/S-Log2" then
            comp.PPTransform.PPSelector[res.CaptureGammaEquationArray.array[i].Frame] = 7
        elseif lastGammaEquation == "S-Gamut3.Cine/S-Log3-Cine" then
            comp.PPTransform.PPSelector[res.CaptureGammaEquationArray.array[i].Frame] = 8
        elseif lastGammaEquation == "S-Gamut3/S-Log3" then
            comp.PPTransform.PPSelector[res.CaptureGammaEquationArray.array[i].Frame] = 9
        elseif lastGammaEquation == "rec2020/Rec2100-HLG" then
            comp.PPTransform.PPSelector[res.CaptureGammaEquationArray.array[i].Frame] = 10
        elseif lastGammaEquation == "rec709/S-Cinetone" then
            comp.PPTransform.PPSelector[res.CaptureGammaEquationArray.array[i].Frame] = 11
        else
            comp.PPTransform.PPSelector[res.CaptureGammaEquationArray.array[i].Frame] = 13
        end
        :: continue ::
    end
    local masterGainAdjustmentLen = res.CameraMasterGainAdjustmentArray.len
    for i = 0, masterGainAdjustmentLen - 1 do
        if ffi.string(res.CameraMasterGainAdjustmentArray.array[i].Data) == lastGainAdjustment then
            goto continue
        end
        lastGainAdjustment = ffi.string(res.CameraMasterGainAdjustmentArray.array[i].Data)
        comp.GainAdjustment.StyledText[res.CameraMasterGainAdjustmentArray.array[i].Frame] = lastGainAdjustment
        :: continue ::
    end
end

function getSonyRtmdByFrame(filePath, start, batch_count, offset)
    log_line(string.format("处理帧:%d至%d", start, start + batch_count - 1))
    local c_str = ffi.new("char[?]", #filePath + 1)
    ffi.copy(c_str, filePath)
    local res = lib.DrSonyRtmdDisp(c_str, start, batch_count, offset)
    handleRtmdByFrame(res)
    return tonumber(res.Offset)
end

function setBezier()
    comp.CurrentTime = comp:GetAttrs("COMPN_RenderStart")
    comp.ShutterSpeed.StyledText = comp:BezierSpline()
    comp.ExposureMode.StyledText = comp:BezierSpline()
    comp.Aperture.StyledText = comp:BezierSpline()
    comp.ISO.StyledText = comp:BezierSpline()
    comp.FocalLength.StyledText = comp:BezierSpline()
    comp.FocalLength_35mm.StyledText = comp:BezierSpline()
    comp.FocusPosition.StyledText = comp:BezierSpline()
    comp.GammaEquation.StyledText = comp:BezierSpline()
    comp.GainAdjustment.StyledText = comp:BezierSpline()
    comp.WBTransform.WBSelector = comp:BezierSpline()
    comp.FocusAreaTransform.FocusAreaSelector = comp:BezierSpline()
    comp.PPTransform.PPSelector = comp:BezierSpline()
end

function Main()
    log_line("Sony MILC开始")
    if comp == nil then
        MyWindow("请在Fusion页面中打开此脚本")
        return
    end
    mediaIn = comp:FindToolByID("MediaIn")
    if mediaIn == nil then
        MyWindow("您的fusion效果中没有MediaIn节点！")
        return
    end
    if isSonyXAVC() then
        if comp:FindTool("SonyMILC") ~= nil then
            comp.SonyMILC:Delete()
        end
        comp:SetActiveTool(mediaIn)
        comp:DoAction("AddSetting", { filename = "Templates:/Edit/Effects/XiaoLi/Sony MILC.setting" })
    else
        return
    end
    comp.SonyMILC:SetAttrs({ TOOLB_PassThrough = true })

    local filePath = mediaIn:GetData("MediaProps.MEDIA_PATH")
    log_line("获取静态数据")
    getSonyNrtmd(filePath)

    renderStart = comp:GetAttrs("COMPN_RenderStart")
    renderEnd = comp:GetAttrs("COMPN_RenderEnd")

    setBezier()
    local batch_count = 1000
    local start
    local i = 0
    local offset = 0

    log_line("开始获取帧数据")
    while (true)
    do
        start = renderStart + batch_count * i
        if start + batch_count >= renderEnd + 1 then
            offset = getSonyRtmdByFrame(filePath, start, renderEnd - start + 1, offset)
            break
        end
        offset = getSonyRtmdByFrame(filePath, start, batch_count, offset)
        i = i + 1
    end

    comp.SonyMILC:SetAttrs({ TOOLB_PassThrough = false })
    log_line("完成!")
end

Main()
