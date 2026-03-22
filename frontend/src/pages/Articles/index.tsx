import { useEffect, useState } from 'react'
import { Table, Tag, Card, Button, Modal, message, Popconfirm, Form, Input, DatePicker, Space } from 'antd'
import { EyeOutlined, DeleteOutlined as BatchDeleteOutlined, SearchOutlined } from '@ant-design/icons'
import { getArticles, getArticleMarkdown, batchDeleteArticles } from '../../api'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker

export default function Articles() {
  const [loading, setLoading] = useState(false)
  const [articles, setArticles] = useState([])
  const [previewVisible, setPreviewVisible] = useState(false)
  const [markdown, setMarkdown] = useState('')
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([])
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 })
  const [searchForm] = Form.useForm()
  const [searchParams, setSearchParams] = useState<{
    keyword?: string;
    start_date?: string;
    end_date?: string;
  }>({})

  useEffect(() => {
    loadArticles()
  }, [pagination.current, pagination.pageSize, searchParams])

  const loadArticles = async () => {
    setLoading(true)
    try {
      const res = await getArticles({
        skip: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize,
        keyword: searchParams.keyword,
        start_date: searchParams.start_date,
        end_date: searchParams.end_date
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
      const res = await getArticleMarkdown(id)
      setMarkdown(res.data.content || '')
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
      end_date: values.dateRange?.[1]?.format('YYYY-MM-DD')
    })
  }

  const handleReset = () => {
    searchForm.resetFields()
    setPagination(prev => ({ ...prev, current: 1 }))
    setSearchParams({})
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
    { title: '传输方式', dataIndex: 'rule_render', key: 'rule_render',
      render: (v: string) => getRenderTag(v)
    },
    { title: '规则', dataIndex: 'rule_name', key: 'rule_name', ellipsis: true,
      render: (v: string) => v || '-'
    },
    { title: '作者', dataIndex: 'author', key: 'author' },
    { title: '来源', dataIndex: 'url', key: 'url', ellipsis: true,
      render: (v: string) => <a href={v} target="_blank" rel="noopener noreferrer">{v}</a>
    },
    { title: '状态', dataIndex: 'status', key: 'status',
      render: (status: string) => <Tag color={getStatusColor(status)}>{status}</Tag>
    },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at',
      render: (v: string) => dayjs(v).format('YYYY-MM-DD HH:mm')
    },
    { title: '操作', key: 'action', width: 120,
      render: (_: any, record: any) => (
        <Button type="link" icon={<EyeOutlined />} onClick={() => handlePreview(record.id)} />
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
        width={800}
      >
        <pre style={{ whiteSpace: 'pre-wrap', maxHeight: '60vh', overflow: 'auto' }}>
          {markdown}
        </pre>
      </Modal>
    </div>
  )
}
