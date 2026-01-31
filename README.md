# CityScout - 城市分析系统

城市数据采集与分析平台，帮助求职者选择最适合的南方城市定居和工作。

## 功能特点

- **Web后台管理** - 配置城市、关键词、数据源
- **爬虫系统** - 自动采集招聘、房租、论坛评论数据
- **手动导入** - 对于反爬严格的网站提供手动导入方案
- **数据分析** - 城市对比、可视化图表、综合评分
- **数据导出** - CSV、Markdown、AI分析报告

## 功能模块

| 模块 | 路径 | 功能 |
|------|------|------|
| 仪表盘 | `/dashboard` | 数据概览、任务统计、快速操作 |
| 城市管理 | `/cities` | 增删改查目标城市 |
| 关键词管理 | `/keywords` | 配置搜索和排除关键词 |
| 数据源管理 | `/sources` | 启用/禁用数据源 |
| 爬虫任务 | `/tasks` | 创建、启动、取消爬虫任务 |
| 手动导入 | `/manual-import` | 上传 CSV/Excel/JSON 数据 |
| 招聘数据 | `/data/jobs` | 浏览筛选招聘信息 |
| 租房数据 | `/data/rent` | 浏览筛选租房信息 |
| 论坛帖子 | `/data/forum` | 浏览筛选论坛评论 |
| 数据分析 | `/analysis` | 城市对比图表、排名、评分 |
| 数据导出 | `/export` | CSV、Markdown、AI 报告 |
| 系统设置 | `/settings` | 爬虫配置、代理配置 |
| 系统日志 | `/logs` | 任务执行日志查看 |

## 技术栈

- **后端**: Python 3.12, FastAPI, SQLAlchemy 2.0, Celery
- **前端**: Next.js 16, TypeScript, shadcn/ui, TanStack Query, Recharts
- **数据库**: PostgreSQL 16, Redis
- **爬虫**: Playwright
- **部署**: Docker Compose

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- PostgreSQL 16+
- Redis

### 本地开发（Windows）

#### 1. 检查/启动数据库服务

PostgreSQL 和 Redis 是系统级服务，可能已经在运行。先检查状态：

```powershell
# 检查 PostgreSQL 是否运行（端口 5432）
netstat -ano | findstr :5432

# 检查 Redis 是否运行（端口 6379）
netstat -ano | findstr :6379
```

如果看到 `LISTENING` 状态，说明服务已在运行，无需再次启动。

**如果服务未运行，启动方式：**

```powershell
# PostgreSQL（scoop 安装）
# 方式1: 添加到 PATH 后使用
$env:PATH += ";$(scoop prefix postgresql)\bin"
pg_ctl start -D "$(scoop prefix postgresql)\data"

# 方式2: 直接用完整路径
& "$(scoop prefix postgresql)\bin\pg_ctl" start -D "$(scoop prefix postgresql)\data"

# Redis（在新终端窗口运行，会占用该窗口）
redis-server
```

> **注意**: PostgreSQL 和 Redis 是共享服务，不是项目独有的。只要它们在运行，任何需要数据库的项目都可以使用。

#### 2. 启动后端

```powershell
cd backend
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head  # 首次运行
python -m uvicorn app.main:app --reload --port 8001
```

#### 3. 启动前端

```powershell
cd frontend
npm install
npm run dev
```

#### 4. 启动 Celery Worker（爬虫任务需要）

```powershell
cd backend
.venv\Scripts\activate
python -m celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
```

### Docker 部署

```bash
# 复制环境变量
cp .env.example .env

# 启动所有服务
docker-compose up -d

# 数据库迁移
docker-compose exec backend alembic upgrade head
```

### 访问地址

- 前端界面: http://localhost:3000
- API 文档: http://localhost:8000/docs

## 项目结构

```
cityscout/
├── backend/                # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/        # API 路由
│   │   ├── models/        # 数据库模型
│   │   ├── schemas/       # Pydantic 模式
│   │   ├── crawlers/      # 爬虫实现
│   │   └── tasks/         # Celery 任务
│   └── alembic/           # 数据库迁移
├── frontend/               # Next.js 前端
│   ├── src/
│   │   ├── app/           # 页面路由
│   │   ├── components/    # UI 组件
│   │   ├── lib/           # 工具函数
│   │   └── types/         # TypeScript 类型
├── docs/                   # 文档
│   ├── PLAN.md            # 开发计划
│   └── function.md        # 功能说明
└── docker-compose.yml      # Docker 编排
```

## 预置数据

系统初始化后包含：
- **20 个南方城市**：深圳、广州、杭州、南京、苏州等
- **25+ 个关键词**：Python、Java、前端、后端等
- **9 个数据源**：58同城、Boss直聘、V2EX、百度贴吧等

## 文档

- [功能说明与测试指南](docs/function.md)
- [开发计划](docs/PLAN.md)

## 常见问题

### 服务状态检查

```powershell
# 一键检查所有服务状态
netstat -ano | findstr "5432 6379 8000 3000"
```

| 端口 | 服务 | 说明 |
|------|------|------|
| 5432 | PostgreSQL | 数据库 |
| 6379 | Redis | 缓存/消息队列 |
| 8000 | FastAPI | 后端 API |
| 3000 | Next.js | 前端界面 |

### pg_ctl 命令找不到

Scoop 安装的 PostgreSQL 需要手动添加到 PATH：

```powershell
$env:PATH += ";$(scoop prefix postgresql)\bin"
```

### 端口被占用

```powershell
# 查看占用端口的进程
netstat -ano | findstr :端口号

# 终止进程（需要管理员权限）
taskkill /PID 进程号 /F
```

### Celery 命令找不到

使用 `python -m` 方式运行：

```powershell
python -m celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
```

## License

MIT
