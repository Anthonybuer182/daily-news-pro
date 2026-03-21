import { useEffect, useState } from 'react'
import { Table, Tag, Card, Button, Popconfirm, message, Form, Input, Select, DatePicker, Space } from 'antd'
import { DeleteOutlined as BatchDeleteOutlined, SearchOutlined, PlayCircleOutlined } from '@ant-design/icons'
import { getJobs, batchDeleteJobs, batchRunJobs } from '../../api'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker
const { Option } = Select

export default function Jobs() {
  const [loading, setLoading] = useState(false)
  const [jobs, setJobs] = useState([])
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([])
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 })
  const [searchForm] = Form.useForm()
  const [searchParams, setSearchParams] = useState<{
    keyword?: string;
    status?: string;
    start_date?: string;
    end_date?: string;
  }>({})

  useEffect(() => {
    loadJobs()
  }, [pagination.current, pagination.pageSize, searchParams])

  const loadJobs = async () => {
    setLoading(true)
    try {
      const res = await getJobs({
        skip: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize,
        keyword: searchParams.keyword,
        status: searchParams.status,
        start_date: searchParams.start_date,
        end_date: searchParams.end_date
      })
      setJobs(res.data)
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

  const handleBatchRun = async () => {
    if (selectedRowKeys.length === 0) return
    try {
      await batchRunJobs(selectedRowKeys)
      message.success(`成功创建 ${selectedRowKeys.length} 个抓取任务`)
      setSelectedRowKeys([])
      loadJobs()
    } catch (error) {
      message.error('批量执行失败')
    }
  }

  const handleSearch = (values: any) => {
    setPagination(prev => ({ ...prev, current: 1 }))
    setSearchParams({
      keyword: values.keyword,
      status: values.status,
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
        <Form
          form={searchForm}
          layout="inline"
          onFinish={handleSearch}
          style={{ marginBottom: 16 }}
        >
          <Form.Item name="keyword" label="关键词">
            <Input placeholder="搜索规则名称" style={{ width: 200 }} allowClear />
          </Form.Item>
          <Form.Item name="status" label="状态">
            <Select placeholder="选择状态" style={{ width: 120 }} allowClear>
              <Option value="pending">pending</Option>
              <Option value="running">running</Option>
              <Option value="success">success</Option>
              <Option value="failed">failed</Option>
            </Select>
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
            <>
              <Popconfirm title={`确定执行选中的 ${selectedRowKeys.length} 条任务吗?`} onConfirm={handleBatchRun}>
                <Button type="primary" icon={<PlayCircleOutlined />} style={{ marginRight: 8 }}>
                  批量执行 ({selectedRowKeys.length})
                </Button>
              </Popconfirm>
              <Popconfirm title={`确定删除选中的 ${selectedRowKeys.length} 条任务吗?`} onConfirm={handleBatchDelete}>
                <Button danger icon={<BatchDeleteOutlined />}>
                  批量删除 ({selectedRowKeys.length})
                </Button>
              </Popconfirm>
            </>
          )}
        </div>
        <Table
          columns={columns}
          dataSource={jobs}
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
    </div>
  )
}