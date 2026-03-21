import { Card, Form, Input, Button, message } from 'antd'

const FIELD_TIPS = {
  delay_min: '抓取请求之间的最小等待时间（秒）\n\n设置延迟防止请求过快被封，例如设为1表示每次请求后至少等待1秒',
  delay_max: '抓取请求之间的最大等待时间（秒）\n\n与min配合使用，随机等待min~max秒。例如1-3秒表示每次等待1-3秒',
  user_agent: '自定义User-Agent字符串\n\n不设置则使用浏览器默认UA。可用于伪装成特定浏览器或移动端',
}

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
          <Form.Item name="delay_min" label="默认最小延迟(秒)" initialValue={1} tooltip={FIELD_TIPS.delay_min}>
            <Input type="number" />
          </Form.Item>
          <Form.Item name="delay_max" label="默认最大延迟(秒)" initialValue={3} tooltip={FIELD_TIPS.delay_max}>
            <Input type="number" />
          </Form.Item>
          <Form.Item name="user_agent" label="默认 User-Agent" tooltip={FIELD_TIPS.user_agent}>
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
