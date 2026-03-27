# Article Management Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add article editing functionality and optimize preview UI (cards + detail page)

**Architecture:** Two-part enhancement: (1) Full article editing with Markdown editor on frontend + PUT API on backend, (2) Visual redesign of news cards and article detail page.

**Tech Stack:** React 18, TypeScript, Ant Design 5, @uiw/react-md-editor, FastAPI (backend)

---

## File Structure

### Backend Changes
- `backend/app/routers/articles.py` - Add PUT endpoint

### Frontend Changes
- Create: `frontend/src/pages/Articles/Edit.tsx` - Article edit page
- Modify: `frontend/src/App.tsx:32` - Add edit route
- Modify: `frontend/src/api/index.ts:49` - Add updateArticle API
- Modify: `frontend/src/pages/Articles/index.tsx` - Add edit button
- Modify: `frontend/src/pages/Preview/components/NewsCard.tsx` - Redesign card
- Modify: `frontend/src/pages/Preview/ArticleDetail.tsx` - Improve detail layout
- Modify: `frontend/src/pages/Preview/components/ArticleContent.tsx` - Better markdown styling

---

## Task 1: Backend - Add PUT Endpoint

**Files:**
- Modify: `backend/app/routers/articles.py`

- [ ] **Step 1: Add PUT endpoint for article update**

Add after line 92 (after `get_article` function):

```python
@router.put("/{article_id}", response_model=ArticleSchema)
def update_article(article_id: int, article_update: ArticleUpdate, db: Session = Depends(get_db)):
    """更新文章"""
    import os
    import json
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    update_data = article_update.model_dump(exclude_unset=True)

    # 处理 tags 字段（从 List 转为 JSON 字符串存储）
    if 'tags' in update_data:
        update_data['tags'] = json.dumps(update_data['tags'], ensure_ascii=False)

    # 如果提供了 markdown_content，更新 markdown 文件
    if 'markdown_content' in update_data:
        content = update_data.pop('markdown_content')
        if article.markdown_file:
            try:
                with open(article.markdown_file, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to write markdown file: {str(e)}")

    # 更新其他字段
    for field, value in update_data.items():
        setattr(article, field, value)

    db.commit()
    db.refresh(article)
    return article
```

- [ ] **Step 2: Test the new endpoint**

Run: `cd backend && python -c "from app.routers.articles import router; print('Import OK')"`
Expected: Import OK (no errors)

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/articles.py
git commit -m "feat(backend): add PUT endpoint for article updates"
```

---

## Task 2: Frontend API - Add updateArticle

**Files:**
- Modify: `frontend/src/api/index.ts`

- [ ] **Step 1: Add updateArticle API function**

Add after line 49 (after `batchDeleteArticles`):

```typescript
// Articles - update
export const updateArticle = (id: number, data: {
  title?: string;
  author?: string;
  summary?: string;
  markdown_content?: string;
  cover_image?: string;
  tags?: string[];
}) => api.put(`/articles/${id}`, data)
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/index.ts
git commit -m "feat(api): add updateArticle function"
```

---

## Task 3: Frontend - Install Markdown Editor Package

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 1: Install @uiw/react-md-editor**

Run: `cd frontend && npm install @uiw/react-md-editor`
Expected: Package installed successfully

- [ ] **Step 2: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "feat(deps): add @uiw/react-md-editor for article editing"
```

---

## Task 4: Frontend - Add Edit Route

**Files:**
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Import Edit component and add route**

Change line 7 to add Edit import:
```typescript
import Articles, { Edit as ArticleEdit } from './pages/Articles'
```

Add new route after `/articles` route:
```typescript
<Route path="/articles/edit/:id" element={<ArticleEdit />} />
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat(routing): add article edit route"
```

---

## Task 5: Frontend - Create Edit Page

**Files:**
- Create: `frontend/src/pages/Articles/Edit.tsx`
- Modify: `frontend/src/pages/Articles/index.tsx:160-164`

- [ ] **Step 1: Create Edit.tsx with full article edit form**

