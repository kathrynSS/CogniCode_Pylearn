# Python Learning Platform

这是一个基于Flask的Python学习平台，提供交互式学习体验、项目创建、代码分析等功能。

## 功能特性

- 🤖 AI驱动的学习聊天机器人
- 📊 交互式学习进度图表
- 💻 在线IDE和代码执行
- 📝 个人笔记系统
- 🔐 用户认证和会话管理
- 📁 文件上传和管理
- 🎯 个性化学习项目创建

## 项目结构

```
├── app.py                    # 主应用入口文件 (Vercel)
├── server.py                 # 原始服务器文件 (本地开发)
├── vercel.json              # Vercel配置文件
├── requirements.txt         # Python依赖
├── models.py                # 数据库模型
├── auth_middleware.py       # 认证中间件
├── prompt.py                # AI提示词配置
├── app_database.db          # SQLite数据库
├── index.html               # 主页
├── learning_chatbot.html    # 学习聊天机器人页面
├── graph.html               # 学习进度图表页面
├── auth.html                # 用户认证页面
├── styles.css               # 样式文件
├── script.js                # 主要JavaScript文件
├── notes_fix_complete.js    # 笔记功能JavaScript
├── upload_fix.js            # 文件上传JavaScript
└── Resources/               # 用户上传文件目录
```

## Vercel部署

### 部署准备

1. 确保所有文件结构正确
2. 配置环境变量：
   - `DEEPSEEK_API_KEY`: DeepSeek API密钥（可选，用于AI功能）

### 部署步骤

1. 将项目推送到GitHub仓库
2. 在Vercel控制台导入项目
3. Vercel会自动检测Python项目并使用`vercel.json`配置
4. 配置环境变量（如果需要AI功能）
5. 部署完成

### 重要配置文件

- `vercel.json`: Vercel部署配置
- `app.py`: 主应用入口（从server.py复制并适配）
- `requirements.txt`: Python依赖列表
- `.vercelignore`: 部署时忽略的文件

## 环境变量

```
DEEPSEEK_API_KEY=your-deepseek-api-key-here
```

## 本地开发

如果要在本地运行：

```bash
# 安装依赖
pip install -r requirements.txt

# 运行本地服务器
python server.py
```

访问 http://127.0.0.1:5000

## 注意事项

- 生产环境请使用环境变量存储API密钥
- SQLite数据库在Vercel上是只读的，考虑迁移到外部数据库
- 文件上传功能在Vercel上可能受限，考虑使用云存储服务

## 技术栈

- **后端**: Flask, Python
- **前端**: HTML, CSS, JavaScript
- **数据库**: SQLite
- **AI**: DeepSeek API
- **部署**: Vercel
- **认证**: 自定义JWT会话管理 