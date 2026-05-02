# AgentNow × Hermes 术语表（概念对齐）

> 用途：统一团队和大模型协作时对“Agent/模板/Profile/技能/工具/会话”等概念的理解，避免同词不同义。

---

## 一句话总览

- Hermes 的“Agent”更偏**运行时系统**：Profile + Memory + Skills + Tools + Session + Cron。
- AgentNow 的 “Agent/智能体”更偏**企业产品对象**：Template（岗位定义）+ UserAgent（员工实例）+ Conversation（业务会话状态）+ Files（交付物）+ Permission/Audit（治理）。

---

## 术语对照表

| 术语 | Hermes / Hermes WebUI 里的含义 | AgentNow 里的含义 | 备注 |
|---|---|---|---|
| Agent（智能体） | 更像“持续运行的 Agent 系统/运行时”，通过 Profile、工具、技能、记忆来体现能力差异 | 更像“岗位智能体产品对象”，由模板+实例+治理+交付闭环组成 | AgentNow 不等同于 Hermes 的单个工具/技能 |
| Profile | 记忆与执行隔离边界（不同 Profile 互不共享 MEMORY/USER/历史/技能使用轨迹） | 员工侧隔离边界：一个员工固定映射一个 Hermes Profile | 这是“隔离”的关键对象 |
| Session（会话） | 一次对话/任务的运行上下文（WebUI 左侧会话列表） | `agent_conversations`：员工与某个 UserAgent 的一次业务会话 | AgentNow 的会话还需要记录业务阶段与确认点 |
| Memory | 长期记忆（USER/MEMORY 等） | 平台不存员工长期记忆；平台只存业务会话必要运行态 | 长期记忆归 Hermes；平台存治理与闭环数据 |
| Tool（工具） | 可执行动作能力（文件/终端/网络/检索等） | 平台侧“工具策略/白名单”是模板配置的一部分；真正执行通常仍发生在 Hermes 或平台的后端服务中 | “工具”强调可执行，不是 Prompt |
| Skill（技能） | 可复用方法/流程套路（提高任务质量与效率） | 第一版可后置，但平台需要预留“模板如何使用技能/工具”的配置位 | Skill 更像方法库，不是具体业务模板 |
| Template（模板） | Hermes 里可能只是若干配置/提示与工具集合（不是唯一中心概念） | `agent_templates`：岗位智能体模板，包含提示词、交互规则、知识范围、工具策略、版本等 | AgentNow 第一版以模板为主轴运营 |
| Template Version（模板版本） | 可能存在于外部管理或文件快照层 | `agent_template_versions`：模板快照与版本治理 | 用于“可运营、可回溯、可灰度” |
| UserAgent（员工智能体实例） | Hermes 更偏“用户选了哪个 Profile/模型/工具集”的运行态 | `user_agents`：模板发放到员工后的实例（绑定 profile、快照、版本） | 平台治理的关键对象 |
| Knowledge（企业知识） | 通过 MCP/RAG 等方式接入 | AgentNow 管理知识库元数据与文件；Hermes 通过共享方式使用 | “公共知识”不要写进个人记忆 |
| Structured Result（结构化结果） | 可能是工具调用/输出的中间结构 | AgentNow 在会话中缓存结构化结果（如 PPT 的 slide 列表）用于生成文件 | 用于“从对话到交付”的桥梁 |
| Generated File（交付物） | 可能是工作区文件或工具产物 | `agent_generated_files`：平台记录的生成文件（版本、状态、下载） | 交付闭环的一等对象 |
| Action（动作） | WebUI 会把用户输入、审批、澄清等作为不同事件/入口处理 | AgentNow 聊天接口存在 `action_type`，用于区分“普通消息/确认/生成等动作” | 体验稳定性的关键：动作不应伪装成用户消息 |
| Confirmation（确认点） | Hermes/ WebUI 常以审批/澄清/工具确认出现 | AgentNow 业务确认点：大纲确认/模板确认/正式生成确认等 | 业务闭环需要显式记录确认状态 |
| Observability（运行态可见性） | WebUI 强调现场感：会话、工具、工作区、状态清晰可见 | AgentNow 需要补齐：阶段、文件、错误、来源、操作链路可见 | 借鉴的是产品可见性思路，不是技术栈 |

---

## AgentNow 里的“Agent”推荐定义（写给产品与研发）

在 AgentNow 第一版里，建议把“Agent（员工看到的智能体）”定义为：

1. 一套可运营的岗位模板（Template）
2. 一条可治理的发放实例（UserAgent）
3. 一组可追踪的业务会话（Conversation，含阶段/确认/结构化结果）
4. 一条可交付的产物闭环（Generated Files，含下载与版本）
5. 一套企业平台级权限与审计（Permission/Audit）

这个定义能确保 AgentNow 的“Agent”不是简单 Prompt 包装，而是企业系统需要的“可用、可管、可追责、可迭代”的产品对象。
