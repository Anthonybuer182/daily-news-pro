# 前端预览服务实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 Daily News Pro 创建前端预览服务，供普通公众用户查看新闻文章

**Architecture:** 在现有 frontend 中新建 `/preview` 路由，使用 React + Ant Design 实现新闻列表和详情页。后端新增 tags 相关接口。

**Tech Stack:** React 18, TypeScript, Vite, Ant Design 5, FastAPI, SQLAlchemy

---

## 文件结构

### 后端新增/修改
```
backend/app/models/article.py          # 新增 tags 字段
backend/app/routers/articles.py       # 新增 /tags 接口
backend/app/schemas/article.py        # 新增 tags 字段
sql_scripts.sql                       # 新增 tags 字段
```

### 前端新增
```
frontend/src/pages/Preview/
├── index.tsx                         # 预览首页
├── ArticleDetail.tsx                 # 文章详情页
├── components/
│   ├── Header.tsx                   # 顶部导航栏
│   ├── SourceTabs.tsx               # 来源 Tab 切换
│   ├── TimeFilter.tsx               # 时间筛选
│   ├── TagFilter.tsx                # 标签筛选
│   ├── SearchBar.tsx                # 搜索输入框
│   ├── NewsCard.tsx                 # 新闻卡片
│   ├── NewsList.tsx                 # 无限滚动列表
│   └── ArticleContent.tsx            # 文章正文渲染
├── hooks/
│   └── useArticles.ts                # 文章数据 hook
└── context/
    └── FilterContext.tsx             # 筛选状态管理
```

### 前端修改
```
frontend/src/App.tsx                  # 添加 /preview 路由
frontend/src/api/index.ts             # 添加 tags 接口调用
frontend/src/main.tsx                 # 添加 PreviewLayout 路由配置
```

---

## Task 1: 后端 - 添加 Article tags 字段

**Files:**
- Modify: `backend/app/models/article.py`
- Modify: `backend/app/schemas/article.py`
- Modify: `sql_scripts.sql`

- [ ] **Step 1: 修改 Article Model 添加 tags 字段**

```python
# backend/app/models/article.py 第 21 行后添加
tags = Column(Text)  # JSON 格式存储标签数组，如 '["AI", "创业"]'
```

- [ ] **Step 2: 修改 Article Schema 添加 tags 字段**

```python
# backend/app/schemas/article.py
class Article(ArticleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    rule_render: Optional[str] = None
    rule_name: Optional[str] = None
    tags: Optional[List[str]] = []  # 新增

    class Config:
        from_attributes = True
```

- [ ] **Step 3: 修改 sql_scripts.sql Articles 表添加 tags 字段**

```sql
-- 在 articles 表的 error_message 字段后添加
tags TEXT,
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/models/article.py backend/app/schemas/article.py sql_scripts.sql
git commit -m "feat: add tags field to Article model"
```

---

## Task 2: 后端 - 添加 Tags 接口

**Files:**
- Modify: `backend/app/routers/articles.py`

- [ ] **Step 1: 添加获取所有标签接口**

在 `backend/app/routers/articles.py` 添加：

```python
@router.get("/tags")
def get_tags(db: Session = Depends(get_db)):
    """获取所有已使用的标签列表"""
    articles = db.query(Article.tags).filter(Article.tags.isnot(None)).all()
    all_tags = set()
    for article in articles:
        if article.tags:
            import json
            try:
                tags_list = json.loads(article.tags)
                if isinstance(tags_list, list):
                    all_tags.update(tags_list)
            except:
                pass
    return list(all_tags)
```

- [ ] **Step 2: 修改 get_articles 接口支持 tags 和 source 筛选**

更新 `backend/app/routers/articles.py` 的 `get_articles` 函数：