```tsx
import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Form, Input, Button, message, Space, Select, Breadcrumb } from 'antd'
import { ArrowLeftOutlined, SaveOutlined } from '@ant-design/icons'
import '@uiw/react-md-editor/markdown-editor.css'
import '@uiw/react-md-editor/markdown.css'
import { getArticle, getArticleMarkdown, updateArticle, getTags } from '../../api'
import MDEditor from '@uiw/react-md-editor'

const { TextArea } = Input

export function Edit() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [form] = Form.useForm()
  const [markdownContent, setMarkdownContent] = useState('')
  const [availableTags, setAvailableTags] = useState<string[]>([])

  useEffect(() => {
    // Load article data and tags in parallel
    Promise.all([
      getArticle(Number(id)),
      getArticleMarkdown(Number(id)),
      getTags()
    ]).then(([articleRes, markdownRes, tagsRes]) => {
      const article = articleRes.data
      form.setFieldsValue({
        title: article.title,
        author: article.author,
        summary: article.summary,
        cover_image: article.cover_image,
        tags: article.tags || []
      })
      setMarkdownContent(markdownRes.data.content || '')
      const tagNames = (tagsRes.data || []).map((t: any) => t.name)
      setAvailableTags(tagNames)
    }).catch(() => {
      message.error('加载文章失败')
      navigate('/articles')
    })
  }, [id])

  const handleSave = async () => {
    try {
      const values = await form.validateFields()
      setSaving(true)
      await updateArticle(Number(id), {
        ...values,
        markdown_content: markdownContent
      })
      message.success('保存成功')
      navigate('/articles')
    } catch (error: any) {
      if (error.errorFields) {
        message.error('请检查表单必填项')
      } else {
        message.error('保存失败')
      }
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <Breadcrumb
        items={[
          { title: <a onClick={() => navigate('/articles')}>文章管理</a> },
          { title: '编辑文章' }
        ]}
        style={{ marginBottom: 16 }}
      />

      <Card>
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            title: '',
            author: '',
            summary: '',
            cover_image: '',
            tags: []
          }}
        >
          <Form.Item
            name="title"
            label="标题"
            rules={[{ required: true, message: '请输入标题' }]}
          >
            <Input placeholder="文章标题" maxLength={500} />
          </Form.Item>

          <Form.Item name="author" label="作者">
            <Input placeholder="作者" maxLength={255} style={{ width: 200 }} />
          </Form.Item>

          <Form.Item name="cover_image" label="封面图片">
            <Input placeholder="封面图片 URL" style={{ width: 400 }} />
          </Form.Item>

          <Form.Item name="summary" label="摘要">
            <TextArea placeholder="文章摘要" rows={3} />
          </Form.Item>

          <Form.Item name="tags" label="标签">
            <Select
              mode="multiple"
              placeholder="选择标签"
              style={{ width: 300 }}
              options={availableTags.map(t => ({ label: t, value: t }))}
            />
          </Form.Item>

          <Form.Item label="正文">
            <div data-color-mode="light">
              <MDEditor
                value={markdownContent}
                onChange={setMarkdownContent}
                height={400}
                preview="edit"
              />
            </div>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button
                icon={<ArrowLeftOutlined />}
                onClick={() => navigate('/articles')}
              >
                取消
              </Button>
              <Button
                type="primary"
                icon={<SaveOutlined />}
                loading={saving}
                onClick={handleSave}
              >
                保存
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default Edit
```

- [ ] **Step 2: Add export to Articles index.tsx**

Change line 7 from:
```typescript
import Articles from './pages/Articles'
```
to:
```typescript
import Articles, { Edit as ArticleEdit } from './pages/Articles'
```

And export ArticleEdit in App.tsx (already done in Task 4).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Articles/Edit.tsx frontend/src/pages/Articles/index.tsx
git commit -m "feat(articles): add article edit page with markdown editor"
```

---

## Task 6: Frontend - Add Edit Button to Articles List

**Files:**
- Modify: `frontend/src/pages/Articles/index.tsx:160-164`

- [ ] **Step 1: Add edit button to table columns**

Add useNavigate import from react-router-dom:
```typescript
import { useNavigate } from 'react-router-dom'
```

Add EditOutlined import from @ant-design/icons (line 3):
```typescript
import { EyeOutlined, DeleteOutlined, EditOutlined, SearchOutlined } from '@ant-design/icons'
```

Initialize navigate in the component:
```typescript
const navigate = useNavigate()
```

Add edit action column after the existing actions column:
```typescript
{
  title: '操作',
  key: 'action',
  width: 150,
  render: (_: any, record: any) => (
    <Space>
      <Button type="link" icon={<EditOutlined />} onClick={() => navigate(`/articles/edit/${record.id}`)} />
      <Button type="link" icon={<EyeOutlined />} onClick={() => handlePreview(record.id)} />
    </Space>
  )
}
```

**Note:** Keep the existing actions column and add the Edit button to it (don't create a duplicate column). The existing column already has the EyeOutlined preview button - just add EditOutlined alongside it.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/Articles/index.tsx
git commit -m "feat(articles): add edit button to article list"
```

