# 智现 AgentNow 企业智能体平台 - 后端服务

基于 Python 3.11 + FastAPI 的企业智能体平台后端服务。

## 技术栈

- **语言**: Python 3.11+
- **框架**: FastAPI
- **数据库**: MySQL 8.0+
- **ORM**: SQLAlchemy 2.0+
- **认证**: JWT (python-jose)
- **密码加密**: bcrypt
- **依赖管理**: UV

## 项目结构

```
backend/
├── app/
│   ├── __init__.py          # 应用初始化
│   ├── config.py            # 配置管理
│   ├── main.py              # FastAPI 入口文件
│   ├── models/              # 数据模型
│   │   ├── __init__.py
│   │   └── user.py         # 用户模型
│   ├── routers/             # API 路由
│   │   ├── __init__.py
│   │   └── auth.py         # 认证相关 API
│   ├── schemas/             # Pydantic 数据模型
│   │   ├── __init__.py
│   │   └── user.py
│   └── services/            # 业务逻辑
│       ├── __init__.py
│       └── auth_service.py   # 认证服务
├── data/
│   └── database.sql          # 数据库初始化脚本
├── .env.example             # 环境变量示例
├── pyproject.toml            # 项目配置
└── README.md                 # 本文档
```

## 快速开始

### 1. 环境准备

确保已安装：
- Python 3.11+
- MySQL 8.0+
- UV (Python 包管理器)

安装 UV:
```bash
pip install uv
```

### 2. 安装依赖

```bash
cd backend
uv sync
```

### 3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，修改数据库连接配置：

```env
# 数据库配置
DATABASE_URL=mysql+pymysql://root:你的密码@localhost:3306/agentnow

# JWT配置 (生产环境请修改为随机字符串)
JWT_SECRET_KEY=your_random_secret_key_here

# 默认管理员配置
DEFAULT_ADMIN_PHONE=admin
DEFAULT_ADMIN_PASSWORD=123456
```

### 4. 初始化数据库

方式一：执行 SQL 脚本
```bash
mysql -u root -p < data/database.sql
```

方式二：启动应用时自动创建表（需确保数据库 `agentnow` 已存在）

### 5. 启动开发服务器

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 接口

### 认证相关 (前缀: /api/v1)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /auth/login | 用户登录 | 否 |
| POST | /auth/change-password | 修改密码 | 是 |
| GET | /auth/me | 获取当前用户信息 | 是 |
| POST | /auth/logout | 用户登出 | 否 |

### 公共接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | / | 根路径，返回服务信息 |
| GET | /health | 健康检查 |

## 默认管理员账号

应用启动时会自动初始化默认管理员账号：

- **手机号**: `admin`
- **默认密码**: `123456`
- **角色**: `admin`

> ⚠️ 注意：首次登录后必须修改密码！

## 登录流程示例

### 1. 登录

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone":"admin","password":"123456"}'
```

响应：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "phone": "admin",
    "username": "系统管理员",
    "role": "admin",
    "is_active": true,
    "is_default_password": true,
    ...
  }
}
```

注意：`is_default_password` 为 `true` 表示需要修改密码。

### 2. 修改密码

```bash
curl -X POST http://localhost:8000/api/v1/auth/change-password \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 你的access_token" \
  -d '{"old_password":"123456","new_password":"你的新密码"}'
```

### 3. 获取当前用户信息

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer 你的access_token"
```

## 数据库表结构

### users 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键，自增 |
| phone | VARCHAR(20) | 手机号（登录账号），唯一 |
| password_hash | VARCHAR(255) | 密码哈希 |
| username | VARCHAR(50) | 用户名 |
| role | VARCHAR(20) | 角色：admin/user |
| is_active | BOOLEAN | 是否激活 |
| is_default_password | BOOLEAN | 是否为默认密码 |
| hermes_profile | VARCHAR(100) | 对应 Hermes Profile 名称 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

## 开发命令

```bash
# 安装依赖
uv sync

# 运行开发服务器
uv run uvicorn app.main:app --reload

# 代码格式化
uv run ruff check .
uv run ruff format .

# 类型检查
uv run mypy .
```

## 部署

### 使用 Docker 部署（可选）

```dockerfile
# Dockerfile 示例
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install uv && uv sync --frozen

COPY . .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 许可证

内部使用