```python
@router.get("", response_model=List[ArticleSchema])
def get_articles(
    skip: int = 0,
    limit: int = 20,
    rule_id: int = None,
    status: str = None,
    keyword: str = None,
    start_date: str = None,
    end_date: str = None,
    source: str = None,      # 新增：来源名称筛选
    time_range: str = None,  # 新增：today, week, month
    tags: str = None,        # 新增：逗号分隔的标签列表
    db: Session = Depends(get_db)
):
    query = db.query(Article).options(joinedload(Article.rule))

    # 原有筛选
    if rule_id:
        query = query.filter(Article.rule_id == rule_id)
    if status:
        query = query.filter(Article.status == status)
    if keyword:
        keyword_pattern = f"%{keyword}%"
        query = query.filter(
            (Article.title.ilike(keyword_pattern)) |
            (Article.summary.ilike(keyword_pattern))
        )

    # 来源筛选（通过 rule.name）
    if source:
        query = query.join(Article.rule).filter(Rule.name == source)

    # 时间范围筛选
    if time_range:
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        if time_range == 'today':
            query = query.filter(Article.created_at >= now.replace(hour=0, minute=0, second=0))
        elif time_range == 'week':
            query = query.filter(Article.created_at >= now - timedelta(days=7))
        elif time_range == 'month':
            query = query.filter(Article.created_at >= now - timedelta(days=30))

    # 标签筛选
    if tags:
        for tag in tags.split(','):
            query = query.filter(Article.tags.ilike(f'%"{tag.strip()}"%'))

    if start_date:
        query = query.filter(Article.created_at >= start_date)
    if end_date:
        query = query.filter(Article.created_at <= end_date)

    total = query.count()
    articles = query.order_by(Article.created_at.desc()).offset(skip).limit(limit).all()

    # 添加 rule_render 和 rule_name
    for article in articles:
        if article.rule:
            article.rule_render = article.rule.render
            article.rule_name = article.rule.name

    articles_data = [ArticleSchema.model_validate(article).model_dump(mode='json') for article in articles]
    response = JSONResponse(content=articles_data)
    response.headers["X-Total-Count"] = str(total)
    return response
```

- [ ] **Step 3: 添加 Rule import**

在文件顶部添加：
```python
from app.models import Article, Rule
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/routers/articles.py
git commit -m "feat: add tags endpoint and advanced filters to articles API"
```

---

## Task 3: 前端 - API 扩展

**Files:**
- Modify: `frontend/src/api/index.ts`

- [ ] **Step 1: 添加 tags 接口和扩展 getArticles**

```typescript
// frontend/src/api/index.ts 第 33 行后添加

// Articles - 扩展现有接口
export const getArticles = (params?: {
  skip?: number;
  limit?: number;
  rule_id?: number;
  status?: string;
  keyword?: string;
  start_date?: string;
  end_date?: string;
  source?: string;       // 来源名称
  time_range?: string;   // today, week, month
  tags?: string;         // 逗号分隔的标签列表
}) => api.get('/articles', { params });

export const getTags = () => api.get('/articles/tags');
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/api/index.ts
git commit -m "feat: add getTags API and extend getArticles with preview filters"
```

---

## Task 4: 前端 - 筛选状态管理

**Files:**
- Create: `frontend/src/pages/Preview/context/FilterContext.tsx`

- [ ] **Step 1: 创建 FilterContext**

```typescript
// frontend/src/pages/Preview/context/FilterContext.tsx
import { createContext, useContext, useState, ReactNode } from 'react';

export interface PreviewFilter {
  source: string;      // 来源（空=全部）
  timeRange: '' | 'today' | 'week' | 'month';
  tags: string[];      // 选中标签
  keyword: string;     // 搜索关键词
}

interface FilterContextType {
  filter: PreviewFilter;
  setFilter: (filter: PreviewFilter) => void;
  resetFilter: () => void;
}

const defaultFilter: PreviewFilter = {
  source: '',
  timeRange: '',
  tags: [],
  keyword: '',
};

const FilterContext = createContext<FilterContextType | undefined>(undefined);

export function FilterProvider({ children }: { children: ReactNode }) {
  const [filter, setFilter] = useState<PreviewFilter>(defaultFilter);

  const resetFilter = () => setFilter(defaultFilter);

  return (
    <FilterContext.Provider value={{ filter, setFilter, resetFilter }}>
      {children}
    </FilterContext.Provider>
  );
}

export function useFilter() {
  const context = useContext(FilterContext);
  if (!context) {
    throw new Error('useFilter must be used within FilterProvider');
  }
  return context;
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/pages/Preview/context/FilterContext.tsx
git commit -m "feat: add FilterContext for preview page state management"
```

