# Hermes WebUI 项目研究

## 一、项目定位

`hermes-webui` 是 Hermes Agent 的浏览器端界面项目，对应仓库为：

- `https://github.com/nesquena/hermes-webui`

这个项目的目标不是重新实现一套智能体系统，而是给已经存在的 Hermes Agent 提供一个轻量、可自托管、接近 CLI 体验的 Web 交互界面。

从项目 README 的表述来看，它强调几个关键词：

- 与 Hermes CLI 尽量保持 1:1 的能力对齐
- 不引入前端框架和打包构建链
- 直接复用现有 Hermes Agent、现有模型配置、现有记忆和能力
- 通过浏览器提供更易用的聊天、会话、工作区和控制中心体验

换句话说，这不是一个“独立 Agent 平台”，而是一个 Hermes 的 Web 外壳和控制台。

---

## 二、开发框架与技术栈

这个项目的技术路线非常特别，属于“极轻量、弱依赖、便于 Agent 直接改代码”的风格。

### 2.1 后端框架

后端没有使用 FastAPI、Flask、Django 之类的常见 Web 框架，而是直接使用 Python 标准库：

- `http.server`
- `BaseHTTPRequestHandler`
- `ThreadingHTTPServer`

主入口在：

- `hermes-webui/server.py`

从实现上看，`server.py` 只是一个很薄的启动壳，负责：

- 启动 HTTP 服务
- 处理认证中间逻辑
- 将 GET / POST 请求分发给 `api/routes.py`
- 启动网关监听器
- 初始化目录、权限、TLS、日志等运行环境

真正的业务逻辑基本都放在 `api/` 目录下。

### 2.2 前端框架

前端没有使用 Vue、React、Svelte，也没有使用 Vite / Webpack / Rollup。

它的前端是：

- 原生 HTML
- 原生 CSS
- 原生 JavaScript

核心静态资源目录：

- `hermes-webui/static/`

README 和 `ARCHITECTURE.md` 都明确强调：

- no build step
- no framework
- no bundler
- just Python and vanilla JS

所以它本质上是一个经典的“服务端静态文件 + 原生 JS 模块”应用。

### 2.3 运行依赖

`requirements.txt` 只有一个明确依赖：

- `pyyaml>=6.0`

这说明 WebUI 本身依赖极少，重度能力都不在这个仓库里，而是在 Hermes Agent 自己的运行环境里。

### 2.4 通信方式

项目使用了两类主要通信方式：

- 普通 HTTP 接口
- SSE（Server-Sent Events）流式事件

其中聊天流式输出、审批通知、澄清通知、网关状态推送等，都走 SSE。

这意味着它虽然没有用 WebSocket，但已经具备比较完整的“服务端持续推送”能力。

### 2.5 状态与存储方式

这个项目没有数据库，状态主要通过本地文件保存，尤其是 JSON 文件和 Hermes 自己的目录结构。

`ARCHITECTURE.md` 里给出的运行态目录大致包括：

- `sessions/`：每个会话一个 JSON 文件
- `workspaces.json`：工作区列表
- `settings.json`：用户设置
- `projects.json`：项目分组
- `last_workspace.txt`：最近工作区

也就是说，它更像一个“本地文件驱动型 Web 应用”，而不是传统数据库型 Web 系统。

---

## 三、整体架构特点

### 3.1 后端结构

后端主要分两层：

1. `server.py`
   - 启动服务
   - 统一认证检查
   - 请求入口
   - TLS / 启动配置 / watcher

2. `api/`
   - 具体业务模块
   - 路由处理
   - 会话、工作区、认证、模型、Provider、终端、上传、审批、澄清、Cron 等能力

核心模块包括：

- `api/routes.py`：主路由分发中心
- `api/auth.py`：登录与鉴权
- `api/config.py`：运行配置发现与环境控制
- `api/models.py`：会话模型与本地持久化
- `api/profiles.py`：Hermes Profile 管理
- `api/streaming.py`：聊天流式输出
- `api/workspace.py`：工作区文件访问
- `api/terminal.py`：终端能力
- `api/onboarding.py`：首次启动引导
- `api/providers.py`：模型 Provider 管理
- `api/oauth.py`：OAuth 相关支持
- `api/background.py`：后台任务
- `api/clarify.py`：澄清交互
- `api/session_ops.py`：会话操作
- `api/state_sync.py`：状态同步
- `api/updates.py`：更新检查