---

## Task 7: Frontend - Redesign NewsCard

**Files:**
- Modify: `frontend/src/pages/Preview/components/NewsCard.tsx`

- [ ] **Step 1: Rewrite NewsCard with new design**

Replace the entire file content with:

```tsx
import { Card, Tag } from 'antd'
import { Link } from 'react-router-dom'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(relativeTime)

interface NewsCardProps {
  article: {
    id: number
    title: string
    summary: string
    cover_image: string
    rule_name: string
    created_at: string
    tags: string[]
  }
}

export default function NewsCard({ article }: NewsCardProps) {
  const isDarkMode = document.body.classList.contains('dark-mode')

  return (
    <Link to={`/preview/article/${article.id}`} style={{ display: 'block' }}>
      <Card
        hoverable
        style={{
          height: '100%',
          borderRadius: 12,
          overflow: 'hidden',
          transition: 'transform 0.2s, box-shadow 0.2s',
        }}
        styles={{
          body: {
            padding: 0,
            background: isDarkMode ? '#1f1f1f' : '#fff',
          }
        }}
        onMouseEnter={(e) => {
          const card = e.currentTarget as HTMLElement
          card.style.transform = 'translateY(-4px)'
          card.style.boxShadow = isDarkMode ? '0 8px 24px rgba(0,0,0,0.4)' : '0 8px 24px rgba(0,0,0,0.12)'
        }}
        onMouseLeave={(e) => {
          const card = e.currentTarget as HTMLElement
          card.style.transform = 'translateY(0)'
          card.style.boxShadow = 'none'
        }}
      >
        {/* Cover Image with Gradient Overlay */}
        <div style={{ position: 'relative', height: 200, overflow: 'hidden' }}>
          {article.cover_image ? (
            <img
              alt={article.title}
              src={article.cover_image}
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          ) : (
            <div style={{
              width: '100%',
              height: '100%',
              background: isDarkMode ? '#2d2d2d' : '#f0f0f0',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: isDarkMode ? '#666' : '#999'
            }}>
              无封面图
            </div>
          )}

          {/* Gradient overlay */}
          <div style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            height: '60%',
            background: 'linear-gradient(to top, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0) 100%)',
            pointerEvents: 'none'
          }} />

          {/* Tags on image */}
          {article.tags && article.tags.length > 0 && (
            <div style={{
              position: 'absolute',
              top: 12,
              left: 12,
              display: 'flex',
              gap: 6,
              flexWrap: 'wrap'
            }}>
              {article.tags.slice(0, 2).map(tag => (
                <Tag
                  key={tag}
                  style={{
                    borderRadius: 12,
                    background: 'rgba(255,255,255,0.25)',
                    border: 'none',
                    color: '#fff',
                    backdropFilter: 'blur(4px)'
                  }}
                >
                  {tag}
                </Tag>
              ))}
            </div>
          )}

          {/* Source/Time badge */}
          <div style={{
            position: 'absolute',
            bottom: 12,
            right: 12,
            display: 'flex',
            gap: 8,
            alignItems: 'center'
          }}>
            <span style={{
              fontSize: 11,
              color: 'rgba(255,255,255,0.85)',
              background: 'rgba(0,0,0,0.3)',
              padding: '2px 8px',
              borderRadius: 10,
              backdropFilter: 'blur(4px)'
            }}>
              {article.rule_name}
            </span>
          </div>
        </div>

        {/* Content */}
        <div style={{ padding: '16px' }}>
          <h3 style={{
            fontSize: 16,
            fontWeight: 600,
            marginBottom: 8,
            color: isDarkMode ? '#e8e8e8' : 'rgba(0,0,0,0.88)',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
            lineHeight: 1.4,
            minHeight: 44
          }}>
            {article.title}
          </h3>

          {article.summary && (
            <p style={{
              fontSize: 13,
              color: isDarkMode ? '#888' : '#999',
              marginBottom: 8,
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
              lineHeight: 1.5
            }}>
              {article.summary}
            </p>
          )}

          <span style={{
            fontSize: 12,
            color: isDarkMode ? '#666' : '#aaa'
          }}>
            {dayjs(article.created_at).fromNow()}
          </span>
        </div>
      </Card>
    </Link>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/Preview/components/NewsCard.tsx
git commit -m "feat(preview): redesign NewsCard with gradient overlay and badges"
```