---

## Task 5: 前端 - useArticles Hook

**Files:**
- Create: `frontend/src/pages/Preview/hooks/useArticles.ts`

- [ ] **Step 1: 创建 useArticles Hook**

```typescript
// frontend/src/pages/Preview/hooks/useArticles.ts
import { useState, useEffect, useCallback } from 'react';
import { getArticles } from '../../api';
import { useFilter, PreviewFilter } from '../context/FilterContext';

interface Article {
  id: number;
  title: string;
  summary: string;
  cover_image: string;
  url: string;
  author: string;
  publish_time: string;
  created_at: string;
  rule_name: string;
  tags: string[];
}

interface UseArticlesResult {
  articles: Article[];
  loading: boolean;
  loadingMore: boolean;
  hasMore: boolean;
  loadMore: () => void;
  refresh: () => void;
  total: number;
}

export function useArticles(): UseArticlesResult {
  const { filter } = useFilter();
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [skip, setSkip] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [total, setTotal] = useState(0);
  const LIMIT = 20;

  const buildParams = useCallback((offset: number) => {
    const params: any = {
      skip: offset,
      limit: LIMIT,
      status: 'success',
    };
    if (filter.keyword) params.keyword = filter.keyword;
    if (filter.source) params.source = filter.source;
    if (filter.timeRange) params.time_range = filter.timeRange;
    if (filter.tags.length > 0) params.tags = filter.tags.join(',');
    return params;
  }, [filter]);

  const loadArticles = useCallback(async (offset: number, isLoadMore = false) => {
    if (isLoadMore) {
      setLoadingMore(true);
    } else {
      setLoading(true);
    }

    try {
      const res = await getArticles(buildParams(offset));
      const newArticles = res.data;
      const totalCount = parseInt(res.headers['x-total-count'] || '0');

      if (isLoadMore) {
        setArticles(prev => [...prev, ...newArticles]);
      } else {
        setArticles(newArticles);
      }

      setTotal(totalCount);
      setHasMore(offset + newArticles.length < totalCount);
      setSkip(offset + newArticles.length);
    } catch (error) {
      console.error('Failed to load articles:', error);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, [buildParams]);

  useEffect(() => {
    setSkip(0);
    setHasMore(true);
    loadArticles(0);
  }, [filter]);

  const loadMore = useCallback(() => {
    if (!loadingMore && hasMore) {
      loadArticles(skip, true);
    }
  }, [loadArticles, skip, loadingMore, hasMore]);

  const refresh = useCallback(() => {
    setSkip(0);
    setHasMore(true);
    loadArticles(0);
  }, [loadArticles]);

  return { articles, loading, loadingMore, hasMore, loadMore, refresh, total };
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/pages/Preview/hooks/useArticles.ts
git commit -m "feat: add useArticles hook for preview page"
```

---

## Task 6: 前端 - 预览首页组件 (Header, SourceTabs, TimeFilter, TagFilter, SearchBar)

**Files:**
- Create: `frontend/src/pages/Preview/components/Header.tsx`
- Create: `frontend/src/pages/Preview/components/SourceTabs.tsx`
- Create: `frontend/src/pages/Preview/components/TimeFilter.tsx`
- Create: `frontend/src/pages/Preview/components/TagFilter.tsx`
- Create: `frontend/src/pages/Preview/components/SearchBar.tsx`

