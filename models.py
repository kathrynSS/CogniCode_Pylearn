import os
import psycopg2
import psycopg2.extras
import hashlib
import secrets
import json
from datetime import datetime, timedelta
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        """初始化数据库管理器，专为Neon数据库优化"""
        self.db_type = 'postgresql'
        self.connection_string = None
        
        # 尝试从环境变量获取数据库连接
        postgres_url = os.getenv('POSTGRES_URL') or os.getenv('DATABASE_URL')
        
        if not postgres_url:
            logger.error("❌ 没有找到数据库连接字符串!")
            logger.error("💡 请在Vercel中设置以下环境变量之一:")
            logger.error("   - POSTGRES_URL (Neon推荐)")
            logger.error("   - DATABASE_URL (Vercel标准)")
            logger.error("🔧 如何设置:")
            logger.error("   1. 在Vercel项目中添加Neon数据库")
            logger.error("   2. Vercel会自动设置环境变量")
            logger.error("   3. 重新部署项目")
            raise RuntimeError("缺少数据库连接字符串，请设置 POSTGRES_URL 或 DATABASE_URL 环境变量")
        
        self.connection_string = postgres_url
        logger.info("✅ 使用环境变量中的数据库连接")
        
        # 检测数据库提供商
        if 'neon.tech' in postgres_url:
            logger.info("🟢 检测到 Neon 数据库 - 已优化配置")
        elif 'supabase.co' in postgres_url:
            logger.info("🟢 检测到 Supabase 数据库")
        elif 'vercel-postgres' in postgres_url:
            logger.info("🟢 检测到 Vercel Postgres")
        else:
            logger.info("🟢 检测到 PostgreSQL 数据库")
            
        logger.info(f"🔗 连接到: {postgres_url.split('@')[1].split('/')[0] if '@' in postgres_url else 'Unknown'}")
        
        try:
            logger.info("🔌 测试数据库连接...")
            # 测试PostgreSQL连接（针对Serverless优化）
            test_conn = psycopg2.connect(
                self.connection_string,
                # Serverless优化配置
                connect_timeout=10,
                application_name="CogniCode-App"
            )
            test_conn.close()
            logger.info("✅ 数据库连接成功!")
            logger.info("🚀 连接已优化用于Serverless环境")
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            logger.error("💡 请检查:")
            logger.error("   1. 环境变量是否正确设置")
            logger.error("   2. 数据库是否处于活跃状态")
            logger.error("   3. 网络连接是否正常")
            raise RuntimeError(f"PostgreSQL数据库连接失败: {e}")
        
        # 初始化数据库表
        self.init_database()
        logger.info(f"✅ 数据库初始化完成")
    
    def get_connection(self):
        """获取数据库连接（Serverless优化）"""
        return psycopg2.connect(
            self.connection_string,
            connect_timeout=10,
            application_name="CogniCode-App"
        )
    
    def init_database(self):
        """初始化数据库表结构"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 用户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    profile_data JSONB DEFAULT '{}'
                )
            ''')
            
            # 用户会话表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    session_token VARCHAR(255) UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 聊天记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    conversation_id VARCHAR(255) NOT NULL,
                    message_type VARCHAR(20) NOT NULL,
                    message_content TEXT NOT NULL,
                    context_data JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 用户项目表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_projects (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    project_id VARCHAR(255) NOT NULL,
                    project_data JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, project_id)
                )
            ''')
            
            # 用户笔记表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_notes (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    title VARCHAR(255) NOT NULL,
                    content TEXT NOT NULL,
                    topic VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 用户文件表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_files (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    filename VARCHAR(255) NOT NULL,
                    original_filename VARCHAR(255) NOT NULL,
                    file_path TEXT,
                    file_size INTEGER NOT NULL,
                    mime_type VARCHAR(100),
                    tags JSONB DEFAULT '[]',
                    drive_file_id VARCHAR(255),
                    drive_folder_id VARCHAR(255),
                    storage_type VARCHAR(20) DEFAULT 'local',
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引（针对查询性能优化）
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_messages_user_conversation ON chat_messages(user_id, conversation_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_projects_user_id ON user_projects(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_notes_user_id ON user_notes(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_files_user_id ON user_files(user_id)')
            
            conn.commit()
            logger.info("✅ 数据库表和索引初始化成功")
            
        except Exception as e:
            logger.error(f"❌ 数据库表初始化失败: {e}")
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()
    
    def _execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        """执行数据库查询的通用方法（连接池优化）"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch_one:
                result = cursor.fetchone()
                return dict(result) if result else None
            elif fetch_all:
                results = cursor.fetchall()
                return [dict(row) for row in results]
            else:
                conn.commit()
                return cursor.rowcount
                
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库查询失败: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def create_user(self, username, email, password):
        """创建新用户"""
        try:
            # 检查用户名和邮箱是否已存在
            existing_user = self._execute_query(
                'SELECT id FROM users WHERE username = %s OR email = %s',
                (username, email),
                fetch_one=True
            )
            
            if existing_user:
                return None, "Username or email already exists"
            
            # 创建密码哈希
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # 插入新用户
            query = '''
                INSERT INTO users (username, email, password_hash) 
                VALUES (%s, %s, %s) RETURNING id
            '''
            result = self._execute_query(query, (username, email, password_hash), fetch_one=True)
            user_id = result['id'] if result else None
            
            if user_id:
                return user_id, "User created successfully"
            else:
                return None, "Failed to create user"
            
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
            return None, f"Failed to create user: {str(e)}"
    
    def authenticate_user(self, username_or_email, password):
        """验证用户登录"""
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            query = '''
                SELECT id, username, email, created_at 
                FROM users 
                WHERE (username = %s OR email = %s) AND password_hash = %s
            '''
            
            user = self._execute_query(
                query,
                (username_or_email, username_or_email, password_hash),
                fetch_one=True
            )
            
            if user:
                return user, "Login successful"
            else:
                return None, "Invalid username/email or password"
            
        except Exception as e:
            logger.error(f"用户认证失败: {e}")
            return None, f"Authentication failed: {str(e)}"
    
    def create_session(self, user_id, expires_hours=24):
        """创建用户会话"""
        try:
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=expires_hours)
            
            query = '''
                INSERT INTO user_sessions (user_id, session_token, expires_at) 
                VALUES (%s, %s, %s) RETURNING session_token
            '''
            
            result = self._execute_query(
                query, 
                (user_id, session_token, expires_at), 
                fetch_one=True
            )
            
            return result['session_token'] if result else None
            
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            return None

    def get_user_by_session(self, session_token):
        """通过会话令牌获取用户信息"""
        try:
            query = '''
                SELECT u.id, u.username, u.email, u.created_at, u.profile_data,
                       s.expires_at
                FROM users u
                JOIN user_sessions s ON u.id = s.user_id
                WHERE s.session_token = %s AND s.expires_at > NOW()
            '''
            
            result = self._execute_query(query, (session_token,), fetch_one=True)
            return result
            
        except Exception as e:
            logger.error(f"获取用户会话失败: {e}")
            return None

    def delete_session(self, session_token):
        """删除用户会话"""
        try:
            query = 'DELETE FROM user_sessions WHERE session_token = %s'
            return self._execute_query(query, (session_token,))
        except Exception as e:
            logger.error(f"删除会话失败: {e}")
            return 0

    def get_user_by_id(self, user_id):
        """通过ID获取用户信息"""
        try:
            query = '''
                SELECT id, username, email, created_at, updated_at, profile_data
                FROM users 
                WHERE id = %s
            '''
            return self._execute_query(query, (user_id,), fetch_one=True)
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return None

    def save_chat_message(self, user_id, conversation_id, message_type, message_content, context_data=None):
        """保存聊天消息"""
        try:
            query = '''
                INSERT INTO chat_messages (user_id, conversation_id, message_type, message_content, context_data)
                VALUES (%s, %s, %s, %s, %s)
            '''
            context_json = json.dumps(context_data) if context_data else '{}'
            return self._execute_query(query, (user_id, conversation_id, message_type, message_content, context_json))
        except Exception as e:
            logger.error(f"保存聊天消息失败: {e}")
            return 0

    def get_user_chat_history(self, user_id, conversation_id=None, limit=50):
        """获取用户聊天历史"""
        try:
            if conversation_id:
                query = '''
                    SELECT * FROM chat_messages 
                    WHERE user_id = %s AND conversation_id = %s 
                    ORDER BY created_at DESC LIMIT %s
                '''
                params = (user_id, conversation_id, limit)
            else:
                query = '''
                    SELECT * FROM chat_messages 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC LIMIT %s
                '''
                params = (user_id, limit)
            
            return self._execute_query(query, params, fetch_all=True)
        except Exception as e:
            logger.error(f"获取聊天历史失败: {e}")
            return []

    def delete_user_chat_history(self, user_id, conversation_id=None):
        """删除用户聊天历史"""
        try:
            if conversation_id:
                query = 'DELETE FROM chat_messages WHERE user_id = %s AND conversation_id = %s'
                params = (user_id, conversation_id)
            else:
                query = 'DELETE FROM chat_messages WHERE user_id = %s'
                params = (user_id,)
            
            return self._execute_query(query, params)
        except Exception as e:
            logger.error(f"删除聊天历史失败: {e}")
            return 0

    def save_user_project(self, user_id, project_id, project_data):
        """保存或更新用户项目"""
        try:
            project_json = json.dumps(project_data)
            
            # 使用 UPSERT 语法
            query = '''
                INSERT INTO user_projects (user_id, project_id, project_data, updated_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id, project_id) 
                DO UPDATE SET 
                    project_data = EXCLUDED.project_data,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            '''
            
            result = self._execute_query(query, (user_id, project_id, project_json), fetch_one=True)
            return result['id'] if result else None
            
        except Exception as e:
            logger.error(f"保存用户项目失败: {e}")
            return None

    def get_user_projects(self, user_id):
        """获取用户的所有项目"""
        try:
            query = '''
                SELECT project_id, project_data, created_at, updated_at
                FROM user_projects 
                WHERE user_id = %s 
                ORDER BY updated_at DESC
            '''
            return self._execute_query(query, (user_id,), fetch_all=True)
        except Exception as e:
            logger.error(f"获取用户项目失败: {e}")
            return []

    def delete_user_project(self, user_id, project_id):
        """删除用户项目"""
        try:
            query = 'DELETE FROM user_projects WHERE user_id = %s AND project_id = %s'
            return self._execute_query(query, (user_id, project_id))
        except Exception as e:
            logger.error(f"删除用户项目失败: {e}")
            return 0

    def save_user_note(self, user_id, title, content, topic=None, note_id=None):
        """保存或更新用户笔记"""
        try:
            if note_id:
                # 更新现有笔记
                query = '''
                    UPDATE user_notes 
                    SET title = %s, content = %s, topic = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND user_id = %s
                    RETURNING id
                '''
                result = self._execute_query(query, (title, content, topic, note_id, user_id), fetch_one=True)
            else:
                # 创建新笔记
                query = '''
                    INSERT INTO user_notes (user_id, title, content, topic)
                    VALUES (%s, %s, %s, %s) RETURNING id
                '''
                result = self._execute_query(query, (user_id, title, content, topic), fetch_one=True)
            
            return result['id'] if result else None
            
        except Exception as e:
            logger.error(f"保存用户笔记失败: {e}")
            return None

    def get_user_notes(self, user_id):
        """获取用户的所有笔记"""
        try:
            query = '''
                SELECT id, title, content, topic, created_at, updated_at
                FROM user_notes 
                WHERE user_id = %s 
                ORDER BY updated_at DESC
            '''
            return self._execute_query(query, (user_id,), fetch_all=True)
        except Exception as e:
            logger.error(f"获取用户笔记失败: {e}")
            return []

    def delete_user_note(self, user_id, note_id):
        """删除用户笔记"""
        try:
            query = 'DELETE FROM user_notes WHERE id = %s AND user_id = %s'
            return self._execute_query(query, (note_id, user_id))
        except Exception as e:
            logger.error(f"删除用户笔记失败: {e}")
            return 0

    def save_user_file(self, user_id, filename, original_filename, file_path=None, file_size=0, mime_type=None, tags=None, drive_file_id=None, drive_folder_id=None, storage_type='local'):
        """保存用户文件信息"""
        try:
            tags_json = json.dumps(tags) if tags else '[]'
            
            query = '''
                INSERT INTO user_files 
                (user_id, filename, original_filename, file_path, file_size, mime_type, tags, drive_file_id, drive_folder_id, storage_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
                RETURNING id
            '''
            
            result = self._execute_query(
                query, 
                (user_id, filename, original_filename, file_path, file_size, mime_type, tags_json, drive_file_id, drive_folder_id, storage_type),
                fetch_one=True
            )
            
            return result['id'] if result else None
            
        except Exception as e:
            logger.error(f"保存用户文件失败: {e}")
            return None

    def get_user_files(self, user_id):
        """获取用户的所有文件"""
        try:
            query = '''
                SELECT id, filename, original_filename, file_path, file_size, mime_type, tags, 
                       drive_file_id, drive_folder_id, storage_type, uploaded_at
                FROM user_files 
                WHERE user_id = %s 
                ORDER BY uploaded_at DESC
            '''
            return self._execute_query(query, (user_id,), fetch_all=True)
        except Exception as e:
            logger.error(f"获取用户文件失败: {e}")
            return []

    def get_user_statistics(self, user_id):
        """获取用户统计信息"""
        try:
            # 获取项目数量
            projects_query = 'SELECT COUNT(*) as count FROM user_projects WHERE user_id = %s'
            projects_result = self._execute_query(projects_query, (user_id,), fetch_one=True)
            projects_count = projects_result['count'] if projects_result else 0
            
            # 获取笔记数量
            notes_query = 'SELECT COUNT(*) as count FROM user_notes WHERE user_id = %s'
            notes_result = self._execute_query(notes_query, (user_id,), fetch_one=True)
            notes_count = notes_result['count'] if notes_result else 0
            
            # 获取文件数量
            files_query = 'SELECT COUNT(*) as count FROM user_files WHERE user_id = %s'
            files_result = self._execute_query(files_query, (user_id,), fetch_one=True)
            files_count = files_result['count'] if files_result else 0
            
            # 获取聊天消息数量
            messages_query = 'SELECT COUNT(*) as count FROM chat_messages WHERE user_id = %s'
            messages_result = self._execute_query(messages_query, (user_id,), fetch_one=True)
            messages_count = messages_result['count'] if messages_result else 0
            
            return {
                'projects_count': projects_count,
                'notes_count': notes_count,
                'files_count': files_count,
                'messages_count': messages_count
            }
            
        except Exception as e:
            logger.error(f"获取用户统计信息失败: {e}")
            return {
                'projects_count': 0,
                'notes_count': 0,
                'files_count': 0,
                'messages_count': 0
            }

    def verify_resource_ownership(self, user_id, resource_type, resource_id):
        """验证资源所有权"""
        try:
            if resource_type == 'project':
                query = 'SELECT COUNT(*) as count FROM user_projects WHERE user_id = %s AND project_id = %s'
            elif resource_type == 'note':
                query = 'SELECT COUNT(*) as count FROM user_notes WHERE user_id = %s AND id = %s'
            elif resource_type == 'file':
                query = 'SELECT COUNT(*) as count FROM user_files WHERE user_id = %s AND id = %s'
            else:
                return False
                
            result = self._execute_query(query, (user_id, resource_id), fetch_one=True)
            return result['count'] > 0 if result else False
            
        except Exception as e:
            logger.error(f"验证资源所有权失败: {e}")
            return False 