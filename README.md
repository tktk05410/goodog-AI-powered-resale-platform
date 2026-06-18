# GoodDog 智能化二手交易平台

基于 Vue3 + Flask + MySQL 的智能化二手交易平台，集成 Qwen3.7-plus 多模态 AI 实现商品自动识别、标签生成、价格估算与文案生成。

## 项目介绍

GoodDog 是一款智能化的二手交易平台，旨在为用户提供一个安全、便捷、智能化的闲置物品交易环境。平台支持商品发布与浏览、即时通讯、订单交易、数据统计等核心功能，并通过 AI 能力辅助用户快速完成商品定价、标签生成与文案撰写，提升交易效率与体验。

> 截图存放位置：`docs/images/`。将对应页面的截图按下方文件名放入该目录后，README 会自动显示。

| 位置 | 文件名 |
|------|--------|
| 首页预览 | `docs/images/home.png` |
| 商品详情 | `docs/images/product-detail.png` |
| 发布商品 | `docs/images/publish.png` |
| 个人中心 | `docs/images/profile.png` |
| 统计页面 | `docs/images/stats.png` |
| 对话页面 | `docs/images/messages.png` |
| 项目管理后台 | `docs/images/admin.png` |

### 首页预览

![首页预览](docs/images/home.png)

### 商品详情

![商品详情](docs/images/product-detail.png)

### 发布商品

![发布商品](docs/images/publish.png)

### 个人中心

![个人中心](docs/images/profile.png)

### 统计页面

![统计页面](docs/images/stats.png)

### 对话页面

![对话页面](docs/images/messages.png)

### 项目管理后台

![项目管理后台](docs/images/admin.png)

## 技术架构

- **前端**: Vue3 + Vite + Element Plus + ECharts
- **后端**: Flask + SQLAlchemy + JWT 认证
- **AI 服务**: Qwen3.7-plus（多模态文本分类 + 图像识别 + 文案生成）
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

### 3. Docker 部署

```bash
docker-compose up -d
```

## 项目结构

```
goodog/
├── app.py                 # 应用入口
├── requirements.txt       # Python 依赖
├── backend/               # 后端代码
│   ├── app.py           # Flask 应用工厂
│   ├── config.py        # 配置文件
│   ├── models.py        # 数据模型
│   └── routes/          # API 路由
│       ├── auth.py
│       ├── products.py
│       ├── transactions.py
│       ├── messages.py
│       ├── users.py
│       ├── ai.py
│       ├── logs.py
│       ├── stats.py
│       ├── admin.py     # 管理员后台
│       └── tags.py      # 标签管理
├── ai_services/          # AI 服务
│   ├── text_classifier.py   # 文本分类、标签生成、价格估算、文案生成
│   └── image_processor.py   # 图像识别与标签生成
├── frontend/             # 前端代码
│   ├── src/
│   │   ├── views/       # 页面组件
│   │   ├── router/      # 路由配置
│   │   ├── store/       # 状态管理
│   │   └── api/         # API 封装
│   └── package.json
├── database/             # 数据库脚本
├── uploads/              # 上传文件目录
└── docker-compose.yml   # Docker 配置
```

## 数据库设计

本项目采用 MySQL 8.0 作为关系型数据库，库名为 `goodog_date`，字符集使用 `utf8mb4` 以支持完整中文与表情符号存储。数据库核心围绕 **用户、商品、交易、消息、标签、日志** 六大业务模块设计，通过外键与索引保证数据一致性与查询效率。

### 核心数据表

| 表名 | 说明 | 关键字段 |
|------|------|----------|
| `user` | 用户信息 | `id`、`username`、`password_hash`、`credit_score`、`face_encoding` |
| `product` | 商品信息 | `id`、`title`、`description`、`type`（sell/buy）、`price`、`status`、`user_id` |
| `transaction` | 交易订单 | `id`、`product_id`、`buyer_id`、`seller_id`、`state`（pending/paid/done/canceled） |
| `message` | 用户消息 | `id`、`from_user`、`to_user`、`content`、`is_read`、`ai_summary` |
| `system_log` | 系统操作日志 | `log_id`、`user_id`、`action`、`detail`（JSON）、`timestamp` |
| `tag` | 标签字典 | `id`、`name`、`color`、`is_ai_generated` |
| `product_tag` | 商品与标签多对多关联 | `id`、`product_id`、`tag_id`、`is_ai_generated` |

### 设计要点

- **用户与商品**：`product.user_id` 外键关联 `user.id`，发布者删除账号时级联删除其商品。
- **商品与交易**：`transaction.product_id` 外键关联 `product.id`，确保每笔交易都有明确商品主体。
- **用户与消息**：`message.from_user` / `to_user` 均外键关联 `user.id`，支持双向会话查询。
- **标签系统**：`tag` 与 `product` 通过中间表 `product_tag` 实现多对多关系，支持 AI 生成标签标识。
- **全文检索**：`product` 表对 `title` 与 `description` 建立 `FULLTEXT` 索引，用于商品搜索。
- **统一字符集**：所有表使用 `utf8mb4_unicode_ci` 排序规则，避免中文与特殊字符存储问题。

完整建表语句见 [`database/init_db.sql`](database/init_db.sql)。

## API 接口

| 模块 | 路径 | 说明 |
|------|------|------|
| 认证 | `/api/auth/*` | 登录、注册、JWT |
| 商品 | `/api/products/*` | CRUD 操作 |
| 交易 | `/api/transactions/*` | 订单状态管理 |
| 消息 | `/api/messages/*` | 即时通讯 |
| 用户 | `/api/users/*` | 个人信息 |
| AI 服务 | `/api/ai/*` | 图像处理、文本分类、价格估算、文案生成 |
| 统计 | `/api/stats/*` | 数据可视化 |
| 日志 | `/api/logs/*` | 操作日志 |
| 标签 | `/api/tags/*` | 标签 CRUD、商品标签管理 |
| 管理后台 | `/api/admin/*` | 数据统计、用户管理、商品管理 |

## 核心功能

### 商品管理
- 商品发布（出售 / 求购）
- 求购商品支持设置"理想价格"
- 图片上传与 AI 识别
- 商品搜索（标题、描述、标签）
- 商品状态管理（上架 / 下架 / 已售出）

### 标签系统
- **AI 自动打标签**：发布商品时，AI 自动分析标题、描述和图片生成相关标签
- **手动管理标签**：用户可在商品详情页和发布页增删改查标签
- **标签搜索**：支持通过标签名称搜索商品
- **标签展示**：商品列表页和详情页展示标签，AI 生成的标签带有"AI"标识

### AI 辅助功能
- **AI 价格估算**：根据商品标题、描述、成色自动估算参考价格区间
- **AI 文案生成**：一键生成商品描述文案，优化商品信息
- **AI 图像识别**：上传图片后自动识别商品类别并生成标签

### 交易管理
- 订单创建与状态流转
- 支付沙盒（支付宝 / 微信 / 余额）
- 交易记录查询

### 消息系统
- 用户间即时通讯
- AI 消息摘要
- 未读消息计数

### 数据统计
- 平台运营数据可视化
- 用户行为分析
- 用户活跃时段统计

### 管理员后台
- **数据概览**：注册用户、商品总数、在售 / 已售、消息总数
- **用户管理**：查看所有用户，可删除非管理员账号
- **商品管理**：查看所有商品，可直接编辑或删除任意商品
- **系统日志**：查看系统操作记录
- 默认管理员账号：`admin` / `admin12345`

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
