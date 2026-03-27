# 文章管理模块增强设计

## 概述

对前端文章管理模块进行两项增强：
1. 新增文章编辑功能（独立编辑页）
2. 优化文章预览效果（卡片列表 + 详情页）

---

## 1. 文章编辑功能

### 1.1 路由设计

| 路由 | 组件 | 职责 |
|------|------|------|
| `/articles/edit/:id` | `Articles/Edit.tsx` | 编辑文章表单 |

### 1.2 编辑字段

| 字段 | 组件类型 | 说明 |
|------|----------|------|
| 标题 | Input | 必填，最大长度 500 |
| 作者 | Input | 选填，最大长度 255 |
| 摘要 | Textarea | 选填，文章简介 |
| 正文 | Markdown 编辑器 | 必填，支持实时预览 |
| 封面图片 | Input + 预览 | 选填，URL 输入 + 图片预览 |
| 标签 | Multi-Select | 多选，选项来自 tags API |

### 1.3 页面布局

```
+------------------------------------------+
|  面包屑: 文章管理 / 编辑文章               |
+------------------------------------------+
|  +--------------------------------------+ |
|  |  标题输入                            | |
|  +--------------------------------------+ |
|  |  作者输入    |  封面图片URL输入        | |
|  +--------------------------------------+ |
|  |  摘要输入                            | |
|  +--------------------------------------+ |
|  |  标签选择                            | |
|  +--------------------------------------+ |
|  |  正文 (Markdown 编辑器 + 预览并排)    | |
|  |  +-------------+ +-------------+     | |
|  |  | 编辑区域    | | 实时预览    |     | |
|  |  +-------------+ +-------------+     | |
|  +--------------------------------------+ |
|                        [取消] [保存]      |
+------------------------------------------+
```

### 1.4 Markdown 编辑器

- 使用 `@uiw/react-md-editor` 或类似库
- 左右分栏：左侧编辑，右侧预览
- 支持常用 Markdown 语法
- 响应式，屏幕窄时预览可折叠

### 1.5 API 变更

**复用现有 API**:

| 用途 | 端点 | 说明 |
|------|------|------|
| 获取文章详情 | `GET /api/articles/{id}` | 已存在，用于加载编辑数据 |
| 获取文章正文 | `GET /api/articles/{id}/markdown` | 已存在，获取 Markdown 内容 |
| 获取标签列表 | `GET /api/tags` | 已存在（`getTags`），用于填充标签选择 |
| 更新文章 | `PUT /api/articles/{id}` | **新增** |

**新增后端接口**:

```typescript
// PUT /api/articles/{id}
// Request
{
  title?: string;
  author?: string;
  summary?: string;
  markdown_content?: string;  // 更新的 Markdown 内容
  cover_image?: string;
  tags?: string[];
}

// Response
{
  id: number;
  title: string;
  ...
}
```

**前端 API**:

```typescript
// src/api/index.ts
// 复用现有
getArticle(id: number) => api.get(`/articles/${id}`)
getArticleMarkdown(id: number) => api.get(`/articles/${id}/markdown`)
getTags() => api.get('/tags')

// 新增
updateArticle(id: number, data: {
  title?: string;
  author?: string;
  summary?: string;
  markdown_content?: string;
  cover_image?: string;
  tags?: string[];
}) => api.put(`/articles/${id}`, data)
```

### 1.6 交互流程

1. 文章列表点击编辑图标 → `navigate(/articles/edit/${id})`
2. 编辑页加载时调用 `getArticle(id)` + `getArticleMarkdown(id)` 获取数据
3. 用户编辑，点击保存 → 调用 `updateArticle` → 成功后 `navigate(/articles)`
4. 点击取消 → `navigate(/articles)`

---

## 2. 预览卡片优化

### 2.1 组件文件

- `src/pages/Preview/components/NewsCard.tsx` - 重构

### 2.2 设计规范

**卡片结构**:
```
+------------------------+
|                        |
|      封面图片           |
|   (带渐变遮罩叠加)      |
|                        |
| +--------------------+ |
| | 标签1  标签2        | |
| +--------------------+ |
| | 标题文字            | |
| | 来源 · 时间         | |
| +--------------------+ |
+------------------------+
```

**设计细节**:

| 元素 | 样式 |
|------|------|
| 封面图 | 高度 200px，object-fit: cover，圆角 12px |
| 渐变遮罩 | 底部 50% 透明渐变到深色 |
| 标题 | 白色，16-18px，加粗，放在图片底部 |
| 标签 | 彩色胶囊，圆角 12px，半透明背景，放在标题上方 |
| 来源/时间 | 白色半透明徽章，放在封面图右下角 |
| 卡片背景 | 圆角 12px，悬停时阴影加深，轻微上移 |
| 悬停效果 | transform: translateY(-4px), box-shadow 增强 |

### 2.3 深色模式

- 所有颜色在深色模式下自动适配
- 渐变遮罩在深色模式下加深
- 白色文字改为浅色

---

## 3. 文章详情页优化

### 3.1 组件文件

- `src/pages/Preview/ArticleDetail.tsx` - 重构
- `src/pages/Preview/components/ArticleContent.tsx` - 重构

### 3.2 设计规范

**页面结构**:
```
+------------------------------------------+
|  Header (可折叠返回按钮)                   |
+------------------------------------------+
|  +--------------------------------------+ |
|  | 封面图 (全宽，最大高度 400px)         | |
|  +--------------------------------------+ |
|                                          |
|  标题 (大号字体，居中或左对齐)              |
|  作者 · 发布时间                           |
|  +--------------------------------------+ |
|  | 标签列表                              | |
|  +--------------------------------------+ |
|                                          |
|  正文内容                                 |
|  (max-width: 720px, 行高 1.8)            |
|                                          |
+------------------------------------------+
```

**设计细节**:

| 元素 | 样式 |
|------|------|
| 页面最大宽度 | 800px，居中 |
| 封面图 | 全宽展示，圆角 12px，max-height 400px |
| 标题 | 32-36px，加粗，margin-bottom 16px |
| 元信息 | 作者、发布时间，灰色，14px |
| 标签区 | 圆角胶囊彩色标签，gap 8px |
| 正文容器 | max-width 720px，行高 1.8 |
| Markdown h1-h3 | 有足够的上下间距 |
| 代码块 | 深色背景，圆角，copy 按钮 |
| 引用 | 左侧边框，斜体样式 |
| 图片 | 圆角，居中，最大宽度 100% |

---

## 4. 文件变更清单

### 新增文件
- `frontend/src/pages/Articles/Edit.tsx` - 文章编辑页

### 修改文件
- `frontend/src/pages/Articles/index.tsx` - 添加编辑按钮和路由跳转
- `frontend/src/pages/Preview/components/NewsCard.tsx` - 卡片样式优化
- `frontend/src/pages/Preview/ArticleDetail.tsx` - 详情页重构
- `frontend/src/pages/Preview/components/ArticleContent.tsx` - 内容样式优化
- `frontend/src/App.tsx` - 添加编辑路由
- `frontend/src/api/index.ts` - 添加 updateArticle API

### 后端文件
- `backend/app/routers/articles.py` - 添加 PUT endpoint
- `backend/app/schemas/article.py` - 添加 Update schema

---

## 5. 成功标准

1. 文章列表可以点击编辑进入独立编辑页
2. 编辑页完整支持所有字段编辑
3. Markdown 编辑器支持实时预览
4. 保存后正确更新数据并返回列表
5. 预览卡片视觉效果明显提升
6. 文章详情页阅读体验舒适
7. 深色模式正常适配
