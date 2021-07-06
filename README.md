[English Version](README-EN.md)
## 使用方法
### 前置条件
1. Windows：安装Python运行环境，需要安装3.6版本[Windows官网下载链接](https://www.python.org/ftp/python/3.6.8/python-3.6.8.exe) 通过EXE安装的DaVinci Resolve可以识别，其他方法安装的不能识别。<br/>
   Mac：跳过。自带2.7版本跳过本步骤。
2. 下载对应脚本放置在指定目录，可至Release页面下载压缩包直接放置在对应目录（Windows、Mac将单独提供压缩包）<br/>
  Mac OS X: `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Comp`<br/>
  Windows: `%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Fusion\Scripts\Comp`
   
### 如何使用
1. 元数据解析<br/>
在达芬奇内，打开 工作区->脚本->Comp->XiaoLi->Metadata Parser 执行日志可以在 工作区->控制台 内查看


2. 快速调色工具<br/>
在达芬奇内，打开 工作区->脚本->Comp->XiaoLi->Color Grading Tool 执行日志可以在 工作区->控制台 内查看<br/>
  a.选择是否开启RCM颜色空间匹配（色彩科学DaVinci YRGB Color Managed），选择是否开启自定义调色<br/>
  b.新增/修改选项（方案），功能类似于预设<br/>
  c.为单个方案新增/修改预定义调色方案，需要选择DRX文件名(由DRX Management自动生成)，匹配条件（条件支持所有、摄像机类型、摄像机序列号、关键词、输入色彩空间(RCM)、片段色彩、旗标）<br/>
  d.选择是否指定调色版本，如果指定颜色版本不存在，将自动创建相应的调色版本，未指定则使用当前调色版本<br/>
  f.点击Save Config进行保存配置或Execute直接执行，执行会自动保存配置<br/>
  g.如需使用使用无视图模式：编辑源代码,修改`gui_mode = True`为`gui_mode = False`
   

3. 调色拷贝工具<br/>
在达芬奇内，打开 工作区->脚本->Comp->XiaoLi->Color Grading Copy Tool 执行日志可以在 工作区->控制台 内查看<br/>
  a.打开后会自动显示当前选择的时间线项，如未显示则需要在调色界面或者编辑界面中选中对应时间线项,再点击刷新按钮<br/>
  b.选择拷贝至所有时间线项/同一片段的时间线项/相同摄像机类型/相同摄像机序列号/相同关键词/相同输入色彩空间/相同片段色彩/相同旗标<br/>
  c.选择是否指定调色版本，如果指定颜色版本不存在，将自动创建相应的调色版本，未指定则使用当前调色版本<br/>
  d.点击Execute执行
  d.如需使用无视图模式：编辑源代码，修改`gui_mode = True`为`gui_mode = False`，以及`default_option`,`default_assign_color_version`,`default_color_version_name`三个字段对应值


4. DRX文件管理<br/>
在达芬奇内，打开 工作区->脚本->Comp->XiaoLi->DRX Management 执行日志可以在 工作区->控制台 内查看<br/>
  a.选择需要查找DRX文件的根目录<br/>
  b.点击刷新按钮，更新目录以及递归目录所有DRX文件列表<br/>
  c.如需使用无视图模式：编辑源代码，修改`gui_mode = True`为`gui_mode = False`

5. 字幕转化工具<br/>
你是个聪明的娃er，要学会如何自己去摸索了！

---
## 文件说明
### 压缩包内文件
* Color Grading Tool.py（支持有、无视图模式）<br/>
  1、使用RCM时支持通过视频文件元数据自动匹配输入色彩空间<br/>
  2、任意模式下基于DRX文件按条件匹配应用调色，支持配置持久化 （DRX文件是达芬奇能够识别的保存节点以及调色信息的文件） 
  

* Color Grading Copy Tool.py（支持有、无视图模式）<br/>
  1、单次调色可快速复制到时间线上其他项，支持全部或按照条件复制<br/>


* Metadata Parser.py(无视图脚本) 借助动态链接库解析视频文件元数据


* resolve-metadata.dll/resolve-metadata.so 动态链接库文件，源码可参见另外一个项目

### 代码库文件
* _config-grading-config.json "Color Grading Tool.py"对应的默认配置文件，更新色彩空间匹配规则时，可将对应的配置项拷贝到自己的配置文件中
* JianYing Subtitle Conversation.py顾名思义借助外部工具将其生成的json文件转换为通用的srt文件，提供给达芬奇使用

---
## 关于源码
1. 源码基于Python3.6开发，并不适配Mac OS的2.7版本，适配版本将放在压缩包内单独提供，会出现Mac版本脚本较Windows版本少的情况，我会尽快补全，未来考虑一套代码兼容Python3和2
2. 因为M1版本的Mac安装指定版本的Python有一定的难度，达芬奇并不支持2.7以及3.6以外的版本，最新的Mac OS预装的Python3已经高于3.6版本，而Python2官方已经停止维护，已经不建议使用，但是版本号肯定不会更新，对于适配比较友好
，理论上Windows也可以用2.7版本，没有特殊需求不建议使用。
   
### 源码贡献
* 如果你知道各种LOG格式对应的RCM的输入色彩空间，欢迎与我联系或者直接贡献源码。
* 如果你有各相机厂商的Tag标签定义或者元数据相关的白皮书什么的也欢迎联系我。

---
### 色彩空间匹配规则手动更新方法
色彩空间匹配可将下面这段中的rules对应的数据拷贝至你自己的conf.json文件中，注意拷贝前后需要符合JSON文件格式
```json
{
  "Color Space Match Rules": {
    "enabled": true,
    "_comments": "this is for RCM only!",
    "rules": [
      {
        "manufacturer": "Atomos",
        "details": [
          {
            "Gamma Notes": "CLog",
            "Color Space Notes": "Cinema",
            "Input Color Space": "Canon Cinema Gamut/Canon Log"
          },
          {
            "Gamma Notes": "CLog2",
            "Color Space Notes": "Cinema",
            "Input Color Space": "Canon Cinema Gamut/Canon Log2"
          },
          {
            "Gamma Notes": "CLog3",
            "Color Space Notes": "Cinema",
            "Input Color Space": "Canon Cinema Gamut/Canon Log3"
          },
          {
            "Gamma Notes": "F-Log",
            "Color Space Notes": "F-Gamut",
            "Input Color Space": "FujiFilm F-Log"
          },
          {
            "Gamma Notes": "V-Log",
            "Color Space Notes": "V-Gamut",
            "Input Color Space": "Panasonic V-Gamut/V-Log"
          },
          {
            "Gamma Notes": "SLog3",
            "Color Space Notes": "SGamut3.cine",
            "Input Color Space": "S-Gamut3.Cine/S-Log3"
          },
          {
            "Gamma Notes": "SLog3",
            "Color Space Notes": "SGamut3",
            "Input Color Space": "S-Gamut3/S-Log3"
          },
          {
            "Gamma Notes": "N-Log",
            "Color Space Notes": "BT.2020",
            "Input Color Space": "Nikon N-Log"
          },
          {
            "Gamma Notes": "HLG",
            "Color Space Notes": "BT.2020",
            "Input Color Space": "Rec.2100 HLG"
          }
        ]
      },
      {
        "manufacturer": "Fujifilm",
        "details": [
          {
            "Gamma Notes": "F-log",
            "Color Space Notes": "",
            "Input Color Space": "FujiFilm F-Log"
          }
        ]
      },
      {
        "manufacturer": "Panasonic",
        "details": [
          {
            "Gamma Notes": "V-Log",
            "Color Space Notes": "V-Gamut",
            "Input Color Space": "Panasonic V-Gamut/V-Log"
          }
        ]
      },
      {
        "manufacturer": "Sony",
        "details": [
          {
            "Gamma Notes": "s-log3-cine",
            "Color Space Notes": "s-gamut3-cine",
            "Input Color Space": "S-Gamut3.Cine/S-Log3"
          },
          {
            "Gamma Notes": "s-log3",
            "Color Space Notes": "s-gamut3",
            "Input Color Space": "S-Gamut3/S-Log3"
          }
        ]
      }
    ]
  }
}
```

---
## Q&A
Q: 为何没有提供中文界面？<br/>
A: emmm，本来是要做国际化的，支持中英文版本的，与达芬奇内语言设置同步，找到了对应的API`fusion:GetPrefs("Global.UserInterface.Language")`，切换中英文无法正确获得语言设置，国际化工作暂时搁置。界面中都是简单英文单词，对各位难度应该不大。
07-02 Update:Win系统下%appdata%目录下`%appdata%\Blackmagic Design\DaVinci Resolve\Preferences\config.user.xml`中能够读取到系统语言设置


Q: 喂！有BUG啊，如何反馈？<br/>
A: 在你能找到我的方式内联系我，或者按照规范提交ISSUE。

