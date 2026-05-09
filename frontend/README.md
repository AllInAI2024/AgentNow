# 智现 AgentNow 企业智能体平台 - 前端应用

基于 Vue 3 + TypeScript + Ant Design Vue 的企业智能体平台前端应用。

## 技术栈

| 技术 | 版本 | 说明 |
|------|------|------|
| **Vue** | 3.5.13 | 渐进式 JavaScript 框架 |
| **TypeScript** | 5.6.3 | 类型安全的 JavaScript 超集 |
| **Vite** | 6.0.3 | 下一代前端构建工具 |
| **Ant Design Vue** | 4.2.3 | 企业级 UI 组件库 |
| **Vue Router** | 4.4.5 | 官方路由管理器 |
| **Pinia** | 2.2.6 | 新一代状态管理库 |
| **Axios** | 1.7.7 | HTTP 客户端库 |

## 项目结构

```
frontend/
├── src/
│   ├── api/                    # API 接口层
│   │   ├── auth.ts            # 认证相关 API
│   │   └── http.ts            # Axios 封装
│   ├── assets/
│   │   └── styles/
│   │       └── global.css     # 全局样式
│   ├── router/
│   │   └── index.ts           # 路由配置
│   ├── stores/
│   │   └── user.ts            # 用户状态管理 (Pinia)
│   ├── types/
│   │   └── index.ts           # TypeScript 类型定义
│   ├── views/
│   │   ├── Login.vue          # 登录页面
│   │   ├── Dashboard.vue      # 工作台页面
│   │   ├── ChangePassword.vue # 首次登录修改密码页面
│   │   └── PasswordSettings.vue # 密码设置页面
│   ├── App.vue                # 根组件
│   └── main.ts                # 入口文件
├── index.html                 # HTML 模板
├── package.json               # 项目配置
├── tsconfig.json              # TypeScript 配置
├── tsconfig.node.json         # Node.js TypeScript 配置
└── vite.config.ts             # Vite 配置
```

## 快速开始

### 1. 环境准备

确保已安装：
- Node.js 18+
- npm 9+ 或 pnpm 8+

### 2. 安装依赖

```bash
cd frontend
npm install
```

### 3. 配置

开发环境已默认配置好 API 代理，无需额外配置：

- 前端端口：`5116`
- API 代理目标：`http://localhost:5117` (后端服务)

如需修改配置，编辑 `vite.config.ts`：

```typescript
server: {
  port: 5116,
  host: '0.0.0.0',
  proxy: {
    '/api': {
      target: 'http://localhost:5117',  // 后端服务地址
      changeOrigin: true,
    },
  },
},
```

### 4. 启动开发服务器

```bash
npm run dev
```

访问地址：http://localhost:5116

### 5. 构建生产版本

```bash
npm run build
```

构建产物输出到 `dist/` 目录。

### 6. 预览生产构建

```bash
npm run preview
```

### 7. 类型检查

```bash
npm run typecheck
```

## 核心功能

### 1. 用户认证

- **登录**：使用手机号和密码登录，获取 JWT Token
- **登出**：清除本地存储的 Token 和用户信息
- **Token 管理**：自动将 Token 添加到请求头
- **状态持久化**：登录状态保存在 localStorage

### 2. 路由守卫

路由配置了以下守卫逻辑：

| 路由 | 权限要求 | 说明 |
|------|----------|------|
| `/login` | 无需认证 | 已登录用户会自动跳转 |
| `/change-password` | 需要认证 + 默认密码 | 首次登录强制修改密码 |
| `/settings/password` | 需要认证 | 普通密码修改页面 |
| `/dashboard` | 需要认证 | 工作台主页面 |
| `/*` | 自动重定向 | 未匹配路由重定向到首页 |

### 3. 主题定制

项目使用 Ant Design Vue 的主题定制功能，主要定制内容：

- **主色调**：`#165DFF` (蓝色系)
- **圆角**：统一为 8px
- **阴影**：按钮添加悬浮阴影效果
- **滚动条**：自定义滚动条样式

主题配置位于 `App.vue` 的 `themeConfig` 对象中。