### 3.2 前端结构

前端模块化程度很高，虽然是原生 JS，但组织并不混乱。

核心文件包括：

- `static/index.html`：主页面骨架
- `static/style.css`：全局样式
- `static/ui.js`：全局 UI 状态和主要页面逻辑
- `static/messages.js`：消息发送、流式消息处理
- `static/sessions.js`：会话列表、搜索、切换
- `static/workspace.js`：文件浏览、预览、下载、保存
- `static/panels.js`：各种控制面板
- `static/commands.js`：斜杠命令
- `static/onboarding.js`：首次启动引导
- `static/boot.js`：应用启动和事件绑定
- `static/terminal.js`：终端前端逻辑

### 3.3 设计风格

从 `README.md`、`DESIGN.md` 和 `ARCHITECTURE.md` 看，这个项目的设计目标非常明确：

- 聊天内容优先
- 调试信息、工具调用、思考过程默认降权展示
- 工具调用不是一条条独立聊天消息，而是折叠成辅助信息
- 整体风格偏冷静、克制、开发者控制台

它更像“给开发者或高级用户使用的 Hermes 控制台”，而不是面向普通大众的对话产品。

---

## 四、项目实现了哪些功能

结合 README、架构文档、目录和接口实现，这个项目已经覆盖的能力非常多。

### 4.1 Hermes 聊天与流式会话

这是最核心的功能。

项目支持：

- 新建会话
- 会话列表
- 历史会话切换
- 流式聊天输出
- 会话消息持久化
- 会话标题自动生成
- 会话导入 / 导出
- 会话压缩
- 会话搜索

并且它不是简单聊天窗口，而是尽量对齐 Hermes CLI 的会话模型。

### 4.2 工作区文件浏览与预览

右侧 workspace 面板支持较完整的文件工作流：

- 浏览目录
- 展开 / 折叠目录
- 读取文件
- 预览文本、图片、媒体等内容
- 下载文件
- 保存文件
- 新建文件
- 删除文件
- 重命名文件
- 创建目录

这说明 WebUI 已经不仅是聊天界面，还承担了一个轻量 IDE / 文件工作台的角色。

### 4.3 会话与项目管理

从 `sessions.js`、`models.py` 和架构文档可以看出，它支持：

- 会话创建
- 会话归档
- 会话置顶
- 会话项目分组
- 会话元数据管理
- 会话导入 CLI 数据
- 跨刷新恢复状态

### 4.4 Profile 管理

Hermes 的一个核心能力是多 Profile 隔离，这个 WebUI 明显把它当成一等能力来做了。

它支持：

- 选择当前 Profile
- 读取和切换 Profile
- 按请求绑定 Profile 上下文
- 基于不同 Profile 运行同一个界面下的会话

这点和你当前 AgentNow 智能体系统里“一个员工一个 Profile”的思路非常相关。

### 4.5 Provider / 模型管理

项目支持多模型 Provider 管理，并且前端已经做了不少细节：

- 模型下拉选择
- Provider 分组
- 实时拉取 live models
- Provider 兼容性校验
- 活跃 Provider 上下文感知

说明它不是把模型配置写死，而是把 Provider 抽象成可管理对象。

### 4.6 认证与登录

虽然这是个轻量应用，但并不是裸奔：

- 支持密码认证
- 支持登录页
- 支持 Cookie 鉴权
- 支持 401 后跳转登录
- 支持同源限制与一些安全控制

项目 README 也明确提醒：

- 如果绑定到非本地地址，应该启用密码保护

### 4.7 首次引导与安装辅助

这个项目非常重视“开箱即用”：