- [ ] **Step 1: 创建 Header 组件**

```typescript
// frontend/src/pages/Preview/components/Header.tsx
import { useState } from 'react';
import { Layout, Input, Button, Tooltip } from 'antd';
import { SearchOutlined, BgColorsOutlined } from '@ant-design/icons';
import { Link } from 'react-router-dom';

const { Header: AntHeader } = Layout;

interface HeaderProps {
  keyword: string;
  onKeywordChange: (keyword: string) => void;
  onSearch: () => void;
}

export default function Header({ keyword, onKeywordChange, onSearch }: HeaderProps) {
  const [darkMode, setDarkMode] = useState(false);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    document.body.classList.toggle('dark-mode', !darkMode);
  };

  return (
    <AntHeader style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      background: '#001529',
      padding: '0 24px'
    }}>
      <Link to="/preview" style={{ color: '#fff', fontSize: 18, fontWeight: 'bold' }}>
        Daily News
      </Link>

      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <Input
          placeholder="搜索新闻..."
          value={keyword}
          onChange={e => onKeywordChange(e.target.value)}
          onPressEnter={onSearch}
          style={{ width: 200 }}
          allowClear
        />
        <Tooltip title="深色模式">
          <Button
            type="text"
            icon={<BgColorsOutlined />}
            onClick={toggleDarkMode}
            style={{ color: '#fff' }}
          />
        </Tooltip>
      </div>
    </AntHeader>
  );
}
```

- [ ] **Step 2: 创建 SourceTabs 组件**

```typescript
// frontend/src/pages/Preview/components/SourceTabs.tsx
import { Tabs } from 'antd';
import { useFilter } from '../context/FilterContext';

interface SourceTabsProps {
  sources: string[];
}

export default function SourceTabs({ sources }: SourceTabsProps) {
  const { filter, setFilter } = useFilter();

  const tabs = [
    { key: '', label: '全部' },
    ...sources.map(source => ({ key: source, label: source }))
  ];

  const handleChange = (key: string) => {
    setFilter({ ...filter, source: key });
  };

  return (
    <Tabs
      activeKey={filter.source}
      onChange={handleChange}
      items={tabs}
      style={{ marginBottom: 0 }}
    />
  );
}
```

- [ ] **Step 3: 创建 TimeFilter 组件**

```typescript
// frontend/src/pages/Preview/components/TimeFilter.tsx
import { Radio } from 'antd';
import { useFilter } from '../context/FilterContext';

export default function TimeFilter() {
  const { filter, setFilter } = useFilter();

  const options = [
    { value: '', label: '全部' },
    { value: 'today', label: '当天' },
    { value: 'week', label: '本周' },
    { value: 'month', label: '当月' },
  ];

  return (
    <Radio.Group
      value={filter.timeRange}
      onChange={e => setFilter({ ...filter, timeRange: e.target.value })}
      options={options}
      optionType="button"
      buttonStyle="solid"
    />
  );
}
```

- [ ] **Step 4: 创建 TagFilter 组件**

```typescript
// frontend/src/pages/Preview/components/TagFilter.tsx
import { Tag } from 'antd';
import { useFilter } from '../context/FilterContext';

interface TagFilterProps {
  availableTags: string[];
}

export default function TagFilter({ availableTags }: TagFilterProps) {
  const { filter, setFilter } = useFilter();

  const toggleTag = (tag: string) => {
    const newTags = filter.tags.includes(tag)
      ? filter.tags.filter(t => t !== tag)
      : [...filter.tags, tag];
    setFilter({ ...filter, tags: newTags });
  };

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
      {availableTags.map(tag => (
        <Tag
          key={tag}
          color={filter.tags.includes(tag) ? 'blue' : 'default'}
          onClick={() => toggleTag(tag)}
          style={{ cursor: 'pointer' }}
        >
          {tag}
        </Tag>
      ))}
    </div>
  );
}
```

