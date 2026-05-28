#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Operation Dashboard - 作战仪表盘 v3.1
为考研学习者定制的每日任务管理系统
版本：3.1 - 所有任务可编辑
"""

import os
import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from functools import wraps
from flask import Flask, jsonify, request, send_from_directory, redirect, session, send_file
from flask_cors import CORS
import shutil 

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'operation-dashboard-secret-key-2024')
CORS(app)

# 配置
DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(__file__), 'data', 'operations.db'))
STATIC_PATH = os.path.dirname(__file__)
ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH', hashlib.sha256('admin123'.encode()).hexdigest())

# # 时区配置：北京时间 UTC+8
# BEIJING_OFFSET = timedelta(hours=8)

def now():
    """获取当前北京时间（无论服务器/本地时区如何，都正确）"""
    return datetime.now(ZoneInfo("Asia/Shanghai"))
    return datetime.now(ZoneInfo("America/New_York"))

    # """获取当前本地时间"""
    # return datetime.now()  # 自动使用系统时区

# 默认任务模板 - 首次运行时导入数据库（之后可编辑）
DEFAULT_TASKS = [
    # 周一 - 数学日
    {"name": "多元微积分(梯度/极值/重积分)", "category": "main", "weekdays": "0"},
    {"name": "OGCP录音", "category": "optional", "weekdays": "0"},
    {"name": "Godot摸鱼", "category": "optional", "weekdays": "0"},
    {"name": "Kimi语法", "category": "optional", "weekdays": "0"},
    {"name": "背单词", "category": "optional", "weekdays": "0,1,2,3,4"},
    # 周二 - CS日
    {"name": "数据结构(树/图/C语言)", "category": "main", "weekdays": "1"},
    {"name": "OGCP录音", "category": "optional", "weekdays": "1"},
    {"name": "Godot摸鱼", "category": "optional", "weekdays": "1"},
    {"name": "Kimi语法", "category": "optional", "weekdays": "1"},
    # 周三 - 英语日
    {"name": "逻辑内功(段落逻辑/长难句)", "category": "main", "weekdays": "2"},
    {"name": "Kimi补漏(虚拟语气)", "category": "optional", "weekdays": "2"},
    {"name": "OGCP录音", "category": "optional", "weekdays": "2"},
    # 周四 - 数学日
    {"name": "微积分进阶(计算/应用题)", "category": "main", "weekdays": "3"},
    {"name": "OGCP录音", "category": "optional", "weekdays": "3"},
    {"name": "Godot摸鱼", "category": "optional", "weekdays": "3"},
    {"name": "Kimi语法", "category": "optional", "weekdays": "3"},
    # 周五 - 英语实战
    {"name": "真题套卷(2010后真题)", "category": "main", "weekdays": "4"},
    {"name": "Kimi语法", "category": "optional", "weekdays": "4"},
    {"name": "OGCP录音", "category": "optional", "weekdays": "4"},
    # 周六 - 假期
    {"name": "错题扫除(不学新课)", "category": "main", "weekdays": "5"},
    {"name": "OpenGuitar数据清洗", "category": "optional", "weekdays": "5"},
    {"name": "KimiCode托管", "category": "optional", "weekdays": "5"},
    {"name": "Godot摸鱼", "category": "optional", "weekdays": "5"},
    # 周日 - CS日
    {"name": "工作室之夜(非强制)", "category": "main", "weekdays": "6"},
    {"name": "彻底躺平、陪家人、出游", "category": "optional", "weekdays": "6"},
    {"name": "Godot摸鱼", "category": "optional", "weekdays": "6"},
]

# 星期类型映射
DAY_TYPES = {
    0: "数学日",
    1: "英语日",
    2: "CS日",
    3: "数学日",
    4: "英语实战",
    5: "假期",
    6: "CS日"
}

# 成就系统配置
ACHIEVEMENTS = {
    "first_blood": {"id": "first_blood", "name": "首战告捷", "desc": "完成第一个任务", "icon": "🎯"},
    "streak_3": {"id": "streak_3", "name": "三连击", "desc": "连续打卡3天", "icon": "🔥"},
    "streak_7": {"id": "streak_7", "name": "一周战士", "desc": "连续打卡7天", "icon": "⚡"},
    "streak_30": {"id": "streak_30", "name": "月度冠军", "desc": "连续打卡30天", "icon": "👑"},
    "perfect_day": {"id": "perfect_day", "name": "完美一天", "desc": "主线+支线全部完成", "icon": "💎"},
    "task_master": {"id": "task_master", "name": "任务大师", "desc": "累计完成100个任务", "icon": "🏆"},
    "main_master": {"id": "main_master", "name": "主线达人", "desc": "累计完成50个主线任务", "icon": "🥇"},
    "math_master": {"id": "math_master", "name": "数学达人", "desc": "完成10个数学日", "icon": "📐"},
    "cs_master": {"id": "cs_master", "name": "CS专家", "desc": "完成10个CS日", "icon": "💻"},
    "english_master": {"id": "english_master", "name": "英语通", "desc": "完成10个英语日", "icon": "📚"}
}


def init_database():
    """初始化SQLite数据库 - v3.1版本"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 任务模板表 - 存储所有任务定义（包括原系统任务）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT NOT NULL,
            task_category TEXT DEFAULT 'optional',
            weekdays TEXT NOT NULL,
            is_system INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 每日任务实例表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            task_name TEXT NOT NULL,
            task_type TEXT NOT NULL,
            task_category TEXT DEFAULT 'optional',
            template_id INTEGER,
            completed INTEGER DEFAULT 0,
            completed_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date, task_name)
        )
    ''')
    
    # 每日统计表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE NOT NULL,
            total_tasks INTEGER DEFAULT 0,
            main_tasks INTEGER DEFAULT 0,
            main_completed INTEGER DEFAULT 0,
            optional_tasks INTEGER DEFAULT 0,
            optional_completed INTEGER DEFAULT 0,
            completion_rate REAL DEFAULT 0,
            main_completed_rate REAL DEFAULT 0,
            day_type TEXT,
            is_valid_checkin INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 连续打卡记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS streak_record (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            current_streak INTEGER DEFAULT 0,
            max_streak INTEGER DEFAULT 0,
            last_check_date TEXT
        )
    ''')
    
    # 成就表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            achievement_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            icon TEXT,
            unlocked_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 累计统计表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lifetime_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_tasks_completed INTEGER DEFAULT 0,
            main_tasks_completed INTEGER DEFAULT 0,
            optional_tasks_completed INTEGER DEFAULT 0,
            total_study_days INTEGER DEFAULT 0,
            total_perfect_days INTEGER DEFAULT 0,
            math_days INTEGER DEFAULT 0,
            cs_days INTEGER DEFAULT 0,
            english_days INTEGER DEFAULT 0,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 初始化连续打卡记录
    cursor.execute('SELECT COUNT(*) FROM streak_record')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO streak_record (current_streak, max_streak) VALUES (0, 0)')
    
    # 初始化累计统计
    cursor.execute('SELECT COUNT(*) FROM lifetime_stats')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO lifetime_stats DEFAULT VALUES')
    
    # 初始化默认任务（如果任务表为空）
    cursor.execute('SELECT COUNT(*) FROM task_templates')
    if cursor.fetchone()[0] == 0:
        for task in DEFAULT_TASKS:
            cursor.execute('''
                INSERT INTO task_templates (task_name, task_category, weekdays, is_system)
                VALUES (?, ?, ?, 1)
            ''', (task['name'], task['category'], task['weekdays']))
    
    conn.commit()
    conn.close()


