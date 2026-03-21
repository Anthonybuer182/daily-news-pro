import { useEffect, useState } from 'react'
import { Table, Button, Space, Tag, message, Popconfirm, Form, Input, Select } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, PlayCircleOutlined, StopOutlined, DeleteOutlined as BatchDeleteOutlined, SearchOutlined } from '@ant-design/icons'
import { getRules, deleteRule, enableRule, disableRule, runRule, batchDeleteRules, batchRunRules } from '../../api'
import RuleModal from './RuleModal'

const { Option } = Select

export default function Rules() {
  const [loading, setLoading] = useState(false)
  const [rules, setRules] = useState([])
  const [modalVisible, setModalVisible] = useState(false)
  const [editingRule, setEditingRule] = useState(null)
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([])
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 })
  const [searchForm] = Form.useForm()
  const [searchParams, setSearchParams] = useState<{
    keyword?: string;
    status?: string;
  }>({})

  useEffect(() => {
    loadRules()
  }, [pagination.current, pagination.pageSize, searchParams])

  const loadRules = async () => {
    setLoading(true)
    try {
      const res = await getRules({
        skip: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize,
        keyword: searchParams.keyword,
        status: searchParams.status
      })
      setRules(res.data)
      const total = res.headers['x-total-count'] || res.data.length
      setPagination(prev => ({ ...prev, total }))
    } catch (error) {
      message.error('加载规则失败')
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

  const handleDelete = async (id: number) => {
    try {
      await deleteRule(id)
      message.success('删除成功')
      loadRules()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleBatchDelete = async () => {
    if (selectedRowKeys.length === 0) return
    try {
      await batchDeleteRules(selectedRowKeys)
      message.success(`成功删除 ${selectedRowKeys.length} 条规则`)
      setSelectedRowKeys([])
      loadRules()
    } catch (error) {
      message.error('批量删除失败')
    }
  }

  const handleBatchRun = async () => {
    if (selectedRowKeys.length === 0) return
    try {
      await batchRunRules(selectedRowKeys)
      message.success(`成功创建 ${selectedRowKeys.length} 个抓取任务`)
    } catch (error) {
      message.error('批量执行失败')
    }
  }

  const handleToggleStatus = async (rule: any) => {
    try {
      if (rule.status === 'enabled') {
        await disableRule(rule.id)
        message.success('已禁用')
      } else {
        await enableRule(rule.id)
        message.success('已启用')
      }
      loadRules()
    } catch (error) {
      message.error('操作失败')
    }
  }

  const handleRun = async (rule: any) => {
    try {
      await runRule(rule.id)
      message.success('任务已创建并开始执行')
    } catch (error) {
      message.error('创建任务失败')
    }
  }

  const handleDeselectAll = () => {
    setSelectedRowKeys([])
  }

  const handleSearch = (values: any) => {
    setPagination(prev => ({ ...prev, current: 1 }))
    setSearchParams({
      keyword: values.keyword,
      status: values.status
    })
  }

  const handleReset = () => {
    searchForm.resetFields()
    setPagination(prev => ({ ...prev, current: 1 }))
    setSearchParams({})
  }

  const getFetchMethodTag = (record: any) => {
    let method = record.fetch_method
    if (!method) {
      method = record.render === 'browser' ? 'playwright' : 'httpx'
    }
    const tagMap: Record<string, { color: string; text: string }> = {
      httpx: { color: 'blue', text: 'HTTP' },
      playwright: { color: 'green', text: '浏览器' },
    }
    const tag = tagMap[method] || { color: 'default', text: method }
    return <Tag color={tag.color}>{tag.text}</Tag>
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: '名称', dataIndex: 'name', key: 'name', ellipsis: true },
    { title: '来源', dataIndex: 'source_url', key: 'source_url', ellipsis: true,
      render: (v: string) => v ? <a href={v} target="_blank" rel="noopener noreferrer">{v}</a> : '-'
    },
    { title: '传输方式', key: 'fetch_method',
      render: (_: any, record: any) => getFetchMethodTag(record)
    },
    { title: '状态', dataIndex: 'status', key: 'status',
      render: (status: string) => (
        <Tag color={status === 'enabled' ? 'green' : 'red'}>{status}</Tag>
      )
    },
    { title: '操作', key: 'action',
      render: (_: any, record: any) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => {
            setEditingRule(record)
            setModalVisible(true)
          }} />
          <Button type="link" icon={<PlayCircleOutlined />} onClick={() => handleRun(record)} />
          <Button type="link" icon={<StopOutlined />} onClick={() => handleToggleStatus(record)} />
          <Popconfirm title="确定删除?" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      )
    },
  ]

  return (
    <div>
      <h1>规则管理</h1>
      <Form
        form={searchForm}
        layout="inline"
        onFinish={handleSearch}
        style={{ marginBottom: 16 }}
      >
        <Form.Item name="keyword" label="关键词">
          <Input placeholder="搜索名称/来源" style={{ width: 200 }} allowClear />
        </Form.Item>
        <Form.Item name="status" label="状态">
          <Select placeholder="选择状态" style={{ width: 120 }} allowClear>
            <Option value="enabled">enabled</Option>
            <Option value="disabled">disabled</Option>
          </Select>
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
        <Button type="primary" icon={<PlusOutlined />} onClick={() => {
          setEditingRule(null)
          setModalVisible(true)
        }}>
          新建规则
        </Button>
        {selectedRowKeys.length > 0 && (
          <Button onClick={handleDeselectAll} style={{ marginLeft: 8 }}>
            取消全选
          </Button>
        )}
        {selectedRowKeys.length > 0 && (
          <>
            <Popconfirm title={`确定执行选中的 ${selectedRowKeys.length} 条规则吗?`} onConfirm={handleBatchRun}>
              <Button type="primary" icon={<PlayCircleOutlined />} style={{ marginLeft: 8 }}>
                批量执行 ({selectedRowKeys.length})
              </Button>
            </Popconfirm>
            <Popconfirm title={`确定删除选中的 ${selectedRowKeys.length} 条规则吗?`} onConfirm={handleBatchDelete}>
              <Button danger icon={<BatchDeleteOutlined />} style={{ marginLeft: 8 }}>
                批量删除 ({selectedRowKeys.length})
              </Button>
            </Popconfirm>
          </>
        )}
      </div>
      <Table
        columns={columns}
        dataSource={rules}
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
      <RuleModal
        visible={modalVisible}
        rule={editingRule}
        onClose={() => {
          setModalVisible(false)
          setEditingRule(null)
        }}
        onSuccess={() => {
          setModalVisible(false)
          loadRules()
        }}
      />
    </div>
  )
}