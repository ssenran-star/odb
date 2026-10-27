# 今天吃什么 🍽️

选择困难症终结者 - 智能推荐今天吃什么

**在线体验**: https://jin-tian-chi-shen-me-2026-sju7xlq7hm5.qoder.zone

## 功能特性

- 🎰 **转盘随机推荐** - 转一转决定吃什么
- 🔍 **语义搜索** - 输入"想吃辣的"、"清淡的"等自然语言搜索
- 🎯 **智能筛选** - 按菜系、辣度、价位过滤
- 😋 **反馈学习** - 记录喜欢/不喜欢，越用越懂你
- 📋 **历史记录** - 查看最近吃过的，避免重复推荐

## 技术架构

### 前端
- React + TypeScript
- Tailwind CSS + shadcn/ui
- Vite 构建

### 后端
- Deno Edge Function
- seekdb 语义搜索
- PowerContext 用户记忆

### 核心技术集成

#### seekdb - 数据存储与检索
seekdb 是 OceanBase 开源的 AI 原生向量数据库，提供：
- **语义搜索**: 基于向量相似度的自然语言查询
- **混合搜索**: 关键词匹配 + 语义搜索结合
- **自动向量化**: 无需手动计算 embedding

```typescript
// 初始化 seekdb 客户端
const seekdb = new SeekDBClient({
  host: "127.0.0.1",
  port: 2881,
  database: "food_app",
});

// 语义搜索
const results = await seekdb.search("想吃辣的", {
  category: "chinese",
  spicyLevel: 2,
});
```

#### PowerContext - 记忆与上下文
PowerContext 是 OceanBase 开源的 AI Agent 上下文服务，提供：
- **用户偏好记忆**: 保存口味偏好、饮食禁忌
- **历史记录管理**: 追踪用餐历史，避免重复推荐
- **反馈学习**: 根据用户反馈优化推荐

```typescript
// 初始化 PowerContext 客户端
const powerContext = new PowerContextClient({
  baseUrl: "http://127.0.0.1:8000",
  scope: "what-to-eat",
});

// 获取用户偏好
const prefs = await powerContext.getPreferences(userId);

// 记录反馈
await powerContext.updateFeedback(userId, foodId, true);
```

## 项目结构

```
├── src/
│   ├── App.tsx              # 主应用组件
│   ├── components/          # UI 组件
│   │   ├── SpinWheel.tsx    # 转盘组件
│   │   ├── FoodCard.tsx     # 菜品卡片
│   │   ├── FilterPanel.tsx  # 筛选面板
│   │   ├── HistoryPanel.tsx # 历史记录
│   │   └── SearchResults.tsx # 搜索结果
│   ├── data/
│   │   └── foods.ts         # 菜品数据
│   └── lib/
│       └── api.ts           # API 客户端
├── functions/
│   ├── index.ts             # Deno 入口
│   ├── handler.ts           # API 处理器
│   ├── data.ts              # 函数端数据
│   ├── seekdb-client.ts     # seekdb 客户端
│   └── powercontext-client.ts # PowerContext 客户端
├── dist/                    # 构建输出
└── dev/                     # 本地开发
```

## 本地开发

### 前置要求
- Node.js >= 22.13.0
- Deno (用于后端函数)
- seekdb (可选，用于真实语义搜索)
- PowerContext (可选，用于真实用户记忆)

### 安装依赖
```bash
npm ci
```

### 启动开发服务器
```bash
# 前端
npm run dev

# 后端（新终端）
deno run --allow-net=127.0.0.1:8000 dev/function-local.ts
```

### 构建
```bash
npm run build
```

## 部署到 Qoder Sites

项目已通过 Qoder Sites 部署：

```bash
# 准备站点
# 使用 Qoder Desktop 的 Sites 功能自动完成

# 发布
# 通过 Qoder Sites 管理界面发布
```

## 配置真实服务

### seekdb 部署
参考 [seekdb 官方文档](https://github.com/oceanbase/seekdb) 部署 seekdb 服务。

在 `functions/handler.ts` 中设置：
```typescript
const USE_REAL_SERVICES = true;

const SEEKDB_CONFIG = {
  host: "your-seekdb-host",
  port: 2881,
  user: "root",
  password: "",
  database: "food_app",
};
```

### PowerContext 部署
参考 [PowerContext 官方文档](https://github.com/oceanbase/powercontext) 部署 PowerContext 服务。

```bash
# 安装
pip install powercontext

# 启动服务
powercontext server run
```

在 `functions/handler.ts` 中设置：
```typescript
const POWERCONTEXT_CONFIG = {
  baseUrl: "http://your-powercontext-host:8000",
  scope: "what-to-eat",
};
```

## API 接口

### 菜品相关
- `GET /api/foods` - 获取所有菜品（支持筛选）
- `GET /api/foods/search?q=关键词` - 语义搜索
- `GET /api/foods/random` - 随机推荐
- `GET /api/categories` - 获取分类

### 用户相关
- `GET /api/user/preferences` - 获取用户偏好
- `POST /api/user/preferences` - 更新用户偏好
- `GET /api/user/history` - 获取用餐历史
- `POST /api/user/history` - 添加用餐记录
- `POST /api/feedback` - 记录反馈

### 系统相关
- `GET /api/services/status` - 检查服务状态

## 开发过程记录

本项目完全使用 Qoder 开发：

1. **需求拆解**: Qoder 帮助分析功能需求，确定 MVP 范围
2. **代码生成**: 使用 Qoder 生成前端组件和后端 API
3. **调试优化**: Qoder 协助排查问题，优化代码
4. **部署发布**: 通过 Qoder Sites 一键部署

## 许可证

MIT

## 相关链接

- [seekdb](https://github.com/oceanbase/seekdb) - OceanBase 向量数据库
- [PowerContext](https://github.com/oceanbase/powercontext) - AI Agent 上下文服务
- [Qoder](https://qoder.com) - 智能体编程平台
- [seekdb-js](https://github.com/oceanbase/seekdb-js) - JavaScript/TypeScript SDK
