comp:SetActiveTool(comp:FindToolByID("MediaOut"))
mediaOutNode = comp.ActiveTool

if mediaOutNode then
    -- Add Color Space Transform
    comp:DoAction("AddSetting", {filename = "Macros:/Wide Gamut Color Space Display.setting"})

    -- Add MediaOut Display Color Space Transform
    if mediaOutNode:FindMainInput(1) and mediaOutNode:FindMainInput(1):GetConnectedOutput() then
        connectedNode = mediaOutNode:FindMainInput(1):GetConnectedOutput():GetTool()
        comp:SetActiveTool(connectedNode)
        comp:DoAction("AddSetting", {filename = "Macros:/Wide Gamut Color Space Transform.setting"})
    else
        comp:SetActiveTool()
        comp:DoAction("AddSetting", {filename = "Macros:/Wide Gamut Color Space Transform.setting"})
        mediaOutNode.Input:ConnectTo(comp.ActiveTool.Output)
    end
end

-- Disable Viewer LUT
if comp:GetPreviewList().LeftView.View.CurrentViewer then
    comp:GetPreviewList().LeftView.View.CurrentViewer:EnableLUT(false)
end
comp:GetPreviewList().RightView:ViewOn(comp:FindTool("WideGamutColorSpaceDisplay"))
if comp:GetPreviewList().RightView.View.CurrentViewer then
    comp:GetPreviewList().RightView.View.CurrentViewer:EnableLUT(false)
end
