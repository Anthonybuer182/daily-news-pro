import { useEffect, useState } from 'react'
import { Table, Button, Space, Modal, Form, Input, Switch, message, Popconfirm, Tag, Select } from 'antd'
import { getModelConfigs, createModelConfig, updateModelConfig, deleteModelConfig, setDefaultModelConfig } from '../../api'

interface ModelConfig {
  id: number
  name: string
  api_type: string
  api_base: string
  api_key: string
  model: string
  is_default: boolean
  created_at: string
  updated_at: string
}

const API_TYPE_OPTIONS = [
  { label: 'OpenAI 兼容', value: 'openai' },
  { label: 'Anthropic (Claude)', value: 'anthropic' },
  { label: 'Google (Gemini)', value: 'google' },
]

export default function ModelConfigs() {
  const [configs, setConfigs] = useState<ModelConfig[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingConfig, setEditingConfig] = useState<ModelConfig | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    fetchConfigs()
  }, [])

  const fetchConfigs = async () => {
    setLoading(true)
    try {
      const res = await getModelConfigs()
      setConfigs(res.data)
    } catch (error) {
      message.error('获取配置失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    setEditingConfig(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (record: ModelConfig) => {
    setEditingConfig(record)
    form.setFieldsValue(record)
    setModalVisible(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteModelConfig(id)
      message.success('删除成功')
      fetchConfigs()
    } catch {
      message.error('删除失败')
    }
  }

  const handleSetDefault = async (id: number) => {
    try {
      await setDefaultModelConfig(id)
      message.success('设置成功')
      fetchConfigs()
    } catch {
      message.error('设置失败')
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      if (editingConfig) {
        await updateModelConfig(editingConfig.id, values)
      } else {
        await createModelConfig(values)
      }
      message.success(editingConfig ? '更新成功' : '创建成功')
      setModalVisible(false)
      fetchConfigs()
    } catch (error) {
      message.error(editingConfig ? '更新失败' : '创建失败')
    }
  }

  const columns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    {
      title: 'API 类型',
      dataIndex: 'api_type',
      key: 'api_type',
      render: (api_type: string) => {
      const map: Record<string, string> = { openai: 'OpenAI', anthropic: 'Anthropic', google: 'Google' }
      return map[api_type] || api_type
    }
    },
    { title: 'API 地址', dataIndex: 'api_base', key: 'api_base', ellipsis: true },
    { title: '模型', dataIndex: 'model', key: 'model' },
    {
      title: '默认',
      dataIndex: 'is_default',
      key: 'is_default',
      render: (is_default: boolean) => is_default ? <Tag color="gold">默认</Tag> : null
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: ModelConfig) => (
        <Space>
          <Button type="link" size="small" onClick={() => handleEdit(record)}>编辑</Button>
          {!record.is_default && (
            <Button type="link" size="small" onClick={() => handleSetDefault(record.id)}>设为默认</Button>
          )}
          <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" size="small" danger>删除</Button>
          </Popconfirm>
        </Space>
      )
    }
  ]

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" onClick={handleAdd}>添加配置</Button>
      </div>
      <Table columns={columns} dataSource={configs} rowKey="id" loading={loading} />

      <Modal
        title={editingConfig ? '编辑配置' : '添加配置'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={handleSubmit}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入名称' }]}>
            <Input placeholder="如：OpenAI" />
          </Form.Item>
          <Form.Item name="api_type" label="API 类型">
            <Select options={API_TYPE_OPTIONS} placeholder="选择 API 类型" />
          </Form.Item>
          <Form.Item name="api_base" label="API 地址" rules={[{ required: true, message: '请输入 API 地址' }]}>
            <Input placeholder="https://api.openai.com/v1" />
          </Form.Item>
          <Form.Item name="api_key" label="API 密钥" rules={[{ required: true, message: '请输入 API 密钥' }]}>
            <Input.Password placeholder="sk-..." />
          </Form.Item>
          <Form.Item name="model" label="模型" rules={[{ required: true, message: '请输入模型名称' }]}>
            <Input placeholder="gpt-4o-mini" />
          </Form.Item>
          <Form.Item name="is_default" label="设为默认" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}