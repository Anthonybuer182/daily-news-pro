# 日志管理模块设计

## 概述

在管理后台添加独立的"日志管理"模块，方便用户在平台内直接查看爬取任务的运行日志，无需登录 IDE 查看问题。

## 页面设计

### 路由
- URL: `/logs`
- Sidebar 菜单: `日志管理`
- 图标: `FileTextOutlined` 或新增 `审计` 类图标

### 布局
```
┌─────────────────────────────────────────────────┐
│  日志管理                                        │
├─────────────────────────────────────────────────┤
│  [Job ▼]  [级别 ▼]  [时间范围         ]  [搜索] │
├─────────────────────────────────────────────────┤
│  时间           │ 任务      │ 级别  │ 消息       │
├─────────────────────────────────────────────────┤
│  03-24 10:30   │ 规则-新浪  │ ERROR │ 连接超时   │
│  03-24 10:28   │ 规则-腾讯  │ INFO  │ 成功抓取   │
└─────────────────────────────────────────────────┘
```

### 筛选功能
| 筛选项 | 类型 | 说明 |
|--------|------|------|
| Job | 下拉选择 | 列出所有任务，空=全部 |
| 级别 | 多选 | error / warning / info |
| 时间 | 日期范围 | 默认最近24小时 |

### 列表字段
| 字段 | 格式 | 说明 |
|------|------|------|
| 时间 | `YYYY-MM-DD HH:mm:ss` | created_at |
| 任务 | 文本 | job.name |
| 级别 | Tag | error=red, warning=orange, info=blue |
| 消息 | 截断文本 | 超过200字符截断，hover显示完整 |

### 交互
- 点击行展开详情面板，显示完整日志消息
- 支持分页（默认20条/页）

## API 设计

### GET /api/logs
获取日志列表

**Query 参数:**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| job_id | int | 否 | 按任务筛选 |
| level | string | 否 | error/warning/info |
| start_time | datetime | 否 | 开始时间 |
| end_time | datetime | 否 | 结束时间 |
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页条数，默认20 |

**响应:**
```json
{
  "items": [
    {
      "id": 1,
      "job_id": 1,
      "job_name": "规则-新浪",
      "level": "error",
      "message": "连接超时",
      "created_at": "2026-03-24T10:30:00"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

## 技术实现

### 前端
- 新建页面: `frontend/src/pages/Logs/index.tsx`
- 使用 Ant Design Table + FilterBar
- 复用项目现有组件模式

### 后端
- 新建 router: `backend/app/routers/logs.py`
- 已有 Log 模型，无需修改 models
- 关联 Job 表查询任务名称

## 文件变更

### 前端新增
- `frontend/src/pages/Logs/index.tsx`

### 前端修改
- `frontend/src/App.tsx` - 添加 /logs 路由
- `frontend/src/components/Sidebar.tsx` - 添加日志管理菜单

### 后端新增
- `backend/app/routers/logs.py`
- `backend/app/schemas/log.py` (如需要 Pydantic schema)

### 后端修改
- `backend/app/routers/__init__.py` - 注册 logs router