- [ ] **Step 5: 创建 SearchBar 组件**

```typescript
// frontend/src/pages/Preview/components/SearchBar.tsx
import { Input } from 'antd';
import { SearchOutlined } from '@ant-design/icons';

interface SearchBarProps {
  keyword: string;
  onChange: (keyword: string) => void;
  onSearch: () => void;
}

export default function SearchBar({ keyword, onChange, onSearch }: SearchBarProps) {
  return (
    <Input
      placeholder="搜索文章标题或摘要..."
      prefix={<SearchOutlined />}
      value={keyword}
      onChange={e => onChange(e.target.value)}
      onPressEnter={onSearch}
      allowClear
      size="large"
    />
  );
}
```

- [ ] **Step 6: 提交**

```bash
git add frontend/src/pages/Preview/components/Header.tsx
git add frontend/src/pages/Preview/components/SourceTabs.tsx
git add frontend/src/pages/Preview/components/TimeFilter.tsx
git add frontend/src/pages/Preview/components/TagFilter.tsx
git add frontend/src/pages/Preview/components/SearchBar.tsx
git commit -m "feat: add preview page filter components (Header, SourceTabs, TimeFilter, TagFilter, SearchBar)"
```

---

## Task 7: 前端 - NewsCard 和 NewsList 组件

**Files:**
- Create: `frontend/src/pages/Preview/components/NewsCard.tsx`
- Create: `frontend/src/pages/Preview/components/NewsList.tsx`

- [ ] **Step 1: 创建 NewsCard 组件**

```typescript
// frontend/src/pages/Preview/components/NewsCard.tsx
import { Card, Tag, Typography } from 'antd';
import { Link } from 'react-router-dom';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);

const { Text } = Typography;

interface NewsCardProps {
  article: {
    id: number;
    title: string;
    summary: string;
    cover_image: string;
    rule_name: string;
    created_at: string;
    tags: string[];
  };
}

export default function NewsCard({ article }: NewsCardProps) {
  return (
    <Link to={`/preview/article/${article.id}`}>
      <Card
        hoverable
        cover={article.cover_image && <img alt={article.title} src={article.cover_image} style={{ height: 160, objectFit: 'cover' }} />}
        style={{ height: '100%' }}
      >
        <Card.Meta
          title={article.title}
          description={
            <>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {article.rule_name} · {dayjs(article.created_at).fromNow()}
              </Text>
              {article.summary && (
                <p style={{ marginTop: 8, color: '#666', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                  {article.summary}
                </p>
              )}
              {article.tags && article.tags.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  {article.tags.slice(0, 3).map(tag => (
                    <Tag key={tag} style={{ marginBottom: 4 }}>{tag}</Tag>
                  ))}
                </div>
              )}
            </>
          }
        />
      </Card>
    </Link>
  );
}
```

- [ ] **Step 2: 创建 NewsList 组件**

```typescript
// frontend/src/pages/Preview/components/NewsList.tsx
import { useEffect, useRef } from 'react';
import { Row, Col, Spin } from 'antd';
import NewsCard from './NewsCard';
import { useArticles } from '../hooks/useArticles';

interface NewsListProps {
  onTotalChange: (total: number) => void;
}

export default function NewsList({ onTotalChange }: NewsListProps) {
  const { articles, loading, loadingMore, hasMore, loadMore, total } = useArticles();
  const observerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    onTotalChange(total);
  }, [total, onTotalChange]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting && hasMore && !loadingMore) {
          loadMore();
        }
      },
      { threshold: 0.1 }
    );

    if (observerRef.current) {
      observer.observe(observerRef.current);
    }

    return () => observer.disconnect();
  }, [hasMore, loadingMore, loadMore]);

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 50 }}><Spin size="large" /></div>;
  }

  if (articles.length === 0) {
    return <div style={{ textAlign: 'center', padding: 50, color: '#999' }}>暂无新闻</div>;
  }

  return (
    <div>
      <Row gutter={[16, 16]}>
        {articles.map(article => (
          <Col key={article.id} xs={24} sm={12} md={8} lg={6}>
            <NewsCard article={article} />
          </Col>
        ))}
      </Row>
      <div ref={observerRef} style={{ textAlign: 'center', padding: 20 }}>
        {loadingMore && <Spin />}
        {!hasMore && articles.length > 0 && (
          <span style={{ color: '#999' }}>没有更多了</span>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/pages/Preview/components/NewsCard.tsx
git add frontend/src/pages/Preview/components/NewsList.tsx
git commit -m "feat: add NewsCard and NewsList components with infinite scroll"
```

