# Operation Dashboard - 作战仪表盘 v3.1

> 为考研学习者定制的每日任务管理系统，支持全量任务编辑和管理后台。

## 核心特性

- **主线/支线任务系统** - 主线必做（打卡依据），支线选做（加分项）
- **24小时灵活完成** - 不强制时段，任意时间可完成
- **全量任务可编辑** - 系统内置任务与自定义任务统一管理，均可增删改
- **只读展示页** - `/view` 路由供快速查看
- **管理后台** - `/admin` 路由，密码保护，支持CRUD
- **数据持久化** - SQLite本地存储，支持数据库导入/导出
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
- 查看所有任务模板（系统内置 + 自定义，均可编辑）
- 添加任务模板（名称、类型、适用星期）
- 编辑任务模板
- 删除任务模板
- 导出/导入数据库文件（用于备份与迁移）

**任务类型：**
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

### 系统内置主线任务（首次启动时导入，之后可在管理后台编辑）

| 星期 | 类型 | 主线任务 |
|------|------|----------|
| 周一 | 数学日 | 多元微积分(梯度/极值/重积分) |
| 周二 | CS日 | 数据结构(树/图/C语言) |
| 周三 | 英语日 | 逻辑内功(段落逻辑/长难句) |
| 周四 | 数学日 | 微积分进阶(计算/应用题) |
| 周五 | 英语实战 | 真题套卷(2010后真题) |
| 周六 | 项目日 | 错题扫除(不学新课) |
| 周日 | 机动日 | 工作室之夜(非强制) |

### 系统内置支线任务

- OGCP录音（周一至周五）
- Godot摸鱼（周一、二、三、四、六、日）
- Kimi语法（周一、二、三、四、五）
- 背单词（周一至周五）
- Kimi补漏·虚拟语气（周三）
- OpenGuitar数据清洗（周六）
- KimiCode托管（周六）
- 彻底躺平、陪家人、出游（周日）

---

## API 接口

### 公开接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/today` | GET | 获取今日任务及统计 |
| `/api/week` | GET | 获取本周7天统计 |
| `/api/export` | GET | 导出全量数据（JSON） |
| `/api/history/<date>` | GET | 获取指定日期记录 |
| `/api/history/range/<start>/<end>` | GET | 获取日期范围内历史记录 |
| `/api/lifetime` | GET | 获取累计统计 |
| `/api/achievements` | GET | 获取成就列表 |
| `/api/task/<id>` | POST | 切换任务完成状态 |

### 管理接口（需登录）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/admin/login` | POST | 登录 |
| `/api/admin/logout` | POST | 登出 |
| `/api/admin/check-auth` | GET | 检查登录状态 |
| `/api/admin/task-templates` | GET | 获取所有任务模板 |
| `/api/admin/task-templates` | POST | 创建任务模板 |
| `/api/admin/task-templates/<id>` | PUT | 更新任务模板 |
| `/api/admin/task-templates/<id>` | DELETE | 删除任务模板 |
| `/api/admin/export-db` | GET | 导出数据库文件（.db） |
| `/api/admin/import-db` | POST | 导入数据库文件（.db） |

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

**祝所有人考研顺利！** 🎯
