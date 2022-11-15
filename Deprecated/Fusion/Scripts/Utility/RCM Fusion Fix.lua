project = resolve:GetProjectManager():GetCurrentProject()
project_settings = project:GetSetting()
color_science_mode = project_settings['colorScienceMode']
timeline_working_luminance_mode = project_settings['timelineWorkingLuminanceMode']
timeline_working_luminance = project_settings['timelineWorkingLuminance']
separate_color_space_and_gamma = project_settings['separateColorSpaceAndGamma']
color_space_output_gamma = project_settings['colorSpaceOutputGamma']
color_space_output = project_settings['colorSpaceOutput']

source_color_space_rec709 = "Rec.709"
source_color_space_rec2020 = "Rec.2020"
source_color_space_dw = "DaVinci WG"

source_gamma_twoPointFour = "Gamma 2.4"
source_gamma_hlg = "Rec.2100 HLG"
source_gamma_pq = "Rec.2100 ST2084"
source_gamma_di = "DaVinci Intermediate"

target_color_space_default = "REC709_COLORSPACE"
target_color_space_rec2020 = "REC2020_COLORSPACE"
target_color_space_dw = "DWG_COLORSPACE"

target_gamma_default = "TWOPOINTFOUR_GAMMA"
target_gamma_hlg = "GAMMA_REC2100_HLG_EOTF"
target_gamma_pq = "GAMMA_REC2100_PQ_EOTF"
target_gamma_di = "DAV_INTER_OETF_GAMMA"

local function getLuminance()
    if timeline_working_luminance_mode == 'Custom' then
        timeline_luminance = timeline_working_luminance
    else
        if string.find(timeline_working_luminance_mode, '/') then
            timeline_luminance = string.match(timeline_working_luminance_mode, '.*%/(%d+)')
        else
            timeline_luminance = string.match(timeline_working_luminance_mode, '[SH]DR (%d+)')
        end
    end
end

local function getOutputColorSpaceAndGamma()
    if tonumber(separate_color_space_and_gamma) == 1 then
        source_output_color_space = color_space_output
        source_output_gamma = color_space_output_gamma
    elseif tonumber(separate_color_space_and_gamma) == 0 then
        if color_space_output == "Rec.709 Gamma 2.4" then
            source_output_color_space = source_color_space_rec709
            source_output_gamma = source_gamma_twoPointFour
        elseif color_space_output == "Rec.2020 Gamma 2.4" then
            source_output_color_space = source_color_space_rec2020
            source_output_gamma = source_gamma_twoPointFour
        elseif color_space_output == "Rec.2100 HLG" then
            source_output_color_space = source_color_space_rec2020
            source_output_gamma = source_gamma_hlg
        elseif color_space_output == "Rec.2100 ST2084" then
            source_output_color_space = source_color_space_rec2020
            source_output_gamma = source_gamma_pq
        elseif color_space_output == "DaVinci WG" then
            source_output_color_space = source_color_space_dw
            source_output_gamma = source_gamma_di
        end
    end

    if source_output_color_space == source_color_space_rec709 then
        target_color_space = target_color_space_default
    elseif source_output_color_space == source_color_space_rec2020 then
        target_color_space = target_color_space_rec2020
    elseif source_output_color_space == source_color_space_dw then
        target_color_space = target_color_space_dw
    end

    if source_output_gamma == source_gamma_twoPointFour then
        target_gamma = target_gamma_default
    elseif source_output_gamma == source_gamma_hlg then
        target_gamma = target_gamma_hlg
    elseif source_output_gamma == source_gamma_pq then
        target_gamma = target_gamma_pq
    elseif source_output_gamma == source_gamma_di then
        target_gamma = target_gamma_di
    end
end

