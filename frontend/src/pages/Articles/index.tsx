import { useEffect, useState } from 'react'
import { Table, Tag, Card, Button, Modal, message, Popconfirm } from 'antd'
import { EyeOutlined, DeleteOutlined as BatchDeleteOutlined } from '@ant-design/icons'
import { getArticles, getArticleMarkdown, batchDeleteArticles } from '../../api'
import dayjs from 'dayjs'

export default function Articles() {
  const [loading, setLoading] = useState(false)
  const [articles, setArticles] = useState([])
  const [previewVisible, setPreviewVisible] = useState(false)
  const [markdown, setMarkdown] = useState('')
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([])
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 })

  useEffect(() => {
    loadArticles()
  }, [pagination.current, pagination.pageSize])

  const loadArticles = async () => {
    setLoading(true)
    try {
      const res = await getArticles({
        skip: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize
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

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      success: 'green',
      failed: 'red',
      pending: 'orange',
    }
    return colors[status] || 'default'
  }

  const getSourceTypeTag = (type: string) => {
    const tagMap: Record<string, { color: string; text: string }> = {
      rss: { color: 'orange', text: 'RSS' },
      api: { color: 'blue', text: 'API' },
      playwright: { color: 'green', text: '网页抓取' },
    }
    const tag = tagMap[type] || { color: 'default', text: type || '-' }
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
    { title: '传输方式', dataIndex: 'rule_source_type', key: 'rule_source_type',
      render: (v: string) => getSourceTypeTag(v)
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