- `bootstrap.py` 会自动发现 Hermes Agent
- 缺失时尝试官方安装
- 自动创建 Python 环境
- 安装 WebUI 依赖
- 启动服务并检查 `/health`
- 自动打开浏览器
- 进入首次 onboarding 流程

说明它把“让用户快速跑起来”作为产品的一部分，而不只是一个开发者 demo。

### 4.8 终端能力

从 `api/routes.py` 中已经能看到终端相关接口：

- terminal start
- terminal input
- terminal resize
- terminal close
- terminal output

这意味着 WebUI 里已经内嵌了终端交互能力，不只是单纯发消息给 Agent。

### 4.9 审批与澄清机制

项目里专门有：

- approval pending / SSE / respond
- clarify pending / SSE / respond

这说明 Hermes 在 WebUI 中已经支持：

- 危险操作审批
- 需要用户补充信息时的澄清
- 通过实时事件驱动前端更新

这是一个比较成熟的 Agent 产品特征，不是普通聊天框会有的能力。

### 4.10 Cron / 后台任务 / 自治运行

项目支持 Cron 和后台任务相关能力，包括：

- cron create / update / delete
- cron run / pause / resume
- cron history
- cron output
- recent status
- background task 处理

这与 Hermes 的“持续运行、离线自动执行任务”定位一致。

### 4.11 技能、记忆、MCP、扩展

从接口和目录来看，还支持：

- skills 保存 / 删除
- memory 读写
- MCP servers 列表 / 更新 / 删除
- extensions 扩展注入
- gateway watcher 与状态同步

这说明这个项目不仅是聊天 UI，而是 Hermes 整体能力的 Web 控制台。

### 4.12 上传、媒体与预览

项目支持：

- 文件上传
- 原始文件读取
- 媒体内容响应
- byte-range 流式读取
- HTML / PDF / SVG / 音视频等预览相关能力

从测试文件名也能看出，它在富媒体渲染和预览上投入不少。

---

## 五、核心实现方式总结

### 5.1 路由方式

项目没有使用框架路由，而是在 `api/routes.py` 里集中处理 GET / POST 路由。

这带来的特点是：

- 上手直接
- 调试方便
- 对 Agent 修改友好
- 但文件会越来越大，后期维护压力也会上升

从函数数量看，`api/routes.py` 已经是非常重的核心文件。

### 5.2 流式输出方式

聊天采用了“POST 启动 + GET SSE 订阅”的双接口设计：

1. 先发起聊天启动请求
2. 后端创建队列和后台线程
3. 前端再通过 SSE 订阅流式事件
4. 事件包括 token、tool、approval、done、error 等

这是一种很实用的实现方案，避免了直接使用 WebSocket 的复杂度。

### 5.3 会话存储方式

会话是本地 JSON 文件，不依赖数据库。

优点：

- 部署简单
- 本地调试方便
- 和单机自托管场景契合

缺点：

- 并发和一致性能力有限
- 会话规模大时扫描性能会下降
- 不适合企业级多用户高并发平台直接照搬

### 5.4 环境耦合方式

这个 WebUI 很依赖 Hermes 现有运行环境：

- 会复用 Hermes Agent 的 venv
- 会复用 Hermes 的 Profile
- 会复用 Hermes 的模型配置
- 会复用 Hermes 的记忆和工具系统

所以它本质上是“围绕 Hermes 生态做 UI 层封装”，不是独立服务体系。

---

## 六、这个项目的优点

### 6.1 极轻量

- 后端几乎零框架
- 前端零打包
- 依赖极少
- 启动链路简单

### 6.2 对 Agent 编码非常友好

因为没有复杂构建体系，也没有重前端框架，AI 或开发者直接在终端里读改文件会更容易。

### 6.3 功能覆盖 surprisingly 完整

虽然技术栈很轻，但能力并不弱，已经覆盖：

- 聊天
- 会话
- 文件
- 终端
- Profile
- Provider
- 审批
- 澄清
- Cron
- 记忆
- 技能
- MCP

### 6.4 非常符合 Hermes 的自托管理念

项目本身的部署和数据组织方式，都和 Hermes “自托管、长期运行、跨会话记忆”的产品理念保持一致。

