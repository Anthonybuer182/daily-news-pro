import { useEffect, useState } from 'react'
import { Card, Table, Button, Space, Input, message, Modal, Form, Popconfirm } from 'antd'
import { getTags, createTag, updateTag, deleteTag, batchCreateTags } from '../../api'

interface TagItem {
  id: number
  name: string
  created_at: string
}

export default function Tags() {
  const [tags, setTags] = useState<TagItem[]>([])
  const [loading, setLoading] = useState(false)

  // 编辑相关
  const [modalVisible, setModalVisible] = useState(false)
  const [editingTag, setEditingTag] = useState<TagItem | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    fetchTags()
  }, [])

  const fetchTags = async () => {
    setLoading(true)
    try {
      const res = await getTags()
      setTags(res.data)
    } catch (error) {
      message.error('获取标签失败')
    } finally {
      setLoading(false)
    }
  }

  // 添加标签
  const handleAdd = () => {
    setEditingTag(null)
    form.resetFields()
    setModalVisible(true)
  }

  // 编辑标签
  const handleEdit = (record: TagItem) => {
    setEditingTag(record)
    form.setFieldsValue({ name: record.name })
    setModalVisible(true)
  }

  // 删除标签
  const handleDelete = async (id: number) => {
    try {
      await deleteTag(id)
      message.success('删除成功')
      fetchTags()
    } catch (error) {
      message.error('删除失败')
    }
  }

  // 保存标签
  const handleSave = async () => {
    try {
      const values = await form.validateFields()
      if (editingTag) {
        await updateTag(editingTag.id, values)
        message.success('更新成功')
      } else {
        await createTag(values)
        message.success('创建成功')
      }
      setModalVisible(false)
      fetchTags()
    } catch (error) {
      message.error(editingTag ? '更新失败' : '创建失败')
    }
  }

  // 批量添加标签
  const handleBatchAdd = async () => {
    Modal.confirm({
      title: '批量添加标签',
      content: (
        <Input.TextArea
          id="batch-tags-input"
          rows={4}
          placeholder="输入标签，每行一个或用逗号分隔"
        />
      ),
      onOk: async () => {
        const input = document.getElementById('batch-tags-input') as HTMLTextAreaElement
        const text = input?.value || ''
        const names = text.split(/[,\n]/).map(n => n.trim()).filter(n => n)
        if (names.length === 0) {
          message.warning('请输入标签')
          return
        }
        try {
          const res = await batchCreateTags(names)
          const created = res.data.created || []
          const skipped = res.data.skipped || []
          if (created.length > 0) {
            message.success(`成功添加 ${created.length} 个标签`)
          }
          if (skipped.length > 0) {
            message.info(`${skipped.length} 个标签已存在`)
          }
          fetchTags()
        } catch (error) {
          message.error('批量添加失败')
        }
      }
    })
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    { title: '标签名称', dataIndex: 'name', key: 'name' },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: TagItem) => (
        <Space>
          <Button type="link" size="small" onClick={() => handleEdit(record)}>编辑</Button>
          <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" size="small" danger>删除</Button>
          </Popconfirm>
        </Space>
      )
    }
  ]

  return (
    <div>
      <Card
        title="标签管理"
        extra={
          <Space>
            <Button onClick={handleBatchAdd}>批量添加</Button>
            <Button type="primary" onClick={handleAdd}>添加标签</Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={tags}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Card title="说明" style={{ marginTop: 16 }}>
        <ul style={{ color: '#666', margin: 0, paddingLeft: 20 }}>
          <li>标签用于对文章进行分类</li>
          <li>LLM 会根据文章内容自动打标签，最多打 3 个标签</li>
          <li>删除标签不会影响已打标签的文章</li>
        </ul>
      </Card>

      {/* 添加/编辑标签弹窗 */}
      <Modal
        title={editingTag ? '编辑标签' : '添加标签'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={handleSave}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="标签名称"
            rules={[{ required: true, message: '请输入标签名称' }]}
          >
            <Input placeholder="请输入标签名称" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
