"use client";

import { Card, Form, Input, Button, message, Spin, Tabs, Tag, Typography } from "antd";
import { KeyOutlined, LockOutlined, EyeInvisibleOutlined, EyeOutlined } from "@ant-design/icons";
import { useCredentialFields, usePlatformCredentials, useSaveCredential } from "@/hooks/useCredentials";
import { useState } from "react";

const { TextArea } = Input;
const { Text } = Typography;

/** 平台中文名映射 */
const PLATFORM_NAMES: Record<string, string> = {
  zhihu: "知乎",
  youtube: "YouTube",
  tiktok: "TikTok",
  x_twitter: "X (Twitter)",
};

/** 平台颜色映射 */
const PLATFORM_COLORS: Record<string, string> = {
  zhihu: "#0066FF",
  youtube: "#FF0000",
  tiktok: "#000000",
  x_twitter: "#1DA1F2",
};

/** 每个平台显示为一张独立的 Card */
function PlatformCredentialCard({ code }: { code: string }) {
  const { data: fieldsData } = useCredentialFields();
  const { data: credData, isLoading } = usePlatformCredentials(code);
  const saveCredential = useSaveCredential();

  const [form] = Form.useForm();
  const [showValues, setShowValues] = useState(false);

  const fields = fieldsData?.data?.[code] || [];
  const masked = credData?.data?.masked || {};
  const platformName = PLATFORM_NAMES[code] || code;
  const color = PLATFORM_COLORS[code] || "#666";

  const onFinish = (values: Record<string, string>) => {
    // 清理空值（用户未填写表示不修改）
    const config: Record<string, string> = {};
    let hasValue = false;
    for (const field of fields) {
      const val = (values[field.key] || "").trim();
      if (val) {
        config[field.key] = val;
        hasValue = true;
      } else if (!masked[`${field.key}_set`]) {
        // 如果原本就没设置且用户留空，跳过
        continue;
      }
    }

    if (!hasValue) {
      message.warning("请至少填写一个凭证字段");
      return;
    }

    saveCredential.mutate(
      { code, config },
      {
        onSuccess: (res) => {
          if (res.code === 0) {
            message.success(`${platformName} 凭证已保存`);
            form.resetFields();
          } else {
            message.error(res.message || "保存失败");
          }
        },
        onError: () => message.error("网络错误，请稍后重试"),
      }
    );
  };

  if (isLoading) {
    return (
      <Card style={{ borderRadius: 12, marginBottom: 16 }}>
        <div style={{ textAlign: "center", padding: 40 }}><Spin /></div>
      </Card>
    );
  }

  return (
    <Card
      style={{ borderRadius: 12, marginBottom: 16, borderLeft: `4px solid ${color}` }}
      title={
        <span>
          <KeyOutlined style={{ color, marginRight: 8 }} />
          {platformName}
        </span>
      }
      extra={
        <Tag color={masked[`${fields[0]?.key}_set`] ? "success" : "default"}>
          {masked[`${fields[0]?.key}_set`] ? "已配置" : "未配置"}
        </Tag>
      }
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        autoComplete="off"
      >
        {fields.map((field) => (
          <Form.Item
            key={field.key}
            label={field.label}
            name={field.key}
            extra={
              masked[`${field.key}_set`] ? (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  当前值: {masked[field.key]}
                </Text>
              ) : null
            }
          >
            {field.type === "textarea" ? (
              <TextArea
                rows={3}
                placeholder={`输入${field.label}（留空则不修改）`}
                style={{ fontFamily: "monospace" }}
              />
            ) : (
              <Input.Password
                placeholder={`输入${field.label}（留空则不修改）`}
                iconRender={(visible) => (visible ? <EyeOutlined /> : <EyeInvisibleOutlined />)}
                style={{ fontFamily: "monospace" }}
              />
            )}
          </Form.Item>
        ))}

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={saveCredential.isPending}
            icon={<LockOutlined />}
            block
          >
            保存凭证
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
}

export default function CredentialsPage() {
  const { data: fieldsData, isLoading: fieldsLoading } = useCredentialFields();

  if (fieldsLoading) {
    return <div style={{ textAlign: "center", padding: 60 }}><Spin size="large" /></div>;
  }

  const platformCodes = Object.keys(fieldsData?.data || {});
  // 按指定顺序排列
  const preferredOrder = ["zhihu", "youtube", "tiktok", "x_twitter"];
  const sortedCodes = preferredOrder.filter((c) => platformCodes.includes(c));

  return (
    <div>
      <Card style={{ borderRadius: 12, marginBottom: 16 }}>
        <div style={{ marginBottom: 8 }}>
          <h3 style={{ margin: 0 }}>平台凭证管理</h3>
        </div>
        <Text type="secondary">
          以下平台需要配置凭证才能正常采集数据。凭证以 JSON 格式存储在数据库中，
          仅具有管理员权限的用户可以查看和修改。配置完成后，下次定时采集任务会自动使用新的凭证。
        </Text>
      </Card>

      {sortedCodes.map((code) => (
        <PlatformCredentialCard key={code} code={code} />
      ))}
    </div>
  );
}
