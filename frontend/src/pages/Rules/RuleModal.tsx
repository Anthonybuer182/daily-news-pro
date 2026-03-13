import { useEffect, useState } from 'react'
import { Modal, Form, Input, Select, InputNumber } from 'antd'
import { createRule, updateRule } from '../../api'

interface RuleModalProps {
  visible: boolean
  rule: any
  onClose: () => void
  onSuccess: () => void
}

export default function RuleModal({ visible, rule, onClose, onSuccess }: RuleModalProps) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (visible && rule) {
      form.setFieldsValue(rule)
    } else if (visible) {
      form.resetFields()
      form.setFieldsValue({
        crawl_method: 'playwright',
        crawl_mode: 'hybrid',
        delay_min: 1,
        delay_max: 3,
        status: 'disabled',
      })
    }
  }, [visible, rule])

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)
      if (rule) {
        await updateRule(rule.id, values)
      } else {
        await createRule(values)
      }
      onSuccess()
    } catch (error) {
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title={rule ? '编辑规则' : '新建规则'}
      open={visible}
      onCancel={onClose}
      onOk={handleSubmit}
      confirmLoading={loading}
      width={600}
    >
      <Form form={form} layout="vertical">
        <Form.Item name="name" label="规则名称" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item name="site_url" label="网站 URL">
          <Input />
        </Form.Item>
        <Form.Item name="list_url" label="列表页 URL">
          <Input />
        </Form.Item>
        <Form.Item name="crawl_method" label="抓取方式">
          <Select>
            <Select.Option value="playwright">Playwright</Select.Option>
            <Select.Option value="trafilatura">Trafilatura</Select.Option>
            <Select.Option value="hybrid">混合模式</Select.Option>
          </Select>
        </Form.Item>
        <Form.Item name="crawl_mode" label="抓取模式">
          <Select>
            <Select.Option value="smart">智能推断</Select.Option>
            <Select.Option value="manual">手动配置</Select.Option>
            <Select.Option value="hybrid">混合模式</Select.Option>
          </Select>
        </Form.Item>
        <Form.Item name="title_selector" label="标题选择器">
          <Input />
        </Form.Item>
        <Form.Item name="content_selector" label="内容选择器">
          <Input />
        </Form.Item>
        <Form.Item name="detail_url_pattern" label="详情页 URL 匹配">
          <Input />
        </Form.Item>
        <Form.Item name="exclude_patterns" label="排除 URL 模式">
          <Input.TextArea rows={2} placeholder="JSON 数组格式" />
        </Form.Item>
        <Form.Item name="delay_min" label="最小延迟(秒)">
          <InputNumber min={0} />
        </Form.Item>
        <Form.Item name="delay_max" label="最大延迟(秒)">
          <InputNumber min={0} />
        </Form.Item>
        <Form.Item name="user_agent" label="User-Agent">
          <Input />
        </Form.Item>
        <Form.Item name="cron_expression" label="定时表达式">
          <Input placeholder="0 0 * * *" />
        </Form.Item>
      </Form>
    </Modal>
  )
}
