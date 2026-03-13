import { useEffect, useState } from 'react'
import { Table, Tag, Card, Button, Modal, message } from 'antd'
import { EyeOutlined } from '@ant-design/icons'
import { getArticles, getArticleMarkdown } from '../../api'
import dayjs from 'dayjs'

export default function Articles() {
  const [loading, setLoading] = useState(false)
  const [articles, setArticles] = useState([])
  const [previewVisible, setPreviewVisible] = useState(false)
  const [markdown, setMarkdown] = useState('')

  useEffect(() => {
    loadArticles()
  }, [])

  const loadArticles = async () => {
    setLoading(true)
    try {
      const res = await getArticles()
      setArticles(res.data)
    } catch (error) {
      console.error(error)
    } finally {
      setLoading(false)
    }
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

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      success: 'green',
      failed: 'red',
      pending: 'orange',
    }
    return colors[status] || 'default'
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
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
        <Table columns={columns} dataSource={articles} rowKey="id" loading={loading} />
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
