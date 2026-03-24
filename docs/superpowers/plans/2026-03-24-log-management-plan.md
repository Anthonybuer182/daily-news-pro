# 日志管理模块实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在管理后台添加独立的日志管理页面，支持按任务/级别/时间筛选查看爬取日志

**Architecture:** 前端新增 `/logs` 页面 + 后端新增 `/api/logs` 路由，复用现有 Log 模型

**Tech Stack:** React + Ant Design (前端), FastAPI + SQLAlchemy (后端)

---

## 文件变更总览

### 后端新增
- `backend/app/routers/logs.py` - 日志 API 路由
- `backend/app/schemas/log.py` - Pydantic schema

### 后端修改
- `backend/app/main.py` - 注册 logs router
- `backend/app/routers/__init__.py` - 导出 logs router
- `backend/app/schemas/__init__.py` - 添加 Log schema 导出

### 前端新增
- `frontend/src/pages/Logs/index.tsx` - 日志列表页面
- `frontend/src/api/index.ts` - 添加 getLogs API

### 前端修改
- `frontend/src/App.tsx` - 添加 /logs 路由
- `frontend/src/components/Sidebar.tsx` - 添加日志管理菜单项

---

## Task 1: 后端 - 创建日志 Schema

**Files:**
- Create: `backend/app/schemas/log.py`

- [ ] **Step 1: 创建 Pydantic Schema**

```python
# backend/app/schemas/log.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class LogResponse(BaseModel):
    id: int
    job_id: int
    level: str
    message: str
    created_at: datetime
    job_name: Optional[str] = None

    class Config:
        from_attributes = True
```

- [ ] **Step 2: 提交**

```bash
git add backend/app/schemas/log.py backend/app/schemas/__init__.py
git commit -m "feat: add Log Pydantic schema"
```

---

## Task 2: 后端 - 更新 __init__ 导出

**Files:**
- Modify: `backend/app/schemas/__init__.py`
- Modify: `backend/app/routers/__init__.py`

- [ ] **Step 1: 更新 schemas/__init__.py**

```python
# backend/app/schemas/__init__.py 添加
from app.schemas.log import LogResponse
# 添加到 __all__ 列表
```

- [ ] **Step 2: 更新 routers/__init__.py**

```python
# backend/app/routers/__init__.py
from app.routers.logs import router as logs_router
from app.routers import rules, articles, jobs, preview, debug, channels

__all__ = ["logs_router", "rules", "articles", "jobs", "preview", "debug", "channels"]
```

- [ ] **Step 3: 提交**

```bash
git add backend/app/schemas/__init__.py backend/app/routers/__init__.py
git commit -m "feat: export logs router and schema"
```

---

## Task 3: 后端 - 创建日志 Router

**Files:**
- Create: `backend/app/routers/logs.py`

- [ ] **Step 1: 创建日志路由**

```python
# backend/app/routers/logs.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import Log, Job
from app.schemas.log import LogResponse
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/logs", tags=["logs"])

@router.get("")
def get_logs(
    skip: int = 0,
    limit: int = 20,
    job_id: int = None,
    level: str = None,
    start_time: str = None,
    end_time: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(Log).options(joinedload(Log.job))

    if job_id:
        query = query.filter(Log.job_id == job_id)
    if level:
        query = query.filter(Log.level == level)
    if start_time:
        query = query.filter(Log.created_at >= start_time)
    if end_time:
        query = query.filter(Log.created_at <= end_time)

    total = query.count()
    logs = query.order_by(Log.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for log in logs:
        job_name = log.job.rule.name if log.job and log.job.rule else f"Job-{log.job_id}"
        result.append({
            "id": log.id,
            "job_id": log.job_id,
            "level": log.level,
            "message": log.message,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "job_name": job_name
        })

    response = JSONResponse(content=result)
    response.headers["X-Total-Count"] = str(total)
    return response
```

- [ ] **Step 2: 提交**

```bash
git add backend/app/routers/logs.py
git commit -m "feat: add logs API router"
```

---

## Task 4: 后端 - 注册 Router

**Files:**
- Modify: `backend/app/main.py:5` - 添加 logs 导入
- Modify: `backend/app/main.py:31` - 添加 logs router

- [ ] **Step 1: 更新 main.py**

```python
# backend/app/main.py line 5
from app.routers import rules, articles, jobs, preview, debug, channels, logs

# backend/app/main.py line 31 (after channels.router)
app.include_router(logs.router)
```

- [ ] **Step 2: 提交**

```bash
git add backend/app/main.py
git commit -m "feat: register logs router in main app"
```

---

## Task 5: 前端 - 添加 API 方法

**Files:**
- Modify: `frontend/src/api/index.ts`

- [ ] **Step 1: 添加日志 API**

```typescript
// frontend/src/api/index.ts 末尾添加

// Logs
export const getLogs = (params?: {
  skip?: number;
  limit?: number;
  job_id?: number;
  level?: string;
  start_time?: string;
  end_time?: string;
}) => api.get('/logs', { params });
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/api/index.ts
git commit -m "feat: add getLogs API method"
```

---

## Task 6: 前端 - 创建日志页面

**Files:**
- Create: `frontend/src/pages/Logs/index.tsx`

- [ ] **Step 1: 创建日志页面组件**

