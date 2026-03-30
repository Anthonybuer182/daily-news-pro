import { useEffect, useState } from 'react'
import { Table, Tag, Card, Form, Select, DatePicker, Space, Button, message, Popconfirm } from 'antd'
import { SearchOutlined, DeleteOutlined } from '@ant-design/icons'
import { getLogs, getJobs, batchDeleteLogs } from '../../api'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker

export default function Logs() {
  const [loading, setLoading] = useState(false)
  const [logs, setLogs] = useState<any[]>([])
  const [jobs, setJobs] = useState<any[]>([])
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([])
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
      current: pag.current || 1,
      pageSize: pag.pageSize || 20
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

  const handleBatchDelete = async () => {
    if (selectedRowKeys.length === 0) return
    try {
      await batchDeleteLogs(selectedRowKeys)
      message.success(`成功删除 ${selectedRowKeys.length} 条日志`)
      setSelectedRowKeys([])
      loadLogs()
    } catch (error) {
      console.error(error)
      message.error('批量删除失败')
    }
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
                <Select.Option key={job.id} value={job.id}>{job.rule_name || `规则${job.rule_id}`}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="level" label="级别">
            <Select placeholder="选择级别" style={{ width: 120 }} allowClear>
              <Select.Option value="error">ERROR</Select.Option>
              <Select.Option value="warning">WARNING</Select.Option>
              <Select.Option value="info">INFO</Select.Option>
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

        <div style={{ marginBottom: 16 }}>
          {selectedRowKeys.length > 0 && (
            <Popconfirm title={`确定删除选中的 ${selectedRowKeys.length} 条日志吗?`} onConfirm={handleBatchDelete}>
              <Button danger icon={<DeleteOutlined />}>
                批量删除 ({selectedRowKeys.length})
              </Button>
            </Popconfirm>
          )}
        </div>

        <Table
          columns={columns}
          dataSource={logs}
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
            pageSizeOptions: ['20', '50', '100', '200'],
            showTotal: (total: number) => `共 ${total} 条`
          }}
          onChange={handleTableChange}
        />
      </Card>
    </div>
  )
}
