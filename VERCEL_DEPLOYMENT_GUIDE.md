# Vercel 部署指南

## 🚀 部署到 Vercel

### 1. 数据库设置

#### 方式1：使用 Supabase（推荐 ⭐⭐⭐⭐⭐）

**为什么推荐Supabase：**
- 完全免费（500MB存储）
- 设置简单，5分钟完成
- 有可视化管理界面
- 专为现代应用优化

**快速设置：**
1. 访问 [supabase.com](https://supabase.com) 创建项目
2. 获取数据库连接字符串
3. 在Vercel中设置 `POSTGRES_URL` 环境变量

详细步骤请参考：[SUPABASE_SETUP_GUIDE.md](./SUPABASE_SETUP_GUIDE.md)

#### 方式2：使用 Vercel Postgres（如果可用）

**注意：** Vercel Postgres可能在某些地区不可用

1. 登录 [Vercel Dashboard](https://vercel.com/dashboard)
2. 创建新项目或选择现有项目
3. 在项目设置中，点击 "Storage" 选项卡
4. 点击 "Create Database" → 选择 "Postgres"
5. 完成数据库创建后，Vercel 会自动生成 `POSTGRES_URL` 环境变量

#### 方式3：其他免费PostgreSQL服务

- **Neon**（PostgreSQL，免费层3GB）- [neon.tech](https://neon.tech)
- **Railway**（512MB RAM，1GB存储）- [railway.app](https://railway.app)  
- **Render**（90天免费PostgreSQL）- [render.com](https://render.com)
- **ElephantSQL**（20MB免费层）- [elephantsql.com](https://elephantsql.com)

### 2. 环境变量配置

在 Vercel 项目设置的 "Environment Variables" 中添加：

#### 必需变量：
```
POSTGRES_URL=postgresql://username:password@host:port/database
```

#### 可选变量：
```
DEEPSEEK_API_KEY=your-deepseek-api-key
GOOGLE_DRIVE_CREDENTIALS={"type":"service_account",...}
GOOGLE_DRIVE_CREDENTIALS_PATH=path/to/credentials.json
```

### 3. 文件结构

确保项目根目录包含：
```
/
├── server.py                 # 主应用文件
├── models.py                 # 数据库模型（已更新支持PostgreSQL）
├── auth_middleware.py        # 认证中间件
├── requirements.txt          # Python依赖（已更新）
├── vercel.json              # Vercel配置
├── index.html               # 前端文件
├── learning_chatbot.html    # 学习聊天机器人页面
├── online_ide.html          # 在线IDE页面
└── static/                  # 静态资源
```

### 4. 部署步骤

#### 通过 Git 部署（推荐）：

1. 将代码推送到 GitHub/GitLab 仓库
2. 在 Vercel 中导入项目
3. 配置环境变量
4. 部署

#### 通过 Vercel CLI：

```bash
npm install -g vercel
vercel login
vercel --prod
```

### 5. 数据库自动迁移

应用启动时会自动：
1. 检测是否有 `POSTGRES_URL` 环境变量
2. 如果有，使用 PostgreSQL；否则回退到 SQLite（仅本地开发）
3. 自动创建所需的数据库表

### 6. 验证部署

部署成功后，检查：
1. 访问主页：`https://your-app.vercel.app`
2. 检查数据库连接：查看 Vercel 函数日志
3. 测试用户注册/登录功能
4. 测试聊天机器人功能

### 7. 常见问题

#### Q: 数据库连接失败
A: 检查 `POSTGRES_URL` 格式是否正确，确保数据库服务正常运行

#### Q: 函数超时
A: 检查 `vercel.json` 中的 `maxDuration` 设置

#### Q: 模块导入错误
A: 确保 `requirements.txt` 包含所有必需的依赖

#### Q: 静态文件无法访问
A: 检查 `vercel.json` 的路由配置

### 8. 性能优化

1. **数据库连接池**：PostgreSQL 自动管理连接
2. **文件存储**：使用 Google Drive 而非本地存储
3. **缓存**：考虑使用 Vercel KV 存储会话数据
4. **CDN**：静态资源自动通过 Vercel CDN 分发

### 9. 监控和日志

- 在 Vercel Dashboard 中查看函数日志
- 设置错误通知
- 监控数据库连接和查询性能

## 🔐 安全注意事项

1. 不要在代码中硬编码API密钥
2. 使用环境变量存储敏感信息
3. 定期轮换数据库密码
4. 启用数据库SSL连接

## 📊 成本估算

- **Vercel**：免费层足够个人项目使用
- **Vercel Postgres**：免费层包含256MB存储
- **外部数据库**：多数服务商提供免费层 