def get_db_connection():
    """获取数据库连接 - 添加超时和隔离级别设置"""
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    # 启用WAL模式以提高并发性能
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=5000')
    return conn


def get_task_templates(weekday=None):
    """获取任务模板列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if weekday is not None:
        # 使用 ',' || weekdays || ',' 来统一处理各种位置匹配
        # 例如: weekdays="0,1,2,3,4" 变成 ",0,1,2,3,4,"
        # 然后匹配 ",3," 即可找到任意位置的 weekday
        cursor.execute('''
            SELECT * FROM task_templates 
            WHERE weekdays = 'all' 
               OR ',' || weekdays || ',' LIKE ?
        ''', (f'%,{weekday},%',))
    else:
        cursor.execute('SELECT * FROM task_templates ORDER BY id')
    
    tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tasks


def generate_daily_tasks(date_str=None):
    """生成指定日期的任务列表"""
    if date_str is None:
        date_str = now().strftime('%Y-%m-%d')
    
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    weekday = date_obj.weekday()
    day_type = DAY_TYPES.get(weekday, "学习日")
    
    # 获取适用的任务模板
    templates = get_task_templates(weekday)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    tasks = []
    
    for template in templates:
        # 检查今日是否已存在该任务（通过任务名称精确匹配）
        cursor.execute('''
            SELECT id, completed, completed_at, template_id FROM tasks 
            WHERE date = ? AND task_name = ?
        ''', (date_str, template['task_name']))
        row = cursor.fetchone()
        
        if row:
            # 已存在，更新template_id关联并返回现有记录
            if row['template_id'] != template['id']:
                cursor.execute('''
                    UPDATE tasks SET template_id = ? WHERE id = ?
                ''', (template['id'], row['id']))
                conn.commit()
            
            tasks.append({
                "id": row['id'],
                "name": template['task_name'],
                "type": template['task_category'],
                "category": template['task_category'],
                "templateId": template['id'],
                "isSystem": bool(template['is_system']),
                "completed": bool(row['completed']),
                "completedAt": row['completed_at']
            })
        else:
            # 创建新任务实例，使用INSERT OR IGNORE避免冲突
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO tasks (date, task_name, task_type, task_category, template_id, completed)
                    VALUES (?, ?, ?, ?, ?, 0)
                ''', (date_str, template['task_name'], template['task_category'], 
                      template['task_category'], template['id']))
                conn.commit()
                
                # 获取刚插入或已存在的记录ID
                cursor.execute('''
                    SELECT id, completed, completed_at FROM tasks WHERE date = ? AND task_name = ?
                ''', (date_str, template['task_name']))
                row = cursor.fetchone()
                
                if row:
                    tasks.append({
                        "id": row['id'],
                        "name": template['task_name'],
                        "type": template['task_category'],
                        "category": template['task_category'],
                        "templateId": template['id'],
                        "isSystem": bool(template['is_system']),
                        "completed": bool(row['completed']),
                        "completedAt": row['completed_at']
                    })
            except Exception as e:
                print(f"Error inserting task {template['task_name']}: {e}")
                continue
    
    conn.close()
    
    # 按类别排序：主线在前，支线在后
    tasks.sort(key=lambda x: (0 if x['category'] == 'main' else 1, x['id']))
    
    return tasks, day_type


def update_daily_stats(date_str, day_type=None):
    """更新每日统计"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 统计主线任务
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(completed) as completed
        FROM tasks WHERE date = ? AND task_category = 'main'
    ''', (date_str,))
    main_row = cursor.fetchone()
    main_total = main_row['total'] or 0
    main_completed = main_row['completed'] or 0
    main_rate = (main_completed / main_total * 100) if main_total > 0 else 0
    
    # 统计支线任务
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(completed) as completed
        FROM tasks WHERE date = ? AND task_category = 'optional'
    ''', (date_str,))
    opt_row = cursor.fetchone()
    opt_total = opt_row['total'] or 0
    opt_completed = opt_row['completed'] or 0
    
    total = main_total + opt_total
    total_completed = main_completed + opt_completed
    total_rate = (total_completed / total * 100) if total > 0 else 0
    
    # 主线必须100%完成才算有效打卡
    is_valid_checkin = 1 if main_completed >= main_total and main_total > 0 else 0
    
    cursor.execute('''
        INSERT OR REPLACE INTO daily_stats 
        (date, total_tasks, main_tasks, main_completed, optional_tasks, optional_completed,
         completion_rate, main_completed_rate, day_type, is_valid_checkin)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (date_str, total, main_total, main_completed, opt_total, opt_completed,
          total_rate, main_rate, day_type, is_valid_checkin))
    
    conn.commit()
    conn.close()
    
    return {
        "total": total,
        "completed": total_completed,
        "rate": total_rate,
        "mainTotal": main_total,
        "mainCompleted": main_completed,
        "mainRate": main_rate,
        "optionalTotal": opt_total,
        "optionalCompleted": opt_completed,
        "isValidCheckin": bool(is_valid_checkin)
    }


def get_streak_info():
    """获取连续打卡信息"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM streak_record LIMIT 1')
    record = cursor.fetchone()
    
    if record is None:
        conn.close()
        return {"current": 0, "max": 0}
    
    current_streak = record['current_streak']
    max_streak = record['max_streak']
    last_check = record['last_check_date']
    
    today = now().strftime('%Y-%m-%d')
    yesterday = (now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    if last_check == today or last_check == yesterday:
        conn.close()
        return {"current": current_streak, "max": max_streak}
    else:
        cursor.execute('UPDATE streak_record SET current_streak = 0')
        conn.commit()
        conn.close()
        return {"current": 0, "max": max_streak}


def update_streak(date_str):
    """更新连续打卡天数"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT is_valid_checkin FROM daily_stats WHERE date = ?
    ''', (date_str,))
    row = cursor.fetchone()
    
    if row and row['is_valid_checkin']:
        cursor.execute('SELECT * FROM streak_record LIMIT 1')
        record = cursor.fetchone()
        
        last_check = record['last_check_date']
        yesterday = (datetime.strptime(date_str, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
        
        if last_check == yesterday or last_check == date_str:
            new_streak = record['current_streak'] + 1 if last_check != date_str else record['current_streak']
            new_max = max(new_streak, record['max_streak'])
            
            cursor.execute('''
                UPDATE streak_record 
                SET current_streak = ?, max_streak = ?, last_check_date = ?
            ''', (new_streak, new_max, date_str))
        else:
            cursor.execute('''
                UPDATE streak_record 
                SET current_streak = 1, last_check_date = ?
            ''', (date_str,))
        
        conn.commit()
    
    conn.close()


def get_week_stats():
    """获取本周7天统计"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    today = now()
    week_data = []
    
    for i in range(7):
        date_obj = today - timedelta(days=6-i)
        date_str = date_obj.strftime('%Y-%m-%d')
        weekday = date_obj.weekday()
        
        cursor.execute('''
            SELECT * FROM daily_stats WHERE date = ?
        ''', (date_str,))
        row = cursor.fetchone()
        
        if row:
            week_data.append({
                "date": date_str,
                "weekday": ["一", "二", "三", "四", "五", "六", "日"][weekday],
                "rate": row['completion_rate'],
                "mainRate": row['main_completed_rate'],
                "completed": row['main_completed'],
                "total": row['main_tasks'],
                "isValidCheckin": bool(row['is_valid_checkin']),
                "dayType": row['day_type']
            })
        else:
            tasks, day_type = generate_daily_tasks(date_str)
            main_tasks = [t for t in tasks if t['category'] == 'main']
            completed = sum(1 for t in main_tasks if t['completed'])
            total = len(main_tasks)
            rate = (completed / total * 100) if total > 0 else 0
            
            week_data.append({
                "date": date_str,
                "weekday": ["一", "二", "三", "四", "五", "六", "日"][weekday],
                "rate": rate,
                "mainRate": rate,
                "completed": completed,
                "total": total,
                "isValidCheckin": completed >= total and total > 0,
                "dayType": day_type
            })
    
    conn.close()
    return week_data


def get_lifetime_stats():
    """获取累计学习统计"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM lifetime_stats LIMIT 1')
    record = cursor.fetchone()
    
    if record is None:
        conn.close()
        return {
            "totalTasks": 0,
            "mainTasks": 0,
            "optionalTasks": 0,
            "studyDays": 0,
            "perfectDays": 0,
            "mathDays": 0,
            "csDays": 0,
            "englishDays": 0
        }
    
    conn.close()
    return {
        "totalTasks": record['total_tasks_completed'],
        "mainTasks": record['main_tasks_completed'],
        "optionalTasks": record['optional_tasks_completed'],
        "studyDays": record['total_study_days'],
        "perfectDays": record['total_perfect_days'],
        "mathDays": record['math_days'],
        "csDays": record['cs_days'],
        "englishDays": record['english_days']
    }


def adjust_lifetime_stats(task_category, delta):
    """调整累计统计"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if task_category == 'main':
        cursor.execute('''
            UPDATE lifetime_stats SET
                total_tasks_completed = MAX(0, total_tasks_completed + ?),
                main_tasks_completed = MAX(0, main_tasks_completed + ?),
                updated_at = CURRENT_TIMESTAMP
        ''', (delta, delta))
    else:
        cursor.execute('''
            UPDATE lifetime_stats SET
                total_tasks_completed = MAX(0, total_tasks_completed + ?),
                optional_tasks_completed = MAX(0, optional_tasks_completed + ?),
                updated_at = CURRENT_TIMESTAMP
        ''', (delta, delta))
    
    conn.commit()
    conn.close()


def check_achievements():
    """检查并解锁成就"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT achievement_id FROM achievements')
    unlocked = {row['achievement_id'] for row in cursor.fetchall()}
    
    cursor.execute('SELECT * FROM lifetime_stats LIMIT 1')
    stats = cursor.fetchone()
    
    cursor.execute('SELECT * FROM streak_record LIMIT 1')
    streak = cursor.fetchone()
    
    new_achievements = []
    
    if stats:
        if stats['total_tasks_completed'] >= 1 and 'first_blood' not in unlocked:
            new_achievements.append('first_blood')
        if stats['total_tasks_completed'] >= 100 and 'task_master' not in unlocked:
            new_achievements.append('task_master')
        if stats['main_tasks_completed'] >= 50 and 'main_master' not in unlocked:
            new_achievements.append('main_master')
        if stats['math_days'] >= 10 and 'math_master' not in unlocked:
            new_achievements.append('math_master')
        if stats['cs_days'] >= 10 and 'cs_master' not in unlocked:
            new_achievements.append('cs_master')
        if stats['english_days'] >= 10 and 'english_master' not in unlocked:
            new_achievements.append('english_master')
    
    if streak:
        if streak['current_streak'] >= 3 and 'streak_3' not in unlocked:
            new_achievements.append('streak_3')
        if streak['current_streak'] >= 7 and 'streak_7' not in unlocked:
            new_achievements.append('streak_7')
        if streak['current_streak'] >= 30 and 'streak_30' not in unlocked:
            new_achievements.append('streak_30')
    
    for ach_id in new_achievements:
        ach = ACHIEVEMENTS[ach_id]
        cursor.execute('''
            INSERT INTO achievements (achievement_id, name, description, icon)
            VALUES (?, ?, ?, ?)
        ''', (ach['id'], ach['name'], ach['desc'], ach['icon']))
    
    conn.commit()
    conn.close()
    
    return [ACHIEVEMENTS[ach_id] for ach_id in new_achievements]


def get_all_achievements():
    """获取所有成就状态"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT achievement_id FROM achievements')
    unlocked = {row['achievement_id'] for row in cursor.fetchall()}
    
    conn.close()
    
    result = []
    for ach_id, ach in ACHIEVEMENTS.items():
        result.append({**ach, "unlocked": ach_id in unlocked})
    
    return result


def get_completed_tasks_by_date(date_str):
    """获取指定日期已完成的任务详情"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT task_name, task_category, completed_at 
        FROM tasks 
        WHERE date = ? AND completed = 1
        ORDER BY completed_at
    ''', (date_str,))
    
    tasks = []
    for row in cursor.fetchall():
        tasks.append({
            "name": row['task_name'],
            "category": row['task_category'],
            "completedAt": row['completed_at']
        })
    
    conn.close()
    return tasks


# ==================== 登录验证装饰器 ====================

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect('/admin/login')
        return f(*args, **kwargs)
    return decorated_function


# ==================== 页面路由 ====================

@app.route('/')
def index():
    """返回主页面"""
    return send_from_directory(STATIC_PATH, 'dashboard.html')


@app.route('/view')
def view_page():
    """返回只读展示页面"""
    return send_from_directory(STATIC_PATH, 'view.html')


@app.route('/admin')
@admin_required
def admin_page():
    """返回管理后台页面"""
    return send_from_directory(STATIC_PATH, 'admin.html')


@app.route('/admin/login')
def admin_login_page():
    """返回登录页面"""
    return send_from_directory(STATIC_PATH, 'login.html')


# ==================== API 路由 ====================



@app.route('/api/today')
def get_today():
    """获取今日任务列表+状态"""
    date_str = now().strftime('%Y-%m-%d')
    tasks, day_type = generate_daily_tasks(date_str)
    stats = update_daily_stats(date_str, day_type)
    streak = get_streak_info()
    lifetime = get_lifetime_stats()
    achievements = get_all_achievements()
    completed_tasks = get_completed_tasks_by_date(date_str)
    
    # 分离主线和支线任务
    main_tasks = [t for t in tasks if t['category'] == 'main']
    optional_tasks = [t for t in tasks if t['category'] == 'optional']
    
    return jsonify({
        "date": date_str,
        "weekday": now().weekday(),
        "dayType": day_type,
        "mainTasks": main_tasks,
        "optionalTasks": optional_tasks,
        "allTasks": tasks,
        "completedTasks": completed_tasks,
        "stats": stats,
        "streak": streak,
        "lifetime": lifetime,
        "achievements": achievements
    })


@app.route('/api/task/<int:task_id>', methods=['POST'])
def toggle_task(task_id):
    """切换任务完成状态"""
    date_str = now().strftime('%Y-%m-%d')
    data = request.get_json() or {}
    new_completed = data.get('completed', True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取任务当前状态
    cursor.execute('''
        SELECT task_name, task_category, completed FROM tasks WHERE date = ? AND id = ?
    ''', (date_str, task_id))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return jsonify({"success": False, "error": "Task not found"}), 404
    
    task_category = row['task_category']
    old_completed = bool(row['completed'])
    
    # 更新任务状态
    completed_at = now().strftime('%Y-%m-%d %H:%M:%S') if new_completed else None
    cursor.execute('''
        UPDATE tasks SET completed = ?, completed_at = ? WHERE date = ? AND id = ?
    ''', (1 if new_completed else 0, completed_at, date_str, task_id))
    conn.commit()
    conn.close()
    
    weekday = now().weekday()
    day_type = DAY_TYPES.get(weekday, "学习日")
    
    # 更新每日统计
    stats = update_daily_stats(date_str, day_type)
    
    # 根据状态变化调整累计统计
    if old_completed != new_completed:
        if new_completed:
            adjust_lifetime_stats(task_category, 1)
        else:
            adjust_lifetime_stats(task_category, -1)
    
    # 更新连续打卡
    update_streak(date_str)
    
    # 检查成就
    new_achievements = []
    if new_completed and not old_completed:
        new_achievements = check_achievements()
    
    return jsonify({
        "success": True,
        "taskId": task_id,
        "completed": new_completed,
        "completedAt": now().strftime('%H:%M') if new_completed else None,
        "stats": stats,
        "newAchievements": new_achievements
    })


@app.route('/api/week')
def get_week():
    """获取本周7天统计"""
    week_data = get_week_stats()
    streak = get_streak_info()
    
    return jsonify({
        "weekData": week_data,
        "streak": streak
    })


@app.route('/api/export')
def export_data():
    """导出所有数据为JSON"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM tasks ORDER BY date')
    tasks = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute('SELECT * FROM daily_stats ORDER BY date')
    stats = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute('SELECT * FROM streak_record LIMIT 1')
    streak = dict(cursor.fetchone()) if cursor.fetchone() else {}
    
    cursor.execute('SELECT * FROM lifetime_stats LIMIT 1')
    lifetime = dict(cursor.fetchone()) if cursor.fetchone() else {}
    
    cursor.execute('SELECT * FROM achievements')
    achievements = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute('SELECT * FROM task_templates')
    templates = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({
        "exportTime": now().strftime('%Y-%m-%d %H:%M:%S'),
        "tasks": tasks,
        "dailyStats": stats,
        "streak": streak,
        "lifetime": lifetime,
        "achievements": achievements,
        "taskTemplates": templates
    })


@app.route('/api/history/<date_str>')
def get_history(date_str):
    """获取指定日期的任务完成情况"""
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400
    
    tasks, day_type = generate_daily_tasks(date_str)
    completed_tasks = get_completed_tasks_by_date(date_str)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM daily_stats WHERE date = ?', (date_str,))
    stats_row = cursor.fetchone()
    
    conn.close()
    
    main_tasks = [t for t in tasks if t['category'] == 'main']
    
    stats = {
        "total": stats_row['total_tasks'] if stats_row else len(tasks),
        "completed": stats_row['main_completed'] if stats_row else sum(1 for t in main_tasks if t['completed']),
        "rate": stats_row['completion_rate'] if stats_row else 0,
        "mainRate": stats_row['main_completed_rate'] if stats_row else 0,
        "isValidCheckin": stats_row['is_valid_checkin'] if stats_row else False
    }
    
    return jsonify({
        "date": date_str,
        "dayType": day_type,
        "tasks": tasks,
        "completedTasks": completed_tasks,
        "stats": stats
    })


@app.route('/api/history/range/<start_date>/<end_date>')
def get_history_range(start_date, end_date):
    """获取日期范围内的历史记录"""
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 查询日期范围内所有已有的记录
    cursor.execute('''
        SELECT * FROM daily_stats 
        WHERE date >= ? AND date <= ?
        ORDER BY date DESC
    ''', (start_date, end_date))
    
    # 将查询结果存入字典，方便查找
    existing_records = {}
    for row in cursor.fetchall():
        existing_records[row['date']] = {
            "date": row['date'],
            "dayType": row['day_type'],
            "total": row['total_tasks'],
            "completed": row['main_completed'],
            "rate": row['completion_rate'],
            "mainRate": row['main_completed_rate'],
            "isValidCheckin": bool(row['is_valid_checkin'])
        }
    
    conn.close()
    
    # 填充日期范围内所有日期，没有记录的显示为0%
    history = []
    current = end
    while current >= start:
        date_str = current.strftime('%Y-%m-%d')
        weekday = current.weekday()
        day_type = DAY_TYPES.get(weekday, "学习日")
        
        if date_str in existing_records:
            history.append(existing_records[date_str])
        else:
            # 没有打卡记录，生成当日任务模板获取主线任务数
            tasks, _ = generate_daily_tasks(date_str)
            main_tasks = [t for t in tasks if t['category'] == 'main']
            main_total = len(main_tasks)
            
            history.append({
                "date": date_str,
                "dayType": day_type,
                "total": main_total,
                "completed": 0,
                "rate": 0.0,
                "mainRate": 0.0,
                "isValidCheckin": False
            })
        
        current -= timedelta(days=1)
    
    return jsonify({
        "startDate": start_date,
        "endDate": end_date,
        "history": history
    })


@app.route('/api/lifetime')
def get_lifetime():
    """获取累计学习统计"""
    lifetime = get_lifetime_stats()
    achievements = get_all_achievements()
    
    return jsonify({
        "lifetime": lifetime,
        "achievements": achievements
    })


@app.route('/api/achievements')
def get_achievements():
    """获取所有成就"""
    achievements = get_all_achievements()
    return jsonify({"achievements": achievements})


# ==================== 管理后台 API ====================

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """管理员登录"""
    data = request.get_json() or {}
    password = data.get('password', '')
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    if password_hash == ADMIN_PASSWORD_HASH:
        session['admin_logged_in'] = True
        return jsonify({"success": True, "message": "登录成功"})
    else:
        return jsonify({"success": False, "error": "密码错误"}), 401


@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    """管理员登出"""
    session.pop('admin_logged_in', None)
    return jsonify({"success": True, "message": "已登出"})


@app.route('/api/admin/check-auth')
@admin_required
def check_admin_auth():
    """检查管理员登录状态"""
    return jsonify({"authenticated": True})


@app.route('/api/admin/task-templates')
@admin_required
def get_all_task_templates():
    """获取所有任务模板"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM task_templates ORDER BY id')
    templates = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return jsonify({"templates": templates})


@app.route('/api/admin/task-templates', methods=['POST'])
@admin_required
def create_task_template():
    """创建任务模板"""
    data = request.get_json() or {}
    
    task_name = data.get('task_name', '').strip()
    task_category = data.get('task_category', 'optional')
    weekdays = data.get('weekdays', 'all')
    
    if not task_name:
        return jsonify({"success": False, "error": "任务名称不能为空"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO task_templates (task_name, task_category, weekdays, is_system)
            VALUES (?, ?, ?, 0)
        ''', (task_name, task_category, weekdays))
        conn.commit()
        template_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "任务创建成功",
            "template": {
                "id": template_id,
                "task_name": task_name,
                "task_category": task_category,
                "weekdays": weekdays,
                "is_system": 0
            }
        })
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"success": False, "error": "任务名称已存在"}), 400


