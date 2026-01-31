# CityScout 功能说明与测试指南

> 本文档列出 CityScout 系统的所有功能及测试步骤

---

## 系统概述

CityScout 是一个城市分析系统，帮助求职者评估南方城市的工作和生活成本。

**技术栈：**
- 后端：FastAPI + SQLAlchemy 2.0 + PostgreSQL + Redis + Celery
- 前端：Next.js 14 + TypeScript + shadcn/ui + TanStack Query + Recharts

---

## 启动系统

### 1. 启动后端服务

```bash
# 进入后端目录
cd backend

# 激活虚拟环境
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 启动 FastAPI
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 启动前端服务

```bash
# 进入前端目录
cd frontend

# 启动开发服务器
npm run dev
```

### 3. 启动 Celery Worker（用于爬虫任务）

```bash
cd backend
celery -A app.celery_app worker --loglevel=info --pool=solo

# 激活虚拟环境
.venv\Scripts\activate

# 用 python -m 方式运行 celery
python -m celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
```

### 4. 访问系统

- 前端界面：http://localhost:3000
- 后端 API 文档：http://localhost:8000/docs

---

## 功能模块

### 一、仪表盘 (`/dashboard`)

**功能：**
- 显示系统数据概览（城市数、招聘数、租房数、论坛帖子数）
- 显示爬虫任务统计（等待/运行/成功/失败）
- 显示最近 5 个任务
- 提供快速操作入口

**测试步骤：**
1. 访问 http://localhost:3000/dashboard
2. 检查数据卡片是否显示正确数量
3. 检查任务统计是否与实际任务状态一致
4. 点击快速操作按钮，验证跳转正确

---

### 二、城市管理 (`/cities`)

**功能：**
- 查看城市列表（名称、省份、等级、状态）
- 新增城市
- 编辑城市
- 删除城市
- 启用/禁用城市

**测试步骤：**

| 步骤 | 操作 | 预期结果 |
|------|------|---------|
| 1 | 访问 /cities | 显示城市列表，应有 20 个预置城市 |
| 2 | 点击「新增城市」按钮 | 弹出表单对话框 |
| 3 | 填写城市名称、省份、等级，点击保存 | 新城市出现在列表中 |
| 4 | 点击某城市的「编辑」按钮 | 弹出编辑对话框，显示当前信息 |
| 5 | 修改信息后保存 | 列表更新为新信息 |
| 6 | 点击启用/禁用开关 | 状态切换，提示成功 |
| 7 | 点击「删除」按钮 | 确认后城市从列表消失 |

**API 端点：**
- `GET /api/v1/cities` - 获取城市列表
- `POST /api/v1/cities` - 创建城市
- `PUT /api/v1/cities/{id}` - 更新城市
- `DELETE /api/v1/cities/{id}` - 删除城市
- `PATCH /api/v1/cities/{id}/toggle` - 切换启用状态

---

### 三、关键词管理 (`/keywords`)

**功能：**
- 查看关键词列表（按分类筛选）
- 新增关键词
- 编辑关键词
- 删除关键词

**分类说明：**
- `job_search` - 招聘搜索关键词（如：Python、前端、后端）
- `job_exclude` - 排除关键词（如：销售、保险）
- `forum_topic` - 论坛话题关键词（如：定居、工作体验）

**测试步骤：**

| 步骤 | 操作 | 预期结果 |
|------|------|---------|
| 1 | 访问 /keywords | 显示关键词列表 |
| 2 | 切换分类标签（全部/招聘/排除/论坛） | 列表按分类过滤 |
| 3 | 点击「新增关键词」 | 弹出表单 |
| 4 | 选择分类、输入关键词、选择优先级 | 保存成功 |
| 5 | 编辑已有关键词 | 修改成功 |
| 6 | 删除关键词 | 删除成功 |

---

### 四、数据源管理 (`/sources`)

**功能：**
- 查看数据源列表
- 启用/禁用数据源

**预置数据源：**
| 名称 | 类型 | 说明 |
|------|------|------|
| 58同城 | job/rent | 招聘和租房数据 |
| Boss直聘 | job | 招聘数据（需手动导入） |
| V2EX | forum | 技术论坛 |
| 百度贴吧 | forum | 城市贴吧 |
| 知乎 | forum | 问答社区（需手动导入） |
| 微博 | forum | 社交媒体（需手动导入） |
| 小红书 | forum | 生活分享（需手动导入） |

**测试步骤：**
1. 访问 /sources
2. 查看数据源列表
3. 切换启用/禁用开关
4. 验证状态变化

---

### 五、爬虫任务 (`/tasks`)

**功能：**
- 查看任务列表（状态筛选、分页）
- 创建单个任务
- 批量创建任务
- 启动/取消任务

**任务类型：**
- `job_crawl` - 招聘数据爬取
- `rent_crawl` - 租房数据爬取
- `forum_crawl` - 论坛数据爬取

**任务状态：**
- `pending` - 等待中
- `running` - 运行中
- `success` - 成功
- `failed` - 失败
- `cancelled` - 已取消

**测试步骤：**

| 步骤 | 操作 | 预期结果 |
|------|------|---------|
| 1 | 访问 /tasks | 显示任务列表 |
| 2 | 点击「创建任务」 | 弹出表单 |
| 3 | 选择任务类型、数据源、城市 | 任务创建成功 |
| 4 | 点击「批量创建」 | 弹出批量表单 |
| 5 | 选择所有城市创建任务 | 多个任务同时创建 |
| 6 | 点击「启动」按钮 | 任务状态变为 running |
| 7 | 点击「取消」按钮 | 任务状态变为 cancelled |

**注意：** 需要启动 Celery Worker 才能实际执行爬虫任务

---

### 六、数据浏览

#### 6.1 招聘数据 (`/data/jobs`)

**功能：**
- 查看招聘列表（分页、筛选）
- 按城市筛选
- 搜索职位/公司
- 查看职位详情

**测试步骤：**
1. 访问 /data/jobs
2. 查看统计卡片（总数、平均薪资等）
3. 使用城市下拉框筛选
4. 在搜索框输入关键词
5. 点击某条数据的「查看」按钮
6. 查看详情抽屉中的完整信息
7. 点击「查看原始链接」跳转到源网站

#### 6.2 租房数据 (`/data/rent`)

**功能：**
- 查看租房列表（分页、筛选）
- 按城市、类型（整租/合租/公寓）筛选
- 搜索标题/小区
- 查看房源详情

**测试步骤：**
1. 访问 /data/rent
2. 查看统计卡片（总数、平均价格、平均面积等）
3. 筛选城市和房屋类型
4. 搜索关键词
5. 查看详情

#### 6.3 论坛帖子 (`/data/forum`)

**功能：**
- 查看帖子列表（分页、筛选）
- 按城市、来源（V2EX/贴吧等）筛选
- 搜索标题/内容
- 查看帖子详情

**测试步骤：**
1. 访问 /data/forum
2. 查看统计卡片
3. 筛选城市和来源
4. 搜索关键词
5. 查看详情

---

### 七、手动导入 (`/manual-import`)

#### 7.1 搜索指南 (`/manual-import/guide`)

**功能：**
- 生成各平台的搜索链接（结合城市和关键词）
- 一键复制链接
- 打开目标网站

**支持平台：**
- Boss直聘
- 知乎
- 微博
- 小红书

**测试步骤：**
1. 访问 /manual-import/guide
2. 切换不同平台标签
3. 查看生成的搜索链接列表
4. 点击「复制链接」按钮
5. 点击「打开」按钮验证链接有效

#### 7.2 数据导入 (`/manual-import`)

**功能：**
- 下载数据模板（CSV）
- 上传文件导入（CSV/Excel）
- JSON 数据导入
- 预览和验证数据
- 执行导入

**测试步骤：**

| 步骤 | 操作 | 预期结果 |
|------|------|---------|
| 1 | 访问 /manual-import | 显示导入页面 |
| 2 | 选择数据类型（招聘/租房/论坛） | - |
| 3 | 选择城市和数据源 | - |
| 4 | 点击「下载模板」 | 下载对应类型的 CSV 模板 |
| 5 | 填写模板数据 | - |
| 6 | 上传文件 | 文件名显示在页面 |
| 7 | 点击「预览数据」 | 显示数据预览和验证结果 |
| 8 | 点击「执行导入」 | 显示导入结果（成功/跳过/错误数） |
| 9 | 切换到「JSON导入」标签 | - |
| 10 | 粘贴 JSON 数据 | - |
| 11 | 点击「导入JSON数据」 | 执行导入 |

**JSON 导入格式示例（招聘）：**
```json
[
  {
    "title": "Python开发工程师",
    "company": "某科技公司",
    "salary_min": 15000,
    "salary_max": 25000,
    "district": "南山区",
    "experience": "3-5年",
    "education": "本科"
  }
]
```

---

### 八、数据分析 (`/analysis`)

#### 8.1 城市对比

**功能：**
- 薪资对比柱状图（按城市）
- 租金对比柱状图（按城市）
- 城市数据对比表

**测试步骤：**
1. 访问 /analysis
2. 默认显示「城市对比」标签
3. 查看薪资柱状图
4. 查看租金柱状图
5. 查看数据对比表

#### 8.2 维度排名

**功能：**
- 按维度查看城市排名
- 支持维度：平均薪资、平均租金、薪租比、岗位数量、讨论热度

**测试步骤：**
1. 切换到「维度排名」标签
2. 使用下拉框切换维度
3. 查看排名列表（金银铜奖牌样式）

#### 8.3 综合评分

**功能：**
- 多维度加权评分
- 雷达图展示 Top 5 城市
- 综合排名表

**测试步骤：**
1. 切换到「综合评分」标签
2. 查看 Top 5 城市雷达图
3. 查看综合排名表（包含各维度得分）

---

### 九、数据导出 (`/export`)

#### 9.1 CSV 导出

**功能：**
- 导出城市综合对比表（CSV 格式，Excel 可直接打开）

**测试步骤：**
1. 访问 /export
2. 点击「下载 CSV」按钮
3. 用 Excel 打开下载的文件
4. 验证数据完整性

#### 9.2 Markdown 导出

**功能：**
- 导出论坛评论汇总（Markdown 格式）
- 可选择特定城市

**测试步骤：**
1. 选择城市（可选全部）
2. 点击「下载 Markdown」
3. 用 Markdown 编辑器打开
4. 验证内容格式

#### 9.3 AI 分析报告

**功能：**
- 生成 AI 分析提示词
- 一键复制到剪贴板
- 可用于 ChatGPT、Claude 等 AI 工具

**测试步骤：**
1. 点击「生成分析提示词」
2. 查看生成的提示词内容
3. 点击「复制」按钮
4. 粘贴到 AI 对话工具验证效果

---

### 十、系统设置 (`/settings`)

**功能：**
- 爬虫配置（请求间隔、页面超时、最大重试、最大页数）
- User-Agent 轮换开关
- 代理配置（启用/禁用、轮换）
- 代理列表管理（添加、删除、测试）

**测试步骤：**

| 步骤 | 操作 | 预期结果 |
|------|------|---------|
| 1 | 访问 /settings | 显示设置页面，默认「爬虫配置」标签 |
| 2 | 修改请求间隔为 3 秒 | 输入框值更新 |
| 3 | 点击「保存配置」 | 提示保存成功 |
| 4 | 刷新页面 | 请求间隔仍为 3 秒 |
| 5 | 切换到「代理配置」标签 | 显示代理设置 |
| 6 | 输入代理地址，点击添加 | 代理出现在列表中 |
| 7 | 点击代理的「测试」按钮 | 显示测试结果（可用/不可用） |
| 8 | 点击「删除」按钮 | 代理从列表移除 |
| 9 | 点击「保存配置」 | 提示保存成功 |

---

### 十一、系统日志 (`/logs`)

**功能：**
- 查看任务执行日志
- 按日志级别筛选（信息/警告/错误）
- 按任务类型筛选
- 按时间范围筛选
- 日志统计卡片

**测试步骤：**

| 步骤 | 操作 | 预期结果 |
|------|------|---------|
| 1 | 访问 /logs | 显示日志页面和统计卡片 |
| 2 | 查看统计卡片 | 显示总数、信息、警告、错误数量 |
| 3 | 选择日志级别「错误」 | 仅显示失败任务日志 |
| 4 | 选择任务类型「招聘采集」 | 仅显示招聘采集任务日志 |
| 5 | 选择时间范围「最近 1 天」 | 仅显示 24 小时内的日志 |
| 6 | 点击「刷新」按钮 | 日志列表刷新 |
| 7 | 翻页 | 分页正常工作 |

---

## API 端点汇总

| 模块 | 端点 | 方法 | 说明 |
|------|------|------|------|
| 仪表盘 | /api/v1/dashboard/overview | GET | 获取概览数据 |
| 城市 | /api/v1/cities | GET/POST | 列表/创建 |
| 城市 | /api/v1/cities/{id} | GET/PUT/DELETE | 详情/更新/删除 |
| 城市 | /api/v1/cities/{id}/toggle | PATCH | 切换状态 |
| 关键词 | /api/v1/keywords | GET/POST | 列表/创建 |
| 关键词 | /api/v1/keywords/{id} | GET/PUT/DELETE | 详情/更新/删除 |
| 数据源 | /api/v1/sources | GET/POST | 列表/创建 |
| 数据源 | /api/v1/sources/{id}/toggle | PATCH | 切换状态 |
| 任务 | /api/v1/tasks | GET/POST | 列表/创建 |
| 任务 | /api/v1/tasks/batch | POST | 批量创建 |
| 任务 | /api/v1/tasks/{id}/start | POST | 启动任务 |
| 任务 | /api/v1/tasks/{id}/cancel | POST | 取消任务 |
| 招聘 | /api/v1/jobs | GET | 列表（分页、筛选） |
| 招聘 | /api/v1/jobs/{id} | GET | 详情 |
| 招聘 | /api/v1/jobs/stats/summary | GET | 统计 |
| 租房 | /api/v1/rent | GET | 列表 |
| 租房 | /api/v1/rent/{id} | GET | 详情 |
| 租房 | /api/v1/rent/stats/summary | GET | 统计 |
| 论坛 | /api/v1/forum | GET | 列表 |
| 论坛 | /api/v1/forum/{id} | GET | 详情 |
| 论坛 | /api/v1/forum/stats/summary | GET | 统计 |
| 导入 | /api/v1/import/guide | GET | 搜索指南 |
| 导入 | /api/v1/import/template/{type} | GET | 下载模板 |
| 导入 | /api/v1/import/preview | POST | 预览数据 |
| 导入 | /api/v1/import/execute | POST | 执行导入 |
| 导入 | /api/v1/import/json | POST | JSON导入 |
| 分析 | /api/v1/analysis/city-comparison | GET | 城市对比 |
| 分析 | /api/v1/analysis/rankings | GET | 维度排名 |
| 分析 | /api/v1/analysis/score | GET | 综合评分 |
| 导出 | /api/v1/export/excel/city-comparison | GET | CSV导出 |
| 导出 | /api/v1/export/markdown/forum-summary | GET | MD导出 |
| 导出 | /api/v1/export/ai-report | GET | AI提示词 |
| 设置 | /api/v1/settings | GET/PUT | 获取/更新全部设置 |
| 设置 | /api/v1/settings/crawler | GET/PUT | 爬虫配置 |
| 设置 | /api/v1/settings/proxy | GET/PUT | 代理配置 |
| 设置 | /api/v1/settings/proxy/test | POST | 测试代理 |
| 日志 | /api/v1/logs | GET | 日志列表（分页、筛选） |
| 日志 | /api/v1/logs/stats | GET | 日志统计 |

---

## 常见问题

### Q: API 返回 404

**原因：** 后端未加载新路由

**解决：** 重启后端服务 `Ctrl+C` 然后重新运行 uvicorn

### Q: 爬虫任务一直是 pending 状态

**原因：** Celery Worker 未启动

**解决：** 启动 Worker
```bash
celery -A app.celery_app worker --loglevel=info --pool=solo
```

### Q: 数据库连接失败

**原因：** PostgreSQL 未启动

**解决：**
```bash
# Windows (使用 scoop 安装的 PostgreSQL)
pg_ctl start

# 或检查服务
sc query postgresql
```

### Q: Redis 连接失败

**原因：** Redis 未启动

**解决：**
```bash
redis-server
```

---

## 测试数据准备

系统启动后默认已有：
- 20 个南方城市（深圳、广州、杭州等）
- 25+ 个关键词（Python、Java、前端等）
- 9 个数据源（58同城、Boss直聘、V2EX等）

如需测试数据浏览和分析功能，可通过以下方式添加数据：

1. **手动导入**：使用 /manual-import 页面导入 CSV/JSON 数据
2. **运行爬虫**：创建并启动爬虫任务（需 Celery Worker）
3. **直接插入**：通过数据库 SQL 或 API 直接插入测试数据

---

*文档版本：1.1 | 更新时间：2026-01-31*