---

## Task 8: 前端 - 预览首页

**Files:**
- Create: `frontend/src/pages/Preview/index.tsx`

- [ ] **Step 1: 创建预览首页**

```typescript
// frontend/src/pages/Preview/index.tsx
import { useState, useEffect } from 'react';
import { Layout, Card } from 'antd';
import Header from './components/Header';
import SourceTabs from './components/SourceTabs';
import TimeFilter from './components/TimeFilter';
import TagFilter from './components/TagFilter';
import NewsList from './components/NewsList';
import { FilterProvider, useFilter } from './context/FilterContext';
import { getRules, getTags } from '../../api';

const { Content } = Layout;

function PreviewContent() {
  const { filter, setFilter } = useFilter();
  const [sources, setSources] = useState<string[]>([]);
  const [availableTags, setAvailableTags] = useState<string[]>([]);
  const [total, setTotal] = useState(0);
  const [keyword, setKeyword] = useState('');

  useEffect(() => {
    // 加载来源列表
    getRules().then(res => {
      const names = res.data.map((r: any) => r.name).filter(Boolean);
      setSources([...new Set(names)]);
    });

    // 加载标签列表
    getTags().then(res => {
      setAvailableTags(res.data || []);
    });
  }, []);

  const handleSearch = () => {
    setFilter({ ...filter, keyword });
  };

  const handleKeywordChange = (value: string) => {
    setKeyword(value);
    if (!value) {
      setFilter({ ...filter, keyword: '' });
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        keyword={keyword}
        onKeywordChange={handleKeywordChange}
        onSearch={handleSearch}
      />
      <Content style={{ padding: 24 }}>
        <Card style={{ marginBottom: 16 }}>
          <SourceTabs sources={sources} />
        </Card>
        <Card style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
            <span style={{ fontWeight: 500 }}>时间:</span>
            <TimeFilter />
            <span style={{ fontWeight: 500, marginLeft: 16 }}>标签:</span>
            <TagFilter availableTags={availableTags} />
          </div>
        </Card>
        <div style={{ marginBottom: 16, color: '#666' }}>
          共 {total} 篇新闻
        </div>
        <NewsList onTotalChange={setTotal} />
      </Content>
    </Layout>
  );
}

export default function Preview() {
  return (
    <FilterProvider>
      <PreviewContent />
    </FilterProvider>
  );
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/pages/Preview/index.tsx
git commit -m "feat: add preview homepage with filters and news list"
```

---

## Task 9: 前端 - 文章详情页

**Files:**
- Create: `frontend/src/pages/Preview/ArticleDetail.tsx`
- Create: `frontend/src/pages/Preview/components/ArticleContent.tsx`

- [ ] **Step 1: 创建 ArticleContent 组件**

