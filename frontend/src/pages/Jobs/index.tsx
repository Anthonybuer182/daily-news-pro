import { useEffect, useState } from 'react'
import { Table, Tag, Card } from 'antd'
import { getJobs } from '../../api'
import dayjs from 'dayjs'

export default function Jobs() {
  const [loading, setLoading] = useState(false)
  const [jobs, setJobs] = useState([])

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
    { title: '规则ID', dataIndex: 'rule_id', key: 'rule_id', width: 80 },
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
        <Table columns={columns} dataSource={jobs} rowKey="id" loading={loading} />
      </Card>
    </div>
  )
}
