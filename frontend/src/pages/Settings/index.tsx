import { Card, Form, Input, Button, message } from 'antd'

export default function Settings() {
  const [form] = Form.useForm()

  const handleSave = () => {
    message.success('设置已保存')
  }

  return (
    <div>
      <h1>系统设置</h1>
      <Card title="通用设置">
        <Form form={form} layout="vertical" style={{ maxWidth: 400 }}>
          <Form.Item name="delay_min" label="默认最小延迟(秒)" initialValue={1}>
            <Input type="number" />
          </Form.Item>
          <Form.Item name="delay_max" label="默认最大延迟(秒)" initialValue={3}>
            <Input type="number" />
          </Form.Item>
          <Form.Item name="user_agent" label="默认 User-Agent">
            <Input />
          </Form.Item>
          <Form.Item>
            <Button type="primary" onClick={handleSave}>保存设置</Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}
