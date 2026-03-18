import { useEffect, useState } from 'react'
import { Table, Tag, Card, Button, Popconfirm, message } from 'antd'
import { DeleteOutlined as BatchDeleteOutlined } from '@ant-design/icons'
import { getJobs, batchDeleteJobs } from '../../api'
import dayjs from 'dayjs'

export default function Jobs() {
  const [loading, setLoading] = useState(false)
  const [jobs, setJobs] = useState([])
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([])

  useEffect(() => {
    loadJobs()
  }, [])

  const loadJobs = async () => {
    setLoading(true)
    try {
      const res = await getJobs()
      setJobs(res.data)
    } catch (error) {
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleBatchDelete = async () => {
    if (selectedRowKeys.length === 0) return
    try {
      await batchDeleteJobs(selectedRowKeys)
      message.success(`成功删除 ${selectedRowKeys.length} 条任务`)
      setSelectedRowKeys([])
      loadJobs()
    } catch (error) {
      message.error('批量删除失败')
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      success: 'green',
      failed: 'red',
      running: 'blue',
      pending: 'orange',
    }
    return colors[status] || 'default'
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: '规则', dataIndex: 'rule_name', key: 'rule_name', ellipsis: true,
      render: (v: string, record: any) => v || `规则${record.rule_id}`
    },
    { title: '触发类型', dataIndex: 'trigger_type', key: 'trigger_type' },
    { title: '状态', dataIndex: 'status', key: 'status',
      render: (status: string) => <Tag color={getStatusColor(status)}>{status}</Tag>
    },
    { title: '文章数', dataIndex: 'articles_count', key: 'articles_count' },
    { title: '成功', dataIndex: 'success_count', key: 'success_count' },
    { title: '失败', dataIndex: 'failed_count', key: 'failed_count' },
    { title: '开始时间', dataIndex: 'started_at', key: 'started_at',
      render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD HH:mm:ss') : '-'
    },
    { title: '结束时间', dataIndex: 'finished_at', key: 'finished_at',
      render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD HH:mm:ss') : '-'
    },
  ]

  return (
    <div>
      <h1>任务管理</h1>
      <Card>
        <div style={{ marginBottom: 16 }}>
          {selectedRowKeys.length > 0 && (
            <Popconfirm title={`确定删除选中的 ${selectedRowKeys.length} 条任务吗?`} onConfirm={handleBatchDelete}>
              <Button danger icon={<BatchDeleteOutlined />}>
                批量删除 ({selectedRowKeys.length})
              </Button>
            </Popconfirm>
          )}
        </div>
        <Table
          columns={columns}
          dataSource={jobs}
          rowKey="id"
          loading={loading}
          rowSelection={{
            selectedRowKeys,
            onChange: (keys: number[]) => setSelectedRowKeys(keys),
          }}
        />
      </Card>
    </div>
  )
}
