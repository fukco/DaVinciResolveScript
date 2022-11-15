--MIT License
--
--Copyright (c) 2021 Michael, https://github.com/fukco
--
--Permission is hereby granted, free of charge, to any person obtaining a copy
--of this software and associated documentation files (the "Software"), to deal
--in the Software without restriction, including without limitation the rights
--to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
--copies of the Software, and to permit persons to whom the Software is
--furnished to do so, subject to the following conditions:
--
--The above copyright notice and this permission notice shall be included in all
--copies or substantial portions of the Software.
--
--THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
--IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
--FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
--AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
--LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
--OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
--SOFTWARE.

if ffi.os == "Windows" then
    --如果修改过安装路径，请修改此处路径，修改为
    --jianyingProjectLocation = “C:/your/path”
    --bcutProjectLocation = “C:/your/path”
    --注意windows拷贝路径请将右斜杠(\)修改为左斜杠(/)
    jianyingProjectLocation = os.getenv("userprofile") .. "/AppData/Local/JianyingPro/User Data/Projects/com.lveditor.draft"
    bcutProjectLocation = os.getenv("userprofile") .. "/Documents/MYVideoProject"
elseif ffi.os == "OSX" then
    jianyingProjectLocation = os.getenv("HOME") .. "/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
end

json = require "json"

local lib
if ffi.os == "Windows" then
    lib = ffi.load(fusion:MapPath('LuaModules:/subtitle-tool.dll'))
elseif ffi.os == "OSX" then
    if ffi.arch == "x64" then
        lib = ffi.load(fusion:MapPath('LuaModules:/subtitle-tool-amd64.dylib'))
    elseif ffi.arch == "arm64" then
        lib = ffi.load(fusion:MapPath('LuaModules:/subtitle-tool-arm64.dylib'))
    end
end

ffi.cdef [[
    extern __declspec(dllexport) _Bool JExportByProjectName(char* name, char* basePath, char* outputPath);
    extern __declspec(dllexport) _Bool BExportById(char* name, char* id, char* basePath, char* outputPath);
]]

local jianyingFile = io.open(jianyingProjectLocation .. "/root_meta_info.json", "r")
local contents = ""
local jianyingTable = {}
local bcutTable = {}
if jianyingFile then
    contents = jianyingFile:read("*a")
    jianyingTable = json.decode(contents);
    io.close(jianyingFile)
end

if bcutProjectLocation then
    local bcutFile = io.open(bcutProjectLocation .. "/draftInfo.json", "r")
    if bcutFile then
        contents = bcutFile:read("*a")
        bcutTable = json.decode(contents);
        io.close(bcutFile)
    end
end

local ui = fu.UIManager
local disp = bmd.UIDispatcher(ui)

resolve = Resolve()
projectManager = resolve:GetProjectManager()
project = projectManager:GetCurrentProject()
mediaPool = project:GetMediaPool()

-- some element IDs
tabsID = "MyTabs"
stackID = "MyStack"

