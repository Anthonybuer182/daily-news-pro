import { useEffect, useState } from 'react'
import { Table, Button, Space, Tag, message, Popconfirm, Form, Input, Switch, Modal, Select, Tabs } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, ExperimentOutlined, SendOutlined as SendNowOutlined, SettingOutlined } from '@ant-design/icons'
import { getChannels, createChannel, updateChannel, deleteChannel, testChannel, sendNow, addChannelWebhook, deleteChannelWebhook } from '../../api'

const { TextArea } = Input

// 飞书默认模板
const FEISHU_TEMPLATE = `{
  "msg_type": "interactive",
  "card": {
    "header": {
      "title": {
        "tag": "plain_text",
        "content": "📰 今日新闻汇总（ {{ articles|length }} 篇）"
      },
      "template": "blue"
    },
    "elements": [
      {% for article in articles -%}
      {
        "tag": "div",
        "text": {
          "tag": "lark_md",
          "content": "**【{{ article.title }}】**\\\\n\\\\n摘要：{{ article.summary }}\\\\n\\\\n来源：{{ article.rule_name }}{% if article.publish_time %} | 时间：{{ article.publish_time }}{% endif %}\\\\n\\\\n[查看原文]({{ article.url }})"
        }
      }{% if not loop.last %},{"tag": "hr"}{% endif %}
      {% endfor %}
    ]
  }
}`

// 钉钉默认模板
const DINGTALK_TEMPLATE = `{
  "msgtype": "markdown",
  "markdown": {
    "title": "📰 今日新闻汇总",
    "text": "{% for article in articles %}**【{{ article.title }}】**\\\\n\\\\n> {{ article.summary }}\\\\n\\\\n来源：{{ article.rule_name }}{% if article.publish_time %} | {{ article.publish_time }}{% endif %}\\\\n\\\\n[查看原文]({{ article.url }})\\\\n\\\\n---\\\\n\\\\n{% endfor %}"
  }
}`

