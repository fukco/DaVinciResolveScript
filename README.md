[![GitHub release](https://img.shields.io/github/release/fukco/DaVinciResolveScript?&style=flat-square)](https://github.com/fukco/DaVinciResolveScript/releases/latest)
[![Paypal Donate](https://img.shields.io/badge/donate-paypal-00457c.svg?logo=paypal&style=flat-square)](https://www.paypal.com/donate/?business=9BGFEVJPEFZAQ&no_recurring=0&currency_code=USD&source=qr)
[![Bilibili](https://img.shields.io/badge/dynamic/json?label=Bilibili&query=%24.data.follower&url=https%3A%2F%2Fapi.bilibili.com%2Fx%2Frelation%2Fstat%3Fvmid%3D26755389&style=social&logo=Bilibili)](https://space.bilibili.com/26755389)
[![Youtube](https://img.shields.io/youtube/channel/subscribers/UCb7NsYnLmtPTn-yddNTcVKA?style=social&label=Youtube)](https://www.youtube.com/@geek-lee)

[English Version](README-EN.md)

## 支持范围
### 达芬奇版本
17+
Sony MILC使用了Multi Merge节点，需要18.5+版本
从达芬奇19开始，BMD修复了开启RCM，色差偏移的bug，所以移除了相关修复脚本，如果需要请从Deprecated目录手动下载并放置指定目录

### 操作系统
* Windows
* Mac OS(Intel/Apple Silicon均可)

## 使用方法

### 安装
   ![脚本安装](assets/脚本安装界面.png)
1. 将下载好的`Script Installer.lua`拖拽到Fusion界面中释放会出现UI界面或者复制粘贴代码到控制台运行<br/>
2. 文件选择框选择下载的压缩包<br/>
3. 下拉框选择`for all users` Or `for specfic user`<br/>
4. 点击执行
5. 安装压缩包后，后续可以通过点击【工作区/脚本/Script Installer】执行

### 使用

1. 元数据解析<br/>
   在达芬奇内，打开 工作区->脚本->Metadata Parser 执行日志可以在 工作区->控制台 内查看


2. RCM色彩空间匹配<br/>
   在达芬奇内，打开 工作区->脚本->RCM Color Space Match 执行日志可以在 工作区->控制台 内查看<br/>
   ![脚本安装](assets/RCM色彩匹配.png)<br/>
   a.视图中展示了RCM（色彩科学DaVinci YRGB Color Managed）色彩空间匹配规则<br/>
   b.支持开启元数据解析，如果未单独解析元数据，需要勾选此选项，默认勾选<br/>
   c.支持Atomos录机LOG素材以及Legal素材Data Level批量修改为Full，同时支持所有Atomos素材Data
   Level批量修改为Full（后者的操作你最好能弄明白原理是否需要使用此功能，错误操作会导致素材还原与预期不一致）<br/>
   d.点击执行，将媒体池中所有元数据符合a中规则的片段，按照规则指定其input color space，Atomos素材按照指定规则修改其Data Level<br/>
   e.如需使用使用无视图模式：编辑源代码,修改`gui_mode = 1`为`gui_mode = 0`，无视图模式默认开启元数据解析以及Atomos的LOG素材和Legal素材Data Level修改<br/>
   f.佳能相机暂无法解析到拍摄使用的LOG格式，暂时无法自动匹配，如需批量匹配佳能素材可以使用智能媒体夹过滤佳能素材并全选设置对应输入色彩空间


3. ~~RCM下色彩偏移修复~~【达芬奇19开始移除】<br/>
   Fusion页面任意节点右键脚本->RCM Color Shift Fix
   18.1版本开始，Text+在RCM下做了一定的修改，请更新脚本到0.9.0版本


4. ~~DRX文件管理~~【暂未正式推出】<br/>
   在达芬奇内，打开 工作区->脚本->DRX Management 执行日志可以在 工作区->控制台 内查看<br/>
   a.选择需要查找DRX文件的根目录<br/>
   b.点击刷新按钮，更新目录以及递归目录所有DRX文件列表<br/>
   c.如需使用无视图模式：编辑源代码，修改`gui_mode = 1`为`gui_mode = 0`


5. ~~调色工具~~【暂未正式推出】<br/>
   在达芬奇内，打开 工作区->脚本->Color Grading Tool 执行日志可以在 工作区->控制台 内查看<br/><br/>
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


## 文件说明
![目录结构](assets/压缩包目录结构.png)
压缩包分为：全量版本以及仅Lua版本，前者脚本更全但是需要额外安装Python环境，后者无需安装Python环境使用达芬奇内置的Lua解释器，M1芯片MAC暂时不支持Python3.6，但是相对全量版本，脚本没有那么全面，如有需要我会尽力补全Lua版本脚本

### 脚本说明
<table>
  <tr>
    <th>文件夹</th>
    <th>文件名</th>
    <th>作用</th>
  </tr>
  <tr>
    <td rowspan="1">Scripts/Comp</td>
    <td>Sony MILC.lua</td>
    <td>索尼微单参数界面</td>
  </tr>
  <tr>
    <td rowspan="3">Scripts/Utility</td>
    <td>Metadata Parser.lua</td>
    <td>元数据解析</td>
  </tr>
  <tr>
    <td>RCM Color Space Match.lua</td>
    <td>RCM色彩空间匹配</td>
  </tr>
  <tr>
    <td>Script Installer.lua</td>
    <td>脚本安装助手</td>
  </tr>
</table>

达芬奇19移除的脚本
<table>
  <tr>
    <th>文件夹</th>
    <th>文件名</th>
    <th>作用</th>
  </tr>
  <tr>
    <td rowspan="2">Config</td>
    <td>RCMColorSpaceMatchHotkey.fu</td>
    <td>Fusion快捷键注册，快速调色启动</td>
  </tr>
  <tr>
    <td>RCMFusionDisplayViewOn.fu</td>
    <td>Fusion中RCM色彩修正显示节点</td>
  </tr>
  <tr>
    <td rowspan="2">Macros</td>
    <td>RCM Color Space Display.setting</td>
    <td>RCM Fusion颜色偏移显示修正</td>
  </tr>
  <tr>
    <td>RCM Color Space Transform.setting</td>
    <td>RCM Fusion颜色偏移输出修正</td>
  </tr>
  <tr>
    <td>Scripts/Tool</td>
    <td>RCM Color Shift Fix.lua</td>
    <td>RCM色彩修正Tool脚本</td>
  </tr>
</table>

附加的Python脚本
<table>
  <tr>
    <th>文件夹</th>
    <th>文件名</th>
    <th>作用</th>
  </tr>
  <tr>
    <td rowspan="4">Scripts/Utility</td>
    <td>Metadata parser.py</td>
    <td>元数据解析</td>
  </tr>
  <tr>
    <td>RCM Color Space Match.py</td>
    <td>RCM色彩空间匹配</td>
  </tr>
  <tr>
    <td>DRX Management.py</td>
    <td>DRX管理</td>
  </tr>
  <tr>
    <td>Color Grading Tool.py</td>
    <td>调色工具</td>
  </tr>
</table>

补充说明
* Metadata Parser(无视图脚本) 借助动态链接库解析视频文件元数据


* RCM Color Space Match（支持有、无视图模式）<br/>
  1、使用RCM时支持通过视频文件元数据自动匹配输入色彩空间<br/>


* DRX Management（支持有、无视图模式）<br/>
  1、整理DRX文件，并按照目录拼接生成DRX文件显示名，供Color Grading Tool使用


* Color Grading Tool<br/>
  1、单次调色可快速复制到时间线上其他项，支持全部或按照条件复制<br/>
  2、基于DRX文件按条件匹配应用调色，支持配置持久化 （DRX文件是达芬奇能够识别的保存节点以及调色信息的文件）


* .dll .dylib后缀文件为动态链接库，源码使用Golang编写，参见另外一个项目

## 关于源码

1. ~~源码基于Python3.6开发，并不适配Mac OS自带的2.7版本，特别标注的除外~~
2. ~~Mac OS当前版本自带2.7以及高于3.6版本的Python，非M1芯片Mac建议安装Python3.6~~

### 源码贡献

* 如果你知道各种LOG格式对应的RCM的输入色彩空间，欢迎与我联系或者直接贡献源码。
* 如果你有各相机厂商的Tag标签定义或者元数据相关的白皮书什么的也欢迎联系我。

## 更新注意事项

### 色彩空间匹配规则

* 色彩空间匹配规则如果需要添加，可以与我联系，或者自己摸索代码依葫芦画瓢即可。

## Q&A

**Q: Apple Silicon支持情况？**<br/>
支持

**Q: 喂！有BUG啊，如何反馈？**<br/>
A: 在你能找到我的方式内联系我，或者按照规范提交ISSUE。

