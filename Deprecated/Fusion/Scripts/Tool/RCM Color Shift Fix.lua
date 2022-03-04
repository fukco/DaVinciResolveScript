--deprecated
--only support rec.709 & DaVinci Wide Gamut
project = resolve:GetProjectManager():GetCurrentProject()
color_science_mode = project:GetSetting('colorScienceMode')
color_space_timeline = project:GetSetting('colorSpaceTimeline')

if color_science_mode == 'davinciYRGBColorManagedv2' then
    mediaOutNode = comp:FindToolByID("MediaOut")
    mediaInNode = comp:FindToolByID("MediaIn")
    comp:SetActiveTool(mediaOutNode)

    local addTransformNode = true
    local addDisplayNode = true
    if mediaInNode and mediaInNode:GetData('MediaProps').MEDIA_IS_SOURCE_RES then
        addTransformNode = false
        if mediaInNode:GetData('MediaProps').MEDIA_FORMAT_TYPE == 'DNG' then
            addDisplayNode = false
        end
    end

    if mediaOutNode then
        if color_space_timeline == 'Rec.709 Gamma 2.4' then
            -- Add Color Space Transform
            if addDisplayNode and not comp:FindTool("Rec709ColorSpaceDisplay") then
                comp:DoAction("AddSetting", { filename = "Macros:/Rec709 Color Space Display.setting" })
            end

            -- Add MediaOut Display Color Space Transform
            if addTransformNode and not comp:FindTool("Rec709ColorSpaceTransform") then
                if mediaOutNode:FindMainInput(1) and mediaOutNode:FindMainInput(1):GetConnectedOutput() then
                    connectedNode = mediaOutNode:FindMainInput(1):GetConnectedOutput():GetTool()
                    while connectedNode.ParentTool do
                        connectedNode = connectedNode.ParentTool
                    end
                    comp:SetActiveTool(connectedNode)
                    comp:DoAction("AddSetting", { filename = "Macros:/Rec709 Color Space Transform.setting" })
                else
                    comp:SetActiveTool()
                    comp:DoAction("AddSetting", { filename = "Macros:/Rec709 Color Space Transform.setting" })
                    mediaOutNode.Input:ConnectTo(comp.ActiveTool.Output)
                end
            end
        elseif color_space_timeline == 'DaVinci WG' then
            -- Add Color Space Transform
            if addDisplayNode and not comp:FindTool("WideGamutColorSpaceDisplay") then
                comp:DoAction("AddSetting", { filename = "Macros:/Wide Gamut Color Space Display.setting" })
            end

            -- Add MediaOut Display Color Space Transform
            if addTransformNode and not comp:FindTool("WideGamutColorSpaceTransform") then
                if mediaOutNode:FindMainInput(1) and mediaOutNode:FindMainInput(1):GetConnectedOutput() then
                    connectedNode = mediaOutNode:FindMainInput(1):GetConnectedOutput():GetTool()
                    while connectedNode.ParentTool do
                        connectedNode = connectedNode.ParentTool
                    end
                    comp:SetActiveTool(connectedNode)
                    comp:DoAction("AddSetting", { filename = "Macros:/Wide Gamut Color Space Transform.setting" })
                else
                    comp:SetActiveTool()
                    comp:DoAction("AddSetting", { filename = "Macros:/Wide Gamut Color Space Transform.setting" })
                    mediaOutNode.Input:ConnectTo(comp.ActiveTool.Output)
                end
            end
        end
        -- Disable Viewer LUT
        if addTransformNode and comp:GetPreviewList().LeftView.View.CurrentViewer then
            comp:GetPreviewList().LeftView.View.CurrentViewer:EnableLUT(false)
        end
        if comp:FindTool("Rec709ColorSpaceDisplay") then
            comp:GetPreviewList().RightView:ViewOn(comp:FindTool("Rec709ColorSpaceDisplay"))
            if comp:GetPreviewList().RightView.View.CurrentViewer then
                comp:GetPreviewList().RightView.View.CurrentViewer:EnableLUT(false)
            end
        elseif comp:FindTool("WideGamutColorSpaceDisplay") then
            comp:GetPreviewList().RightView:ViewOn(comp:FindTool("WideGamutColorSpaceDisplay"))
            if comp:GetPreviewList().RightView.View.CurrentViewer then
                comp:GetPreviewList().RightView.View.CurrentViewer:EnableLUT(false)
            end
        end

    end
end
