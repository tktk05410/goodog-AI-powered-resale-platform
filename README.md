# GoodDog 校园二手交易平台

基于Vue3 + Flask + MySQL的校园二手交易平台，集成Qwen3.7-plus多模态AI实现商品自动识别与标签生成。

## 技术架构

- **前端**: Vue3 + Vite + Element Plus + ECharts
- **后端**: Flask + SQLAlchemy + JWT认证
- **AI服务**: Qwen3.7-plus（多模态文本分类 + 图像识别）
- **数据库**: MySQL 8.0
- **部署**: Docker + Nginx

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- MySQL 8.0
- Docker (可选)

### 1. 后端启动

```bash
cd backend
pip install -r requirements.txt
python app.py
```

### 2. 前端启动

```bash
cd frontend
npm install
npm run dev
```

### 3. Docker部署

```bash
docker-compose up -d
```

## 项目结构

```
goodog/
├── app.py                 # 应用入口
├── requirements.txt       # Python依赖
├── backend/               # 后端代码
│   ├── app.py           # Flask应用工厂
│   ├── config.py        # 配置文件
│   ├── models.py        # 数据模型
│   └── routes/          # API路由
│       ├── auth.py
│       ├── products.py
│       ├── transactions.py
│       ├── messages.py
│       ├── users.py
│       ├── ai.py
│       ├── logs.py
│       ├── stats.py
│       └── tags.py      # 标签管理
├── ai_services/          # AI服务
│   ├── text_classifier.py   # 文本分类与标签生成
│   └── image_processor.py   # 图像识别与标签生成
├── frontend/             # 前端代码
│   ├── src/
│   │   ├── views/       # 页面组件
│   │   ├── router/      # 路由配置
│   │   ├── store/       # 状态管理
│   │   └── api/         # API封装
│   └── package.json
├── database/             # 数据库脚本
├── uploads/              # 上传文件目录
└── docker-compose.yml   # Docker配置
```

## API接口

| 模块 | 路径 | 说明 |
|------|------|------|
| 认证 | `/api/auth/*` | 登录、注册、JWT |
| 商品 | `/api/products/*` | CRUD操作 |
| 交易 | `/api/transactions/*` | 订单状态管理 |
| 消息 | `/api/messages/*` | 即时通讯 |
| 用户 | `/api/users/*` | 个人信息 |
| AI服务 | `/api/ai/*` | 图像处理、文本分类 |
| 统计 | `/api/stats/*` | 数据可视化 |
| 日志 | `/api/logs/*` | 操作日志 |
| 标签 | `/api/tags/*` | 标签CRUD、商品标签管理 |

## 核心功能

### 标签系统
- **AI自动打标签**：发布商品时，AI自动分析标题、描述和图片生成相关标签
- **手动管理标签**：用户可在商品详情页和发布页增删改查标签
- **标签搜索**：支持通过标签名称搜索商品
- **标签展示**：商品列表页和详情页展示标签，AI生成的标签带有"AI"标识

### 商品管理
- 商品发布（出售/求购）
- 图片上传与AI识别
- 商品搜索（标题、描述、标签）
- 商品状态管理

### 交易管理
- 订单创建与状态流转
- 交易记录查询

### 消息系统
- 用户间即时通讯
- AI消息摘要

### 数据统计
- 平台运营数据可视化
- 用户行为分析

## 环境变量

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=goodog_date
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
```
