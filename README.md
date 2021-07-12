[English Version](README-EN.md)

## 使用方法

### 前置条件

1. Windows：安装Python运行环境，需要安装3.6版本[Windows官网下载链接](https://www.python.org/ftp/python/3.6.8/python-3.6.8.exe)
   通过EXE安装的DaVinci Resolve可以识别，其他方法安装的不能识别。<br/>
   Mac：跳过。自带2.7版本跳过本步骤。


2. 下载对应脚本放置在指定目录，可至Release页面下载压缩包直接放置在对应目录（Windows、Mac将单独提供压缩包）<br/>
   Mac OS X: `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Comp`<br/>
   Windows: `%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Fusion\Scripts\Comp`

### 如何使用

1. 元数据解析<br/>
   在达芬奇内，打开 工作区->脚本->Comp->XiaoLi->Metadata Parser 执行日志可以在 工作区->控制台 内查看


2. RCM色彩空间匹配<br/>
   在达芬奇内，打开 工作区->脚本->Comp->XiaoLi->RCM Color Space Match 执行日志可以在 工作区->控制台 内查看<br/>
   a.视图中展示了RCM（色彩科学DaVinci YRGB Color Managed）色彩空间匹配规则<br/>
   b.支持开启元数据解析，如果未单独解析元数据，需要勾选此选项，默认勾选<br/>
   c.支持Atomos录机LOG素材Data Level批量修改为Full，同时支持所有Atomos素材Data
   Level批量修改为Full（后者的操作你最好能弄明白原理是否需要使用此功能，错误操作会导致素材还原与预期不一致）<br/>
   d.点击执行，将媒体池中所有元数据符合a中规则的片段，按照规则指定其input color space，Atomos素材按照指定规则修改其Data Level<br/>
   e.如需使用使用无视图模式：编辑源代码,修改`gui_mode = True`为`gui_mode = False`，无视图模式默认开启元数据解析以及Atomos的LOG素材Data Level修改<br/>
   f.佳能相机暂无法解析到拍摄使用的LOG格式，暂时无法自动匹配，如需批量匹配佳能素材可以使用智能媒体夹过滤佳能素材并全选设置对应输入色彩空间


3. DRX文件管理<br/>
   在达芬奇内，打开 工作区->脚本->Comp->XiaoLi->DRX Management 执行日志可以在 工作区->控制台 内查看<br/>
   a.选择需要查找DRX文件的根目录<br/>
   b.点击刷新按钮，更新目录以及递归目录所有DRX文件列表<br/>
   c.如需使用无视图模式：编辑源代码，修改`gui_mode = True`为`gui_mode = False`


4. 调色工具<br/>
   在达芬奇内，打开 工作区->脚本->Comp->XiaoLi->Color Grading Tool 执行日志可以在 工作区->控制台 内查看<br/><br/>
   I.调色拷贝工具<br/>
   a.选择拷贝至所有时间线项/同一片段的时间线项/相同摄像机类型/相同摄像机序列号/相同关键词/相同输入色彩空间/相同片段色彩/相同旗标<br/>
   b.选择是否指定调色版本，如果指定颜色版本不存在，将自动创建相应的调色版本，未指定则使用当前调色版本<br/>
   c.点击"拷贝调色"执行<br/><br/>
   II.自定义调色<br/>
   a.新增/修改选项（方案），提前设定<br/>
   b.为单个方案新增/修改预定义调色方案，需要选择DRX文件名(由DRX Management自动生成)，匹配条件（条件支持所有、摄像机类型、摄像机序列号、关键词、输入色彩空间(RCM)
   、片段色彩、旗标），多条件时匹配规则为“同时满足”，如果需要满足“或”的场景，可以使用“添加条目”来实现<br/>
   c.选择是否指定调色版本，如果指定颜色版本不存在，将自动创建相应的调色版本，未指定则使用当前调色版本<br/>
   d.点击"保存配置"进行保存配置或"自定义调色"直接执行，执行会自动保存配置<br/>


5. 字幕转化工具<br/>
   你是个聪明的娃er，要学会如何自己去摸索了！

---

## 文件说明

### 压缩包内文件

* Metadata Parser.py(无视图脚本) 借助动态链接库解析视频文件元数据


* RCM Color Space Match.py（支持有、无视图模式）<br/>
  1、使用RCM时支持通过视频文件元数据自动匹配输入色彩空间<br/>


* DRX Management（支持有、无视图模式）<br/>
  1、整理DRX文件，并按照目录拼接生成DRX文件显示名，供Color Grading Tool使用


* Color Grading Tool.py<br/>
  1、单次调色可快速复制到时间线上其他项，支持全部或按照条件复制<br/>
  2、基于DRX文件按条件匹配应用调色，支持配置持久化 （DRX文件是达芬奇能够识别的保存节点以及调色信息的文件）


* resolve-metadata.dll/resolve-metadata.so 动态链接库文件供元数据解析脚本使用，源码可参见另外一个项目

### 代码库文件

* JianYing Subtitle Conversation.py顾名思义借助外部工具将其生成的json文件转换为通用的srt文件，提供给达芬奇使用

---

## 关于源码

1. 源码基于Python3.6开发，并不适配Mac OS的2.7版本，适配版本将放在压缩包内单独提供，会出现Mac版本脚本较Windows版本少的情况，我会尽快补全，未来考虑一套代码兼容Python3和2
2. 因为M1版本的Mac安装指定版本的Python有一定的难度，达芬奇并不支持2.7以及3.6以外的版本，最新的Mac
   OS预装的Python3已经高于3.6版本，而Python2官方已经停止维护，已经不建议使用，但是版本号肯定不会更新，对于适配比较友好 ，理论上Windows也可以用2.7版本，没有特殊需求不建议使用。

### 源码贡献

* 如果你知道各种LOG格式对应的RCM的输入色彩空间，欢迎与我联系或者直接贡献源码。
* 如果你有各相机厂商的Tag标签定义或者元数据相关的白皮书什么的也欢迎联系我。

---

## 更新注意事项

### 色彩空间匹配规则

* 色彩空间匹配规则如需修改，可以修改代码文件`RCM Color Space Match.py`以下部分，按需新增即可，如果遇到更新脚本文件注意备份手动修改部分

```
color_space_match_list = [ColorSpaceMatchRule("Atomos", "CLog", "Cinema", "Canon Cinema Gamut/Canon Log"),
                          ColorSpaceMatchRule("Atomos", "CLog2", "Cinema", "Canon Cinema Gamut/Canon Log2"),
                          ColorSpaceMatchRule("Atomos", "CLog3", "Cinema", "Canon Cinema Gamut/Canon Log3"),
                          ColorSpaceMatchRule("Atomos", "F-Log", "F-Gamut", "FujiFilm F-Log"),
                          ColorSpaceMatchRule("Atomos", "V-Log", "V-Gamut", "Panasonic V-Gamut/V-Log"),
                          ColorSpaceMatchRule("Atomos", "SLog3", "SGamut3", "S-Gamut3/S-Log3"),
                          ColorSpaceMatchRule("Atomos", "SLog3", "SGamut3Cine", "S-Gamut3.Cine/S-Log3"),
                          ColorSpaceMatchRule("Atomos", "N-Log", "BT.2020", "Nikon N-Log"),
                          ColorSpaceMatchRule("Atomos", "HLG", "BT.2020", "Rec.2100 HLG"),

                          ColorSpaceMatchRule("Fujifilm", "F-log", "", "FujiFilm F-Log"),

                          ColorSpaceMatchRule("Panasonic", "V-Log", "V-Gamut", "Panasonic V-Gamut/V-Log"),

                          ColorSpaceMatchRule("Sony", "s-log2", "s-gamut", "S-Gamut/S-Log2"),
                          ColorSpaceMatchRule("Sony", "s-log3-cine", "s-gamut3-cine", "S-Gamut3.Cine/S-Log3"),
                          ColorSpaceMatchRule("Sony", "s-log3", "s-gamut3", "S-Gamut3/S-Log3"),
                          ]
```

---

## Q&A

Q: 为何没有提供中文界面？<br/>
A: emmm，本来是要做国际化的，支持中英文版本的，与达芬奇内语言设置同步，找到了对应的API`fusion:GetPrefs("Global.UserInterface.Language")`
，切换中英文无法正确获得语言设置，国际化工作暂时搁置。界面中都是简单英文单词，对各位难度应该不大。 07-02 Update:
Win系统下%appdata%目录下`%appdata%\Blackmagic Design\DaVinci Resolve\Preferences\config.user.xml`中能够读取到系统语言设置

Q: 喂！有BUG啊，如何反馈？<br/>
A: 在你能找到我的方式内联系我，或者按照规范提交ISSUE。

