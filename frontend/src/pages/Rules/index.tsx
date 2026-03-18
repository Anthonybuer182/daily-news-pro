import { useEffect, useState } from 'react'
import { Table, Button, Space, Tag, message, Popconfirm } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, PlayCircleOutlined, StopOutlined } from '@ant-design/icons'
import { getRules, deleteRule, enableRule, disableRule, createJob } from '../../api'
import RuleModal from './RuleModal'

export default function Rules() {
  const [loading, setLoading] = useState(false)
  const [rules, setRules] = useState([])
  const [modalVisible, setModalVisible] = useState(false)
  const [editingRule, setEditingRule] = useState(null)

  useEffect(() => {
    loadRules()
  }, [])

  const loadRules = async () => {
    setLoading(true)
    try {
      const res = await getRules()
      setRules(res.data)
    } catch (error) {
      message.error('加载规则失败')
    } finally {
      setLoading(false)
    }
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
      await createJob({ rule_id: rule.id, trigger_type: 'manual' })
      message.success('任务已创建')
    } catch (error) {
      message.error('创建任务失败')
    }
  }

  // 抓取方式标签映射
  const getSourceTypeTag = (type: string) => {
    const tagMap: Record<string, { color: string; text: string }> = {
      rss: { color: 'orange', text: 'RSS' },
      api: { color: 'blue', text: 'API' },
      playwright: { color: 'green', text: '网页抓取' },
    }
    const tag = tagMap[type] || { color: 'default', text: type }
    return <Tag color={tag.color}>{tag.text}</Tag>
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '来源', dataIndex: 'source_url', key: 'source_url', ellipsis: true },
    { title: '抓取方式', dataIndex: 'source_type', key: 'source_type',
      render: (type: string) => getSourceTypeTag(type)
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
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => {
          setEditingRule(null)
          setModalVisible(true)
        }}>
          新建规则
        </Button>
      </div>
      <Table columns={columns} dataSource={rules} rowKey="id" loading={loading} />
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