### 4. 状态管理

使用 Pinia 进行状态管理，当前实现了用户状态：

#### 用户 Store (`stores/user.ts`)

**状态属性**：
- `token` - JWT 访问令牌
- `userInfo` - 用户信息对象

**计算属性**：
- `isLoggedIn` - 是否已登录
- `isAdmin` - 是否为管理员
- `needsChangePassword` - 是否需要修改默认密码

**方法**：
- `login(phone, password)` - 登录
- `logout()` - 登出
- `changePassword(oldPassword, newPassword)` - 修改密码
- `restoreFromStorage()` - 从 localStorage 恢复状态

## API 接口

### 认证接口 (`api/auth.ts`)

| 方法 | 函数名 | 参数 | 返回值 | 说明 |
|------|--------|------|--------|------|
| POST | `login` | `{ phone, password }` | `LoginResult` | 用户登录 |
| POST | `changePassword` | `{ old_password, new_password }` | `APIResponse` | 修改密码 |
| GET | `getCurrentUser` | 无 | `User` | 获取当前用户信息 |
| POST | `logout` | 无 | `APIResponse` | 用户登出 |

### HTTP 客户端 (`api/http.ts`)

基于 Axios 封装，特性：
- 自动添加 JWT Token 到请求头
- 统一的响应拦截处理
- 错误状态码处理

## 类型定义

### 用户类型 (`types/index.ts`)

```typescript
interface User {
  id: number
  phone: string
  username: string
  role: 'admin' | 'user'
  is_active: boolean
  is_default_password: boolean
  hermes_profile: string | null
  created_at: string | null
  updated_at: string | null
}
```

### 其他类型

```typescript
interface LoginParams {
  phone: string
  password: string
}

interface LoginResult {
  access_token: string
  token_type: string
  user: User
}

interface ChangePasswordParams {
  old_password: string
  new_password: string
}

interface APIResponse<T = unknown> {
  code: number
  message: string
  data: T
}
```

## 页面说明

### 1. 登录页面 (`Login.vue`)

用户使用手机号和密码登录。登录成功后：
- 保存 Token 和用户信息到 localStorage
- 根据用户状态跳转：
  - 首次登录（默认密码）→ 跳转修改密码页面
  - 非首次登录 → 跳转工作台

### 2. 修改密码页面 (`ChangePassword.vue`)

首次登录强制修改密码页面：
- 验证旧密码
- 新密码强度要求（可配置）
- 两次输入密码一致校验
- 修改成功后自动更新用户状态

### 3. 密码设置页面 (`PasswordSettings.vue`)

登录后的密码修改页面，与修改密码页面功能类似，但用于用户主动修改密码。

### 4. 工作台页面 (`Dashboard.vue`)

登录后的主页面，目前为基础框架页面，后续将扩展：
- 智能体对话入口
- 对话历史列表
- 知识库管理入口
- 系统配置

## 开发指南

### 添加新页面

1. 在 `views/` 目录下创建新的 Vue 组件
2. 在 `router/index.ts` 中添加路由配置
3. 配置路由元信息（`meta`）：
   - `title` - 页面标题
   - `requiresAuth` - 是否需要认证
   - `requiresChangePassword` - 是否需要修改密码状态

### 添加新 API

1. 在 `types/index.ts` 中定义请求和响应类型
2. 在 `api/` 目录下创建新的 API 模块
3. 使用 `http` 客户端进行请求

### 状态管理扩展

如需添加新的 Store：

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useXxxStore = defineStore('xxx', () => {
  // 状态
  const data = ref()
  
  // 计算属性
  const computedData = computed(() => ...)
  
  // 方法
  const fetchData = async () => { ... }
  
  return { data, computedData, fetchData }
})
```

## 默认账号

首次启动后端服务时会自动创建默认管理员账号：

- **账号**: `13651165117`
- **默认密码**: `123456`
- **角色**: `admin`

> ⚠️ 注意：首次登录后必须修改密码！

## 相关文档

- [后端服务文档](../backend/README.md)
- [项目规格说明书](../md/SPEC.md)

## 许可证

内部使用
