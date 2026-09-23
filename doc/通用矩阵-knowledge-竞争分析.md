# Notion、Obsidian、飞书、语雀、OneNote 竞争格局深度分析报告

本地报告：http://127.0.0.1:3400/report/r_542762ae1bc54a42a8d23d1da9842bea

研究状态：needs_review；正文审校：passed。

事实覆盖 18/20；满足时效 0/20。

## 品牌 × 维度覆盖

| 品牌 | 维度 | 核验事实数 | 高可信数 | 状态 | 缺口 |
|---|---|---:|---:|---|---|
| Notion | 功能对比 | 2 | 2 | background_only | 仅有窗口外或日期不明资料，缺近30天来源 |
| Notion | 用户口碑 | 0 | 0 | missing | 缺少本品牌本维度的已核验事实 |
| Notion | 生态壁垒 | 1 | 1 | background_only | 仅有窗口外或日期不明资料，缺近30天来源 |
| Notion | 技术架构 | 2 | 2 | background_only | 仅有窗口外或日期不明资料，缺近30天来源 |
| Obsidian | 功能对比 | 2 | 2 | background_only | 仅有窗口外或日期不明资料，缺近30天来源 |
| Obsidian | 用户口碑 | 2 | 0 | background_only | 仅有窗口外或日期不明资料，缺近30天来源 |
| Obsidian | 生态壁垒 | 2 | 2 | background_only | 仅有窗口外或日期不明资料，缺近30天来源 |
| Obsidian | 技术架构 | 2 | 2 | background_only | 仅有窗口外或日期不明资料，缺近30天来源 |
| 飞书 | 功能对比 | 1 | 1 | background_only | 仅有窗口外或日期不明资料，缺近30天来源 |
| 飞书 | 用户口碑 | 2 | 0 | background_only | 仅有窗口外或日期不明资料，缺近30天来源 |
| 飞书 | 生态壁垒 | 2 | 2 | background_only | 仅有窗口外或日期不明资料，缺近30天来源 |
| 飞书 | 技术架构 | 2 | 2 | background_only | 仅有窗口外或日期不明资料，缺近30天来源 |
| 语雀 | 功能对比 | 2 | 2 | background_only | 仅有窗口外或日期不明资料，缺近30天来源 |
| 语雀 | 用户口碑 | 0 | 0 | missing | 缺少本品牌本维度的已核验事实 |
| 语雀 | 生态壁垒 | 2 | 0 | background_only | 仅有窗口外或日期不明资料，缺近30天来源 |
| 语雀 | 技术架构 | 2 | 0 | background_only | 仅有窗口外或日期不明资料，缺近30天来源 |
| OneNote | 功能对比 | 2 | 2 | background_only | 仅有窗口外或日期不明资料，缺近30天来源 |
| OneNote | 用户口碑 | 2 | 0 | background_only | 仅有窗口外或日期不明资料，缺近30天来源 |
| OneNote | 生态壁垒 | 1 | 1 | background_only | 仅有窗口外或日期不明资料，缺近30天来源 |
| OneNote | 技术架构 | 2 | 2 | background_only | 仅有窗口外或日期不明资料，缺近30天来源 |

## 研究摘要

