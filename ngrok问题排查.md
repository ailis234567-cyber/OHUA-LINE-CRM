# 🔍 ngrok 意外停止问题排查

## 常见原因

### 1. **ngrok 未配置 authtoken** ⭐ 最常见

**症状**：ngrok 启动后立即退出

**解决方法**：
```bash
# 检查是否已配置
ngrok config check

# 如果未配置，运行：
ngrok config add-authtoken 你的token
```

**获取 token**：
1. 访问：https://dashboard.ngrok.com/signup
2. 注册账号
3. 获取 authtoken：https://dashboard.ngrok.com/get-started/your-authtoken

---

### 2. **authtoken 无效或过期**

**症状**：ngrok 启动后显示认证错误

**解决方法**：
```bash
# 重新配置正确的 token
ngrok config add-authtoken 新的token
```

---

### 3. **网络连接问题**

**症状**：ngrok 无法连接到服务器

**解决方法**：
- 检查网络连接
- 检查防火墙设置
- 尝试使用 VPN

---

### 4. **端口被占用**

**症状**：ngrok 显示端口错误

**解决方法**：
- 检查端口 5001 是否被占用
- 或者修改 Web 应用使用其他端口

---

### 5. **ngrok 版本问题**

**症状**：ngrok 命令执行失败

**解决方法**：
```bash
# 更新 ngrok
brew upgrade ngrok

# 或重新安装
brew uninstall ngrok
brew install ngrok
```

---

## 🔧 诊断步骤

### 步骤 1: 检查 ngrok 是否安装
```bash
which ngrok
ngrok version
```

### 步骤 2: 检查 ngrok 配置
```bash
ngrok config check
```

如果显示错误，说明未配置 authtoken。

### 步骤 3: 手动测试 ngrok
```bash
# 先启动 Web 应用
python web_app.py

# 在另一个终端测试 ngrok
ngrok http 5001
```

查看是否有错误信息。

### 步骤 4: 查看详细错误
在 GUI 的日志区域查看具体错误信息，通常会显示：
- "authtoken" 相关错误 → 需要配置 token
- "port" 相关错误 → 端口问题
- "connection" 相关错误 → 网络问题

---

## ✅ 快速修复

### 如果看到 "authtoken" 相关错误：

1. **获取 authtoken**
   - 访问：https://dashboard.ngrok.com/get-started/your-authtoken
   - 复制你的 authtoken

2. **配置 ngrok**
   ```bash
   ngrok config add-authtoken 你的token
   ```

3. **验证配置**
   ```bash
   ngrok config check
   ```
   应该显示 "Valid configuration file"

4. **重新启动**
   - 在 GUI 中点击 "停止 ngrok"
   - 再点击 "启动 ngrok"

---

## 📝 检查清单

- [ ] ngrok 已安装 (`which ngrok` 有输出)
- [ ] ngrok 已配置 authtoken (`ngrok config check` 成功)
- [ ] Web 服务已启动（端口 5001）
- [ ] 网络连接正常
- [ ] 防火墙允许 ngrok 连接

---

## 🆘 如果还是不行

1. **查看 GUI 日志**：查看具体的错误信息
2. **手动测试**：在终端手动运行 `ngrok http 5001` 查看错误
3. **检查 ngrok 状态**：访问 http://127.0.0.1:4040 查看 ngrok 状态页面

---

## 💡 提示

GUI 现在会：
- ✅ 自动检查 ngrok 是否已配置
- ✅ 显示详细的错误信息
- ✅ 在日志中记录错误原因

查看 GUI 的日志区域，通常会显示具体的错误原因！

