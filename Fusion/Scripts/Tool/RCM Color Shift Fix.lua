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

version_greater_equal_than_18_1 = false
local versions = resolve:GetVersion()
if versions[1] > 18 or (versions[1] == 18 and versions[2] >= 1) then
    version_greater_equal_than_18_1 = true
end

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

local function change_transform1(tool)
    if version_greater_equal_than_18_1 then
        tool.tmType = "TM_NONE"
    else
        tool.dstLumMax = tonumber(timeline_luminance)
        tool.inputColorSpace = target_color_space
        tool.inputGamma = target_gamma
        tool.doInvOOTF = 1
    end
end

local function change_display2(tool)
    if version_greater_equal_than_18_1 then
        tool.tmType = "TM_NONE"
    else
        tool.srcLumMax = tonumber(timeline_luminance)
        tool.outputColorSpace = target_color_space
        tool.outputGamma = target_gamma
        tool.doFwdOOTF = 1
    end
end

if color_science_mode == 'davinciYRGBColorManagedv2' then
    mediaOutNode = comp:FindToolByID("MediaOut")
    mediaInNode = comp:FindToolByID("MediaIn")
    comp:SetActiveTool(mediaOutNode)

    local addTransformNode = true
    local addDisplayNode = true

    if mediaInNode then
        addTransformNode = false
    end

    if mediaOutNode then
        -- Step1. Add Display Fix Macro
        if addDisplayNode and not comp:FindTool("RCMColorSpaceDisplay") and not comp:FindTool("RCMFusionDisplay1") then
            comp:DoAction("AddSetting", { filename = "Macros:/RCM Color Space Display.setting" })
        end

        -- Step2. Add Color Space Transform Macro
        if addTransformNode and not comp:FindTool("RCMColorSpaceTransform") and not comp:FindTool("RCMFusionTransform1") then
            if mediaOutNode:FindMainInput(1) and mediaOutNode:FindMainInput(1):GetConnectedOutput() then
                connectedNode = mediaOutNode:FindMainInput(1):GetConnectedOutput():GetTool()
                while connectedNode.ParentTool do
                    connectedNode = connectedNode.ParentTool
                end
                comp:SetActiveTool(connectedNode)
                comp:DoAction("AddSetting", { filename = "Macros:/RCM Color Space Transform.setting" })
            else
                comp:SetActiveTool()
                comp:DoAction("AddSetting", { filename = "Macros:/RCM Color Space Transform.setting" })
                mediaOutNode.Input:ConnectTo(comp.ActiveTool.Output)
            end
        end

        -- Step3. Change Params
        getLuminance()
        getOutputColorSpaceAndGamma()
        group_transform = comp:FindTool("RCMColorSpaceTransform")
        group_display = comp:FindTool("RCMColorSpaceDisplay")
        if group_transform then
            for _, child in ipairs(group_transform:GetChildrenList()) do
                if child:GetInput('inputColorSpace') ~= "TIMELINE_COLORSPACE" then
                    change_transform1(child)
                end
            end
        end
        if group_display then
            for _, child in ipairs(group_display:GetChildrenList()) do
                if child:GetInput('outputColorSpace') ~= "TIMELINE_COLORSPACE" then
                    change_display2(child)
                end
            end
        end
        if comp:FindTool("RCMFusionTransform1") then
            change_transform1(comp:FindTool("RCMFusionTransform1"))
        end
        if comp:FindTool("RCMFusionDisplay2") then
            change_display2(comp:FindTool("RCMFusionDisplay2"))
        end

        -- Step4. Disable Viewer LUT
        if addTransformNode and comp:GetPreviewList().LeftView.View.CurrentViewer then
            comp:GetPreviewList().LeftView.View.CurrentViewer:EnableLUT(false)
        end
        displayNode = comp:FindTool("RCMColorSpaceDisplay")
        if not displayNode then
            displayNode = comp:FindTool("RCMFusionDisplay2")
        end
        if displayNode then
            comp:GetPreviewList().RightView:ViewOn(displayNode)
            if comp:GetPreviewList().RightView.View.CurrentViewer then
                comp:GetPreviewList().RightView.View.CurrentViewer:EnableLUT(false)
            end
        end

    end
end
