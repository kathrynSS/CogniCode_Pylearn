from functools import wraps
from flask import request, jsonify, g
from models import DatabaseManager

# 初始化数据库管理器
db_manager = DatabaseManager()

def init_auth_middleware(app):
    """初始化认证中间件"""
    
    @app.before_request
    def load_user():
        """在每个请求前加载用户信息"""
        g.current_user = None
        
        # 从请求头或cookie中获取会话令牌
        auth_token = request.headers.get('Authorization')
        if auth_token and auth_token.startswith('Bearer '):
            session_token = auth_token.split(' ')[1]
        else:
            session_token = request.cookies.get('session_token')
        
        if session_token:
            user = db_manager.validate_session(session_token)
            if user:
                g.current_user = user
                g.session_token = session_token

def require_auth(f):
    """装饰器：要求用户登录"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.current_user:
            return jsonify({
                'error': '需要登录',
                'code': 'AUTH_REQUIRED'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def require_owner(resource_user_id_func):
    """装饰器：要求用户拥有资源的权限"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not g.current_user:
                return jsonify({
                    'error': '需要登录',
                    'code': 'AUTH_REQUIRED'
                }), 401
            
            # 获取资源所有者ID
            resource_user_id = resource_user_id_func(*args, **kwargs)
            
            if g.current_user['id'] != resource_user_id:
                return jsonify({
                    'error': '无权访问此资源',
                    'code': 'FORBIDDEN'
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def optional_auth(f):
    """装饰器：可选认证，不强制要求登录"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 用户信息已在 before_request 中加载
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """获取当前登录用户"""
    return getattr(g, 'current_user', None)

def get_current_user_id():
    """获取当前登录用户ID"""
    user = get_current_user()
    return user['id'] if user else None 