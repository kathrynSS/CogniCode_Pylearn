import os
import hashlib
import secrets
from datetime import datetime, timedelta
import json

# 根据环境选择数据库驱动
# Always import both drivers if available
sqlite3 = None
psycopg2 = None

try:
    import sqlite3
    print("✅ SQLite3 available")
except ImportError:
    print("❌ SQLite3 not available")

try:
    import psycopg2
    import psycopg2.extras
    from psycopg2 import sql
    print("✅ PostgreSQL (psycopg2) available")
except ImportError:
    print("❌ PostgreSQL (psycopg2) not available")

# Check if we have at least one database driver
if not sqlite3 and not psycopg2:
    raise ImportError("Neither psycopg2 nor sqlite3 is available")

# Default to PostgreSQL if available, but will be determined at runtime
DB_TYPE = 'postgresql' if psycopg2 else 'sqlite'

class DatabaseManager:
    def __init__(self, db_path='app_database.db'):
        # Determine database type based on environment and availability
        self.db_url = os.getenv('POSTGRES_URL') or os.getenv('DATABASE_URL')
        
        if self.db_url and psycopg2:
            self.db_type = 'postgresql'
            print(f"✅ Using PostgreSQL: {self.db_url[:50]}...")
        elif sqlite3:
            self.db_type = 'sqlite'
            self.db_path = db_path
            print("✅ Using SQLite for local development")
        else:
            raise RuntimeError("No database driver available")
            
        self.init_database()
    
    def get_connection(self):
        """获取数据库连接"""
        if self.db_type == 'postgresql':
            return psycopg2.connect(self.db_url)
        else:
            return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """初始化数据库表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if self.db_type == 'postgresql':
            # PostgreSQL 表创建语句
            
            # 用户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    salt VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    profile_data TEXT
                )
            ''')
            
            # 用户会话表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    session_token VARCHAR(255) UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # 用户项目表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_projects (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    project_id VARCHAR(100) NOT NULL,
                    project_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # 用户文件表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_files (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    filename VARCHAR(255) NOT NULL,
                    original_filename VARCHAR(255) NOT NULL,
                    file_path VARCHAR(500),
                    drive_file_id VARCHAR(255),
                    drive_folder_id VARCHAR(255),
                    file_size INTEGER,
                    mime_type VARCHAR(100),
                    tags TEXT,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    storage_type VARCHAR(20) DEFAULT 'drive',
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # 用户笔记表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_notes (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # 用户聊天记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_chat_history (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    conversation_id VARCHAR(100),
                    message_type VARCHAR(20) NOT NULL,
                    message_content TEXT NOT NULL,
                    context_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
        else:
            # SQLite 表创建语句（保持原有逻辑）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    salt VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    profile_data TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token VARCHAR(255) UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    project_id VARCHAR(100) NOT NULL,
                    project_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    filename VARCHAR(255) NOT NULL,
                    original_filename VARCHAR(255) NOT NULL,
                    file_path VARCHAR(500),
                    drive_file_id VARCHAR(255),
                    drive_folder_id VARCHAR(255),
                    file_size INTEGER,
                    mime_type VARCHAR(100),
                    tags TEXT,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    storage_type VARCHAR(20) DEFAULT 'drive',
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # 添加新列到现有表（如果不存在）- SQLite特定
            try:
                cursor.execute('ALTER TABLE user_files ADD COLUMN drive_file_id VARCHAR(255)')
            except sqlite3.OperationalError:
                pass
                
            try:
                cursor.execute('ALTER TABLE user_files ADD COLUMN drive_folder_id VARCHAR(255)')
            except sqlite3.OperationalError:
                pass
                
            try:
                cursor.execute('ALTER TABLE user_files ADD COLUMN storage_type VARCHAR(20) DEFAULT "drive"')
            except sqlite3.OperationalError:
                pass
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    conversation_id VARCHAR(100),
                    message_type VARCHAR(20) NOT NULL,
                    message_content TEXT NOT NULL,
                    context_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        """创建密码哈希"""
        salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac('sha256', 
                                           password.encode('utf-8'), 
                                           salt.encode('utf-8'), 
                                           100000)
        return password_hash.hex(), salt
    
    def verify_password(self, password, password_hash, salt):
        """验证密码"""
        computed_hash = hashlib.pbkdf2_hmac('sha256',
                                          password.encode('utf-8'),
                                          salt.encode('utf-8'),
                                          100000)
        return computed_hash.hex() == password_hash
    
    def create_user(self, username, email, password, profile_data=None):
        """创建新用户"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 检查用户名和邮箱是否已存在
            cursor.execute('SELECT id FROM users WHERE username = %s OR email = %s' if self.db_type == 'postgresql' 
                          else 'SELECT id FROM users WHERE username = ? OR email = ?', 
                          (username, email))
            if cursor.fetchone():
                return None, "用户名或邮箱已存在"
            
            # 创建密码哈希
            password_hash, salt = self.hash_password(password)
            
            # 插入新用户
            if self.db_type == 'postgresql':
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, salt, profile_data)
                    VALUES (%s, %s, %s, %s, %s) RETURNING id
                ''', (username, email, password_hash, salt, 
                      json.dumps(profile_data) if profile_data else None))
                user_id = cursor.fetchone()[0]
            else:
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, salt, profile_data)
                    VALUES (?, ?, ?, ?, ?)
                ''', (username, email, password_hash, salt, 
                      json.dumps(profile_data) if profile_data else None))
                user_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            return user_id, "用户创建成功"
            
        except Exception as e:
            return None, f"创建用户失败: {str(e)}"
    
    def authenticate_user(self, username_or_email, password):
        """用户登录验证"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 查找用户
            if self.db_type == 'postgresql':
                cursor.execute('''
                    SELECT id, username, email, password_hash, salt, is_active 
                    FROM users 
                    WHERE (username = %s OR email = %s) AND is_active = TRUE
                ''', (username_or_email, username_or_email))
            else:
                cursor.execute('''
                    SELECT id, username, email, password_hash, salt, is_active 
                    FROM users 
                    WHERE (username = ? OR email = ?) AND is_active = 1
                ''', (username_or_email, username_or_email))
            
            user = cursor.fetchone()
            if not user:
                return None, "用户不存在或已被禁用"
            
            user_id, username, email, password_hash, salt, is_active = user
            
            # 验证密码
            if not self.verify_password(password, password_hash, salt):
                return None, "密码错误"
            
            # 更新最后登录时间
            if self.db_type == 'postgresql':
                cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s', (user_id,))
            else:
                cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user_id,))
            
            conn.commit()
            conn.close()
            
            return {
                'id': user_id,
                'username': username,
                'email': email
            }, "登录成功"
            
        except Exception as e:
            return None, f"登录失败: {str(e)}"
    
    def create_session(self, user_id, expires_hours=24):
        """创建用户会话"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 生成会话令牌
            session_token = secrets.token_urlsafe(64)
            expires_at = datetime.now() + timedelta(hours=expires_hours)
            
            # 清理过期会话
            if self.db_type == 'postgresql':
                cursor.execute('DELETE FROM user_sessions WHERE expires_at < CURRENT_TIMESTAMP')
                cursor.execute('''
                    INSERT INTO user_sessions (user_id, session_token, expires_at)
                    VALUES (%s, %s, %s)
                ''', (user_id, session_token, expires_at))
            else:
                cursor.execute('DELETE FROM user_sessions WHERE expires_at < CURRENT_TIMESTAMP')
                cursor.execute('''
                    INSERT INTO user_sessions (user_id, session_token, expires_at)
                    VALUES (?, ?, ?)
                ''', (user_id, session_token, expires_at))
            
            conn.commit()
            conn.close()
            
            return session_token
            
        except Exception as e:
            return None
    
    def validate_session(self, session_token):
        """验证会话令牌"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if self.db_type == 'postgresql':
                cursor.execute('''
                    SELECT s.user_id, u.username, u.email
                    FROM user_sessions s
                    JOIN users u ON s.user_id = u.id
                    WHERE s.session_token = %s AND s.expires_at > CURRENT_TIMESTAMP AND u.is_active = TRUE
                ''', (session_token,))
            else:
                cursor.execute('''
                    SELECT s.user_id, u.username, u.email
                    FROM user_sessions s
                    JOIN users u ON s.user_id = u.id
                    WHERE s.session_token = ? AND s.expires_at > CURRENT_TIMESTAMP AND u.is_active = 1
                ''', (session_token,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'id': result[0],
                    'username': result[1],
                    'email': result[2]
                }
            return None
            
        except Exception as e:
            return None
    
    def delete_session(self, session_token):
        """删除会话（登出）"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if self.db_type == 'postgresql':
                cursor.execute('DELETE FROM user_sessions WHERE session_token = %s', (session_token,))
            else:
                cursor.execute('DELETE FROM user_sessions WHERE session_token = ?', (session_token,))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            return False
    
    def cleanup_expired_sessions(self):
        """清理所有过期会话"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM user_sessions WHERE expires_at < CURRENT_TIMESTAMP')
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            return False
    
    def get_user_by_id(self, user_id):
        """根据ID获取用户信息"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if self.db_type == 'postgresql':
                cursor.execute('''
                    SELECT id, username, email, created_at, last_login, profile_data
                    FROM users 
                    WHERE id = %s AND is_active = TRUE
                ''', (user_id,))
            else:
                cursor.execute('''
                    SELECT id, username, email, created_at, last_login, profile_data
                    FROM users 
                    WHERE id = ? AND is_active = 1
                ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                profile_data = json.loads(result[5]) if result[5] else {}
                return {
                    'id': result[0],
                    'username': result[1],
                    'email': result[2],
                    'created_at': result[3],
                    'last_login': result[4],
                    'profile_data': profile_data
                }
            return None
            
        except Exception as e:
            return None
    
    def save_user_project(self, user_id, project_id, project_data):
        """保存用户项目"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 检查项目是否已存在
            if self.db_type == 'postgresql':
                cursor.execute('SELECT id FROM user_projects WHERE user_id = %s AND project_id = %s',
                              (user_id, project_id))
            else:
                cursor.execute('SELECT id FROM user_projects WHERE user_id = ? AND project_id = ?',
                              (user_id, project_id))
            
            if cursor.fetchone():
                # 更新现有项目
                if self.db_type == 'postgresql':
                    cursor.execute('''
                        UPDATE user_projects 
                        SET project_data = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = %s AND project_id = %s
                    ''', (json.dumps(project_data), user_id, project_id))
                else:
                    cursor.execute('''
                        UPDATE user_projects 
                        SET project_data = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ? AND project_id = ?
                    ''', (json.dumps(project_data), user_id, project_id))
            else:
                # 创建新项目
                if self.db_type == 'postgresql':
                    cursor.execute('''
                        INSERT INTO user_projects (user_id, project_id, project_data)
                        VALUES (%s, %s, %s)
                    ''', (user_id, project_id, json.dumps(project_data)))
                else:
                    cursor.execute('''
                        INSERT INTO user_projects (user_id, project_id, project_data)
                        VALUES (?, ?, ?)
                    ''', (user_id, project_id, json.dumps(project_data)))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            return False
    
    def get_user_projects(self, user_id):
        """获取用户所有项目"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if self.db_type == 'postgresql':
                cursor.execute('''
                    SELECT project_id, project_data, created_at, updated_at
                    FROM user_projects 
                    WHERE user_id = %s
                    ORDER BY updated_at DESC
                ''', (user_id,))
            else:
                cursor.execute('''
                    SELECT project_id, project_data, created_at, updated_at
                    FROM user_projects 
                    WHERE user_id = ?
                    ORDER BY updated_at DESC
                ''', (user_id,))
            
            results = cursor.fetchall()
            conn.close()
            
            projects = {}
            for result in results:
                projects[result[0]] = {
                    'data': json.loads(result[1]),
                    'created_at': result[2],
                    'updated_at': result[3],
                    'owner_id': user_id
                }
            
            return projects
            
        except Exception as e:
            return {}
    
    def delete_user_project(self, user_id, project_id):
        """删除用户项目"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if self.db_type == 'postgresql':
                cursor.execute('''
                    DELETE FROM user_projects 
                    WHERE user_id = %s AND project_id = %s
                ''', (user_id, project_id))
            else:
                cursor.execute('''
                    DELETE FROM user_projects 
                    WHERE user_id = ? AND project_id = ?
                ''', (user_id, project_id))
            
            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()
            
            return rows_affected > 0
            
        except Exception as e:
            return False
    
    def delete_user_file(self, user_id, file_id):
        """删除用户文件记录"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if self.db_type == 'postgresql':
                cursor.execute('''
                    DELETE FROM user_files 
                    WHERE user_id = %s AND id = %s
                ''', (user_id, file_id))
            else:
                cursor.execute('''
                    DELETE FROM user_files 
                    WHERE user_id = ? AND id = ?
                ''', (user_id, file_id))
            
            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()
            
            return rows_affected > 0
            
        except Exception as e:
            return False
    
    def save_user_file(self, user_id, filename, original_filename, file_path=None, 
                       file_size=None, mime_type=None, tags=None, drive_file_id=None, 
                       drive_folder_id=None, storage_type='drive'):
        """保存用户文件信息"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if self.db_type == 'postgresql':
                cursor.execute('''
                    INSERT INTO user_files 
                    (user_id, filename, original_filename, file_path, drive_file_id, 
                     drive_folder_id, file_size, mime_type, tags, storage_type)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                ''', (user_id, filename, original_filename, file_path, drive_file_id,
                      drive_folder_id, file_size, mime_type, 
                      json.dumps(tags) if tags else None, storage_type))
                file_id = cursor.fetchone()[0]
            else:
                cursor.execute('''
                    INSERT INTO user_files 
                    (user_id, filename, original_filename, file_path, drive_file_id, 
                     drive_folder_id, file_size, mime_type, tags, storage_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, filename, original_filename, file_path, drive_file_id,
                      drive_folder_id, file_size, mime_type, 
                      json.dumps(tags) if tags else None, storage_type))
                file_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            return file_id
            
        except Exception as e:
            print(f"Error saving file: {e}")
            return None
    
    def get_user_files(self, user_id):
        """获取用户所有文件"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if self.db_type == 'postgresql':
                cursor.execute('''
                    SELECT id, filename, original_filename, file_path, drive_file_id,
                           drive_folder_id, file_size, mime_type, tags, uploaded_at, storage_type
                    FROM user_files 
                    WHERE user_id = %s
                    ORDER BY uploaded_at DESC
                ''', (user_id,))
            else:
                cursor.execute('''
                    SELECT id, filename, original_filename, file_path, drive_file_id,
                           drive_folder_id, file_size, mime_type, tags, uploaded_at, storage_type
                    FROM user_files 
                    WHERE user_id = ?
                    ORDER BY uploaded_at DESC
                ''', (user_id,))
            
            results = cursor.fetchall()
            conn.close()
            
            files = []
            for result in results:
                files.append({
                    'id': result[0],
                    'filename': result[1],
                    'original_filename': result[2],
                    'file_path': result[3],
                    'drive_file_id': result[4],
                    'drive_folder_id': result[5],
                    'file_size': result[6],
                    'mime_type': result[7],
                    'tags': json.loads(result[8]) if result[8] else [],
                    'uploaded_at': result[9],
                    'storage_type': result[10] if len(result) > 10 else 'local'
                })
            
            return files
            
        except Exception as e:
            print(f"Error getting user files: {e}")
            return []
    
    def save_chat_message(self, user_id, conversation_id, message_type, 
                         message_content, context_data=None):
        """保存聊天消息"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if self.db_type == 'postgresql':
                cursor.execute('''
                    INSERT INTO user_chat_history 
                    (user_id, conversation_id, message_type, message_content, context_data)
                    VALUES (%s, %s, %s, %s, %s) RETURNING id
                ''', (user_id, conversation_id, message_type, message_content,
                      json.dumps(context_data) if context_data else None))
                message_id = cursor.fetchone()[0]
            else:
                cursor.execute('''
                    INSERT INTO user_chat_history 
                    (user_id, conversation_id, message_type, message_content, context_data)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, conversation_id, message_type, message_content,
                      json.dumps(context_data) if context_data else None))
                message_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            return message_id
            
        except Exception as e:
            return None
    
    def get_user_chat_history(self, user_id, conversation_id=None, limit=100):
        """获取用户聊天记录"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if conversation_id:
                if self.db_type == 'postgresql':
                    cursor.execute('''
                        SELECT id, conversation_id, message_type, message_content, 
                               context_data, created_at
                        FROM user_chat_history 
                        WHERE user_id = %s AND conversation_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                    ''', (user_id, conversation_id, limit))
                else:
                    cursor.execute('''
                        SELECT id, conversation_id, message_type, message_content, 
                               context_data, created_at
                        FROM user_chat_history 
                        WHERE user_id = ? AND conversation_id = ?
                        ORDER BY created_at DESC
                        LIMIT ?
                    ''', (user_id, conversation_id, limit))
            else:
                if self.db_type == 'postgresql':
                    cursor.execute('''
                        SELECT id, conversation_id, message_type, message_content, 
                               context_data, created_at
                        FROM user_chat_history 
                        WHERE user_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                    ''', (user_id, limit))
                else:
                    cursor.execute('''
                        SELECT id, conversation_id, message_type, message_content, 
                               context_data, created_at
                        FROM user_chat_history 
                        WHERE user_id = ?
                        ORDER BY created_at DESC
                        LIMIT ?
                    ''', (user_id, limit))
            
            results = cursor.fetchall()
            conn.close()
            
            messages = []
            for result in results:
                messages.append({
                    'id': result[0],
                    'conversation_id': result[1],
                    'message_type': result[2],
                    'message_content': result[3],
                    'context_data': json.loads(result[4]) if result[4] else None,
                    'created_at': result[5],
                    'user_id': user_id
                })
            
            return messages
            
        except Exception as e:
            return []
    
    def delete_user_chat_history(self, user_id, conversation_id=None):
        """删除用户聊天记录"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if conversation_id:
                if self.db_type == 'postgresql':
                    cursor.execute('''
                        DELETE FROM user_chat_history 
                        WHERE user_id = %s AND conversation_id = %s
                    ''', (user_id, conversation_id))
                else:
                    cursor.execute('''
                        DELETE FROM user_chat_history 
                        WHERE user_id = ? AND conversation_id = ?
                    ''', (user_id, conversation_id))
            else:
                if self.db_type == 'postgresql':
                    cursor.execute('''
                        DELETE FROM user_chat_history 
                        WHERE user_id = %s
                    ''', (user_id,))
                else:
                    cursor.execute('''
                        DELETE FROM user_chat_history 
                        WHERE user_id = ?
                    ''', (user_id,))
            
            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()
            
            return rows_affected > 0
            
        except Exception as e:
            return False
    
    def save_user_note(self, user_id, title, content, topic=None, note_id=None):
        """保存用户笔记"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if note_id:
                # Update existing note
                if self.db_type == 'postgresql':
                    cursor.execute('''
                        UPDATE user_notes 
                        SET title = %s, content = %s, tags = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s AND user_id = %s
                    ''', (title, content, json.dumps({'topic': topic}) if topic else None, note_id, user_id))
                else:
                    cursor.execute('''
                        UPDATE user_notes 
                        SET title = ?, content = ?, tags = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ? AND user_id = ?
                    ''', (title, content, json.dumps({'topic': topic}) if topic else None, note_id, user_id))
            else:
                # Create new note
                if self.db_type == 'postgresql':
                    cursor.execute('''
                        INSERT INTO user_notes (user_id, title, content, tags)
                        VALUES (%s, %s, %s, %s) RETURNING id
                    ''', (user_id, title, content, json.dumps({'topic': topic}) if topic else None))
                    note_id = cursor.fetchone()[0]
                else:
                    cursor.execute('''
                        INSERT INTO user_notes (user_id, title, content, tags)
                        VALUES (?, ?, ?, ?)
                    ''', (user_id, title, content, json.dumps({'topic': topic}) if topic else None))
                    note_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            return note_id
            
        except Exception as e:
            print(f"Error saving note: {e}")
            return None
    
    def get_user_notes(self, user_id):
        """获取用户笔记"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if self.db_type == 'postgresql':
                cursor.execute('''
                    SELECT id, title, content, tags, created_at, updated_at
                    FROM user_notes 
                    WHERE user_id = %s
                    ORDER BY updated_at DESC
                ''', (user_id,))
            else:
                cursor.execute('''
                    SELECT id, title, content, tags, created_at, updated_at
                    FROM user_notes 
                    WHERE user_id = ?
                    ORDER BY updated_at DESC
                ''', (user_id,))
            
            results = cursor.fetchall()
            conn.close()
            
            notes = []
            for result in results:
                notes.append({
                    'id': result[0],
                    'title': result[1],
                    'content': result[2],
                    'tags': json.loads(result[3]) if result[3] else [],
                    'created_at': result[4],
                    'updated_at': result[5],
                    'owner_id': user_id
                })
            
            return notes
            
        except Exception as e:
            return []
    
    def delete_user_note(self, user_id, note_id):
        """删除用户笔记"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if self.db_type == 'postgresql':
                cursor.execute('''
                    DELETE FROM user_notes 
                    WHERE id = %s AND user_id = %s
                ''', (note_id, user_id))
            else:
                cursor.execute('''
                    DELETE FROM user_notes 
                    WHERE id = ? AND user_id = ?
                ''', (note_id, user_id))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            return success
            
        except Exception as e:
            print(f"Error deleting note: {e}")
            return False
    
    def verify_resource_ownership(self, user_id, resource_type, resource_id):
        """验证用户是否拥有指定资源的访问权限"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            placeholder = '%s' if self.db_type == 'postgresql' else '?'
            
            if resource_type == 'project':
                cursor.execute(f'''
                    SELECT user_id FROM user_projects 
                    WHERE project_id = {placeholder} AND user_id = {placeholder}
                ''', (resource_id, user_id))
            elif resource_type == 'note':
                cursor.execute(f'''
                    SELECT user_id FROM user_notes 
                    WHERE id = {placeholder} AND user_id = {placeholder}
                ''', (resource_id, user_id))
            elif resource_type == 'file':
                cursor.execute(f'''
                    SELECT user_id FROM user_files 
                    WHERE id = {placeholder} AND user_id = {placeholder}
                ''', (resource_id, user_id))
            elif resource_type == 'chat':
                cursor.execute(f'''
                    SELECT user_id FROM user_chat_history 
                    WHERE id = {placeholder} AND user_id = {placeholder}
                ''', (resource_id, user_id))
            else:
                return False
            
            result = cursor.fetchone()
            conn.close()
            
            return result is not None
            
        except Exception as e:
            return False

    def get_user_statistics(self, user_id):
        """获取用户统计信息"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            placeholder = '%s' if self.db_type == 'postgresql' else '?'
            
            # 获取聊天消息统计
            cursor.execute(f'SELECT COUNT(*) FROM user_chat_history WHERE user_id = {placeholder}', (user_id,))
            total_messages = cursor.fetchone()[0]
            
            # 获取项目统计
            cursor.execute(f'SELECT COUNT(*) FROM user_projects WHERE user_id = {placeholder}', (user_id,))
            total_projects = cursor.fetchone()[0]
            
            # 获取笔记统计
            cursor.execute(f'SELECT COUNT(*) FROM user_notes WHERE user_id = {placeholder}', (user_id,))
            total_notes = cursor.fetchone()[0]
            
            # 获取文件统计
            cursor.execute(f'SELECT COUNT(*) FROM user_files WHERE user_id = {placeholder}', (user_id,))
            total_files = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_messages': total_messages,
                'total_projects': total_projects,
                'total_notes': total_notes,
                'total_files': total_files,
                'user_id': user_id
            }
            
        except Exception as e:
            return {
                'total_messages': 0,
                'total_projects': 0,
                'total_notes': 0,
                'total_files': 0,
                'user_id': user_id
            } 