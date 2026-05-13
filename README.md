# Daily News Pro

一款功能完整的新闻抓取与聚合工具，支持自定义爬取规则、定时任务、AI 分析、翻译及多渠道推送。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI · SQLAlchemy · SQLite · APScheduler · Playwright |
| 前端 | React 18 · TypeScript · Vite · Ant Design 5 |
| 内容提取 | Trafilatura · BeautifulSoup4 · 自定义 CSS 选择器 |
| 推送集成 | 飞书 Webhook · HTTP 自定义推送 |

## 功能特性

- **抓取规则管理**：可视化配置抓取目标 URL、提取字段、请求头等参数
- **渠道管理**：统一管理多个新闻源渠道，支持分组与标签
- **定时任务**：基于 APScheduler 的定时爬取任务，支持 Cron 表达式
- **文章管理**：文章列表、全文展示、标签分类、Markdown 渲染
- **AI 分析**：集成大模型对文章进行摘要与分析
- **翻译服务**：支持文章内容自动翻译
- **内容推送**：支持飞书 Webhook 及自定义 HTTP 推送
- **预览调试**：实时预览抓取结果，内置调试工具
- **Admin 鉴权**：基于 JWT 的管理员认证，全 API 保护

## 目录结构

```
daily-news-pro/
├── backend/                # FastAPI 后端
│   ├── app/
│   │   ├── main.py         # 应用入口
│   │   ├── config.py       # 配置管理
│   │   ├── database.py     # 数据库初始化
│   │   ├── models/         # SQLAlchemy 数据模型
│   │   ├── schemas/        # Pydantic 请求/响应模型
│   │   ├── routers/        # API 路由（articles, rules, jobs, channels 等）
│   │   ├── services/       # 业务逻辑（crawler, scheduler, analyzer 等）
│   │   ├── middleware/     # 鉴权中间件
│   │   └── utils/          # 工具函数
│   ├── data/
│   │   ├── database.db     # SQLite 数据库
│   │   └── articles/       # 文章 Markdown 存储
│   ├── requirements.txt
│   └── .env.example
└── frontend/               # React 前端
    ├── src/
    │   ├── pages/          # 页面组件（Dashboard, Articles, Rules 等）
    │   ├── components/     # 公共组件
    │   ├── api/            # Axios 请求封装
    │   └── types/          # TypeScript 类型定义
    ├── package.json
    └── vite.config.ts
```

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+

### 后端启动

```bash
cd backend

# 创建并激活虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器（用于 JS 渲染页面抓取）
playwright install chromium

# 复制并编辑环境变量
cp .env.example .env
# 修改 .env 中的 ADMIN_PASSWORD 和 SECRET_KEY

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

启动后访问：
- 前端：http://localhost:5173
- 后端 API 文档：http://localhost:8000/docs

### 生产构建

```bash
cd frontend
npm run build
# 构建产物位于 frontend/dist/
```

## 环境变量说明

复制 `backend/.env.example` 为 `backend/.env` 并按需修改：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `HOST` | 服务监听地址 | `0.0.0.0` |
| `PORT` | 服务端口 | `8000` |
| `DATABASE_URL` | 数据库连接地址 | `sqlite:///./data/database.db` |
| `FRONTEND_URL` | 前端地址（CORS 白名单） | `http://localhost:5173` |
| `ADMIN_PASSWORD` | 管理员登录密码 | **必须修改** |
| `SECRET_KEY` | JWT 签名密钥 | **必须修改** |
| `DEFAULT_DELAY_MIN` | 爬取请求最小延迟（秒） | `1` |
| `DEFAULT_DELAY_MAX` | 爬取请求最大延迟（秒） | `3` |

> 生产环境请务必将 `ADMIN_PASSWORD` 和 `SECRET_KEY` 替换为强随机值。
> 生成随机 SECRET_KEY：`openssl rand -hex 32`

## API 文档

后端基于 FastAPI 自动生成 OpenAPI 文档，启动后访问：

- Swagger UI：http://localhost:8000/docs

## License

[MIT](./LICENSE) © 2026 Anthonybuer182