```tsx
// frontend/src/pages/Logs/index.tsx
import { useEffect, useState } from 'react'
import { Table, Tag, Card, Form, Select, DatePicker, Space, Button, message } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import { getLogs, getJobs } from '../../api'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker
const { Option } = Select

export default function Logs() {
  const [loading, setLoading] = useState(false)
  const [logs, setLogs] = useState([])
  const [jobs, setJobs] = useState([])
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 })
  const [searchForm] = Form.useForm()
  const [searchParams, setSearchParams] = useState<{
    job_id?: number;
    level?: string;
    start_time?: string;
    end_time?: string;
  }>({})

  useEffect(() => {
    loadJobs()
  }, [])

  useEffect(() => {
    loadLogs()
  }, [pagination.current, pagination.pageSize, searchParams])

  const loadJobs = async () => {
    try {
      const res = await getJobs({ limit: 1000 })
      setJobs(res.data)
    } catch (error) {
      console.error(error)
    }
  }

  const loadLogs = async () => {
    setLoading(true)
    try {
      const res = await getLogs({
        skip: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize,
        job_id: searchParams.job_id,
        level: searchParams.level,
        start_time: searchParams.start_time,
        end_time: searchParams.end_time
      })
      setLogs(res.data)
      const total = res.headers['x-total-count'] || res.data.length
      setPagination(prev => ({ ...prev, total }))
    } catch (error) {
      console.error(error)
      message.error('加载日志失败')
    } finally {
      setLoading(false)
    }
  }

  const handleTableChange = (pag: any) => {
    setPagination(prev => ({
      ...prev,
      current: pag.current,
      pageSize: pag.pageSize
    }))
  }

  const handleSearch = (values: any) => {
    setPagination(prev => ({ ...prev, current: 1 }))
    setSearchParams({
      job_id: values.job_id,
      level: values.level,
      start_time: values.dateRange?.[0]?.format('YYYY-MM-DD'),
      end_time: values.dateRange?.[1]?.format('YYYY-MM-DD')
    })
  }

  const handleReset = () => {
    searchForm.resetFields()
    setPagination(prev => ({ ...prev, current: 1 }))
    setSearchParams({})
  }

  const getLevelColor = (level: string) => {
    const colors: Record<string, string> = {
      error: 'red',
      warning: 'orange',
      info: 'blue'
    }
    return colors[level] || 'default'
  }

  const columns = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD HH:mm:ss') : '-'
    },
    {
      title: '任务',
      dataIndex: 'job_name',
      key: 'job_name',
      ellipsis: true
    },
    {
      title: '级别',
      dataIndex: 'level',
      key: 'level',
      width: 100,
      render: (level: string) => (
        <Tag color={getLevelColor(level)}>{level?.toUpperCase()}</Tag>
      )
    },
    {
      title: '消息',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true
    }
  ]

  return (
    <div>
      <h1>日志管理</h1>
      <Card>
        <Form
          form={searchForm}
          layout="inline"
          onFinish={handleSearch}
          style={{ marginBottom: 16 }}
        >
          <Form.Item name="job_id" label="任务">
            <Select placeholder="选择任务" style={{ width: 200 }} allowClear>
              {jobs.map(job => (
                <Option key={job.id} value={job.id}>{job.rule_name || `规则${job.rule_id}`}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="level" label="级别">
            <Select placeholder="选择级别" style={{ width: 120 }} allowClear>
              <Option value="error">ERROR</Option>
              <Option value="warning">WARNING</Option>
              <Option value="info">INFO</Option>
            </Select>
          </Form.Item>
          <Form.Item name="dateRange" label="时间范围">
            <RangePicker format="YYYY-MM-DD" allowClear />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" icon={<SearchOutlined />} htmlType="submit">
                查询
              </Button>
              <Button onClick={handleReset}>
                重置
              </Button>
            </Space>
          </Form.Item>
        </Form>

        <Table
          columns={columns}
          dataSource={logs}
          rowKey="id"
          loading={loading}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showSizeChanger: true,
            pageSizeOptions: ['20', '50', '100', '200'],
            showTotal: (total: number) => `共 ${total} 条`
          }}
          onChange={handleTableChange}
        />
      </Card>
    </div>
  )
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/pages/Logs/index.tsx
git commit -m "feat: add Logs page component"
```

---

## Task 7: 前端 - 添加路由和菜单

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/Sidebar.tsx`

- [ ] **Step 1: 更新 App.tsx**

```tsx
// frontend/src/App.tsx 添加 Logs 导入和路由
import Logs from './pages/Logs'

// 在管理后台的 Routes 中添加
<Route path="/logs" element={<Logs />} />
```

- [ ] **Step 2: 更新 Sidebar.tsx**

```tsx
// frontend/src/components/Sidebar.tsx
// 添加导入
import { FileTextOutlined } from '@ant-design/icons'  // 或 CloudOutlined

// 在 menuItems 中添加
{ key: '/logs', icon: <FileTextOutlined />, label: '日志管理' },
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/App.tsx frontend/src/components/Sidebar.tsx
git commit -m "feat: add logs route and sidebar menu"
```

---

## Task 8: 验证

- [ ] **Step 1: 启动后端服务**

```bash
cd backend && source venv/bin/activate && uvicorn app.main:app --reload
```

- [ ] **Step 2: 启动前端服务**

```bash
cd frontend && npm run dev
```

- [ ] **Step 3: 测试 API**

```bash
curl "http://localhost:8000/api/logs"
curl "http://localhost:8000/api/logs?level=error"
curl "http://localhost:8000/api/logs?job_id=1"
```

- [ ] **Step 4: 访问页面**

打开浏览器访问 `http://localhost:5173/logs`，确认：
- [ ] 侧边栏显示"日志管理"菜单
- [ ] 点击跳转至日志列表页
- [ ] 筛选功能正常工作
- [ ] 日志级别颜色正确显示