export default function Channels() {
  const [loading, setLoading] = useState(false)
  const [channels, setChannels] = useState<any[]>([])
  const [modalVisible, setModalVisible] = useState(false)
  const [webhookModalVisible, setWebhookModalVisible] = useState(false)
  const [templateModalVisible, setTemplateModalVisible] = useState(false)
  const [editingChannel, setEditingChannel] = useState<any>(null)
  const [selectedChannelId, setSelectedChannelId] = useState<number | null>(null)
  const [form] = Form.useForm()
  const [webhookForm] = Form.useForm()
  const [templateForm] = Form.useForm()

  useEffect(() => {
    loadChannels()
  }, [])

  const loadChannels = async () => {
    setLoading(true)
    try {
      const res = await getChannels()
      setChannels(res.data)
    } catch (error) {
      message.error('加载渠道失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setEditingChannel(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (record: any) => {
    setEditingChannel(record)
    form.setFieldsValue({
      name: record.name,
      channel_type: record.channel_type || 'http_webhook',
      push_on_crawl: record.push_on_crawl,
      push_on_schedule: record.push_on_schedule,
      schedule_time: record.schedule_time,
      status: record.status,
      http_method: record.http_method || 'POST',
      request_headers: record.request_headers || '{"Content-Type": "application/json"}'
    })
    setModalVisible(true)
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      const data = {
        name: values.name,
        channel_type: values.channel_type || 'http_webhook',
        push_on_crawl: values.push_on_crawl || false,
        push_on_schedule: values.push_on_schedule || false,
        schedule_time: values.schedule_time || '09:00',
        status: values.status || 'enabled',
        http_method: values.http_method || 'POST',
        request_headers: values.request_headers || '{"Content-Type": "application/json"}',
        message_template: values.message_template,
        webhooks: []
      }

      if (editingChannel) {
        await updateChannel(editingChannel.id, data)
        message.success('更新成功')
      } else {
        await createChannel(data)
        message.success('创建成功')
      }
      setModalVisible(false)
      loadChannels()
    } catch (error: any) {
      if (error.errorFields) {
        return
      }
      message.error(editingChannel ? '更新失败' : '创建失败')
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteChannel(id)
      message.success('删除成功')
      loadChannels()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleToggleCrawl = async (record: any) => {
    try {
      await updateChannel(record.id, {
        push_on_crawl: !record.push_on_crawl
      })
      loadChannels()
    } catch (error) {
      message.error('更新失败')
    }
  }

  const handleToggleSchedule = async (record: any) => {
    try {
      await updateChannel(record.id, {
        push_on_schedule: !record.push_on_schedule
      })
      loadChannels()
    } catch (error) {
      message.error('更新失败')
    }
  }

  const handleTest = async (channelId: number) => {
    try {
      const res = await testChannel(channelId)
      if (res.data.success) {
        message.success('测试消息发送成功')
      } else {
        message.error(res.data.message || '测试消息发送失败')
      }
    } catch (error) {
      message.error('测试失败')
    }
  }

  const handleSendNow = async () => {
    try {
      const res = await sendNow()
      if (res.data.success) {
        message.success(`成功推送到 ${res.data.channels_count} 个渠道`)
      } else {
        message.error(res.data.message || '推送失败')
      }
    } catch (error) {
      message.error('推送失败')
    }
  }

  const handleAddWebhook = (channelId: number) => {
    setSelectedChannelId(channelId)
    webhookForm.resetFields()
    setWebhookModalVisible(true)
  }

  const handleWebhookSubmit = async () => {
    try {
      const values = await webhookForm.validateFields()
      if (selectedChannelId) {
        await addChannelWebhook(selectedChannelId, {
          webhook_url: values.webhook_url,
          is_enabled: true
        })
        message.success('添加成功')
        setWebhookModalVisible(false)
        loadChannels()
      }
    } catch (error) {
      message.error('添加失败')
    }
  }

  const handleDeleteWebhook = async (channelId: number, webhookId: number) => {
    try {
      await deleteChannelWebhook(channelId, webhookId)
      message.success('删除成功')
      loadChannels()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleEditTemplate = (record: any) => {
    setSelectedChannelId(record.id)
    templateForm.setFieldsValue({
      message_template: record.message_template || FEISHU_TEMPLATE
    })
    setTemplateModalVisible(true)
  }

  const handleTemplateSubmit = async () => {
    try {
      const values = await templateForm.validateFields()
      if (selectedChannelId) {
        await updateChannel(selectedChannelId, {
          message_template: values.message_template
        })
        message.success('模板更新成功')
        setTemplateModalVisible(false)
        loadChannels()
      }
    } catch (error) {
      message.error('更新模板失败')
    }
  }

  const handleApplyTemplate = (type: string) => {
    if (type === 'feishu') {
      templateForm.setFieldsValue({ message_template: FEISHU_TEMPLATE })
    } else if (type === 'dingtalk') {
      templateForm.setFieldsValue({ message_template: DINGTALK_TEMPLATE })
    }
  }

  const columns = [
    {
      title: '渠道名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '类型',
      dataIndex: 'channel_type',
      key: 'channel_type',
      render: (type: string) => (
        <Tag color={type === 'http_webhook' ? 'blue' : 'green'}>
          {type || 'http_webhook'}
        </Tag>
      )
    },
    {
      title: 'Webhook',
      key: 'webhooks',
      render: (_: any, record: any) => (
        <span>{record.webhooks?.length || 0} 个</span>
      )
    },
    {
      title: '实时推送',
      key: 'push_on_crawl',
      render: (_: any, record: any) => (
        <Switch
          checked={record.push_on_crawl}
          onChange={() => handleToggleCrawl(record)}
        />
      )
    },
    {
      title: '定时推送',
      key: 'push_on_schedule',
      render: (_: any, record: any) => (
        <Switch
          checked={record.push_on_schedule}
          onChange={() => handleToggleSchedule(record)}
        />
      )
    },
    {
      title: '推送时间',
      dataIndex: 'schedule_time',
      key: 'schedule_time',
      render: (time: string, record: any) => record.push_on_schedule ? time : '-'
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'enabled' ? 'green' : 'red'}>
          {status === 'enabled' ? '已启用' : '已禁用'}
        </Tag>
      )
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<ExperimentOutlined />}
            onClick={() => handleTest(record.id)}
          >
            测试
          </Button>
          <Button
            type="link"
            size="small"
            icon={<SettingOutlined />}
            onClick={() => handleEditTemplate(record)}
          >
            模板
          </Button>
          <Button
            type="link"
            size="small"
            onClick={() => handleAddWebhook(record.id)}
          >
            Webhook
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定删除该渠道？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ]

  const expandedRowRender = (record: any) => {
    const webhookColumns = [
      { title: 'Webhook URL', dataIndex: 'webhook_url', key: 'webhook_url', ellipsis: true },
      { title: '状态', dataIndex: 'is_enabled', key: 'is_enabled', render: (enabled: boolean) => enabled ? '启用' : '禁用' },
      {
        title: '操作',
        key: 'action',
        render: (_: any, webhook: any) => (
          <Button
            type="link"
            size="small"
            danger
            onClick={() => handleDeleteWebhook(record.id, webhook.id)}
          >
            删除
          </Button>
        )
      }
    ]

    return (
      <div style={{ padding: '10px 0' }}>
        <Tabs
          items={[
            {
              key: 'webhooks',
              label: 'Webhooks',
              children: (
                <Table
                  columns={webhookColumns}
                  dataSource={record.webhooks}
                  rowKey="id"
                  pagination={false}
                  size="small"
                />
              )
            },
            {
              key: 'config',
              label: '配置信息',
              children: (
                <div style={{ fontSize: '13px', color: '#666' }}>
                  <p><strong>HTTP 方法：</strong>{record.http_method || 'POST'}</p>
                  <p><strong>请求头：</strong>{record.request_headers || '{"Content-Type": "application/json"}'}</p>
                  <p><strong>消息模板：</strong></p>
                  <pre style={{ background: '#f5f5f5', padding: '8px', borderRadius: '4px', maxHeight: '200px', overflow: 'auto' }}>
                    {record.message_template || '（使用默认模板）'}
                  </pre>
                </div>
              )
            }
          ]}
        />
      </div>
    )
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h2>渠道管理</h2>
        <Space>
          <Button type="primary" icon={<SendNowOutlined />} onClick={handleSendNow}>
            立即推送
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            添加渠道
          </Button>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={channels}
        rowKey="id"
        loading={loading}
        expandable={{
          expandedRowRender,
          defaultExpandedRowKeys: []
        }}
      />

      <Modal
        title={editingChannel ? '编辑渠道' : '添加渠道'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        okText="确定"
        cancelText="取消"
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="渠道名称"
            rules={[{ required: true, message: '请输入渠道名称' }]}
          >
            <Input placeholder="例如：产品推送群" />
          </Form.Item>

          <Form.Item
            name="channel_type"
            label="渠道类型"
          >
            <Select>
              <Select.Option value="http_webhook">HTTP Webhook</Select.Option>
              <Select.Option value="feishu">飞书</Select.Option>
              <Select.Option value="dingtalk">钉钉</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="http_method"
            label="HTTP 方法"
          >
            <Select>
              <Select.Option value="POST">POST</Select.Option>
              <Select.Option value="GET">GET</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="request_headers"
            label="请求头（JSON 格式）"
          >
            <Input placeholder='{"Content-Type": "application/json"}' />
          </Form.Item>

          <Form.Item
            name="push_on_crawl"
            label="实时推送"
            valuePropName="checked"
            extra="每次抓取完成后立即推送新文章"
          >
            <Switch />
          </Form.Item>

          <Form.Item
            name="push_on_schedule"
            label="定时推送"
            valuePropName="checked"
            extra="每天定时汇总推送当天文章"
          >
            <Switch />
          </Form.Item>

          <Form.Item
            name="schedule_time"
            label="推送时间"
            extra="当定时推送开启时生效，格式：HH:mm"
          >
            <Input placeholder="09:00" />
          </Form.Item>

          <Form.Item
            name="status"
            label="状态"
          >
            <Select>
              <Select.Option value="enabled">启用</Select.Option>
              <Select.Option value="disabled">禁用</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="添加 Webhook"
        open={webhookModalVisible}
        onOk={handleWebhookSubmit}
        onCancel={() => setWebhookModalVisible(false)}
        okText="确定"
        cancelText="取消"
      >
        <Form form={webhookForm} layout="vertical">
          <Form.Item
            name="webhook_url"
            label="Webhook URL"
            rules={[{ required: true, message: '请输入 Webhook URL' }]}
          >
            <Input placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/..." />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="编辑消息模板"
        open={templateModalVisible}
        onOk={handleTemplateSubmit}
        onCancel={() => setTemplateModalVisible(false)}
        okText="确定"
        cancelText="取消"
        width={800}
      >
        <div style={{ marginBottom: 16 }}>
          <span style={{ marginRight: 8 }}>快速应用模板：</span>
          <Button size="small" onClick={() => handleApplyTemplate('feishu')}>飞书模板</Button>
          <Button size="small" style={{ marginLeft: 8 }} onClick={() => handleApplyTemplate('dingtalk')}>钉钉模板</Button>
        </div>
        <Form form={templateForm} layout="vertical">
          <Form.Item
            name="message_template"
            label="消息模板（Jinja2 格式）"
            extra={
              <div style={{ fontSize: '12px', color: '#999', marginTop: 8 }}>
                <p>使用 Jinja2 模板语法。可用变量：</p>
                <ul style={{ margin: '4px 0' }}>
                  <li><code>articles</code> - 文章列表</li>
                  <li><code>article.title</code> - 文章标题</li>
                  <li><code>article.summary</code> - 文章摘要</li>
                  <li><code>article.rule_name</code> - 来源名称</li>
                  <li><code>article.publish_time</code> - 发布时间</li>
                  <li><code>article.url</code> - 原文链接</li>
                </ul>
              </div>
            }
          >
            <TextArea
              rows={20}
              placeholder="输入消息模板..."
              style={{ fontFamily: 'monospace' }}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}