---

## Task 8: Frontend - Improve ArticleContent Styling

**Files:**
- Modify: `frontend/src/pages/Preview/components/ArticleContent.tsx`

- [ ] **Step 1: Rewrite with improved styling**

Replace the entire file with:

```tsx
import { Typography } from 'antd'
import ReactMarkdown from 'react-markdown'

const { Title, Text } = Typography

interface ArticleContentProps {
  title: string
  author: string
  publish_time: string
  content: string
  cover_image: string
  tags: string[]
}

export default function ArticleContent({
  title,
  author,
  publish_time,
  content,
  cover_image,
  tags
}: ArticleContentProps) {
  const isDarkMode = document.body.classList.contains('dark-mode')

  return (
    <article style={{
      maxWidth: 800,
      margin: '0 auto',
      padding: '0 16px 60px'
    }}>
      {/* Title */}
      <Title
        level={1}
        style={{
          fontSize: 36,
          fontWeight: 700,
          marginBottom: 16,
          color: isDarkMode ? '#e8e8e8' : 'rgba(0,0,0,0.88)',
          lineHeight: 1.3
        }}
      >
        {title}
      </Title>

      {/* Meta info */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        marginBottom: 20,
        color: isDarkMode ? '#888' : '#666',
        fontSize: 14
      }}>
        {author && (
          <span>
            <Text strong style={{ color: isDarkMode ? '#aaa' : '#333' }}>作者</Text>
            {' '}{author}
          </span>
        )}
        {author && publish_time && <span>·</span>}
        {publish_time && <span>{publish_time}</span>}
      </div>

      {/* Tags */}
      {tags && tags.length > 0 && (
        <div style={{
          display: 'flex',
          gap: 8,
          flexWrap: 'wrap',
          marginBottom: 24
        }}>
          {tags.map(tag => (
            <span
              key={tag}
              style={{
                display: 'inline-block',
                padding: '4px 12px',
                background: isDarkMode ? '#2d2d2d' : '#f0f0f0',
                borderRadius: 16,
                fontSize: 13,
                color: isDarkMode ? '#e8e8e8' : '#333'
              }}
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Cover Image */}
      {cover_image && (
        <img
          src={cover_image}
          alt={title}
          style={{
            width: '100%',
            maxHeight: 400,
            objectFit: 'cover',
            borderRadius: 12,
            marginBottom: 32
          }}
        />
      )}

      {/* Article Body */}
      <div
        className="article-body"
        style={{
          lineHeight: 1.8,
          fontSize: 16,
          color: isDarkMode ? '#d0d0d0' : '#333'
        }}
      >
        <ReactMarkdown>{content}</ReactMarkdown>
      </div>

      <style>{`
        .article-body {
          max-width: 720px;
        }
        .article-body h1 {
          font-size: 1.75em;
          margin-top: 2em;
          margin-bottom: 0.75em;
          font-weight: 600;
          color: inherit;
        }
        .article-body h2 {
          font-size: 1.5em;
          margin-top: 1.75em;
          margin-bottom: 0.6em;
          font-weight: 600;
          color: inherit;
        }
        .article-body h3 {
          font-size: 1.25em;
          margin-top: 1.5em;
          margin-bottom: 0.5em;
          font-weight: 600;
          color: inherit;
        }
        .article-body p {
          margin-bottom: 1.25em;
        }
        .article-body img {
          max-width: 100%;
          height: auto;
          border-radius: 8px;
          margin: 1.5em 0;
        }
        .article-body pre {
          background: ${isDarkMode ? '#1a1a1a' : '#f5f5f5'};
          padding: 16px 20px;
          border-radius: 8px;
          overflow-x: auto;
          margin: 1.5em 0;
        }
        .article-body code {
          font-family: 'Fira Code', 'Monaco', monospace;
          font-size: 0.9em;
        }
        .article-body :not(pre) > code {
          background: ${isDarkMode ? '#2d2d2d' : '#f0f0f0'};
          padding: 2px 6px;
          border-radius: 4px;
        }
        .article-body blockquote {
          border-left: 4px solid ${isDarkMode ? '#555' : '#ddd'};
          padding-left: 20px;
          margin: 1.5em 0;
          color: ${isDarkMode ? '#999' : '#666'};
          font-style: italic;
        }
        .article-body ul, .article-body ol {
          margin: 1em 0;
          padding-left: 1.5em;
        }
        .article-body li {
          margin: 0.5em 0;
        }
        .article-body a {
          color: #1890ff;
          text-decoration: none;
        }
        .article-body a:hover {
          text-decoration: underline;
        }
        .article-body hr {
          border: none;
          border-top: 1px solid ${isDarkMode ? '#333' : '#e8e8e8'};
          margin: 2em 0;
        }
        .article-body table {
          width: 100%;
          border-collapse: collapse;
          margin: 1.5em 0;
        }
        .article-body th, .article-body td {
          border: 1px solid ${isDarkMode ? '#333' : '#e8e8e8'};
          padding: 8px 12px;
          text-align: left;
        }
        .article-body th {
          background: ${isDarkMode ? '#2d2d2d' : '#f5f5f5'};
        }
      `}</style>
    </article>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/Preview/components/ArticleContent.tsx
git commit -m "feat(preview): improve ArticleContent styling and dark mode"
```