function rcm_fusion_fix(videoItem, comp)
    local changed = false
    mediaOutNode = comp:FindToolByID("MediaOut")
    mediaInNode = comp:FindToolByID("MediaIn")
    --DaVinci Resolve can not set ActiveTool when a comp has never been opened in fusion
    comp:SetActiveTool(mediaOutNode)
    runInFusion = false
    if comp.ActiveTool then
        runInFusion = true
    end

    getLuminance()
    getOutputColorSpaceAndGamma()

    if mediaOutNode then
        local addTransformNode = true
        local addDisplayNode = true
        if videoItem:GetMediaPoolItem() then
            addTransformNode = false
            if mediaInNode and mediaInNode:GetData('MediaProps').MEDIA_FORMAT_TYPE == 'DNG' then
                addDisplayNode = false
            end
        end

        -- Add Color Space Transform
        if addTransformNode and not comp:FindTool("RCMColorSpaceTransform") then
            if not comp:FindTool("RCMFusionTransform1") then
                if mediaOutNode:FindMainInput(1) and mediaOutNode:FindMainInput(1):GetConnectedOutput() then
                    connectedOutput = mediaOutNode:FindMainInput(1):GetConnectedOutput()
                    connectedNode = connectedOutput:GetTool()
                    while connectedNode.ParentTool do
                        connectedNode = connectedNode.ParentTool
                    end
                    comp:SetActiveTool(connectedNode)
                end
                if runInFusion then
                    tool1 = comp:AddTool('ofx.com.blackmagicdesign.resolvefx.ColorSpaceTransformV2', -32768, -32768)
                else
                    tool1 = comp:AddTool('ofx.com.blackmagicdesign.resolvefx.ColorSpaceTransformV2')
                    tool1.Source:ConnectTo(connectedOutput)
                end
                tool1:SetAttrs({ TOOLS_Name = 'RCMFusionTransform1' })
                tool1.inputColorSpace = target_color_space
                tool1.inputGamma = target_gamma
                tool1.isDstLumMaxCustomEnabled = 1
                tool1.dstLumMax = tonumber(timeline_luminance)
                tool1.doInvOOTF = 1
                changed = true
            end

            if not comp:FindTool("RCMFusionTransform2") then
                if runInFusion then
                    tool2 = comp:AddTool('ofx.com.blackmagicdesign.resolvefx.ColorSpaceTransformV2', -32768, -32768)
                else
                    tool2 = comp:AddTool('ofx.com.blackmagicdesign.resolvefx.ColorSpaceTransformV2')
                    tool2.Source:ConnectTo(tool1.Output)
                    mediaOutNode.Input:ConnectTo(tool2.Output)
                end
                tool2:SetAttrs({ TOOLS_Name = 'RCMFusionTransform2' })
                tool2.outputGamma = "LINEAR_GAMMA"
                tool2.tmType = "TM_NONE"
                changed = true
            end
        end

        -- Add MediaOut Display Color Space Transform
        comp:SetActiveTool(mediaOutNode)
        if addDisplayNode and not comp:FindTool("RCMColorSpaceDisplay") then
            if not comp:FindTool('RCMFusionDisplay1') then
                if runInFusion then
                    tool3 = comp:AddTool('ofx.com.blackmagicdesign.resolvefx.ColorSpaceTransformV2', -32768, -32768)
                else
                    tool3 = comp:AddTool('ofx.com.blackmagicdesign.resolvefx.ColorSpaceTransformV2')
                    tool3.Source:ConnectTo(mediaOutNode.Output)
                end
                tool3:SetAttrs({ TOOLS_Name = 'RCMFusionDisplay1' })
                tool3.inputGamma = "LINEAR_GAMMA"
                tool3.tmType = "TM_NONE"
                changed = true
            end

            if not comp:FindTool('RCMFusionDisplay2') then
                if runInFusion then
                    tool4 = comp:AddTool('ofx.com.blackmagicdesign.resolvefx.ColorSpaceTransformV2', -32768, -32768)
                else
                    tool4 = comp:AddTool('ofx.com.blackmagicdesign.resolvefx.ColorSpaceTransformV2')
                    tool4.Source:ConnectTo(tool3.Output)
                end
                tool4:SetAttrs({ TOOLS_Name = 'RCMFusionDisplay2' })
                tool4.outputColorSpace = target_color_space
                tool4.outputGamma = target_gamma
                tool4.isSrcLumMaxCustomEnabled = 1
                tool4.srcLumMax = tonumber(timeline_luminance)
                tool4.doFwdOOTF = 1
                changed = true
            end
        end
    end
    return changed
end

project = resolve:GetProjectManager():GetCurrentProject()
color_science_mode = project:GetSetting('colorScienceMode')
color_space_timeline = project:GetSetting('colorSpaceTimeline')
n = 0
if color_science_mode == 'davinciYRGBColorManagedv2' then
    timeline = project:GetCurrentTimeline()
    track_count = timeline:GetTrackCount("video")

    for index = 1, track_count do
        items = timeline:GetItemListInTrack("video", index)
        if items and table.getn(items) > 0 then
            for _, v in ipairs(items) do
                count = v:GetFusionCompCount()
                if count == 1 then
                    comp = v:GetFusionCompByIndex(1)
                    if rcm_fusion_fix(v, comp) then
                        n = n + 1
                    end
                elseif count > 1 then
                    print(v:GetName() .. " Fusion comp count more than 1")
                    break
                end
            end
        end
    end
end

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
                Text = n .. ' fusion compositions has been fixed!',
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