---

## 七、这个项目的局限与风险

### 7.1 不适合直接照搬为企业级多用户平台后端

这个项目更偏单机、自托管、个人或小规模使用。

原因包括：

- 使用本地 JSON 文件存储
- 存在进程级全局状态
- 部分环境变量是请求期间动态写入的
- 后端基于 `ThreadingHTTPServer`，不是成熟的企业级 Web 框架

如果要把它当成企业级平台的核心服务，通常还需要重新设计：

- 用户体系
- 数据库存储
- 权限隔离
- 并发控制
- 审计体系

### 7.2 路由与核心逻辑集中度高

`api/routes.py` 很重，说明项目虽然快，但长期维护成本不低。功能继续增长后，模块边界可能越来越模糊。

### 7.3 前端虽然简单，但也意味着大型交互会更难维护

原生 JS 在中小项目里很灵活，但当交互越来越复杂时：

- 状态管理容易分散
- 组件复用能力弱
- 大规模协作成本会更高

### 7.4 更像 Hermes 专用 UI，而不是通用平台

它很多实现是围绕 Hermes 的运行模型设计的，所以复用价值主要体现在“参考架构和交互思路”，而不是直接拿来改成另一个完全不同的平台。

---

## 八、对 AgentNow 的参考价值

结合你当前的 AgentNow 项目，这个仓库最有参考价值的点主要有下面几类。

### 8.1 可以借鉴的方向

1. `Profile` 的一等公民化设计
   - Hermes WebUI 非常重视 Profile 隔离，这和 AgentNow 的“一个员工一个 Hermes Profile”思路高度一致。

2. 聊天流式链路设计
   - 用 SSE 实现流式消息、审批、澄清，思路清晰，适合参考。

3. Agent 控制台式交互
   - 会话、工作区、工具调用、审批、澄清、设置集中在一个 UI 中，这对复杂智能体产品很有借鉴意义。

4. 轻量本地优先
   - 如果只是做内部工具原型，它的“少依赖、少构建、快启动”方式很适合快速试验。

### 8.2 不建议直接照搬的部分

1. 后端技术栈
   - AgentNow 已经是企业平台方向，更适合保持当前更标准的前后端架构，而不是退回到 `http.server + JSON 文件`。

2. 数据存储模式
   - AgentNow 应继续使用数据库来管理会话、文件、模板、审计和员工数据。

3. 路由与业务的集中写法
   - `api/routes.py` 这种超大入口文件，不适合在 AgentNow 继续复制。

4. 单机式运行假设
   - Hermes WebUI 很多设计默认是单用户或轻并发，而 AgentNow 要面向企业员工体系，需要更严格的隔离和治理。

---

## 九、结论

`hermes-webui` 本质上是一个：

- 面向 Hermes Agent 的轻量 Web 控制台
- 技术上采用 Python 标准库后端 + 原生 JS 前端
- 通过 SSE 实现流式交互
- 通过本地 JSON 文件和 Hermes 目录保存状态
- 重点服务于自托管、长期运行、多 Profile、带记忆和工具能力的智能体使用场景

它不是一个通用的企业级 Agent 平台框架，但它在下面这些方面做得很成熟：

- Hermes CLI 到 WebUI 的能力映射
- Profile 与会话管理
- 工作区和文件协同
- 审批 / 澄清 / 流式事件
- Cron / 记忆 / 技能 / MCP / Provider 等 Hermes 能力的统一入口

如果站在 AgentNow 的角度看，这个项目最大的价值不是“直接拿来用”，而是：

- 研究 Hermes 官方 / 社区 Web 交互层是怎么组织的
- 学习它对 Profile、流式消息、审批、澄清、工作区等能力的产品化方式
- 为 AgentNow 后续与 Hermes 的更深层联动提供参考

---

## 十、我对它的一句话判断

如果一句话概括：

`hermes-webui` 是一个非常轻、非常工程化、非常贴近 Hermes 原生运行方式的 Web 控制台，而不是一个通用 Web 平台框架。
