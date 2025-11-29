# Netlib.re 多账号保活脚本

## 项目简介

自动化登录 [Netlib.re](https://www.netlib.re/) 实现账号保活，支持多账号批量管理、智能重试、动态等待。

## 核心优化

### 1. 动态等待替代固定延迟
- ✅ 使用 `wait_for_selector` 等待元素出现
- ✅ 使用 `wait_for_load_state("networkidle")` 等待网络请求完成
- ✅ 设置合理的超时时间（10-30 秒）

### 2. 浏览器资源复用
- ✅ 单个浏览器实例处理所有账号
- ✅ 每个账号使用独立的浏览器上下文（隔离 Cookie）
- ✅ 降低内存占用，提升执行效率

### 3. 指数退避重试机制
- ✅ 超时/失败自动重试最多 3 次
- ✅ 重试间隔：2 秒 → 4 秒 → 8 秒
- ✅ 区分超时异常和业务异常

### 4. 更健壮的选择器
- ✅ 支持 CSS 选择器 + ARIA 角色双重匹配
- ✅ 兼容页面结构变化

### 5. 多通道通知
- ✅ Telegram 分块发送（单条最大 4096 字符）
- ✅ 包含执行统计和时间戳
- ⚠️ 可扩展邮件/企业微信等通知方式

## 使用指南

### 1. Fork 仓库
点击右上角 `Fork` 按钮

### 2. 配置 Secrets
进入 `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

| 变量名 | 示例值 | 说明 |
|--------|--------|------|
| `SITE_ACCOUNTS` | `user1,pass1;user2,pass2` | 多账号配置，分号分隔 |
| `TELEGRAM_BOT_TOKEN` | `123456:ABC-DEF` | Telegram Bot Token |
| `TELEGRAM_CHAT_ID` | `987654321` | Telegram 聊天 ID |

### 3. 启用 Actions
进入 `Actions` 页签，点击 `I understand my workflows, go ahead and enable them`

### 4. 手动测试
在 `Actions` 页面点击 `Netlib Keep-Alive` → `Run workflow`

### 5. 定时执行
默认每月 1 号和 15 号凌晨自动执行

## 环境变量说明

### SITE_ACCOUNTS（必填）
**格式**: `username1,password1;username2,password2;...`

**示例**: 
```
alice,MyP@ssw0rd;bob,SecurePass123
```

### TELEGRAM_BOT_TOKEN（可选）
从 [@BotFather](https://t.me/BotFather) 创建 Bot 获取

### TELEGRAM_CHAT_ID（可选）
发送消息到 [@userinfobot](https://t.me/userinfobot) 获取

## 执行日志示例

```
🚀 开始登录账号: alice (尝试 1/3)
✅ 账号 alice 登录成功
🚀 开始登录账号: bob (尝试 1/3)
⏱️ 账号 bob 超时: Timeout 30000ms exceeded
🔄 2 秒后重试...
✅ 账号 bob 登录成功

📊 执行统计：成功 2 个，失败 0 个
```

## 注意事项

1. **账号密码安全**: 必须使用 GitHub Secrets，切勿硬编码
2. **执行频率**: GitHub Actions 免费额度有限，建议每月 2 次
3. **网络环境**: Actions 使用 GitHub 服务器 IP，可能被部分网站限制
4. **页面变更**: 网站升级可能导致选择器失效，需及时更新

## 故障排查

### 登录失败
1. 检查账号密码是否正确
2. 查看 Actions 日志中的错误信息
3. 手动访问网站确认登录流程是否变更

### Telegram 通知失败
1. 验证 Token 和 Chat ID 是否正确
2. 确认 Bot 已添加到对话中

### 执行超时
1. 检查网络连接
2. 增加 workflow 的 `timeout-minutes`

## 许可证

MIT License

## 免责声明

本项目仅用于技术学习和个人账号保活，使用者需遵守目标网站的服务条款。