@app.route('/api/admin/task-templates/<int:template_id>', methods=['PUT'])
@admin_required
def update_task_template(template_id):
    """更新任务模板"""
    data = request.get_json() or {}
    
    task_name = data.get('task_name', '').strip()
    task_category = data.get('task_category', 'optional')
    weekdays = data.get('weekdays', 'all')
    
    if not task_name:
        return jsonify({"success": False, "error": "任务名称不能为空"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE task_templates 
        SET task_name = ?, task_category = ?, weekdays = ?
        WHERE id = ?
    ''', (task_name, task_category, weekdays, template_id))
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"success": False, "error": "任务不存在"}), 404
    
    conn.commit()
    conn.close()
    
    # 更新今日及未来的任务实例名称
    today = now().strftime('%Y-%m-%d')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE tasks 
        SET task_name = ?, task_category = ?, task_type = ?
        WHERE template_id = ? AND date >= ? AND completed = 0
    ''', (task_name, task_category, task_category, template_id, today))
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "message": "任务更新成功",
        "template": {
            "id": template_id,
            "task_name": task_name,
            "task_category": task_category,
            "weekdays": weekdays
        }
    })


@app.route('/api/admin/task-templates/<int:template_id>', methods=['DELETE'])
@admin_required
def delete_task_template(template_id):
    """删除任务模板"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取任务信息
        cursor.execute('SELECT * FROM task_templates WHERE id = ?', (template_id,))
        template = cursor.fetchone()
        
        if not template:
            conn.close()
            return jsonify({"success": False, "error": "任务不存在"}), 404
        
        # 删除今日及未来的任务实例（先删实例，再删模板）
        today = now().strftime('%Y-%m-%d')
        cursor.execute('DELETE FROM tasks WHERE template_id = ? AND date >= ?', (template_id, today))
        
        # 删除任务模板
        cursor.execute('DELETE FROM task_templates WHERE id = ?', (template_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "任务删除成功"})
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({"success": False, "error": f"删除失败: {str(e)}"}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({"success": False, "error": f"删除失败: {str(e)}"}), 500

# 导出数据库
@app.route('/api/admin/export-db', methods=['GET'])
@admin_required
def export_db():
    """导出数据库文件"""
    return send_file('./data/operations.db', as_attachment=True)

# 导入数据库
@app.route('/api/admin/import-db', methods=['POST'])
@admin_required
def import_db():
    """导入数据库文件"""
    if 'db' not in request.files:
        return jsonify({'success': False, 'error': '没有上传文件'}), 400
    
    file = request.files['db']
    if file.filename == '':
        return jsonify({'success': False, 'error': '文件名为空'}), 400
    
    # 确保是 .db 文件
    if not file.filename.endswith('.db'):
        return jsonify({'success': False, 'error': '必须是 .db 文件'}), 400
    
    # 备份原数据库
    backup_path = './data/operations.db.backup.' + now().strftime('%Y%m%d%H%M%S')
    if os.path.exists('./data/operations.db'):
        shutil.copy2('./data/operations.db', backup_path)
    
    # 保存新数据库
    file.save('./data/operations.db')
    
    return jsonify({
        'success': True, 
        'message': '数据库已恢复，原数据库已备份',
        'backup': backup_path
    })

# 初始化数据库
init_database()

if __name__ == '__main__':
    print("=" * 50)
    print("Operation Dashboard - 作战仪表盘 v3.1")
    print("=" * 50)
    print(f"主页面: http://localhost:5000")
    print(f"只读页: http://localhost:5000/view")
    print(f"管理后台: http://localhost:5000/admin")
    print("=" * 50)
    print("按 Ctrl+C 停止服务器")
    print("=" * 50)
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
