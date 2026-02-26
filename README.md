# Operation Dashboard - 作战仪表盘 v3.0

> 为考研学习者定制的每日任务管理系统，支持自定义任务和管理后台。

## 核心特性

- **主线/支线任务系统** - 主线必做（打卡依据），支线选做（加分项）
- **24小时灵活完成** - 不强制时段，任意时间可完成
- **自定义任务** - 通过管理后台添加额外任务
- **只读展示页** - `/view` 路由供快速查看
- **管理后台** - `/admin` 路由，密码保护，支持CRUD
- **数据持久化** - SQLite本地存储
- **累计统计+成就系统** - 正向反馈

---

## 页面路由

| 路由 | 说明 | 访问权限 |
|------|------|----------|
| `/` | 主页面（可操作） | 公开 |
| `/view` | 只读展示页 | 公开 |
| `/admin` | 管理后台 | 需登录 |
| `/admin/login` | 登录页 | 公开 |

---

## 管理后台

**默认密码：** `admin123`

**功能：**
- 查看系统内置任务（不可编辑）
- 添加自定义任务（名称、类型、适用星期）
- 编辑自定义任务
- 删除自定义任务

**自定义任务类型：**
- 主线必做 - 计入打卡判断
- 支线选做 - 不计入打卡，做了加分

---

## 快速开始

### 本地运行

```bash
# Windows
start.bat

# Mac/Linux
./start.sh
```

### 访问地址

- 主页面：http://localhost:5000
- 只读页：http://localhost:5000/view
- 管理后台：http://localhost:5000/admin

---

## 云端部署（Render）

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `ADMIN_PASSWORD_HASH` | 管理员密码SHA256哈希 | `admin123`的哈希 |
| `SECRET_KEY` | Flask密钥 | 随机字符串 |
| `DB_PATH` | 数据库路径 | `./data/operations.db` |

### 修改密码

```python
import hashlib
password = "你的新密码"
hash = hashlib.sha256(password.encode()).hexdigest()
print(hash)
```

将输出的哈希值设置到 `ADMIN_PASSWORD_HASH` 环境变量。

---

## 课表安排

### 系统内置主线任务

| 星期 | 类型 | 主线任务 |
|------|------|----------|
| 周一 | 数学日 | 多元微积分 |
| 周二 | CS日 | 数据结构 |
| 周三 | 英语日 | 逻辑内功 |
| 周四 | 数学日 | 微积分进阶 |
| 周五 | 英语实战 | 真题套卷 |
| 周六 | 项目日 | 错题扫除 |
| 周日 | 机动日 | 工作室之夜 |

### 系统内置支线任务

- OGCP录音
- Godot摸鱼
- Kimi语法
- 背单词
- Kimi补漏（周三）
- OpenGuitar数据清洗（周六）
- KimiCode托管（周六）
- 彻底躺平（周日）

---

## API 接口

### 公开接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/today` | GET | 获取今日任务 |
| `/api/week` | GET | 获取本周统计 |
| `/api/export` | GET | 导出数据 |
| `/api/history/{date}` | GET | 获取指定日期 |
| `/api/lifetime` | GET | 累计统计 |
| `/api/achievements` | GET | 成就列表 |

### 管理接口（需登录）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/admin/login` | POST | 登录 |
| `/api/admin/logout` | POST | 登出 |
| `/api/admin/custom-tasks` | GET | 获取自定义任务 |
| `/api/admin/custom-tasks` | POST | 创建任务 |
| `/api/admin/custom-tasks/{id}` | PUT | 更新任务 |
| `/api/admin/custom-tasks/{id}` | DELETE | 删除任务 |
| `/api/admin/system-tasks` | GET | 获取系统任务 |

---

## 文件结构

```
operation_dashboard/
├── server.py          # Flask后端
├── dashboard.html     # 主页面
├── view.html          # 只读展示页
├── admin.html         # 管理后台
├── login.html         # 登录页
├── requirements.txt   # Python依赖
├── render.yaml        # Render配置
├── start.bat          # Windows启动
├── start.sh           # Mac/Linux启动
├── README.md          # 说明文档
└── data/              # 数据库目录
    └── operations.db  # SQLite数据库
```

---

## 许可证

MIT License

---

**祝阿早考研顺利！** 🎯
