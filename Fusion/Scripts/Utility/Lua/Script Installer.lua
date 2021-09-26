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

local ui = fu.UIManager
local disp = bmd.UIDispatcher(ui)
local width, height = 500, 150

win = disp:AddWindow({
    ID = 'ScriptInstaller',
    WindowTitle = 'Script Installer',
    Geometry = { 100, 100, width, height },
    Spacing = 10,

    ui:VGroup {
        ID = 'root',

        -- Add your GUI elements here:
        ui:HGroup {
            ui:Label {
                ID = 'FileLabel',
                Text = 'Zip File:',
                Weight = 0,
            },
            ui:HGap(2),
            ui:Label {
                ID = 'FileTxt',
                Text = 'Please enter a zip file path.',
                Weight = 1.5,
            },
            ui:Button {
                ID = 'FileButton',
                Text = 'Select',
                Weight = 0.25,
            },
        },

        ui:HGroup {
            ui:Label {
                Text = 'Path:',
                Weight = 0
            },
            ui:HGap(12),
            ui:ComboBox {
                ID = 'MyCombo',
                Weight = 1.5
            },
            ui:Button {
                ID = 'FolderButton',
                Text = 'Open',
                Weight = 0.25,
            },
        },

        ui:VGap(10),

        ui:Button {
            ID = 'Execute',
            Text = 'Execute',
        }
    },
})

-- The window was closed
function win.On.ScriptInstaller.Close(ev)
    disp:ExitLoop()
end

-- Add your GUI element based event functions here:
itm = win:GetItems()

-- Add the items to the ComboBox menu
itm.MyCombo:AddItem('for all users')
itm.MyCombo:AddItem('for specific user')

-- The Open File button was clicked
function win.On.FileButton.Clicked(ev)
    selectedPath = fu:RequestFile()
    itm.FileTxt.Text = selectedPath
    FilePath = selectedPath
end

function win.On.FolderButton.Clicked(ev)
    -- Add the platform specific folder slash character
    osSeparator = package.config:sub(1,1)

    local path
    if itm.MyCombo.CurrentIndex == 0 then
        path = fusion:MapPath('AllData:')
    elseif itm.MyCombo.CurrentIndex == 1 then
        path = fusion:MapPath('UserData:')
    end
    -- Convert the PathMap and extract just the foldername from the filepath
    path = path:match('(.*' .. osSeparator .. ')')

    -- Open the folder view
    if bmd.fileexists(path) then
        bmd.openfileexternal('Open', path)
    end

end

function win.On.Execute.Clicked(ev)
    if FilePath == nil then
        print("please select file path first!")
        return
    end
    local destinationPath
    if itm.MyCombo.CurrentIndex == 0 then
        destinationPath = fusion:MapPath('AllData:')
    elseif itm.MyCombo.CurrentIndex == 1 then
        destinationPath = fusion:MapPath('UserData:')
    end
    if ffi.os == "Windows" then
        script = 'Expand-Archive -Force -Path "' .. FilePath .. '" -DestinationPath "' .. destinationPath .. '"'
        local pipe = io.popen("powershell -command -", "w")

        pipe:write(script)
        pipe:close()
    elseif ffi.os == 'OSX' then
        os.execute('unzip -oq "' .. FilePath .. '" -d "' .. destinationPath .. '"')
    end
end

win:Show()
disp:RunLoop()
win:Hide()