```typescript
// frontend/src/pages/Preview/components/ArticleContent.tsx
import { Typography } from 'antd';
import ReactMarkdown from 'react-markdown';

const { Title, Text } = Typography;

interface ArticleContentProps {
  title: string;
  author: string;
  publish_time: string;
  content: string;
  cover_image: string;
  tags: string[];
}

export default function ArticleContent({
  title,
  author,
  publish_time,
  content,
  cover_image,
  tags
}: ArticleContentProps) {
  return (
    <article style={{ maxWidth: 800, margin: '0 auto', padding: '0 16px' }}>
      <Title level={2} style={{ marginBottom: 8 }}>{title}</Title>

      <div style={{ color: '#666', marginBottom: 16 }}>
        {author && <span>作者: {author}</span>}
        {author && publish_time && <span> · </span>}
        {publish_time && <span>{publish_time}</span>}
      </div>

      {tags && tags.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          {tags.map(tag => (
            <span key={tag} style={{
              display: 'inline-block',
              padding: '2px 8px',
              marginRight: 8,
              background: '#f0f0f0',
              borderRadius: 4,
              fontSize: 12
            }}>
              {tag}
            </span>
          ))}
        </div>
      )}

      {cover_image && (
        <img
          src={cover_image}
          alt={title}
          style={{ maxWidth: '100%', marginBottom: 24, borderRadius: 8 }}
        />
      )}

      <div className="article-body" style={{ lineHeight: 1.8 }}>
        <ReactMarkdown>{content}</ReactMarkdown>
      </div>

      <style>{`
        .article-body h1 { font-size: 1.5em; margin-top: 1.5em; margin-bottom: 0.5em; }
        .article-body h2 { font-size: 1.3em; margin-top: 1.5em; margin-bottom: 0.5em; }
        .article-body h3 { font-size: 1.1em; margin-top: 1.5em; margin-bottom: 0.5em; }
        .article-body p { margin-bottom: 1em; }
        .article-body img { max-width: 100%; height: auto; }
        .article-body pre { background: #f5f5f5; padding: 16px; border-radius: 4px; overflow-x: auto; }
        .article-body code { background: #f5f5f5; padding: 2px 6px; border-radius: 2px; }
        .article-body blockquote { border-left: 4px solid #ddd; padding-left: 16px; margin-left: 0; color: #666; }
        .dark-mode .article-body pre { background: #2d2d2d; }
        .dark-mode .article-body code { background: #2d2d2d; }
        .dark-mode .article-body blockquote { border-color: #555; }
      `}</style>
    </article>
  );
}
```

- [ ] **Step 2: 创建 ArticleDetail 页面**

```typescript
// frontend/src/pages/Preview/ArticleDetail.tsx
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Layout, Button, Tooltip, Spin, message } from 'antd';
import { ArrowLeftOutlined, BgColorsOutlined, LinkOutlined } from '@ant-design/icons';
import { getArticle, getArticleMarkdown } from '../../api';
import ArticleContent from './components/ArticleContent';

const { Header, Content } = Layout;

export default function ArticleDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [article, setArticle] = useState<any>(null);
  const [markdown, setMarkdown] = useState('');
  const [loading, setLoading] = useState(true);
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    if (!id) return;

    const loadArticle = async () => {
      setLoading(true);
      try {
        const [articleRes, markdownRes] = await Promise.all([
          getArticle(parseInt(id)),
          getArticleMarkdown(parseInt(id))
        ]);
        setArticle(articleRes.data);
        setMarkdown(markdownRes.data.content || '');
      } catch (error) {
        message.error('加载文章失败');
        navigate('/preview');
      } finally {
        setLoading(false);
      }
    };

    loadArticle();
  }, [id, navigate]);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    document.body.classList.toggle('dark-mode', !darkMode);
  };

  if (loading) {
    return (
      <Layout style={{ minHeight: '100vh' }}>
        <Content style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <Spin size="large" />
        </Content>
      </Layout>
    );
  }

  if (!article) {
    return null;
  }

  // 解析 tags
  let tags: string[] = [];
  if (article.tags) {
    try {
      tags = typeof article.tags === 'string' ? JSON.parse(article.tags) : article.tags;
    } catch {
      tags = [];
    }
  }

  return (
    <Layout style={{ minHeight: '100vh', background: darkMode ? '#141414' : '#fff' }}>
      <Header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: darkMode ? '#1f1f1f' : '#001529',
        padding: '0 24px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/preview')}
            style={{ color: '#fff' }}
          >
            返回
          </Button>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Tooltip title="深色模式">
            <Button
              type="text"
              icon={<BgColorsOutlined />}
              onClick={toggleDarkMode}
              style={{ color: '#fff' }}
            />
          </Tooltip>
          {article.url && (
            <Tooltip title="查看原文">
              <Button
                type="text"
                icon={<LinkOutlined />}
                onClick={() => window.open(article.url, '_blank')}
                style={{ color: '#fff' }}
              />
            </Tooltip>
          )}
        </div>
      </Header>
      <Content style={{ padding: '24px 0' }}>
        <ArticleContent
          title={article.title}
          author={article.author}
          publish_time={article.publish_time}
          content={markdown}
          cover_image={article.cover_image}
          tags={tags}
        />
      </Content>
    </Layout>
  );
}
```

- [ ] **Step 3: 安装 react-markdown**

```bash
cd frontend && npm install react-markdown
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/pages/Preview/ArticleDetail.tsx
git add frontend/src/pages/Preview/components/ArticleContent.tsx
git commit -m "feat: add article detail page with markdown rendering"
```

---

## Task 10: 前端 - 路由配置

**Files:**
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 修改 App.tsx 添加预览路由**

```typescript
// frontend/src/App.tsx
import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from 'antd'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Rules from './pages/Rules'
import Jobs from './pages/Jobs'
import Articles from './pages/Articles'
import Preview from './pages/Preview'
import ArticleDetail from './pages/Preview/ArticleDetail'

const { Content } = Layout

function App() {
  return (
    <Routes>
      {/* 管理后台 */}
      <Route path="/" element={
        <Layout style={{ minHeight: '100vh' }}>
          <Sidebar />
          <Layout>
            <Content style={{ margin: '16px', padding: '24px', background: '#fff' }}>
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/rules" element={<Rules />} />
                <Route path="/jobs" element={<Jobs />} />
                <Route path="/articles" element={<Articles />} />
              </Routes>
            </Content>
          </Layout>
        </Layout>
      } />

      {/* 预览服务 */}
      <Route path="/preview" element={<Preview />} />
      <Route path="/preview/article/:id" element={<ArticleDetail />} />
    </Routes>
  )
}

export default App
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/App.tsx
git commit -m "feat: add preview routes to App"
```

---

## Task 11: 集成测试

- [ ] **Step 1: 启动后端服务**

```bash
cd backend && python -m uvicorn app.main:app --reload
```

- [ ] **Step 2: 启动前端服务**

```bash
cd frontend && npm run dev
```

- [ ] **Step 3: 测试预览首页**

访问 `http://localhost:5173/preview`:
- [ ] 检查来源 Tabs 是否正常显示
- [ ] 检查时间筛选是否正常切换
- [ ] 检查标签筛选是否正常
- [ ] 检查搜索功能
- [ ] 检查无限滚动加载

- [ ] **Step 4: 测试文章详情页**

点击任意文章:
- [ ] 检查文章内容是否正确显示
- [ ] 检查 Markdown 渲染
- [ ] 检查深色模式切换
- [ ] 检查原文链接跳转

- [ ] **Step 5: 提交**

```bash
git add -A
git commit -m "test: verify preview service functionality"
```

---

## 总结

完成以上任务后，前端预览服务将具备以下功能：

1. **预览首页** (`/preview`)
   - 来源 Tabs 筛选
   - 时间范围筛选（全部/当天/本周/当月）
   - 标签筛选（多选）
   - 关键词搜索
   - 无限滚动加载

2. **文章详情页** (`/preview/article/:id`)
   - 干净的阅读视图
   - 深色模式切换
   - 原文链接跳转
   - Markdown 内容渲染

3. **后端接口**
   - `GET /api/articles/tags` - 获取所有标签
   - `GET /api/articles` - 支持 source, time_range, tags 参数
