import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Table, Tag, Card, Button, Modal, message, Popconfirm, Form, Input, DatePicker, Space } from 'antd'
import { EyeOutlined, DeleteOutlined as BatchDeleteOutlined, SearchOutlined, EditOutlined } from '@ant-design/icons'
import { getArticles, getArticleMarkdown, batchDeleteArticles, getTags } from '../../api'
import ArticleContent from '../Preview/components/ArticleContent'
import { Select } from 'antd'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker

export { Edit } from './Edit'

export default function Articles() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [articles, setArticles] = useState<any[]>([])
  const [previewVisible, setPreviewVisible] = useState(false)
  const [previewArticle, setPreviewArticle] = useState<any>(null)
  const [markdown, setMarkdown] = useState('')
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([])
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 })
  const [searchForm] = Form.useForm()
  const [availableTags, setAvailableTags] = useState<string[]>([])
  const [searchParams, setSearchParams] = useState<{
    keyword?: string;
    start_date?: string;
    end_date?: string;
    tags?: string;
  }>({})

  useEffect(() => {
    loadArticles()
  }, [pagination.current, pagination.pageSize, searchParams])

  useEffect(() => {
    getTags().then(res => {
      const tagNames = (res.data || []).map((t: any) => t.name)
      setAvailableTags(tagNames)
    })
  }, [])

  const loadArticles = async () => {
    setLoading(true)
    try {
      const res = await getArticles({
        skip: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize,
        keyword: searchParams.keyword,
        start_date: searchParams.start_date,
        end_date: searchParams.end_date,
        tags: searchParams.tags
      })
      setArticles(res.data)
      const total = res.headers['x-total-count'] || res.data.length
      setPagination(prev => ({ ...prev, total }))
    } catch (error) {
      console.error(error)
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

  const handlePreview = async (id: number) => {
    try {
      // Find the article from the current list
      const article = articles.find(a => a.id === id)
      if (article) {
        setPreviewArticle(article)
      }
      const res = await getArticleMarkdown(id)
      // Strip header lines (Source/Author/Date) and cover image from markdown
      const rawMarkdown = res.data.content || ''
      const cleanedMarkdown = rawMarkdown
        .replace(/^\*\*Source\*\*:.*\n?/gm, '')
        .replace(/^\*\*Author\*\*:.*\n?/gm, '')
        .replace(/^\*\*Date\*\*:.*\n?/gm, '')
        .replace(/^#.*\n?/, '') // Remove title line if it starts with #
        .replace(/^!\[[^\]]*\]\([^)]*\)\n?/gm, '') // Remove ![Cover](url) image
        .replace(/^\n+/, '') // Remove leading newlines
        .trim()
      setMarkdown(cleanedMarkdown)
      setPreviewVisible(true)
    } catch (error) {
      message.error('加载失败')
    }
  }

  const handleBatchDelete = async () => {
    if (selectedRowKeys.length === 0) return
    try {
      await batchDeleteArticles(selectedRowKeys)
      message.success(`成功删除 ${selectedRowKeys.length} 篇文章`)
      setSelectedRowKeys([])
      loadArticles()
    } catch (error) {
      message.error('批量删除失败')
    }
  }

  const handleSearch = (values: any) => {
    setPagination(prev => ({ ...prev, current: 1 }))
    setSearchParams({
      keyword: values.keyword,
      start_date: values.dateRange?.[0]?.format('YYYY-MM-DD'),
      end_date: values.dateRange?.[1]?.format('YYYY-MM-DD'),
      tags: values.tags?.join(',')
    })
  }

  const handleReset = () => {
    searchForm.resetFields()
    setPagination(prev => ({ ...prev, current: 1 }))
    setSearchParams({})
  }

  const renderTags = (tags: string[]) => {
    if (!tags || tags.length === 0) return '-'
    return tags.map(tag => <Tag key={tag} color="blue" style={{ marginBottom: 4 }}>{tag}</Tag>)
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      success: 'green',
      failed: 'red',
      pending: 'orange',
    }
    return colors[status] || 'default'
  }

  const getRenderTag = (render: string) => {
    const tagMap: Record<string, { color: string; text: string }> = {
      http: { color: 'blue', text: 'HTTP' },
      browser: { color: 'green', text: '浏览器' },
    }
    const tag = tagMap[render] || { color: 'default', text: render || '-' }
    return <Tag color={tag.color}>{tag.text}</Tag>
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: '封面', dataIndex: 'cover_image', key: 'cover_image', width: 80,
      render: (v: string) => v ? <img src={v} alt="cover" style={{ width: 60, height: 40, objectFit: 'cover', borderRadius: 4 }} /> : '-'
    },
    { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
    { title: '摘要', dataIndex: 'summary', key: 'summary', ellipsis: true,
      render: (v: string) => v || '-'
    },
    { title: '渲染方式', dataIndex: 'rule_render', key: 'rule_render',
      render: (v: string) => getRenderTag(v)
    },
    { title: '规则', dataIndex: 'rule_name', key: 'rule_name', ellipsis: true,
      render: (v: string) => v || '-'
    },
    { title: '作者', dataIndex: 'author', key: 'author',
      render: (v: string) => v || '-'
    },
    { title: '发布时间', dataIndex: 'publish_time', key: 'publish_time',
      render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '-'
    },
    { title: '来源', dataIndex: 'url', key: 'url', ellipsis: true,
      render: (v: string) => <a href={v} target="_blank" rel="noopener noreferrer">{v}</a>
    },
    { title: '状态', dataIndex: 'status', key: 'status',
      render: (status: string) => <Tag color={getStatusColor(status)}>{status}</Tag>
    },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at',
      render: (v: string) => dayjs(v).format('YYYY-MM-DD HH:mm')
    },
    { title: '标签', dataIndex: 'tags', key: 'tags',
      render: (v: string[]) => renderTags(v)
    },
    { title: '操作', key: 'action', width: 150,
      render: (_: any, record: any) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => navigate(`/articles/edit/${record.id}`)} />
          <Button type="link" icon={<EyeOutlined />} onClick={() => handlePreview(record.id)} />
        </Space>
      )
    },
  ]

  return (
    <div>
      <h1>文章管理</h1>
      <Card>
        <Form
          form={searchForm}
          layout="inline"
          onFinish={handleSearch}
          style={{ marginBottom: 16 }}
        >
          <Form.Item name="keyword" label="关键词">
            <Input placeholder="搜索标题/摘要" style={{ width: 200 }} allowClear />
          </Form.Item>
          <Form.Item name="dateRange" label="创建时间">
            <RangePicker format="YYYY-MM-DD" allowClear />
          </Form.Item>
          <Form.Item name="tags" label="标签">
            <Select
              placeholder="选择标签"
              allowClear
              style={{ width: 150 }}
              mode="multiple"
              maxTagCount={2}
              options={availableTags.map(t => ({ label: t, value: t }))}
            />
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
        <div style={{ marginBottom: 16 }}>
          {selectedRowKeys.length > 0 && (
            <Popconfirm title={`确定删除选中的 ${selectedRowKeys.length} 篇文章吗?`} onConfirm={handleBatchDelete}>
              <Button danger icon={<BatchDeleteOutlined />}>
                批量删除 ({selectedRowKeys.length})
              </Button>
            </Popconfirm>
          )}
        </div>
        <Table
          columns={columns}
          dataSource={articles}
          rowKey="id"
          loading={loading}
          rowSelection={{
            selectedRowKeys,
            onChange: (keys) => setSelectedRowKeys(keys as number[]),
          }}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showSizeChanger: true,
            pageSizeOptions: ['10', '20', '50', '100', '200'],
            showTotal: (total: number) => `共 ${total} 条`
          }}
          onChange={handleTableChange}
        />
      </Card>
      <Modal
        title="文章预览"
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        footer={null}
        width={900}
      >
        {previewArticle && (
          <ArticleContent
            title={previewArticle.title}
            author={previewArticle.author}
            publish_time={previewArticle.publish_time ? dayjs(previewArticle.publish_time).format('YYYY-MM-DD HH:mm') : undefined}
            content={markdown}
            cover_image={previewArticle.cover_image}
            tags={previewArticle.tags || []}
            url={previewArticle.url}
          />
        )}
      </Modal>
    </div>
  )
}