---

## Task 9: Frontend - Improve ArticleDetail Page

**Files:**
- Modify: `frontend/src/pages/Preview/ArticleDetail.tsx`

- [ ] **Step 1: Read current file**

First read the current file to understand its structure.

- [ ] **Step 2: Add back button and improve layout**

Based on the spec requirements:
- Add ArrowLeftOutlined button at the top that navigates back
- Ensure max-width is 800px for the content
- Ensure cover image displays at top with max-height 400px

The key improvements are:
1. Wrap content in a container with `maxWidth: 800` and `margin: '0 auto'`
2. Add a back button using `ArrowLeftOutlined` from @ant-design/icons
3. The ArticleContent component (Task 8) handles the internal styling

Example structure:
```tsx
import { Button } from 'antd'
import { ArrowLeftOutlined } from '@ant-design/icons'
// ... existing imports

export default function ArticleDetail() {
  // ... existing logic

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '16px' }}>
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate('/preview')}
        style={{ marginBottom: 16 }}
      >
        返回
      </Button>
      {/* existing article rendering */}
    </div>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Preview/ArticleDetail.tsx
git commit -m "feat(preview): improve ArticleDetail page layout"
```

---

## Task 10: Integration Test

**Files:** None (manual testing)

- [ ] **Step 1: Test article editing flow**

1. Navigate to `/articles`
2. Click edit button on any article
3. Verify edit page loads with correct data
4. Modify a field (e.g., title)
5. Click save
6. Verify redirect to articles list
7. Verify changes are reflected

- [ ] **Step 2: Test preview card redesign**

1. Navigate to `/preview`
2. Verify cards show gradient overlay
3. Verify tags appear on image
4. Verify hover effect works
5. Toggle dark mode and verify colors adapt

- [ ] **Step 3: Test article detail page**

1. Click on any article card
2. Verify cover image displays
3. Verify markdown content is properly styled
4. Verify dark mode works

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Backend PUT endpoint | `articles.py` |
| 2 | Frontend API | `api/index.ts` |
| 3 | Install markdown editor | `package.json` |
| 4 | Add route | `App.tsx` |
| 5 | Create Edit page | `Articles/Edit.tsx` |
| 6 | Edit button | `Articles/index.tsx` |
| 7 | Redesign NewsCard | `NewsCard.tsx` |
| 8 | Improve ArticleContent | `ArticleContent.tsx` |
| 9 | Improve ArticleDetail | `ArticleDetail.tsx` |
| 10 | Integration test | Manual |