在功能对比上，Notion 官方描述其核心为将知识集中到一个记录系统，并通过 AI 即时获取带引用的答案及用代理自动化处理繁琐工作 [来源](https://www.notion.com/)；其帮助中心还列出用 AI 撰写笔记、Q&A、AI 连接器、自定义代理及 MCP 集成等功能 [来源](https://www.notion.com/help/guides/category/ai?ref=indigox.me)。Obsidian 则强调双向链接，可在笔记间建立引用并查看来源 [来源](https://forum-zh.obsidian.md/t/topic/190)，并通过关闭安全模式后安装社区插件扩展功能 [来源](https://forum-zh.obsidian.md/t/topic/134)。飞书文档官方页面仅描述云端储存及“资料带不走，安全有保障”，未说明具体存储位置、加密方式或数据主权细节 [来源](https://www.feishu.cn/landing/brand_ad_docs)。语雀提供官方 MCP Server，允许 AI 助手通过 Model Context Protocol 读写知识库，并支持 Claude Desktop、VS Code、Cursor 等客户端接入 [来源](https://github.com/yuque/yuque-mcp-server)。OneNote 的 Office 365 REST API 文档已不再更新，相关服务现已在 Microsoft Graph 中公开 [来源](https://learn.microsoft.com/zh-cn/previous-versions/office/office-365-api/?redirectedfrom=MSDN)。

在生态壁垒与技术架构上，Notion 官方桌面应用提供 Windows Universal x64/ARM64 版本，并称其为更快、极简的体验 [来源](https://www.notion.com/desktop)。Obsidian 插件主要有 main.js、manifest.json、styles.css 三类文件，用户可从 GitHub releases 下载发行版文件并放入仓库的 .obsidian/plugins 文件夹进行手动安装 [来源](https://forum-zh.obsidian.md/t/topic/134)。飞书开放平台页面展示其集成平台可连接三方数据库，用于实现病案信息管理和催办等自动化场景，但该内容来自 2024 年 3 月发布的社区案例，未说明当前接口开放范围或技术实现细节 [来源](https://open.feishu.cn/community)。语雀提供官方 Node.js SDK 并公开 Yuque API Docs，覆盖 users、groups、repos、docs 等资源；GitHub 仓库显示 169 stars、14 forks、280 个 Used by [来源](https://github.com/yuque/sdk)。OneNote 在企业保护环境中，部分通过 Web 视图显示的功能因 Web 技术限制不受保护，用户可在没有企业保护的情况下将企业数据传输到个人位置；Mac 上的 OneNote 当前不支持 Intune [来源](https://support.microsoft.com/zh-cn/onenote/enterprise-data-protection-considerations-in-microsoft-onenote)。

基于以上已核验事实，建议个人用户选型时优先考虑：若需要 AI 问答、代理自动化及集中记录系统，可重点评估 Notion；若重视本地双向链接和插件扩展，可重点评估 Obsidian；若需要 AI 助手通过 MCP 读写知识库，可重点评估语雀；若已深度使用 Microsoft 365 生态，可重点评估 OneNote 的统一 API 接入；飞书文档目前公开资料仅说明云端储存，缺少存储位置、加密方式及数据主权细节，建议进一步核实后再做判断。 [来源](https://www.notion.com/) [来源](https://forum-zh.obsidian.md/t/topic/134) [来源](https://github.com/yuque/yuque-mcp-server) [来源](https://www.notion.com/help/guides/category/ai?ref=indigox.me) [来源](https://forum-zh.obsidian.md/t/topic/190) [来源](https://www.feishu.cn/landing/brand_ad_docs) [来源](https://learn.microsoft.com/zh-cn/previous-versions/office/office-365-api/?redirectedfrom=MSDN)


## 功能对比

在核心记录与AI能力上，Notion官方首页描述其将知识集中到一个记录系统中，并通过AI即时获取带引用的答案及用代理自动化处理繁琐工作；其帮助中心进一步列出Notion AI可撰写笔记和文档、通过Q&A获取答案、使用AI连接器访问团队知识、构建自定义代理并通过MCP集成连接工具栈 [来源](https://www.notion.com/)[来源](https://www.notion.com/help/guides/category/ai?ref=indigox.me)。Obsidian则以双向链接为特色，可在笔记中用特定语法把词变成链接并看到引用来源，适用于搭建个人知识系统 [来源](https://forum-zh.obsidian.md/t/topic/190)。建议：若优先AI问答与代理自动化，可重点考察Notion；若优先手动构建双向链接的知识网络，可重点考察Obsidian。

在文档编辑与内容形态上，飞书云文档支持多种文件类型和丰富的编辑工具，可创建、编辑和共享文档 [来源](https://www.feishu.cn/template/platform-use-manual-document-download-use-situation)。语雀文档编辑器支持以卡片形式插入表格、脑图、PlantUML、LaTeX公式等内容，并支持视频、PDF文件直接预览；其知识库基于目录编排能力，适合逻辑性要求高的结构化知识沉淀 [来源](https://www.yuque.com/about/products)。OneNote网页版支持插入表格、编辑表格文字及新增或删除行列，但进阶表格功能需使用桌面应用程序；网页版还可查看并还原页面先前版本并自动强调变更部分 [来源](https://learn.microsoft.com/zh-tw/office365/servicedescriptions/office-online-service-description/onenote-online?redirectedfrom=MSDN)。建议：若需要富媒体卡片与结构化目录，可优先考察语雀；若依赖表格进阶操作或版本还原，需确认OneNote桌面端可用性。

在技术架构与可扩展性上，Obsidian基于Electron构建，可使用HTML、CSS和JavaScript开发，并通过Node.js访问本地文件及操作系统API，支持调用Python、Go等脚本，同时可利用Obsidian API更改UI和操作逻辑 [来源](https://forum-zh.obsidian.md/t/topic/1628)。Notion、飞书、语雀、OneNote在本章给定证据中未提供对应技术架构事实，无法并列比较。建议：若需要本地脚本调用与UI定制，可重点考察Obsidian；其余产品的技术架构对比需补充证据后再作判断。


## 用户口碑

已核验的用户口碑证据集中在Obsidian、飞书和OneNote三个品牌，Notion与语雀在给定论点中无对应口碑证据，无法并列比较。Obsidian方面，有作者表示其已具备成为主力笔记管理软件的能力并完成笔记迁移[来源](https://sspai.com/post/63481)，另有作者看中其丰富插件生态，并认为喜欢VSCode的用户大概率也会喜欢Obsidian[来源](https://sspai.com/post/80802)。飞书方面，有作者表示实际体验打消了其“面向管理者开发”的顾虑，认为各客户端风格清爽、弱化管理类功能入口[来源](https://sspai.com/post/58446)，另有作者称飞书是其个人创作与增效、获取优质信息的工具之一[来源](https://sspai.com/post/73374)。

建议选型思路：若重视插件生态与类VSCode体验，可参考Obsidian相关个人评价[来源](https://sspai.com/post/80802)；若关注客户端风格清爽、弱化管理入口，可参考飞书相关个人评价[来源](https://sspai.com/post/58446)；若偏好界面简单直接、笔记结构清晰、无限画布，可参考OneNote相关个人评价[来源](https://ios.sspai.com/post/76228)。Notion与语雀因缺乏已核验口碑证据，本章不作推荐。


## 生态壁垒

在生态壁垒的开放能力上，各产品呈现不同事实。Notion 官方定价页显示，Business 及以上方案可连接 GitHub、Asana 等外部工具，Enterprise 方案提供 SCIM API 用于配置和管理用户与群组，但采集时官方文档未说明这些集成在中国大陆个人用户场景下的可用性或限制 [e_843fe42fff10460dbcd2aa4cfbc2a65d,e_9879da8c3d7c4204bc05e47038ab787f]。Obsidian 支持通过关闭安全模式后安装社区插件来扩展功能，插件安装后还需手动启用才能运行 [来源](https://forum-zh.obsidian.md/t/topic/134)。飞书开放平台提供覆盖招聘、云文档、通讯录、日历、视频会议、审批、考勤打卡、OKR、绩效、安全合规等多个业务模块的服务端 API，开发者可通过自建应用或商店应用调用 [e_2cdce1be3be64ec8a1771885242d4e19,e_25cb94162641422787f1b58338dc5881,e_8d8a7e88b8714f499a0ba0d3223cdb9e]。

语雀提供官方 MCP Server，允许 AI 助手通过 Model Context Protocol 读写语雀知识库，支持 Claude Desktop、VS Code、Cursor、Windsurf、Cline、Trae、Qoder、OpenCode 等客户端接入 [来源](https://github.com/yuque/yuque-mcp-server)；同时提供官方 Node.js SDK，并公开 Yuque API Docs，覆盖 users、groups、repos、docs 等资源，GitHub 仓库显示 169 stars、14 forks、280 个 Used by [来源](https://github.com/yuque/sdk)。OneNote 提供基于 Microsoft 云运行的 RESTful 服务 API，使用 JSON、HTML 和 OData 构建，支持通过 HTTP 请求进行编程访问，除 CRUD 外还提供光学字符识别（OCR）、全文搜索和名片提取等功能 [来源](https://learn.microsoft.com/zh-cn/previous-versions/office/office-365-api/how-to/onenote-landing)。飞书开放平台还提供事件与回调机制，开发者可订阅用户行为事件或配置回调，用于卡片交互、链接预览等需要同步响应的业务场景 [来源](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/event-subscription-guide/callback-subscription)。

建议个人用户在中国大陆选型时，若重视 AI 助手接入与知识库读写，可优先考察语雀的 MCP Server 及 SDK 生态 [来源](https://github.com/yuque/yuque-mcp-server)；若需要深度定制本地插件，可关注 Obsidian 的社区插件机制 [来源](https://forum-zh.obsidian.md/t/topic/134)；若依赖飞书办公套件，可评估其多模块 API 与事件回调能力 [e_2cdce1be3be64ec8a1771885242d4e19,e_dc250e024a36412b8c83d3b33f9f8db5]。Notion 与 OneNote 的集成与 API 能力在给定证据中未涉及中国大陆个人用户场景的可用性，建议进一步核实 [e_843fe42fff10460dbcd2aa4cfbc2a65d,e_05d2fa9a03ca4845a78f2b1f07842a0d]。


## 技术架构

从已核验事实看，五款产品在技术架构上的公开信息密度差异明显。Notion 官方桌面应用提供 Windows Universal x64/ARM64 版本，并称其为更快、极简的体验，移动端支持 iOS 和 Android [来源](https://www.notion.com/desktop)[来源](https://www.notion.com/mobile)。Obsidian 是本地软件，管理本地文件，不上传文件到服务商，用户拥有文件的绝对控制权，文件夹和结构都保存在本地，其同步功能可在任何设备上访问笔记并采用端到端加密 [来源](https://forum-zh.obsidian.md/t/topic/190)[来源](https://obsidian.md/)。飞书文档采用云端储存，官方称“资料带不走，安全有保障”，但未说明具体存储位置、加密方式或数据主权细节 [来源](https://www.feishu.cn/landing/brand_ad_docs)。

语雀官方文档称其数据安全依托蚂蚁集团多年安全技术沉淀及支付宝底层安全能力，并采用双层加密技术方案，对数据的保护贯穿数据安全生命周期，但该证据时间标签为 unknown [来源](https://www.yuque.com/about/security)。OneNote 的 Office 365 REST API 文档已不再更新，相关服务现已在 Microsoft Graph 中公开，后者作为跨 Microsoft 365 的统一 API 端点，以一个端点和单一身份验证令牌授权应用访问数据 [来源](https://learn.microsoft.com/zh-cn/previous-versions/office/office-365-api/?redirectedfrom=MSDN)。飞书开放平台页面展示其集成平台可连接三方数据库，用于病案信息管理和催办等自动化场景，但该内容来自 2024 年 3 月发布的社区案例，未说明当前接口开放范围或技术实现细节 [来源](https://open.feishu.cn/community)。


## 结论与证据边界

在功能层面，Notion 官方将核心能力描述为知识集中记录系统，并通过 AI 提供带引用的答案与代理自动化 [来源](https://www.notion.com/)；Obsidian 则强调双向链接与社区插件扩展，插件需关闭安全模式后手动安装并启用 [来源](https://forum-zh.obsidian.md/t/topic/190)[来源](https://forum-zh.obsidian.md/t/topic/134)。飞书文档官方仅说明云端储存与“资料带不走，安全有保障”，未披露存储位置或加密细节 [来源](https://www.feishu.cn/landing/brand_ad_docs)。建议个人用户若以 AI 检索与自动化优先，可先评估 Notion；若以本地知识网络与插件可控性优先，可先评估 Obsidian。

在生态与技术架构层面，语雀提供官方 MCP Server 与 Node.js SDK，并公开 Yuque API Docs，覆盖 users、groups、repos、docs 等资源，但采集页面未标注发布日期 [来源](https://github.com/yuque/yuque-mcp-server)[来源](https://github.com/yuque/sdk)。OneNote 的 Office 365 REST API 已不再更新，统一迁移至 Microsoft Graph 端点，但企业保护环境中部分 Web 视图功能不受保护，Mac 端不支持 Intune [来源](https://learn.microsoft.com/zh-cn/previous-versions/office/office-365-api/?redirectedfrom=MSDN)[来源](https://support.microsoft.com/zh-cn/onenote/enterprise-data-protection-considerations-in-microsoft-onenote)。建议需要开放 API 与 AI 客户端接入的个人用户优先核验语雀当前接口状态；依赖 Microsoft 365 统一身份与 API 的用户可评估 OneNote，但需注意企业保护边界。

证据边界方面，本次比较仅覆盖给定 Claim 所描述的功能、生态与技术架构事实，未包含价格、用户口碑量化数据或跨品牌功能优劣结论。语雀相关证据未标注发布日期，飞书集成案例来自 2024 年 3 月历史页面，其余多数证据为 background 时间标签，无法据此判断近一月最新状态 [来源](https://open.feishu.cn/community)[来源](https://github.com/yuque/yuque-mcp-server)。建议在选型前补充各产品当前版本、定价与用户反馈的一手核验。


## 附：采集与方法说明

本维度尚未取得满足来源政策和支持性核验的结论，暂不作事实判断。

## 原子事实与时效台账

### Notion · 用户口碑 · c_086a6cbbb49a4b44baabe7007f183d2b

少数派社区作者在2018年12月26日的文章中表示，Notion的块状加动态设计虽然新颖，但门槛较高，与普通编辑器差异大，例如只支持到二级标题、Markdown语法多靠快捷键实现、Block之间不允许跨段落选取，因此第一印象可能较差，“难用”往往是第一个被贴上的标签。

可信度：unverified；核验：partial；来源时间：background。

- [Notion 使用详解:来自未来的笔记协作工具 - 少数派](https://sspai.com/post/52176) · 发布日期：2018-12-26T18:12:00+08:00 · 采集：2026-09-23T06:32:21Z · community/body

### Notion · 用户口碑 · c_98a37de821c74310bda471ad922068ea

少数派社区作者在2025年8月22日的文章中称，Notion数据库的切片及自动化响应能力是其杀手锏，也是多年来让作者觉得它无可替代的重要原因之一；作者认为Obsidian近期推出的Base功能现阶段只能算更好用、更适合新手的可视化版Dataview插件，离Notion的数据库还有很大距离。

可信度：unverified；核验：partial；来源时间：background。

- [共创 | 深度使用 Notion 七年,这是我的经验、技巧与建议 - 少数派](https://sspai.com/post/102031) · 发布日期：2025-08-22T00:00:00+08:00 · 采集：2026-09-23T06:32:22Z · community/body

### 语雀 · 用户口碑 · c_46b8efec2f9a4396bfd41796ca3231ae

少数派作者在2019年12月5日的使用体验中表示，语雀作为个人写作分享平台，其每篇文章下读者可评论、作者可回复，评论和回复的码字体验与编辑文章差别不大，省去了自建博客时频繁更换评论插件的麻烦。

可信度：unverified；核验：partial；来源时间：background。

- [快速拥有自己的博客,语雀或许是不错的选择 - 少数派](https://sspai.com/post/57704) · 发布日期：2019-12-05T17:18:00+08:00 · 采集：2026-09-23T06:32:40Z · community/body

### 语雀 · 用户口碑 · c_e3ae7b9deed1433a90d3907fdb4df841

少数派作者在2019年12月5日的使用体验中提到，语雀背靠大厂且官方文档相对完善，日常碰到问题通过留言等形式会较快得到回复，并附有通过文档评论向官方反馈Gitbook导入bug的过程。

可信度：unverified；核验：partial；来源时间：background。

- [快速拥有自己的博客,语雀或许是不错的选择 - 少数派](https://sspai.com/post/57704) · 发布日期：2019-12-05T17:18:00+08:00 · 采集：2026-09-23T06:32:40Z · community/body

### 语雀 · 生态壁垒 · c_efefd48921314d66a90993e3ce59c9a9

语雀提供官方 MCP Server，允许 AI 助手通过 Model Context Protocol 读写语雀知识库；支持 Claude Desktop、VS Code、Cursor、Windsurf、Cline、Trae、Qoder、OpenCode 等客户端接入。采集时官方文档描述，未标注发布日期。

可信度：medium；核验：supported；来源时间：unknown。

- [语雀 生态壁垒官方资料](https://github.com/yuque/yuque-mcp-server) · 发布日期：未知 · 采集：2026-09-23T06:07:12Z · official/body

### 语雀 · 生态壁垒 · c_888a2d719cb54ab1a8b2e09ae5fda9e8

语雀提供官方 Node.js SDK，并公开 Yuque API Docs，覆盖 users、groups、repos、docs 等资源；GitHub 仓库显示 169 stars、14 forks、280 个 Used by。采集时官方仓库页面描述，未标注发布日期。

可信度：medium；核验：supported；来源时间：unknown。

- [语雀 生态壁垒官方资料](https://github.com/yuque/sdk) · 发布日期：未知 · 采集：2026-09-23T06:07:11Z · official/rendered

### 飞书 · 技术架构 · c_d369937ef07e4da8bfb1c27020e78bdd

飞书文档官方页面描述其文档采用云端储存，并称“资料带不走，安全有保障”。该描述为采集时官方文档描述，未说明具体存储位置、加密方式或数据主权细节。

可信度：high；核验：supported；来源时间：background。

- [飞书文档](https://www.feishu.cn/landing/brand_ad_docs) · 发布日期：2024-02-23T22:51:01+08:00 · 采集：2026-09-23T06:25:37Z · official/rendered

### 飞书 · 技术架构 · c_914aed2876364d4195a5e9623eaefd44

飞书开放平台页面展示其集成平台可连接三方数据库，用于实现病案信息管理和催办等自动化场景。该内容来自2024年3月发布的社区案例，属于采集时官方页面展示的历史案例，未说明当前接口开放范围或技术实现细节。

可信度：high；核验：supported；来源时间：background。

- [飞书开放平台](https://open.feishu.cn/community) · 发布日期：2024-07-23T01:18:33+08:00 · 采集：2026-09-23T06:01:18Z · official/rendered

### 飞书 · 用户口碑 · c_fb191bba910d48919780dcc4ba5eac2e

少数派社区作者在2020年1月14日发布的个人使用体验中表示，飞书实际体验打消了其“面向管理者开发”的顾虑，认为飞书各客户端风格清爽，弱化了管理类功能入口，并把云空间放在较高层级；该评价仅代表该作者个人样本，不能推断为中国大陆个人用户的普遍口碑。

可信度：low；核验：supported；来源时间：background。

- [把飞书融入日常学习流程:一个人的飞书也挺好 - 少数派](https://sspai.com/post/58446) · 发布日期：2020-01-14T18:13:00+08:00 · 采集：2026-09-23T06:32:32Z · community/body

### 飞书 · 用户口碑 · c_c5440c85ad9d4864b3a3b80ee60ed93e

少数派社区作者在2022年5月23日发布的个人回顾中称，飞书是其个人创作与增效、获取优质信息的工具之一，并提到成功带动2位亲戚下载飞书且获得较优秀反馈；该评价仅代表该作者及其提及的个别亲友样本，不能泛化为所有个人用户的评价。

可信度：low；核验：supported；来源时间：background。

- [我与飞书同行的日子 - 少数派](https://sspai.com/post/73374) · 发布日期：2022-05-23T09:38:00+08:00 · 采集：2026-09-23T06:32:33Z · community/body

### OneNote · 技术架构 · c_55421733095d47e8a21741185417517b

OneNote 的 Office 365 REST API 文档已不再更新，OneNote 等 Office 365 服务现已在 Microsoft Graph 中公开；Microsoft Graph 作为跨 Microsoft 365 的统一 API 端点，以一个端点和单一身份验证令牌授权应用程序访问这些服务的数据。

可信度：high；核验：supported；来源时间：background。

- [OneNote](https://learn.microsoft.com/zh-cn/previous-versions/office/office-365-api/?redirectedfrom=MSDN) · 发布日期：2017-04-18T09:55:20+08:00 · 采集：2026-09-23T06:38:58Z · official/body

### OneNote · 技术架构 · c_1d32e30f5c4040538f80b14227d86cf2

在企业保护环境（如 Windows 信息保护或 Microsoft Intune 移动设备管理）中，通过 OneNote 服务提供并在 Web 视图中显示的部分功能因 Web 技术限制不受保护，用户可在没有企业保护的情况下将企业数据传输到个人位置；Mac 上的 OneNote 当前不支持 Intune。

可信度：high；核验：supported；来源时间：background。

- [Enterprise中的数据保护Microsoft OneNote - Microsoft 支持](https://support.microsoft.com/zh-cn/onenote/enterprise-data-protection-considerations-in-microsoft-onenote) · 发布日期：2022-02-24T23:06:59+08:00 · 采集：2026-09-23T06:27:41Z · official/body

### Obsidian · 生态壁垒 · c_1feaa28269594202b3115125a7ca95b4

Obsidian 支持通过关闭安全模式后安装社区插件（Community plugins）来扩展功能，插件安装后还需手动启用才能运行。

可信度：high；核验：supported；来源时间：background。

- [玩转Obsidian的保姆级别教程：如何安装插件？ By Garrett（Wyatt）](https://forum-zh.obsidian.md/t/topic/134) · 发布日期：2021-09-12T03:33:36+00:00 · 采集：2026-09-23T05:53:17Z · official/body

### Obsidian · 生态壁垒 · c_ea8ee65882134312a7cb6d9b58dd011f

Obsidian 插件主要有 main.js、manifest.json、styles.css 三类文件，用户可从 GitHub releases 下载发行版文件并放入仓库的 .obsidian/plugins 文件夹进行手动安装。

可信度：high；核验：supported；来源时间：background。

- [玩转Obsidian的保姆级别教程：如何安装插件？ By Garrett（Wyatt）](https://forum-zh.obsidian.md/t/topic/134) · 发布日期：2021-09-12T03:33:36+00:00 · 采集：2026-09-23T05:53:17Z · official/body

### Obsidian · 功能对比 · c_e6aaa0ab09124e328d28dd93e4a4e0e4

Obsidian 支持双向链接：在笔记中用特定语法把词变成链接，可链接到对应笔记，并在被引用的笔记中看到引用来源。该功能适用于知识工作者或搭建个人知识系统的用户。

可信度：high；核验：supported；来源时间：background。

- [Obsidian是什么以及它能用来做什么](https://forum-zh.obsidian.md/t/topic/190) · 发布日期：2021-09-12T09:12:03+00:00 · 采集：2026-09-23T05:52:52Z · official/body

### Obsidian · 功能对比 · c_21bfd03deb2d4f96a99cde81a0da78f6

Obsidian 基于 Electron 构建，可使用 HTML、CSS 和 JavaScript 进行开发，并通过 Node.js 访问本地文件及操作系统 API；因此支持调用 Python、Go 等脚本，同时可利用 Obsidian API 更改 UI 和操作逻辑。

可信度：high；核验：supported；来源时间：background。

- [obsidian新手不完全指南](https://forum-zh.obsidian.md/t/topic/1628) · 发布日期：2021-11-10T12:09:57+00:00 · 采集：2026-09-23T05:59:44Z · official/body

### OneNote · 用户口碑 · c_4f89d598fa7d40aa93c180820fc8ab06

少数派作者在2022年10月17日发布的文章中表示，OneNote的码字体验停留在十多年前，存在一堆大大小小的遗留问题，但界面简单直接、笔记结构清晰、无限画布自由，使用起来没有心理压力；该作者为获得Markdown支持自行开发了OneMark插件。

可信度：low；核验：supported；来源时间：background。

- [做了个插件让 OneNote 支持 Markdown](https://ios.sspai.com/post/76228) · 发布日期：2022-10-17T08:00:00+08:00 · 采集：2026-09-23T06:32:55Z · community/body

### OneNote · 用户口碑 · c_4334a96bae5741a69cafcf0a35b9e9e9

少数派作者在2021年6月15日发布的文章中表示，OneNote不能分别设置中英文默认字体，后续也不能一键调整，只能手动逐个调整英文字体，一定程度逼死强迫症；该作者同时认为OneNote是最契合其当时状态与需求的工具。

可信度：low；核验：supported；来源时间：background。

- [2021 年,还在坚持 OneNote 的人想说.... - 少数派](https://sspai.com/post/67243) · 发布日期：2021-06-15T02:43:44+08:00 · 采集：2026-09-23T06:32:57Z · community/body

### 飞书 · 生态壁垒 · c_42bc7ad829a94ef49283cae94a73ea66

飞书开放平台提供覆盖招聘、云文档、通讯录、日历、视频会议、审批、考勤打卡、OKR、绩效、安全合规等多个业务模块的服务端 API，开发者可通过自建应用或商店应用调用。

可信度：high；核验：supported；来源时间：background。

- [开发文档-飞书开放平台](https://open.feishu.cn/document/ukTMukTMukTM/uMzM1YjLzMTN24yMzUjN/hire-v1/test/search) · 发布日期：2025-01-07T13:27:10+08:00 · 采集：2026-09-23T05:54:31Z · official/rendered
- [开发文档-飞书开放平台](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/bitable-v1/app-table-field/create) · 发布日期：2025-01-22T11:32:28+08:00 · 采集：2026-09-23T05:54:46Z · official/rendered
- [开发文档-飞书开放平台](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/contact-v3/user/field-overview) · 发布日期：2025-02-12T19:54:12+08:00 · 采集：2026-09-23T06:00:53Z · official/rendered

### 飞书 · 生态壁垒 · c_481eeb9c32514fe982740f087faa1826

飞书开放平台提供事件与回调机制，开发者可订阅用户行为事件或配置回调，用于卡片交互、链接预览等需要同步响应的业务场景。

可信度：high；核验：supported；来源时间：background。

- [开发文档-飞书开放平台](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/event-subscription-guide/callback-subscription) · 发布日期：2025-01-17T02:07:42+08:00 · 采集：2026-09-23T06:01:09Z · official/rendered

### OneNote · 功能对比 · c_7909178627a94080b64c12d895b21d25

OneNote 网页版支持插入表格、编辑表格文字，并可新增或删除行和列等基本表格结构；但将表格转换为 Excel 试算表、设置单元格网底、标题列及在表格单元格中排序数据等进阶表格功能需使用 OneNote 桌面应用程序。

可信度：high；核验：supported；来源时间：background。

- [OneNote 網頁版 - Service Descriptions  Microsoft Docs](https://learn.microsoft.com/zh-tw/office365/servicedescriptions/office-online-service-description/onenote-online?redirectedfrom=MSDN) · 发布日期：2021-09-24T02:03:37+08:00 · 采集：2026-09-23T06:27:01Z · official/body

### OneNote · 功能对比 · c_507f6496db224ca08936b35660c00c36

OneNote 网页版可以查看并还原页面的先前版本，包括作者及时间；系统会比较现在和先前版本的页面，并自动强调显示变更部分。

可信度：high；核验：supported；来源时间：background。

- [OneNote 網頁版 - Service Descriptions  Microsoft Docs](https://learn.microsoft.com/zh-tw/office365/servicedescriptions/office-online-service-description/onenote-online?redirectedfrom=MSDN) · 发布日期：2021-09-24T02:03:37+08:00 · 采集：2026-09-23T06:27:01Z · official/body

### OneNote · 生态壁垒 · c_9a936f28a2984c9b85096cc5266aee8d

OneNote 提供基于 Microsoft 云运行的 RESTful 服务 API，使用 JSON、HTML 和 OData 构建，支持通过 HTTP 请求进行编程访问；除 CRUD 外，还提供光学字符识别（OCR）、全文搜索和名片提取等功能。该描述来自采集时的官方文档，未标注近一月新增。

可信度：high；核验：supported；来源时间：background。

- [OneNote 开发](https://learn.microsoft.com/zh-cn/previous-versions/office/office-365-api/how-to/onenote-landing) · 发布日期：2022-09-22T08:00:00+08:00 · 采集：2026-09-23T05:57:38Z · official/body

### OneNote · 生态壁垒 · c_9ef02c3f86dc4011b4929c2df8c8086b

OneNote 官方文档说明，OneNote 2013 桌面客户端 API 仅用于创建未连接方案中的 Win32 桌面客户端解决方案；对于已连接方案，推荐使用 OneNote 服务 API。该描述来自采集时的官方文档，未标注近一月新增。

可信度：unverified；核验：partial；来源时间：background。

- [OneNote 开发人员参考  Microsoft Learn](https://learn.microsoft.com/zh-cn/office/client-developer/onenote/onenote-developer-reference) · 发布日期：2024-08-19T07:48:14+08:00 · 采集：2026-09-23T06:27:31Z · official/body

### Notion · 功能对比 · c_c10d08fb6260434aaf4c24e358fad250

Notion 官方首页描述其核心功能为：将知识集中到一个记录系统（system of record）中，并通过 AI 即时获取带引用的答案，以及用代理（agents）自动化处理繁琐工作。

可信度：high；核验：supported；来源时间：background。

- [Your connected workspace for wiki, docs & projects  Notion](https://www.notion.com/) · 发布日期：2025-02-11T13:32:21+08:00 · 采集：2026-09-23T05:58:43Z · official/rendered

### Notion · 功能对比 · c_d1f0ec078b0842e8920778a3216d94ad

Notion 官方帮助中心列出 Notion AI 的功能指南，包括：用 AI 撰写更高效的笔记和文档、通过 Q&A 更快获取工作内容答案、使用 AI 连接器访问更多团队知识、构建自定义代理（Custom Agent）并通过 MCP 集成连接到工具栈。

可信度：high；核验：supported；来源时间：background。

- [Notion AI](https://www.notion.com/help/guides/category/ai?ref=indigox.me) · 发布日期：2024-07-30T01:12:06+08:00 · 采集：2026-09-23T06:23:42Z · official/rendered

### 语雀 · 技术架构 · c_ac355a502e9e480088c372075d3594e6

语雀官方文档描述，其数据安全依托蚂蚁集团多年安全技术沉淀，并依托蚂蚁集团支付宝的底层安全能力，让文档安全无忧、服务稳定可靠。

可信度：medium；核验：supported；来源时间：unknown。

- [语雀 技术架构官方资料](https://www.yuque.com/about/security) · 发布日期：未知 · 采集：2026-09-23T06:07:22Z · official/rendered

### 语雀 · 技术架构 · c_0287ccc400a94508afeaf1107c5d5b46

语雀官方文档描述，其数据加密采用双层加密技术方案，对数据的保护贯穿数据安全生命周期。

可信度：medium；核验：supported；来源时间：unknown。

- [语雀 技术架构官方资料](https://www.yuque.com/about/security) · 发布日期：未知 · 采集：2026-09-23T06:07:22Z · official/rendered

### 飞书 · 功能对比 · c_b504e7e5e98d470ebb00a17fb7d097c0

飞书云文档支持多种文件类型和丰富的编辑工具，用户可以根据需要创建、编辑和共享文档。

可信度：high；核验：supported；来源时间：background。

- [详尽平台使用手册,一键下载平台使用文档,掌握平台使用情况 - 飞书官网](https://www.feishu.cn/template/platform-use-manual-document-download-use-situation) · 发布日期：2024-04-12T19:04:22+08:00 · 采集：2026-09-23T05:54:01Z · official/rendered

### 语雀 · 功能对比 · c_abe4f06c47c64a47af223fa2b9f0e692

语雀官方文档描述其文档编辑器支持以卡片形式插入表格、脑图、PlantUML、LaTeX 公式等内容，并支持视频、PDF 文件直接预览；该描述未标注发布日期，采集时官方文档如此呈现。

可信度：high；核验：supported；来源时间：unknown。

- [语雀 功能对比官方资料](https://www.yuque.com/about/products) · 发布日期：未知 · 采集：2026-09-23T06:06:42Z · official/rendered

### 语雀 · 功能对比 · c_c737ed1506ca4e03a115be16a8cf2735

语雀官方文档描述其知识库基于目录编排能力，适合逻辑性要求高的结构化知识内容沉淀，如笔记、课程、白皮书、帮助手册等；该描述未标注发布日期，采集时官方文档如此呈现。

可信度：high；核验：supported；来源时间：unknown。

- [语雀 功能对比官方资料](https://www.yuque.com/about/products) · 发布日期：未知 · 采集：2026-09-23T06:06:42Z · official/rendered

### Notion · 技术架构 · c_baf821f9607e468a81d137a706fed496

Notion 官方桌面应用提供 Windows Universal x64/ARM64 版本，并称其为更快、极简的体验；采集时官方文档描述。

可信度：high；核验：supported；来源时间：background。

- [Notion Desktop App for Mac & Windows  Notion](https://www.notion.com/desktop) · 发布日期：2024-05-07T21:54:04+08:00 · 采集：2026-09-23T05:52:49Z · official/rendered

### Notion · 技术架构 · c_473f469336b649ea88ebed75702c4a19

Notion 官方移动应用支持 iOS 和 Android，官方文档描述可在移动端无干扰工作；采集时官方文档描述。

可信度：high；核验：supported；来源时间：background。

- [Work on the go with Notion for iOS & Android  Notion](https://www.notion.com/mobile) · 发布日期：2024-04-28T23:09:44+08:00 · 采集：2026-09-23T05:59:38Z · official/rendered

### Obsidian · 用户口碑 · c_96dc2c91b16041cb92d5b945bb65fb24

少数派社区作者在2023年7月3日发布的文章中表示，使用Obsidian构建第二大脑时主要看中其丰富的插件生态，并认为喜欢VSCode的用户大概率也会喜欢Obsidian，因为两者体验相似，只是VSCode用于写代码、Obsidian用于记笔记。

可信度：low；核验：supported；来源时间：background。

- [如何「构建第二大脑」,这是我的 Obsidian 实践配方 - 少数派](https://sspai.com/post/80802) · 发布日期：2023-07-03T16:49:00+08:00 · 采集：2026-09-23T06:22:23Z · community/body

### Obsidian · 用户口碑 · c_8e7a21b0cd2a43079412d9510d1e1634

少数派社区作者在2020年11月6日发布的文章中表示，经过一段时间使用和体验，认为Obsidian已经具备成为主力笔记管理软件的能力，并陆续将自己的笔记迁移到Obsidian上进行管理。

可信度：low；核验：supported；来源时间：background。

- [玩转 Obsidian 02:基础设置篇 - 少数派](https://sspai.com/post/63481) · 发布日期：2020-11-06T14:32:00+08:00 · 采集：2026-09-23T06:22:22Z · community/body

### Obsidian · 用户口碑 · c_f4badae8be3943ba8b2b69229f1ba2ce

少数派社区作者在2023年7月3日的文章中表示，选择Obsidian主要看中其丰富的插件生态，并类比称喜欢VSCode的用户大概率也会喜欢Obsidian，区别在于VSCode用于写代码而Obsidian用于记笔记。

可信度：unverified；核验：partial；来源时间：background。

- [如何「构建第二大脑」,这是我的 Obsidian 实践配方 - 少数派](https://sspai.com/post/80802) · 发布日期：2023-07-03T16:49:00+08:00 · 采集：2026-09-23T06:22:23Z · community/body

### Obsidian · 用户口碑 · c_422484b9e75a4b989b3d2be7c6a785f1

少数派社区作者在2020年11月6日的文章中表示，经过一段时间使用和体验，认为Obsidian已经具备成为主力笔记管理软件的能力，并陆续将自己的笔记迁移到Obsidian上进行管理。

可信度：unverified；核验：partial；来源时间：background。

- [玩转 Obsidian 02:基础设置篇 - 少数派](https://sspai.com/post/63481) · 发布日期：2020-11-06T14:32:00+08:00 · 采集：2026-09-23T06:22:22Z · community/body

### Notion · 生态壁垒 · c_3860427889c844489ba7d5bca23c2b27

Notion 官方定价页显示，Business 及以上方案可连接 GitHub、Asana 等外部工具；Enterprise 方案提供 SCIM API 用于配置和管理用户与群组。采集时官方文档描述，未说明这些集成在中国大陆个人用户场景下的可用性或限制。

可信度：high；核验：supported；来源时间：background。

- [Notion Pricing Plans: Free, Plus, Business, Enterprise, & AI.](https://www.notion.com/pricing) · 发布日期：2024-02-07T20:11:46+08:00 · 采集：2026-09-23T06:34:53Z · official/body
- [Notion Pricing Plans: Free, Plus, Business, Enterprise, & AI.](https://www.notion.com/pricing) · 发布日期：2024-02-07T20:11:46+08:00 · 采集：2026-09-23T06:23:55Z · official/body

### Obsidian · 技术架构 · c_3b30c295fa1d489aae77a5be4c8cd005

Obsidian 是一个本地软件，管理本地文件，不上传文件到服务商，用户拥有文件的绝对控制权，文件夹和结构都保存在本地。

可信度：high；核验：supported；来源时间：background。

- [Obsidian是什么以及它能用来做什么](https://forum-zh.obsidian.md/t/topic/190) · 发布日期：2021-09-12T09:12:03+00:00 · 采集：2026-09-23T06:00:01Z · official/body

### Obsidian · 技术架构 · c_5a103e41a81e4b2c971f984e90593818

Obsidian 官方描述其同步功能可在任何设备上访问笔记，并采用端到端加密。

可信度：high；核验：supported；来源时间：background。

- [Obsidian - Sharpen your thinking](https://obsidian.md/) · 发布日期：2025-02-04T13:58:09+08:00 · 采集：2026-09-23T05:53:38Z · official/body

来源时间不等于产品变更时间；单条用户意见不代表群体满意度；高可信不是统计校准概率。