function MainWindow()
    win = disp:AddWindow({
        ID = 'SubtitleTool',
        WindowTitle = '字幕工具By小黎',
        Spacing = 0,

        ui:VGroup {
            -- Add your GUI elements here:
            ui:TabBar {
                CurrentIndex = 0,
                ID = tabsID,
                Weight = 0
            },

            ui.VGap(2),

            ui:Stack {
                Weight = 10,
                ID = stackID,
                ui:VGroup {
                    Weight = 0,
                    ui:VGroup {
                        Weight = 0,
                        ID = "JList"
                    },
                },

                ui:VGroup {
                    Weight = 0,
                    ui:VGroup {
                        Weight = 0,
                        ID = "BList"
                    },
                }
            }
        }
    })

    -- Add your GUI element based event functions here:
    itm = win:GetItems()

    itm[stackID].CurrentIndex = 0

    -- Add the items to the ComboBox menu
    itm[tabsID]:AddTab('剪映')
    itm[tabsID]:AddTab('必剪')

    if jianyingTable.all_draft_store then
        for i = 1, #jianyingTable.all_draft_store do
            local draft = jianyingTable.all_draft_store[#jianyingTable.all_draft_store + 1 - i]
            local min = math.floor(draft.tm_duration / 1000000 / 60)
            local sec = math.ceil(draft.tm_duration % (1000000 * 60) / 1000000)
            local date = os.date("%y/%m/%d %X", draft.tm_draft_modified / 1000000)
            local nameId = string.format("jianying_%s", i)
            local buttonId = string.format("j_export_%s", i)
            child = ui:HGroup {
                ui:TextEdit {
                    Weight = 0,
                    ReadOnly = true,
                    HTML = string.format("<img width=128 height=72 src='%s'", draft.draft_cover),
                    FixedSize = { 138, 82 }
                },
                ui:VGroup {
                    ui:Label { Text = draft.draft_name, ID = nameId },
                    ui:Label { Text = string.format("时长%s:%s", min, sec) },
                    ui:Label { Text = string.format("更新于%s", date) },
                },
                ui:VGroup {
                    ui:HGap(10),
                    ui:Button {
                        Weight = 0,
                        ID = buttonId,
                        Text = "导出SRT"
                    },
                    ui:HGap(10),
                },
            }
            itm["JList"]:AddChild(child)

            function OnJianyingButtonClicked(ev)
                itm = win:GetItems()
                local selectedPath = fu:RequestDir()
                if not selectedPath then
                    return
                end
                local name = itm[nameId].Text
                local c_name = ffi.new("char[?]", #name)
                ffi.copy(c_name, name)
                local c_projectPath = ffi.new("char[?]", #jianyingProjectLocation)
                ffi.copy(c_projectPath, jianyingProjectLocation)
                local c_selectPath = ffi.new("char[?]", #selectedPath)
                ffi.copy(c_selectPath, selectedPath)
                local res = lib.JExportByProjectName(c_name, c_projectPath, c_selectPath)
                GotoSRTFolder()
                mediaPool:ImportMedia({ selectedPath .. "/" .. name })
                AlertWindow(res)
            end

            win.On[buttonId].Clicked = OnJianyingButtonClicked
        end
    else
        itm["JList"]:AddChild(ui:Label { Text = "您的剪映路径设置有误！" })
    end

    if ffi.os == "Windows" then
        if bcutTable.draftInfos then
            table.sort(bcutTable.draftInfos, function(a, b)
                return tonumber(a.modifyTime) < tonumber(b.modifyTime)
            end)

            for i, v in ipairs(bcutTable.draftInfos) do
                local min = math.floor(v.duration / 1000000 / 60)
                local sec = math.ceil(v.duration % (1000000 * 60) / 1000000)
                local date = os.date("%y/%m/%d %X", v.modifyTime / 1000)
                local nameId = string.format("bcut_%s", i)
                local idId = string.format("bcutId_%s", i)
                local buttonId = string.format("b_export_%s", i)
                child = ui:HGroup {
                    ui:TextEdit {
                        Weight = 0,
                        ReadOnly = true,
                        HTML = string.format("<img width=128 height=72 src='%s'", bcutProjectLocation .. "/" .. v.id .. "/cover.jpg"),
                        FixedSize = { 138, 82 }
                    },
                    ui:VGroup {
                        ui:Label { Text = v.name, ID = nameId },
                        ui:Label { Text = v.id, ID = idId, Hidden = true },
                        ui:Label { Text = string.format("时长%s:%s", min, sec) },
                        ui:Label { Text = string.format("更新于%s", date) },
                    },
                    ui:VGroup {
                        ui:HGap(10),
                        ui:Button {
                            Weight = 0,
                            ID = buttonId,
                            Text = "导出SRT"
                        },
                        ui:HGap(10),
                    },
                }
                itm["BList"]:AddChild(child)

                function OnBcutButtonClicked(ev)
                    itm = win:GetItems()
                    local selectedPath = fu:RequestDir()
                    if not selectedPath then
                        return
                    end
                    local name = itm[nameId].Text
                    local c_name = ffi.new("char[?]", #name)
                    ffi.copy(c_name, name)
                    local id = itm[idId].Text
                    local c_id = ffi.new("char[?]", #id)
                    ffi.copy(c_id, id)
                    local c_projectPath = ffi.new("char[?]", #bcutProjectLocation)
                    ffi.copy(c_projectPath, bcutProjectLocation)
                    local c_selectPath = ffi.new("char[?]", #selectedPath)
                    ffi.copy(c_selectPath, selectedPath)
                    local res = lib.BExportById(c_name, c_id, c_projectPath, c_selectPath)
                    AlertWindow(res)
                end

                win.On[buttonId].Clicked = OnBcutButtonClicked

            end
        else
            itm["BList"]:AddChild(ui:Label { Text = "您的必剪路径设置有误!" })
        end
    else
        itm["BList"]:AddChild(ui:Label { Text = "必剪暂不支持您的操作系统" })
    end

    win:Resize({ 600, 600 });
    win:RecalcLayout();

    -- The window was closed
    function win.On.SubtitleTool.Close(ev)
        disp:ExitLoop()
    end

    function win.On.MyTabs.CurrentChanged(ev)
        itm[stackID].CurrentIndex = ev["Index"]
    end

    win:Show()
    disp:RunLoop()
    win:Hide()
    return win, win:GetItems()
end

function GotoSRTFolder()
    for _, v in ipairs(rootFolder:GetSubFolderList()) do
        if 'Subtitles' == v:GetName() then
            mediaPool:SetCurrentFolder(v)
            return
        end
    end
    SRTFolder = mediaPool:AddSubFolder(rootFolder, 'Subtitles')
end

function AlertWindow(success)
    local alertWin = disp:AddWindow({
        ID = "AlertWin",
        WindowTitle = '通知',
        WindowFlags = { Window = true, WindowStaysOnTopHint = true, },

        ui:VGroup {
            ui:Label {
                ID = 'NotificationId',
                Alignment = {
                    AlignHCenter = true,
                    AlignVCenter = true,
                },
            }
        },
    })

    -- Add your GUI element based event functions here:
    local alertItm = alertWin:GetItems()

    if success then
        alertItm.NotificationId["Text"] = "<font color='#39CA41'>导出成功！</font>"
    else
        alertItm.NotificationId["Text"] = "<font color='#922626'>导出失败！</font>"
    end

    alertWin:Resize({ 200, 100 });
    alertWin:RecalcLayout();

    -- The window was closed
    function alertWin.On.AlertWin.Close(ev)
        disp:ExitLoop()
    end

    alertWin:Show()
    disp:RunLoop()
    alertWin:Hide()

    return alertWin, alertWin:GetItems()
end

MainWindow()