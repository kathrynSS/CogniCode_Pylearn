# Supabase PostgreSQL 设置指南

## 🎯 为什么选择Supabase？

- ✅ **完全免费**：500MB存储，足够个人项目使用
- ✅ **零配置**：自动提供PostgreSQL数据库
- ✅ **高性能**：专为现代应用优化
- ✅ **管理界面**：可视化数据库管理
- ✅ **自动备份**：数据安全有保障

## 📋 设置步骤

### 1. 创建Supabase项目

1. 访问 [supabase.com](https://supabase.com)
2. 点击 "Start your project" 
3. 使用GitHub账号登录（推荐）
4. 点击 "New project"

### 2. 配置项目

1. **Organization**: 选择你的组织（通常是你的用户名）
2. **Project name**: 输入项目名称（如：`pylearn-database`）
3. **Database Password**: 设置数据库密码（**请记住这个密码！**）
4. **Region**: 选择离你最近的区域
5. 点击 "Create new project"

### 3. 获取数据库连接信息

项目创建完成后：

1. 在左侧菜单点击 "Settings" ⚙️
2. 点击 "Database"
3. 在 "Connection string" 部分找到 "URI"
4. 复制完整的连接字符串，格式如下：
   ```
   postgresql://postgres:YOUR_PASSWORD@db.xxx.supabase.co:5432/postgres
   ```

### 4. 在Vercel中设置环境变量

1. 在Vercel项目中，点击 "Settings"
2. 点击 "Environment Variables"
3. 添加新变量：
   - **Name**: `POSTGRES_URL`
   - **Value**: 粘贴刚才复制的连接字符串
   - **Environment**: 选择 "Production, Preview, and Development"
4. 点击 "Save"

### 5. 重新部署

1. 在Vercel项目页面，点击 "Deployments"
2. 点击最新部署右侧的 "⋯" 菜单
3. 选择 "Redeploy"

## 🔍 验证连接

部署完成后，查看Vercel函数日志，应该看到：
```
✅ Using PostgreSQL (Vercel Postgres)
🔗 Connecting to PostgreSQL: postgresql://postgres:...
```

## 📊 Supabase管理界面

在Supabase项目中：
- **Table Editor**: 可视化查看和编辑数据
- **SQL Editor**: 执行自定义SQL查询  
- **API**: 自动生成的REST API（本项目不需要）
- **Auth**: 用户认证功能（本项目不需要）

## 🔧 常见问题

### Q: 连接失败怎么办？
A: 检查：
1. 连接字符串是否完整
2. 密码是否正确
3. Vercel环境变量是否保存
4. 是否重新部署

### Q: 数据库在哪里？
A: 在Supabase项目的 "Table Editor" 中可以看到所有表

### Q: 免费额度够用吗？
A: 500MB足够个人学习项目使用，支持数千个用户

### Q: 如何备份数据？
A: Supabase自动备份，也可以在SQL Editor中导出数据

## 💡 额外提示

1. **密码安全**：使用强密码，不要分享
2. **访问限制**：Supabase默认只允许应用访问，很安全
3. **监控使用**：在Supabase仪表板监控存储使用情况
4. **扩展性**：需要更多存储时可以升级到付费计划

## 🎉 完成！

设置完成后，你的PyLearn应用将：
- ✅ 自动使用PostgreSQL数据库
- ✅ 支持多用户数据隔离  
- ✅ 拥有专业级的数据库性能
- ✅ 享受自动备份和高可用性

现在你可以正常使用所有功能：用户注册、项目创建、文件上传、聊天记录等！ 