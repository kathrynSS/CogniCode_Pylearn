import os
from flask import Flask, request, jsonify, send_file, send_from_directory, make_response
from openai import OpenAI
from flask_cors import CORS
import requests
import json
import re
import ast
import traceback
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
from prompt import PROMPTS, PROJECT_TEMPLATES, get_learning_chatbot_prompt, get_step_explanation_prompt, get_code_review_prompt_enhanced, get_adaptive_hint_prompt, get_concept_explanation_prompt, get_reflection_prompt_enhanced, get_resource_recommendation_prompt
import multiprocessing
import signal
import time
from werkzeug.utils import secure_filename
import datetime
import sqlite3
import threading

# 导入认证相关模块
from models import DatabaseManager
from auth_middleware import init_auth_middleware, require_auth, require_owner, optional_auth, get_current_user, get_current_user_id

# 导入Google Drive服务
from google_drive_service import GoogleDriveService

# Vercel部署配置 - 移除静态文件配置，让Vercel处理
app = Flask(__name__)
CORS(app, supports_credentials=True)  # Enable CORS for all routes with credentials support

# 初始化认证中间件
init_auth_middleware(app)

# 初始化数据库 - 使用环境变量或相对路径
db_manager = DatabaseManager()

# 初始化Google Drive服务
drive_service = None
try:
    # 尝试从环境变量获取Google Drive凭据
    credentials_json = os.getenv('GOOGLE_DRIVE_CREDENTIALS')
    credentials_path = os.getenv('GOOGLE_DRIVE_CREDENTIALS_PATH', 'rock-objective-453508-q3-3cf65595ee72.json')
    
    # 指定的Google Drive文件夹ID
    RESOURCES_FOLDER_ID = "1UbGiexxrOamAhGe8zQU-m4Kqyk9j99-2"
    
    if credentials_json:
        drive_service = GoogleDriveService(
            credentials_json=credentials_json,
            resources_folder_id=RESOURCES_FOLDER_ID
        )
        print("✅ Google Drive service initialized from environment variable")
        print(f"📁 Using folder ID: {RESOURCES_FOLDER_ID}")
    elif os.path.exists(credentials_path):
        drive_service = GoogleDriveService(
            credentials_path=credentials_path,
            resources_folder_id=RESOURCES_FOLDER_ID
        )
        print("✅ Google Drive service initialized from file")
        print(f"📁 Using folder ID: {RESOURCES_FOLDER_ID}")
    else:
        print("⚠️  Google Drive credentials not found.")
        print("💡 To enable Google Drive storage:")
        print("   1. Set GOOGLE_DRIVE_CREDENTIALS environment variable with JSON credentials")
        print("   2. Or place rock-objective-453508-q3-3cf65595ee72.json in the project root")
        print("   3. Falling back to local storage")
        
except Exception as e:
    print(f"❌ Failed to initialize Google Drive service: {str(e)}")
    print("🔄 Falling back to local storage")
    drive_service = None

# Configure file upload settings
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'Resources')
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# Storage for user-created projects (in production, use a database)
USER_CREATED_PROJECTS = {}

# Configure OpenAI API client with the new v1.0+ format - Updated to use DeepSeek
API_AVAILABLE = False
client = None

# Instructions for setting up DeepSeek API
print("=" * 60)
print("🤖 DeepSeek API Configuration")
print("=" * 60)

try:
    # HARDCODED API KEY for DeepSeek - WARNING: NOT RECOMMENDED FOR PRODUCTION!
    # Remove this and use environment variables for security
    HARDCODED_API_KEY = "sk-0e2c23a0864043f7bbfcb36546818447"  # DeepSeek API key
    
    # Try to get API key from environment variable first, then fallback to hardcoded
    api_key = os.getenv('DEEPSEEK_API_KEY') or HARDCODED_API_KEY
    
    if not api_key:
        print("⚠️  No DEEPSEEK_API_KEY environment variable found.")
        print("💡 To enable AI-powered project creation:")
        print("   1. Get an API key from https://platform.deepseek.com/")
        print("   2. Set it as an environment variable:")
        print("      Windows: $env:DEEPSEEK_API_KEY='your-key-here'")
        print("      Linux/Mac: export DEEPSEEK_API_KEY='your-key-here'")
        print("   3. Restart the server")
        print("\n🔄 Using fallback template-based project creation for now...")
        print("=" * 60)
        client = None
        API_AVAILABLE = False
    else:
        if api_key == HARDCODED_API_KEY:
            print("⚠️  WARNING: Using hardcoded API key - SECURITY RISK!")
            print("🔒 For production, use environment variables instead")
        else:
            print("✅ Found DEEPSEEK_API_KEY environment variable")
            
        # Initialize DeepSeek client with custom base_url
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        
        # Test the API connection
        print("🔌 Testing DeepSeek API connection...")
        test_response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "user", "content": "Test connection"}
            ],
            max_tokens=5,
            temperature=0.5
        )
        print("✅ DeepSeek API connection successful!")
        print("🚀 AI-powered project creation is ENABLED")
        API_AVAILABLE = True
        
except Exception as e:
    error_message = str(e)
    print(f"❌ DeepSeek API setup failed: {error_message}")
    
    if "unsupported_country_region_territory" in error_message:
        print("🌍 DeepSeek API is not available in your region.")
        print("💡 Solutions:")
        print("   - Use a VPN to access from a supported region")
        print("   - Use template-based project creation (still fully functional)")
    elif "invalid" in error_message.lower() or "unauthorized" in error_message.lower():
        print("🔑 API key appears to be invalid.")
        print("💡 Please check your API key at https://platform.deepseek.com/")
    else:
        print("🔄 Falling back to template-based project creation")
    
    print("📝 Template mode will create functional projects with 4 steps")
    client = None
    API_AVAILABLE = False

print("=" * 60)

# File upload helper functions
def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_icon(filename):
    """Get appropriate icon class for file type"""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if ext == 'pdf':
        return 'fa-file-pdf'
    elif ext in ['doc', 'docx']:
        return 'fa-file-word'
    elif ext == 'txt':
        return 'fa-file-alt'
    else:
        return 'fa-file'

def generate_file_tags(filename):
    """Generate relevant tags for uploaded files based on filename"""
    tags = []
    filename_lower = filename.lower()
    
    # Python-related tags
    if any(keyword in filename_lower for keyword in ['python', 'py']):
        tags.append('Python')
    if any(keyword in filename_lower for keyword in ['basic', 'intro', 'fundamental']):
        tags.append('Basics')
    if any(keyword in filename_lower for keyword in ['function', 'func']):
        tags.append('Functions')
    if any(keyword in filename_lower for keyword in ['class', 'oop', 'object']):
        tags.append('OOP')
    if any(keyword in filename_lower for keyword in ['data', 'structure']):
        tags.append('Data Structures')
    if any(keyword in filename_lower for keyword in ['algorithm', 'algo']):
        tags.append('Algorithms')
    if any(keyword in filename_lower for keyword in ['loop', 'iteration']):
        tags.append('Loops')
    if any(keyword in filename_lower for keyword in ['condition', 'if', 'else']):
        tags.append('Conditionals')
    if any(keyword in filename_lower for keyword in ['variable', 'var']):
        tags.append('Variables')
    if any(keyword in filename_lower for keyword in ['module', 'import']):
        tags.append('Modules')
    
    # If no specific tags found, add general ones
    if not tags:
        tags = ['Python', 'Learning']
    
    return tags[:3]  # Limit to 3 tags

# Helper function to format markdown-like text to HTML with enhanced design
def format_markdown_text(text):
    """
    将markdown格式的文本转换为符合新设计系统的HTML
    修复版本：改善处理顺序，避免格式冲突
    """
    if not text or not isinstance(text, str):
        return ""
    
    # 转义HTML特殊字符，但保留我们要处理的markdown符号
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # Step 1: 处理代码块（最高优先级，避免内容被其他规则处理）
    code_blocks = []
    def replace_code_block(match):
        language = match.group(1) if match.group(1) else 'text'
        code = match.group(2) if len(match.groups()) >= 2 else ''
        # 恢复代码块中的HTML转义
        code = code.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        code_blocks.append((code, language))
        return f"CODE_BLOCK_PLACEHOLDER_{len(code_blocks) - 1}"

    # 匹配三重反引号代码块 - 修复版本，更灵活的匹配
    text = re.sub(r'```(\w*)\s*(.*?)\s*```', replace_code_block, text, flags=re.DOTALL)
    
    # Step 2: 处理行内代码（避免被其他规则干扰）
    inline_codes = []
    def replace_inline_code(match):
        code = match.group(1)
        # 恢复代码中的HTML转义
        code = code.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        inline_codes.append(code)
        return f"INLINE_CODE_PLACEHOLDER_{len(inline_codes) - 1}"
    
    text = re.sub(r'`([^`\n]+)`', replace_inline_code, text)
    
    # Step 3: 处理标题（按优先级处理）- 在换行处理之前
    # 处理带emoji的主标题
    text = re.sub(r'^##\s+([🎯🔍🐛📋🎓🚀✨💡📚🔗⚠️💪📖📊🎨🤖].*?)$', 
                 r'<div class="answer-section"><div class="section-header"><h2 class="section-title"><span class="emoji">\1</span></h2><div class="section-line"></div></div><div class="section-content">', text, flags=re.MULTILINE)
    
    # 处理带emoji的子标题
    text = re.sub(r'^###\s+([📌💡💻🔍📚🔗⚠️💪📖❌✅💡🚫🎯🔧📊⚡].*?)$', 
                 r'<div class="subsection-header"><h3 class="subsection-title">\1</h3><div class="subsection-accent"></div></div>', text, flags=re.MULTILINE)
    
    # 处理普通二级标题
    text = re.sub(r'^##\s+(.+?)$', 
                 r'<div class="answer-section"><div class="section-header"><h2 class="section-title">\1</h2><div class="section-line"></div></div><div class="section-content">', text, flags=re.MULTILINE)
    
    # 处理普通三级标题
    text = re.sub(r'^###\s+(.+?)$', 
                 r'<div class="subsection-header"><h3 class="subsection-title">\1</h3><div class="subsection-accent"></div></div>', text, flags=re.MULTILINE)
    
    # 处理步骤标题
    text = re.sub(r'#{2,}\s+Step\s+(\d+):?\s*(.*?)(?=\n|$)', 
                 r'<div class="step-container"><div class="step-number">\1</div><h3 class="step-heading">\2</h3></div>', text)
    
    # Step 4: 处理状态指示器和徽章（在换行处理之前）
    status_patterns = {
        r'✅\s*([^\n]+)': r'<span class="status-badge status-success"><span class="badge-icon">✅</span><span class="badge-text">\1</span></span>',
        r'⚠️\s*([^\n]+)': r'<span class="status-badge status-warning"><span class="badge-icon">⚠️</span><span class="badge-text">\1</span></span>',
        r'❌\s*([^\n]+)': r'<span class="status-badge status-error"><span class="badge-icon">❌</span><span class="badge-text">\1</span></span>',
        r'💡\s*([^\n]+)': r'<span class="status-badge status-info"><span class="badge-icon">💡</span><span class="badge-text">\1</span></span>',
        r'🔴\s*([^\n]+)': r'<span class="status-badge status-error"><span class="badge-icon">🔴</span><span class="badge-text">\1</span></span>',
        r'🟡\s*([^\n]+)': r'<span class="status-badge status-warning"><span class="badge-icon">🟡</span><span class="badge-text">\1</span></span>',
        r'🟢\s*([^\n]+)': r'<span class="status-badge status-success"><span class="badge-icon">🟢</span><span class="badge-text">\1</span></span>',
    }
    
    for pattern, replacement in status_patterns.items():
        text = re.sub(pattern, replacement, text)
    
    # Step 5: 处理粗体和斜体
    # 处理粗体
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong class="enhanced-bold">\1</strong>', text)
    # 处理斜体
    text = re.sub(r'\*(.*?)\*', r'<em class="enhanced-italic">\1</em>', text)
    
    # Step 6: 处理列表（在换行处理之前）
    # 处理无序列表
    text = re.sub(r'^\s*-\s+(.*?)$', r'<li class="enhanced-bullet-item"><span class="bullet-icon">▸</span><span class="bullet-text">\1</span></li>', text, flags=re.MULTILINE)
    
    # 将连续的列表项包装在ul中
    text = re.sub(r'(<li class="enhanced-bullet-item">.*?</li>\s*)+', 
                 lambda m: f'<ul class="enhanced-bullet-list">{m.group(0)}</ul>', text, flags=re.DOTALL)
    
    # Step 7: 处理特殊框（在换行处理之前）
    highlight_patterns = {
        r'💡\s*提示[：:]\s*(.*?)(?=\n\n|\n$|$)': r'<div class="highlight-box tip"><span class="highlight-icon">💡</span><div class="highlight-text">\1</div></div>',
        r'⚠️\s*警告[：:]\s*(.*?)(?=\n\n|\n$|$)': r'<div class="highlight-box warning"><span class="highlight-icon">⚠️</span><div class="highlight-text">\1</div></div>',
        r'✅\s*成功[：:]\s*(.*?)(?=\n\n|\n$|$)': r'<div class="highlight-box success"><span class="highlight-icon">✅</span><div class="highlight-text">\1</div></div>',
    }
    
    for pattern, replacement in highlight_patterns.items():
        text = re.sub(pattern, replacement, text, flags=re.DOTALL)
    
    # Step 8: 处理信息卡片（在换行处理之前）
    text = re.sub(r'^\*\*(.*?)\*\*[：:]([^:\n]+)$', 
                 r'<div class="info-card"><span class="info-label">\1</span><span class="info-value">\2</span></div>', 
                 text, flags=re.MULTILINE)
    
    # Step 9: 处理链接
    def process_link(match):
        text_part = match.group(1)
        url = match.group(2)
        
        # 检查是否是有效URL
        if url.startswith(('http://', 'https://', 'www.')):
            return f'<a href="{url}" target="_blank" rel="noopener noreferrer" class="enhanced-link"><span class="link-text">{text_part}</span><i class="fas fa-external-link-alt link-icon"></i></a>'
        else:
            return f'<span class="non-clickable-link">{text_part}</span>'
    
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', process_link, text)
    
    # Step 10: 现在处理换行（确保标题和其他格式已经处理完毕）
    text = text.replace('\n', '<br>')
    
    # Step 11: 恢复代码块
    for i, (code, language) in enumerate(code_blocks):
        placeholder = f"CODE_BLOCK_PLACEHOLDER_{i}"
        
        # 简化的代码块，移除语言标签、行数统计和复制按钮
        code_html = f'''<pre><code class="language-{language}">{code.strip()}</code></pre>'''
        text = text.replace(placeholder, code_html)
    
    # Step 12: 恢复行内代码
    for i, code in enumerate(inline_codes):
        placeholder = f"INLINE_CODE_PLACEHOLDER_{i}"
        text = text.replace(placeholder, f'<code class="enhanced-inline-code">{code}</code>')
    
    # Step 13: 清理多余的换行
    text = re.sub(r'(<br>){3,}', '<br><br>', text)
    
    # Step 14: 正确关闭section标签
    # 为每个answer-section添加正确的结束标签
    sections = text.split('<div class="answer-section">')
    if len(sections) > 1:
        formatted_sections = [sections[0]]  # 第一部分（可能为空）
        for i, section in enumerate(sections[1:], 1):
            # 为每个section添加结束标签
            if i < len(sections) - 1:
                # 不是最后一个section，在下一个section前结束
                section_end = '</div></div>'
            else:
                # 最后一个section
                section_end = '</div></div>'
            
            formatted_sections.append('<div class="answer-section">' + section + section_end)
        
        text = ''.join(formatted_sections)
    
    # Step 15: 最终包装
    if text.strip():
        text = f'<div class="enhanced-response-container">{text}</div>'
    
    return text

# Format the response with the proper HTML structure
def format_response(text, question_type="DIRECT", original_question="", include_json_code=True):
    """
    Format AI response with proper HTML structure and styling
    """
    # If already formatted, return as is
    if '<div class="answer-box">' in text:
        return text
    
    # Format the markdown text to HTML
    formatted_text = format_markdown_text(text)
    
    # For step guidance, return clean HTML without extra wrappers
    # The new CSS styles will handle the visual formatting
    return formatted_text

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/learning_chatbot')
def learning_chatbot():
    """Serve the learning chatbot interface"""
    return send_file('learning_chatbot.html')

@app.route('/graph')
def graph():
    """Serve the graph interface"""
    return send_file('graph.html')

@app.route('/auth')
def auth():
    """Serve the auth interface"""
    return send_file('auth.html')

@app.route('/online_ide')
def online_ide():
    """Serve the online IDE page"""
    return send_file('online_ide.html')

# 静态文件服务路由
@app.route('/styles.css')
def serve_css():
    return send_file('styles.css', mimetype='text/css')

@app.route('/script.js')
def serve_js():
    return send_file('script.js', mimetype='application/javascript')

@app.route('/notes_fix_complete.js')
def serve_notes_js():
    return send_file('notes_fix_complete.js', mimetype='application/javascript')

@app.route('/notes_fix.js')
def serve_notes_fix_js():
    return send_file('notes_fix.js', mimetype='application/javascript')

@app.route('/upload_fix.js')
def serve_upload_js():
    return send_file('upload_fix.js', mimetype='application/javascript')

@app.route('/debug_upload.js')
def serve_debug_upload_js():
    return send_file('debug_upload.js', mimetype='application/javascript')

@app.route('/favicon.ico')
def serve_favicon():
    return send_file('favicon.ico')

@app.route('/favicon.svg')
def serve_favicon_svg():
    return send_file('favicon.svg')

# 通用静态文件服务（作为备用）
@app.route('/<path:path>')
def serve_static(path):
    # 安全检查，防止路径遍历攻击
    if '..' in path or path.startswith('/'):
        return "File not found", 404
    
    # 检查文件是否存在
    if os.path.exists(path):
        return send_file(path)
    else:
        return "File not found", 404

@app.route('/api/chat', methods=['POST'])
@optional_auth
def chat():
    try:
        message = request.json.get('message', '')
        code_analysis = request.json.get('code_analysis', None)
        query_classification = request.json.get('query_classification', None)
        conversation_id = request.json.get('conversation_id', 'default')
        
        if not message:
            return jsonify({"error": "No message provided"}), 400

        # 获取当前用户（如果已登录）
        current_user = get_current_user()
        user_id = current_user['id'] if current_user else None

        # 如果用户已登录，确保conversation_id包含用户标识以实现数据隔离
        if user_id:
            conversation_id = f"user_{user_id}_{conversation_id}"

        # Determine question type from query classification
        question_type = "DIRECT"
        system_prompt = PROMPTS["PYTHON_PROJECT_QUICK_RESPONSE_PROMPT"]  # 默认使用简短回答
        
        # 检测是否是"Explain more"类型的请求
        explain_more_indicators = [
            "explain this in more detail",
            "explain more",
            "more details",
            "detailed explanation",
            "elaborate",
            "can you explain",
            "tell me more",
            "expand on",
            "go deeper",
            "more information"
        ]
        
        is_explain_more = any(indicator in message.lower() for indicator in explain_more_indicators)
        
        # 如果是"Explain more"请求，使用详细回答提示词
        if is_explain_more:
            system_prompt = PROMPTS["PYTHON_PROJECT_DETAILED_RESPONSE_PROMPT"]
            question_type = "DETAILED"
        
        # If we have query classification from frontend, use it (这会覆盖上面的检测)
        if query_classification and 'query_type' in query_classification:
            question_type = query_classification['query_type']
            if question_type == "DETAILED":
                system_prompt = PROMPTS["PYTHON_PROJECT_DETAILED_RESPONSE_PROMPT"]
            else:
                system_prompt = PROMPTS["PYTHON_PROJECT_QUICK_RESPONSE_PROMPT"]
        
        # Enhance system prompt with code analysis if available
        if code_analysis:
            problem_type = code_analysis.get('problem_type', 'unknown')
            problem_details = code_analysis.get('problem_details', {})
            
            # Use the specialized code analysis prompt
            system_prompt = PROMPTS["CODE_ANALYSIS_PROMPT"]
            
            # Add code analysis information to the user message
            message = f"""
Code Analysis Results:
- Problem Type: {problem_type}
- Description: {problem_details.get('description', 'Unknown issue')}
- Error Message: {problem_details.get('error', 'No error message')}

User's Original Message:
{message}
"""

        # 保存用户消息到数据库（如果用户已登录）
        if user_id:
            context_data = {
                'code_analysis': code_analysis,
                'query_classification': query_classification,
                'question_type': question_type,
                'user_specific': True  # 标记为用户特定数据
            }
            db_manager.save_chat_message(
                user_id=user_id,
                conversation_id=conversation_id,
                message_type='user',
                message_content=message,
                context_data=context_data
            )

        # Call OpenAI API
        try:
            completion = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": message,
                    },
                ],
            )
            
            # Extract the response
            ai_response = completion.choices[0].message.content
            
            # 保存AI回复到数据库（如果用户已登录）
            if user_id:
                db_manager.save_chat_message(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    message_type='assistant',
                    message_content=ai_response,
                    context_data={'formatted': False, 'user_specific': True}
                )
            
            try:
                # Format the response with proper HTML structure before sending it
                formatted_response = format_response(ai_response, question_type, message)
                
                # Return response with metadata about question classification
                return jsonify({
                    "response": formatted_response,
                    "question_type": question_type,
                    "user_specific": user_id is not None,
                    "conversation_id": conversation_id if user_id else None
                })
            except Exception as format_error:
                import traceback
                print(f"Formatting Error: {str(format_error)}")
                print(traceback.format_exc())
                # Return the raw response if formatting fails
                return jsonify({
                    "response": f"<div class='answer-box'><div class='answer-content'><p>{ai_response}</p></div></div>",
                    "question_type": question_type,
                    "user_specific": user_id is not None
                })
            
        except Exception as e:
            import traceback
            print(f"OpenAI API Error: {str(e)}")
            print(traceback.format_exc())
            return jsonify({
                "error": "I'm having trouble processing your request right now. Please try again later.",
                "details": str(e) if app.debug else None
            }), 500
    
    except Exception as e:
        import traceback
        print(f"Chat Error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/api/detailed_chat', methods=['POST'])
def detailed_chat():
    try:
        message = request.json.get('message', '')
        if not message:
            return jsonify({"error": "No message provided"}), 400

        # Use the detailed response prompt for comprehensive answers
        system_prompt = PROMPTS["PYTHON_PROJECT_DETAILED_RESPONSE_PROMPT"]
        question_type = "DETAILED"
        
        # Call OpenAI API
        try:
            completion = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": message,
                    },
                ],
            )
            
            # Extract the response
            ai_response = completion.choices[0].message.content
            
            try:
                # Format the response with proper HTML structure before sending it
                formatted_response = format_response(ai_response, question_type, message)
                
                # Return response with metadata
                return jsonify({
                    "response": formatted_response,
                    "question_type": "DETAILED"
                })
            except Exception as format_error:
                import traceback
                print(f"Formatting Error: {str(format_error)}")
                print(traceback.format_exc())
                # Return the raw response if formatting fails
                return jsonify({
                    "response": f"<div class='answer-box'><div class='answer-content'><p>{ai_response}</p></div></div>",
                    "question_type": "DETAILED"
                })
                
        except Exception as api_error:
            import traceback
            print(f"API Error: {str(api_error)}")
            print(traceback.format_exc())
            # Fallback to a formatted error message
            return jsonify({
                "response": "Sorry, there was an error connecting to the AI service. Please try again later.",
                "question_type": "DIRECT"
            }), 500
        
    except Exception as e:
        import traceback
        print(f"Server Error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# Add routes to serve static files
@app.route('/<path:path>')
def serve_static(path):
    return send_file(path)

# Problem identification function to analyze code and categorize issues
def identify_problem(code, error_message=None):
    problem_type = "unknown"
    problem_details = {}
    
    # Try static analysis first
    try:
        # Check for syntax errors
        try:
            ast.parse(code)
        except SyntaxError as e:
            problem_type = "syntax_error"
            problem_details = {
                "line": e.lineno,
                "offset": e.offset,
                "text": str(e),
                "description": f"Syntax error on line {e.lineno}: {e.msg}"
            }
            return problem_type, problem_details
            
        # If no syntax errors, try running the code in a sandbox
        if error_message is None:
            try:
                # Create a string buffer to capture stdout
                buffer = StringIO()
                with redirect_stdout(buffer):
                    # Execute the code with a timeout
                    exec(code, {"__builtins__": __builtins__}, {})
                # If we reach here, code executed without errors
                problem_type = "no_error"
                problem_details = {
                    "output": buffer.getvalue(),
                    "description": "Code executed successfully"
                }
            except Exception as e:
                error_message = traceback.format_exc()
                # Continue to error analysis below
        
        # Analyze runtime errors if we have an error message
        if error_message:
            # Check for common error types
            if "IndexError" in error_message:
                problem_type = "index_error"
                problem_details = {
                    "description": "Index error - trying to access an element that doesn't exist",
                    "error": error_message
                }
            elif "KeyError" in error_message:
                problem_type = "key_error"
                problem_details = {
                    "description": "Key error - trying to access a dictionary key that doesn't exist",
                    "error": error_message
                }
            elif "TypeError" in error_message:
                problem_type = "type_error"
                problem_details = {
                    "description": "Type error - operation applied to incorrect data type",
                    "error": error_message
                }
            elif "NameError" in error_message:
                problem_type = "name_error"
                problem_details = {
                    "description": "Name error - using a variable that doesn't exist",
                    "error": error_message
                }
            elif "ImportError" in error_message or "ModuleNotFoundError" in error_message:
                problem_type = "import_error"
                problem_details = {
                    "description": "Import error - module not found or cannot be imported",
                    "error": error_message
                }
            elif "ZeroDivisionError" in error_message:
                problem_type = "zero_division_error"
                problem_details = {
                    "description": "Zero division error - division by zero",
                    "error": error_message
                }
            else:
                problem_type = "runtime_error"
                problem_details = {
                    "description": "Runtime error - the code has errors during execution",
                    "error": error_message
                }
    except Exception as e:
        # If our analysis code itself fails, use LLM-based analysis
        problem_type = "analysis_error"
        problem_details = {
            "description": "Could not analyze code automatically",
            "error": str(e)
        }
    
    return problem_type, problem_details

@app.route('/api/analyze_code', methods=['POST'])
def analyze_code():
    try:
        data = request.json
        code = data.get('code', '')
        error_message = data.get('error_message', None)
        
        if not code:
            return jsonify({"error": "No code provided"}), 400
            
        # First try automatic analysis
        problem_type, problem_details = identify_problem(code, error_message)
        
        # If automatic analysis succeeded with high confidence, return it
        if problem_type != "unknown" and problem_type != "analysis_error":
            return jsonify({
                "problem_type": problem_type,
                "problem_details": problem_details,
                "analysis_method": "automatic"
            })
        
        # Otherwise, use LLM for deeper analysis
        try:
            system_prompt = """
            You are an intelligent Python tutor. Analyze the following student code and output:
            1. Identify any errors (syntax, runtime, logic).
            2. If there is an error message, explain what it means and the likely cause.
            3. Suggest a resource topic or keyword for further help.
            
            Format your response as a JSON object with these fields:
            {
                "problem_type": "syntax_error|runtime_error|logic_error|concept_confusion|no_error",
                "description": "Brief description of the problem",
                "explanation": "Detailed explanation of what's wrong and why",
                "suggested_resource": "Python topic that would help with this issue"
            }
            
            Only respond with the JSON object, nothing else.
            """
            
            completion = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "system", "content": system_prompt},
                          {"role": "user", "content": f"Student code:\n{code}\n\nError message/output:\n{error_message if error_message else 'No error message provided'}"}],
                temperature=0.3
            )
            
            # Parse the LLM response
            try:
                llm_analysis = json.loads(completion.choices[0].message.content)
                return jsonify({
                    **llm_analysis,
                    "analysis_method": "llm"
                })
            except json.JSONDecodeError:
                # If response isn't valid JSON, return raw text with error
                return jsonify({
                    "problem_type": "unknown",
                    "problem_details": {
                        "description": "Could not parse LLM response",
                        "raw_response": completion.choices[0].message.content
                    },
                    "analysis_method": "failed_llm"
                })
                
        except Exception as e:
            return jsonify({
                "problem_type": problem_type,
                "problem_details": problem_details,
                "analysis_method": "automatic_fallback",
                "llm_error": str(e)
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Add a route for NLP query classification
@app.route('/api/classify_query', methods=['POST'])
def classify_query():
    try:
        data = request.json
        query = data.get('query', '')
        
        if not query:
            return jsonify({"error": "No query provided"}), 400
            
        # Simple keyword-based classification first
        detailed_keywords = [
            "how to implement", "explain in detail", "step by step", 
            "code example", "show me how", "implementation", 
            "architecture", "explain the concept", "deep dive", 
            "in depth", "comprehensive"
        ]
        
        # Check if any detailed keywords are in the query
        for keyword in detailed_keywords:
            if keyword.lower() in query.lower():
                return jsonify({
                    "query_type": "DETAILED",
                    "analysis_method": "keyword",
                    "matched_keyword": keyword
                })
                
        # If no keywords match, use LLM for classification
        system_prompt = """
        Classify the following user question:
        - What is the main programming concept or problem type?
        - Is this a direct question (simple, factual) or a detailed question (needs in-depth explanation)?
        
        Format your response as a JSON object with these fields:
        {
            "query_type": "DIRECT|DETAILED",
            "topic": "The main Python concept or problem type",
            "suggested_resource": "A good resource topic for this question"
        }
        
        Only respond with the JSON object, nothing else.
        """
        
        completion = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": f"Question: {query}"}],
            temperature=0.3
        )
        
        # Parse the LLM response
        try:
            llm_analysis = json.loads(completion.choices[0].message.content)
            return jsonify({
                **llm_analysis,
                "analysis_method": "llm"
            })
        except json.JSONDecodeError:
            # Default to DIRECT if we can't parse the response
            return jsonify({
                "query_type": "DIRECT",
                "analysis_method": "default",
                "raw_response": completion.choices[0].message.content
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def run_code_with_timeout(code, timeout=5):
    """Run Python code with timeout and restricted builtins using threading"""
    import threading
    import signal
    import time
    
    # Store the result
    result = {
        'success': False,
        'stdout': '',
        'stderr': '',
        'error': 'Execution failed'
    }
    
    def execute_code():
        try:
            # Prepare safe environment with restricted builtins
            safe_builtins = {
                'abs': abs, 'all': all, 'any': any, 'bool': bool, 
                'chr': chr, 'dict': dict, 'dir': dir, 'divmod': divmod,
                'enumerate': enumerate, 'filter': filter, 'float': float,
                'format': format, 'frozenset': frozenset, 'hash': hash,
                'hex': hex, 'int': int, 'isinstance': isinstance,
                'issubclass': issubclass, 'len': len, 'list': list, 
                'map': map, 'max': max, 'min': min, 'oct': oct,
                'ord': ord, 'pow': pow, 'print': print, 'range': range,
                'repr': repr, 'reversed': reversed, 'round': round,
                'set': set, 'slice': slice, 'sorted': sorted, 'str': str,
                'sum': sum, 'tuple': tuple, 'type': type, 'zip': zip,
                # Add some additional safe functions
                'help': help, 'id': id, 'getattr': getattr, 'hasattr': hasattr,
                'setattr': setattr, 'delattr': delattr, 'callable': callable
            }
            
            # Set up output capture
            stdout_buffer = StringIO()
            stderr_buffer = StringIO()
            
            # Execute the code in a restricted environment
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                # Create a restricted globals environment
                restricted_globals = {
                    "__builtins__": safe_builtins,
                    "__name__": "__main__",
                    "__doc__": None,
                    "__package__": None
                }
                
                # Execute the code
                exec(code, restricted_globals, {})
                
            # Get output
            stdout_output = stdout_buffer.getvalue()
            stderr_output = stderr_buffer.getvalue()
            
            # Update result
            result.update({
                'success': True,
                'stdout': stdout_output,
                'stderr': stderr_output,
                'error': None
            })
            
        except Exception as e:
            # Capture the error
            error_message = str(e)
            if hasattr(e, '__traceback__'):
                import traceback
                error_message = traceback.format_exc()
            
            result.update({
                'success': False,
                'stdout': stdout_buffer.getvalue() if 'stdout_buffer' in locals() else '',
                'stderr': stderr_buffer.getvalue() if 'stderr_buffer' in locals() else '',
                'error': error_message
            })
    
    # Create and start the thread
    thread = threading.Thread(target=execute_code)
    thread.daemon = True  # Make thread daemon so it dies with main process
    thread.start()
    
    # Wait for the thread to complete with timeout
    thread.join(timeout)
    
    # Check if thread is still alive (timeout occurred)
    if thread.is_alive():
        result.update({
            'success': False,
            'stdout': '',
            'stderr': '',
            'error': f'Code execution timed out after {timeout} seconds. This might be due to an infinite loop or long-running operation.'
        })
    
    return result

@app.route('/api/execute_code', methods=['POST'])
def execute_code():
    try:
        data = request.json
        code = data.get('code', '')
        
        if not code:
            return jsonify({"error": "No code provided"}), 400
        
        # Execute the code safely
        result = run_code_with_timeout(code)
        
        # Return the execution result
        return jsonify({
            'success': result['success'],
            'output': result['stdout'],
            'error': result['error'] or result['stderr']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'output': '',
            'error': str(e)
        }), 500

@app.route('/api/projects', methods=['GET'])
@optional_auth
def get_projects():
    """Get available project templates and user projects"""
    try:
        projects = {}
        
        # Add template projects (available to all users)
        for key, value in PROJECT_TEMPLATES.items():
            projects[key] = {
                'name': value['name'],
                'description': value['description'],
                'total_steps': len(value['steps']),
                'type': 'template'
            }
        
        # Add user-created projects (only for authenticated users)
        current_user = get_current_user()
        if current_user:
            user_id = current_user['id']
            user_projects = db_manager.get_user_projects(user_id)
            
            for project_id, project_info in user_projects.items():
                project_data = project_info['data']
                projects[project_id] = {
                    'name': project_data['name'],
                    'description': project_data['description'],
                    'total_steps': len(project_data['steps']),
                    'type': 'user_created',
                    'created_at': project_info['created_at'],
                    'updated_at': project_info['updated_at']
                }
        
        # 添加旧的内存中的项目（兼容性）
        for key, value in USER_CREATED_PROJECTS.items():
            if key not in projects:  # 避免重复
                projects[key] = {
                    'name': value['name'],
                    'description': value['description'],
                    'total_steps': len(value['steps']),
                    'type': 'user_created'
                }
            
        return jsonify({'success': True, 'projects': projects})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def create_fallback_project_steps(project_name, project_description):
    """Create fallback project steps when AI is not available"""
    steps = [
        {
            'step': 1,
            'title': 'Project Setup and Planning',
            'description': f'Set up the basic structure for your {project_name} project. Create the main Python file and understand the project requirements.',
            'concepts': ['variables', 'basic_syntax', 'comments']
        },
        {
            'step': 2,
            'title': 'Basic Functionality',
            'description': 'Implement the core functionality of your project using basic Python concepts.',
            'concepts': ['functions', 'input', 'output']
        },
        {
            'step': 3,
            'title': 'Data Processing and Logic',
            'description': 'Add more complex logic and data processing capabilities to your project.',
            'concepts': ['conditionals', 'loops', 'data_structures']
        },
        {
            'step': 4,
            'title': 'Final Implementation and Testing',
            'description': 'Complete your project implementation and add proper error handling and testing.',
            'concepts': ['error_handling', 'testing', 'file_operations']
        }
    ]
    
    return steps

@app.route('/api/create_project', methods=['POST'])
@require_auth
def create_project():
    """Create a new learning project using AI or fallback to templates"""
    try:
        data = request.get_json()
        project_name = data.get('name', '').strip()
        project_description = data.get('description', '').strip()
        
        # Input validation
        if not project_name:
            return jsonify({'success': False, 'error': 'Project name is required'}), 400
        
        if len(project_name) < 3:
            return jsonify({'success': False, 'error': 'Project name must be at least 3 characters long'}), 400
        
        # 获取当前用户
        current_user = get_current_user()
        user_id = current_user['id']
        
        # Create a unique project ID
        import uuid
        project_id = f"user_{user_id}_{project_name.lower().replace(' ', '_')}_{str(uuid.uuid4())[:8]}"
        
        # Check if API is available for AI-powered project generation
        if API_AVAILABLE and client:
            try:
                # Use AI to generate project steps
                system_prompt = """You are an expert Python programming educator. Generate a comprehensive learning project based on the user's request.

Return your response as a JSON object with the following structure:
{
    "name": "Project Name",
    "description": "Brief description of what students will learn",
    "steps": [
        {
            "step": 1,
            "title": "Step Title",
            "description": "What students will accomplish in this step",
            "concepts": ["concept1", "concept2", "concept3"]
        }
    ]
}

Requirements:
- Create 4-6 progressive learning steps
- Each step should build on previous concepts
- Focus on fundamental Python concepts like variables, functions, loops, conditionals, data structures
- Make it suitable for beginners to intermediate learners
- Include clear learning objectives for each step
- Provide detailed step descriptions that guide students through the learning process

Return ONLY the JSON object, no additional text."""

                user_prompt = f"""Create a Python learning project:
Project Name: {project_name}
Description: {project_description if project_description else f'A Python project focused on {project_name}'}

The project should teach core Python programming concepts through hands-on coding exercises."""

                completion = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
                
                # Parse the AI response
                ai_response = completion.choices[0].message.content.strip()
                
                # Try to extract JSON from the response
                try:
                    # Remove any markdown formatting if present
                    if '```json' in ai_response:
                        ai_response = ai_response.split('```json')[1].split('```')[0].strip()
                    elif '```' in ai_response:
                        ai_response = ai_response.split('```')[1].split('```')[0].strip()
                    
                    project_data = json.loads(ai_response)
                    
                    # Validate the structure
                    if not isinstance(project_data, dict) or 'steps' not in project_data:
                        raise ValueError("Invalid project structure from AI")
                    
                    # Ensure we have the required fields
                    if 'name' not in project_data:
                        project_data['name'] = project_name
                    if 'description' not in project_data:
                        project_data['description'] = project_description or f'A Python learning project: {project_name}'
                    
                    # Validate steps
                    if not isinstance(project_data['steps'], list) or len(project_data['steps']) == 0:
                        raise ValueError("Project must have at least one step")
                    
                    # Ensure each step has required fields
                    for i, step in enumerate(project_data['steps']):
                        if 'step' not in step:
                            step['step'] = i + 1
                        if 'title' not in step:
                            step['title'] = f'Step {i + 1}'
                        if 'description' not in step:
                            step['description'] = 'Learning step description'
                        if 'concepts' not in step:
                            step['concepts'] = ['basic_python']
                    
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    print(f"Failed to parse AI response: {e}")
                    print(f"AI Response: {ai_response}")
                    # Fall back to template-based generation
                    raise Exception("AI response parsing failed")
                
            except Exception as e:
                print(f"AI project generation failed: {e}")
                # Fall back to template-based generation
                project_data = {
                    'name': project_name,
                    'description': project_description or f'A Python learning project: {project_name}',
                    'steps': create_fallback_project_steps(project_name, project_description or f'Learning project focused on {project_name}')
                }
        else:
            # Use fallback template-based generation
            project_data = {
                'name': project_name,
                'description': project_description or f'A Python learning project: {project_name}',
                'steps': create_fallback_project_steps(project_name, project_description or f'Learning project focused on {project_name}')
            }
        
        # Save the project to database
        success = db_manager.save_user_project(user_id, project_id, project_data)
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to save project to database'}), 500
        
        # Also save to memory for compatibility (temporary)
        USER_CREATED_PROJECTS[project_id] = project_data
        
        return jsonify({
            'success': True,
            'message': f'Project "{project_name}" created successfully!',
            'project_id': project_id,
            'project': project_data
        })
        
    except Exception as e:
        import traceback
        print(f"Error creating project: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': f'Failed to create project: {str(e)}'}), 500

# File upload routes
@app.route('/api/upload', methods=['POST'])
@require_auth
def upload_file():
    """Handle file upload - Google Drive integration"""
    try:
        print("File upload request received")
        
        # 获取当前用户
        current_user = get_current_user()
        user_id = current_user['id']
        
        # Check if the post request has the file part
        if 'file' not in request.files:
            print("No file part in request")
            return jsonify({'success': False, 'error': 'No file selected'})
        
        file = request.files['file']
        
        # If user does not select file, browser also submits an empty part without filename
        if file.filename == '':
            print("No file selected")
            return jsonify({'success': False, 'error': 'No file selected'})
        
        # Check file size
        if request.content_length > MAX_FILE_SIZE:
            print(f"File too large: {request.content_length} bytes")
            return jsonify({'success': False, 'error': f'File size exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit'})
        
        if file and allowed_file(file.filename):
            # 保存原始文件名（用于显示）
            original_filename = file.filename
            # 生成安全的文件名（用于存储）
            secure_original_filename = secure_filename(file.filename)
            
            # 如果secure_filename返回空字符串或者只是扩展名，使用默认名称
            if not secure_original_filename or secure_original_filename.startswith('.') or '.' not in secure_original_filename:
                # 从原始文件名提取扩展名
                import os
                _, ext = os.path.splitext(original_filename)
                if not ext:
                    ext = '.file'
                secure_original_filename = f'uploaded_file{ext}'
            
            # 获取MIME类型
            import mimetypes
            mime_type, _ = mimetypes.guess_type(original_filename)
            
            # 生成标签
            tags = generate_file_tags(original_filename)
            
            if drive_service:
                # 使用Google Drive存储
                try:
                    # 读取文件数据到内存
                    file_data = file.read()
                    file_size = len(file_data)
                    
                    # 上传到Google Drive（使用安全文件名）
                    drive_result = drive_service.upload_file_from_memory(
                        file_data=file_data,
                        original_filename=secure_original_filename,
                        user_id=user_id,
                        mime_type=mime_type
                    )
                    
                    # 保存文件信息到数据库（使用原始文件名用于显示）
                    file_id = db_manager.save_user_file(
                        user_id=user_id,
                        filename=drive_result['name'],
                        original_filename=original_filename,  # 保存原始文件名
                        file_path=None,  # 不使用本地路径
                        file_size=file_size,
                        mime_type=mime_type,
                        tags=tags,
                        drive_file_id=drive_result['id'],
                        drive_folder_id=drive_result['drive_folder_id'],
                        storage_type='drive'
                    )
                    
                    if not file_id:
                        # 如果数据库保存失败，删除Google Drive上的文件
                        drive_service.delete_file(drive_result['id'])
                        return jsonify({'success': False, 'error': 'Failed to save file information'}), 500
                    
                    file_info = {
                        'id': file_id,
                        'filename': drive_result['name'],
                        'original_name': original_filename,  # 返回原始文件名
                        'size': file_size,
                        'upload_date': drive_result['created_time'],
                        'tags': tags,
                        'icon': get_file_icon(original_filename),
                        'mime_type': mime_type,
                        'drive_file_id': drive_result['id'],
                        'storage_type': 'drive'
                    }
                    
                    print(f"File uploaded to Google Drive successfully: {file_info}")
                    
                    return jsonify({
                        'success': True, 
                        'message': f'File "{original_filename}" uploaded to Google Drive successfully!',
                        'file': file_info
                    })
                    
                except Exception as e:
                    print(f"Google Drive upload error: {str(e)}")
                    return jsonify({'success': False, 'error': f'Google Drive upload failed: {str(e)}'}), 500
            
            else:
                # 回退到本地存储
                # Generate unique filename with timestamp and user ID
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                name, ext = os.path.splitext(secure_original_filename)
                unique_filename = f"user_{user_id}_{name}_{timestamp}{ext}"
                
                # Create user-specific upload directory
                user_upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], f'user_{user_id}')
                if not os.path.exists(user_upload_dir):
                    os.makedirs(user_upload_dir)
                
                # Save file
                file_path = os.path.join(user_upload_dir, unique_filename)
                print(f"Saving file to local storage: {file_path}")
                
                file.save(file_path)
                
                # Get file info
                file_size = os.path.getsize(file_path)
                upload_date = datetime.datetime.now().isoformat()
                
                # 保存文件信息到数据库（使用原始文件名用于显示）
                file_id = db_manager.save_user_file(
                    user_id=user_id,
                    filename=unique_filename,
                    original_filename=original_filename,  # 保存原始文件名
                    file_path=file_path,
                    file_size=file_size,
                    mime_type=mime_type,
                    tags=tags,
                    storage_type='local'
                )
                
                if not file_id:
                    # 如果数据库保存失败，删除已上传的文件
                    try:
                        os.remove(file_path)
                    except:
                        pass
                    return jsonify({'success': False, 'error': 'Failed to save file information'}), 500
                
                file_info = {
                    'id': file_id,
                    'filename': unique_filename,
                    'original_name': original_filename,  # 返回原始文件名
                    'size': file_size,
                    'upload_date': upload_date,
                    'tags': tags,
                    'icon': get_file_icon(original_filename),
                    'path': file_path,
                    'mime_type': mime_type,
                    'storage_type': 'local'
                }
                
                print(f"File uploaded to local storage successfully: {file_info}")
                
                return jsonify({
                    'success': True, 
                    'message': f'File "{secure_original_filename}" uploaded successfully!',
                    'file': file_info
                })
        else:
            allowed_exts = ', '.join(ALLOWED_EXTENSIONS)
            error_msg = f'Invalid file type. Allowed types: {allowed_exts}'
            print(f"Invalid file type: {file.filename}")
            return jsonify({'success': False, 'error': error_msg})
            
    except Exception as e:
        error_msg = f'Upload failed: {str(e)}'
        print(f"Upload error: {error_msg}")
        return jsonify({'success': False, 'error': error_msg})

@app.route('/api/files', methods=['GET'])
@require_auth
def list_files():
    """List all uploaded files for current user - Google Drive integration"""
    try:
        # 获取当前用户
        current_user = get_current_user()
        user_id = current_user['id']
        
        # 从数据库获取用户文件
        user_files = db_manager.get_user_files(user_id)
        
        files = []
        for file_info in user_files:
            storage_type = file_info.get('storage_type', 'local')
            
            if storage_type == 'drive' and drive_service:
                # Google Drive文件
                files.append({
                    'id': file_info['id'],
                    'filename': file_info['filename'],
                    'original_name': file_info['original_filename'],
                    'size': file_info['file_size'],
                    'upload_date': file_info['uploaded_at'],
                    'tags': file_info['tags'],
                    'icon': get_file_icon(file_info['original_filename']),
                    'mime_type': file_info['mime_type'],
                    'drive_file_id': file_info['drive_file_id'],
                    'storage_type': 'drive'
                })
            elif storage_type == 'local':
                # 本地文件 - 检查文件是否仍然存在
                if file_info['file_path'] and os.path.exists(file_info['file_path']):
                    files.append({
                        'id': file_info['id'],
                        'filename': file_info['filename'],
                        'original_name': file_info['original_filename'],
                        'size': file_info['file_size'],
                        'upload_date': file_info['uploaded_at'],
                        'tags': file_info['tags'],
                        'icon': get_file_icon(file_info['original_filename']),
                        'mime_type': file_info['mime_type'],
                        'storage_type': 'local'
                    })
        
        return jsonify({'success': True, 'files': files})
        
    except Exception as e:
        error_msg = f'Failed to list files: {str(e)}'
        print(f"List files error: {error_msg}")
        return jsonify({'success': False, 'error': error_msg})

@app.route('/api/download/<int:file_id>')
@require_auth
def download_file(file_id):
    """Download a specific file - Google Drive integration"""
    try:
        # 获取当前用户
        current_user = get_current_user()
        user_id = current_user['id']
        
        # 获取用户文件列表
        user_files = db_manager.get_user_files(user_id)
        
        # 查找指定文件
        target_file = None
        for file_info in user_files:
            if file_info['id'] == file_id:
                target_file = file_info
                break
        
        if not target_file:
            return jsonify({'success': False, 'error': 'File not found or access denied'}), 404
        
        storage_type = target_file.get('storage_type', 'local')
        
        if storage_type == 'drive' and drive_service:
            # Google Drive文件下载
            drive_file_id = target_file['drive_file_id']
            if not drive_file_id:
                return jsonify({'success': False, 'error': 'Drive file ID not found'}), 404
            
            try:
                # 从Google Drive下载文件
                file_content = drive_service.download_file(drive_file_id)
                
                # 创建响应
                response = make_response(file_content)
                response.headers['Content-Type'] = target_file['mime_type'] or 'application/octet-stream'
                response.headers['Content-Disposition'] = f'attachment; filename="{target_file["original_filename"]}"'
                return response
                
            except Exception as e:
                print(f"Google Drive download error: {str(e)}")
                return jsonify({'success': False, 'error': f'Google Drive download failed: {str(e)}'}), 500
        
        elif storage_type == 'local':
            # 本地文件下载
            file_path = target_file['file_path']
            if not file_path or not os.path.exists(file_path):
                return jsonify({'success': False, 'error': 'File not found on disk'}), 404
            
            return send_file(
                file_path, 
                as_attachment=True,
                download_name=target_file['original_filename']
            )
        else:
            return jsonify({'success': False, 'error': 'File storage type not supported or service unavailable'}), 400
        
    except Exception as e:
        error_msg = f'Download failed: {str(e)}'
        print(f"Download error: {error_msg}")
        return jsonify({'success': False, 'error': error_msg}), 500

@app.route('/api/delete/<int:file_id>', methods=['DELETE'])
@require_auth
def delete_file(file_id):
    """Delete a specific file - Google Drive integration"""
    try:
        # 获取当前用户
        current_user = get_current_user()
        user_id = current_user['id']
        
        # 获取用户文件列表
        user_files = db_manager.get_user_files(user_id)
        
        # 查找指定文件
        target_file = None
        for file_info in user_files:
            if file_info['id'] == file_id:
                target_file = file_info
                break
        
        if not target_file:
            return jsonify({'success': False, 'error': 'File not found or access denied'}), 404
        
        storage_type = target_file.get('storage_type', 'local')
        
        # 从数据库删除文件记录
        conn = sqlite3.connect(db_manager.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM user_files WHERE id = ? AND user_id = ?', (file_id, user_id))
        conn.commit()
        conn.close()
        
        # 根据存储类型删除实际文件
        if storage_type == 'drive' and drive_service:
            # 删除Google Drive文件
            drive_file_id = target_file.get('drive_file_id')
            if drive_file_id:
                try:
                    drive_service.delete_file(drive_file_id)
                    print(f"Google Drive file deleted: {drive_file_id}")
                except Exception as e:
                    print(f"Warning: Could not delete file from Google Drive: {e}")
        elif storage_type == 'local':
            # 删除本地文件
            try:
                if target_file.get('file_path') and os.path.exists(target_file['file_path']):
                    os.remove(target_file['file_path'])
                    print(f"Local file deleted: {target_file['file_path']}")
            except Exception as e:
                print(f"Warning: Could not delete file from disk: {e}")
        
        return jsonify({
            'success': True, 
            'message': f'File "{target_file["original_filename"]}" deleted successfully'
        })
        
    except Exception as e:
        error_msg = f'Delete failed: {str(e)}'
        print(f"Delete error: {error_msg}")
        return jsonify({'success': False, 'error': error_msg}), 500

# ================================
# 用户认证相关路由
# ================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        
        # 输入验证
        if not username or len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters long'}), 400
        
        if not email or '@' not in email:
            return jsonify({'error': 'Please enter a valid email address'}), 400
        
        if not password or len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        if password != confirm_password:
            return jsonify({'error': 'Passwords do not match'}), 400
        
        # 创建用户
        user_id, message = db_manager.create_user(username, email, password)
        
        if user_id:
            return jsonify({
                'success': True,
                'message': message,
                'user_id': user_id
            }), 201
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        return jsonify({'error': f'注册失败: {str(e)}'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        username_or_email = data.get('username_or_email', '').strip()
        password = data.get('password', '')
        remember_me = data.get('remember_me', False)
        
        if not username_or_email or not password:
            return jsonify({'error': 'Please enter your username/email and password'}), 400
        
        # 验证用户
        user, message = db_manager.authenticate_user(username_or_email, password)
        
        if user:
            # 创建会话
            expires_hours = 24 * 7 if remember_me else 24  # 记住我：7天，否则24小时
            session_token = db_manager.create_session(user['id'], expires_hours)
            
            if session_token:
                # 创建响应
                response = make_response(jsonify({
                    'success': True,
                    'message': message,
                    'user': user
                }))
                
                # 设置cookie
                max_age = expires_hours * 3600 if remember_me else None
                response.set_cookie(
                    'session_token', 
                    session_token,
                    max_age=max_age,
                    httponly=True,
                    secure=False,  # 开发环境设为False，生产环境应设为True
                    samesite='Lax'
                )
                
                return response
            else:
                return jsonify({'error': 'Failed to create session'}), 500
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@app.route('/api/auth/logout', methods=['POST'])
@require_auth
def logout():
    """用户登出 - 改进版本，确保彻底清除session和cookie"""
    try:
        session_token = getattr(g, 'session_token', None)
        
        if session_token:
            # 从数据库删除session
            db_manager.delete_session(session_token)
        
        response = make_response(jsonify({
            'success': True,
            'message': '已成功登出'
        }))
        
        # 清除cookie - 确保使用所有可能的组合来彻底清除
        cookie_attributes = [
            {'path': '/'},
            {'path': '/', 'domain': 'localhost'},
            {'path': '/', 'domain': '127.0.0.1'},
            {'path': '/', 'domain': '.localhost'},
            {'path': '/', 'domain': '.127.0.0.1'},
            {}  # 默认属性
        ]
        
        for attrs in cookie_attributes:
            response.set_cookie(
                'session_token', 
                '', 
                expires=0,
                max_age=0,
                httponly=True,
                secure=False,  # 开发环境
                samesite='Lax',
                **attrs
            )
        
        # 添加额外的header来确保客户端清除缓存
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
        
    except Exception as e:
        return jsonify({'error': f'登出失败: {str(e)}'}), 500

@app.route('/api/auth/logout-all', methods=['POST'])
def logout_all():
    """清除所有会话（不需要认证，用于解决缓存问题）- 改进版本"""
    try:
        # 清除所有会话（包括过期的和有效的）
        conn = sqlite3.connect(db_manager.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM user_sessions')
        conn.commit()
        conn.close()
        
        response = make_response(jsonify({
            'success': True,
            'message': '已清除所有会话'
        }))
        
        # 更彻底的cookie清除
        cookie_attributes = [
            {'path': '/'},
            {'path': '/', 'domain': 'localhost'},
            {'path': '/', 'domain': '127.0.0.1'},
            {'path': '/', 'domain': '.localhost'},
            {'path': '/', 'domain': '.127.0.0.1'},
            {'path': '/', 'domain': None},
            {}  # 默认属性
        ]
        
        for attrs in cookie_attributes:
            response.set_cookie(
                'session_token', 
                '', 
                expires=0,
                max_age=0,
                httponly=True,
                secure=False,
                samesite='Lax',
                **attrs
            )
        
        # 强制清除客户端缓存
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, proxy-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.headers['Clear-Site-Data'] = '"cookies", "storage"'
        
        return response
        
    except Exception as e:
        return jsonify({'error': f'清除会话失败: {str(e)}'}), 500

@app.route('/api/auth/me', methods=['GET'])
@require_auth
def get_current_user_info():
    """获取当前用户信息"""
    try:
        user = get_current_user()
        detailed_user = db_manager.get_user_by_id(user['id'])
        
        if detailed_user:
            return jsonify({
                'success': True,
                'user': detailed_user
            })
        else:
            return jsonify({'error': '用户信息不存在'}), 404
            
    except Exception as e:
        return jsonify({'error': f'获取用户信息失败: {str(e)}'}), 500

@app.route('/api/auth/check', methods=['GET'])
@optional_auth
def check_auth_status():
    """检查认证状态"""
    user = get_current_user()
    
    return jsonify({
        'authenticated': user is not None,
        'user': user
    })

@app.route('/api/user/chat-history', methods=['GET'])
@require_auth
def get_user_chat_history():
    """获取用户聊天历史"""
    try:
        current_user = get_current_user()
        user_id = current_user['id']
        
        conversation_id = request.args.get('conversation_id', None)
        limit = int(request.args.get('limit', 50))
        
        # 如果指定了conversation_id，确保它是用户自己的会话
        if conversation_id and not conversation_id.startswith(f'user_{user_id}_'):
            conversation_id = f'user_{user_id}_{conversation_id}'
        
        chat_history = db_manager.get_user_chat_history(user_id, conversation_id, limit)
        
        return jsonify({
            'success': True,
            'chat_history': chat_history,
            'user_id': user_id,
            'total_count': len(chat_history)
        })
        
    except Exception as e:
        return jsonify({'error': f'获取聊天历史失败: {str(e)}'}), 500

@app.route('/api/user/chat-history', methods=['DELETE'])
@require_auth
def delete_user_chat_history():
    """删除用户聊天历史"""
    try:
        current_user = get_current_user()
        user_id = current_user['id']
        
        data = request.get_json() or {}
        conversation_id = data.get('conversation_id', None)
        
        # 如果指定了conversation_id，确保它是用户自己的会话
        if conversation_id and not conversation_id.startswith(f'user_{user_id}_'):
            conversation_id = f'user_{user_id}_{conversation_id}'
        
        success = db_manager.delete_user_chat_history(user_id, conversation_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': '聊天记录删除成功' if conversation_id else '所有聊天记录删除成功'
            })
        else:
            return jsonify({'error': '删除聊天记录失败，没有找到相关记录'}), 404
        
    except Exception as e:
        return jsonify({'error': f'删除聊天记录失败: {str(e)}'}), 500

@app.route('/api/user/statistics', methods=['GET'])
@require_auth
def get_user_statistics():
    """获取用户数据统计"""
    try:
        current_user = get_current_user()
        user_id = current_user['id']
        
        stats = db_manager.get_user_statistics(user_id)
        
        return jsonify({
            'success': True,
            'statistics': stats,
            'user': {
                'id': current_user['id'],
                'username': current_user['username'],
                'email': current_user['email']
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'获取统计信息失败: {str(e)}'}), 500

@app.route('/api/user/privacy-settings', methods=['GET'])
@require_auth
def get_user_privacy_settings():
    """获取用户隐私设置"""
    try:
        current_user = get_current_user()
        user_id = current_user['id']
        
        # 获取用户详细信息，包括隐私设置
        user_info = db_manager.get_user_by_id(user_id)
        
        if user_info:
            profile_data = user_info.get('profile_data', {})
            privacy_settings = profile_data.get('privacy_settings', {
                'data_isolation': True,  # 默认开启数据隔离
                'share_statistics': False,  # 默认不共享统计信息
                'allow_data_export': True,  # 默认允许数据导出
                'chat_history_retention_days': 365  # 默认保留1年
            })
            
            return jsonify({
                'success': True,
                'privacy_settings': privacy_settings,
                'user_id': user_id
            })
        else:
            return jsonify({'error': '用户信息不存在'}), 404
        
    except Exception as e:
        return jsonify({'error': f'获取隐私设置失败: {str(e)}'}), 500

@app.route('/api/user/privacy-settings', methods=['PUT'])
@require_auth
def update_user_privacy_settings():
    """更新用户隐私设置"""
    try:
        current_user = get_current_user()
        user_id = current_user['id']
        
        data = request.get_json()
        new_privacy_settings = data.get('privacy_settings', {})
        
        # 获取当前用户信息
        user_info = db_manager.get_user_by_id(user_id)
        if not user_info:
            return jsonify({'error': '用户信息不存在'}), 404
        
        # 更新隐私设置
        profile_data = user_info.get('profile_data', {})
        current_privacy = profile_data.get('privacy_settings', {})
        
        # 合并设置，只允许更新特定字段
        allowed_settings = ['data_isolation', 'share_statistics', 'allow_data_export', 'chat_history_retention_days']
        updated_privacy = current_privacy.copy()
        
        for key, value in new_privacy_settings.items():
            if key in allowed_settings:
                updated_privacy[key] = value
        
        profile_data['privacy_settings'] = updated_privacy
        
        # 保存到数据库
        conn = sqlite3.connect(db_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET profile_data = ?
            WHERE id = ?
        ''', (json.dumps(profile_data), user_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '隐私设置更新成功',
            'privacy_settings': updated_privacy
        })
        
    except Exception as e:
        return jsonify({'error': f'更新隐私设置失败: {str(e)}'}), 500

@app.route('/api/user/data-export', methods=['POST'])
@require_auth
def export_user_data():
    """导出用户数据"""
    try:
        current_user = get_current_user()
        user_id = current_user['id']
        
        # 检查用户是否允许数据导出
        user_info = db_manager.get_user_by_id(user_id)
        if user_info:
            profile_data = user_info.get('profile_data', {})
            privacy_settings = profile_data.get('privacy_settings', {})
            if not privacy_settings.get('allow_data_export', True):
                return jsonify({'error': '数据导出已被禁用'}), 403
        
        data = request.get_json() or {}
        include_types = data.get('include_types', ['chat', 'projects', 'notes', 'files'])
        
        export_data = {
            'user_info': {
                'id': user_id,
                'username': current_user['username'],
                'email': current_user['email'],
                'export_date': datetime.datetime.now().isoformat()
            },
            'data': {}
        }
        
        # 导出聊天记录
        if 'chat' in include_types:
            chat_history = db_manager.get_user_chat_history(user_id, limit=10000)
            export_data['data']['chat_history'] = chat_history
        
        # 导出项目
        if 'projects' in include_types:
            projects = db_manager.get_user_projects(user_id)
            export_data['data']['projects'] = projects
        
        # 导出笔记
        if 'notes' in include_types:
            notes = db_manager.get_user_notes(user_id)
            export_data['data']['notes'] = notes
        
        # 导出文件信息（不包含文件内容）
        if 'files' in include_types:
            files = db_manager.get_user_files(user_id)
            export_data['data']['files'] = files
        
        # 添加统计信息
        export_data['statistics'] = db_manager.get_user_statistics(user_id)
        
        return jsonify({
            'success': True,
            'export_data': export_data,
            'message': '数据导出成功'
        })
        
    except Exception as e:
        return jsonify({'error': f'数据导出失败: {str(e)}'}), 500

@app.route('/api/user/projects', methods=['GET'])
@require_auth
def get_user_projects_only():
    """获取用户自己创建的项目"""
    try:
        current_user = get_current_user()
        user_id = current_user['id']
        
        user_projects = db_manager.get_user_projects(user_id)
        
        projects = {}
        for project_id, project_info in user_projects.items():
            project_data = project_info['data']
            projects[project_id] = {
                'name': project_data['name'],
                'description': project_data['description'],
                'total_steps': len(project_data['steps']),
                'type': 'user_created',
                'created_at': project_info['created_at'],
                'updated_at': project_info['updated_at'],
                'steps': project_data['steps']
            }
        
        return jsonify({
            'success': True,
            'projects': projects
        })
        
    except Exception as e:
        return jsonify({'error': f'获取用户项目失败: {str(e)}'}), 500

@app.route('/api/project/<project_id>/step/<int:step_num>', methods=['GET'])
@optional_auth
def get_project_step(project_id, step_num):
    """Get specific project step information with enhanced user access control"""
    try:
        # Check template projects first (available to all)
        project = None
        project_owner = None
        
        if project_id in PROJECT_TEMPLATES:
            project = PROJECT_TEMPLATES[project_id]
            project_owner = 'template'  # Template projects are public
        else:
            # Check user-created projects (need authentication and ownership verification)
            current_user = get_current_user()
            if current_user:
                user_id = current_user['id']
                
                # 检查项目是否属于当前用户
                if db_manager.verify_resource_ownership(user_id, 'project', project_id):
                    user_projects = db_manager.get_user_projects(user_id)
                    if project_id in user_projects:
                        project = user_projects[project_id]['data']
                        project_owner = user_id
                else:
                    return jsonify({
                        'success': False, 
                        'error': 'Project not found or access denied. You can only access your own projects.'
                    }), 403
            
            # 兼容性：检查内存中的项目（临时措施）
            if not project and project_id in USER_CREATED_PROJECTS:
                project = USER_CREATED_PROJECTS[project_id]
                project_owner = 'legacy'  # 标记为遗留数据
        
        if not project:
            return jsonify({
                'success': False, 
                'error': 'Project not found or you do not have permission to access it'
            }), 404
        
        if step_num < 1 or step_num > len(project['steps']):
            return jsonify({'success': False, 'error': 'Step not found'}), 404
        
        step = project['steps'][step_num - 1]
        
        return jsonify({
            'success': True,
            'project_name': project['name'],
            'step': step,
            'total_steps': len(project['steps']),
            'project_owner': project_owner,
            'user_specific': project_owner != 'template'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error accessing project step: {str(e)}'}), 500

# ================================
# 用户项目管理相关路由
# ================================

@app.route('/api/user/project/<project_id>', methods=['DELETE'])
@require_auth
def delete_user_project(project_id):
    """删除用户项目"""
    try:
        current_user = get_current_user()
        user_id = current_user['id']
        
        # 检查项目是否属于当前用户
        user_projects = db_manager.get_user_projects(user_id)
        if project_id not in user_projects:
            return jsonify({'error': '项目不存在或您没有权限删除'}), 404
        
        # 从数据库删除项目
        success = db_manager.delete_user_project(user_id, project_id)
        
        if success:
            # 也从内存中删除（如果存在）
            if project_id in USER_CREATED_PROJECTS:
                del USER_CREATED_PROJECTS[project_id]
            
            return jsonify({
                'success': True,
                'message': '项目删除成功'
            })
        else:
            return jsonify({'error': '删除项目失败'}), 500
            
    except Exception as e:
        return jsonify({'error': f'删除项目失败: {str(e)}'}), 500

@app.route('/api/user/project/<project_id>', methods=['PUT'])
@require_auth
def update_user_project(project_id):
    """更新用户项目"""
    try:
        current_user = get_current_user()
        user_id = current_user['id']
        
        data = request.get_json()
        project_name = data.get('name', '').strip()
        project_description = data.get('description', '').strip()
        project_steps = data.get('steps', [])
        
        # 输入验证
        if not project_name:
            return jsonify({'error': '项目名称不能为空'}), 400
        
        # 检查项目是否属于当前用户
        user_projects = db_manager.get_user_projects(user_id)
        if project_id not in user_projects:
            return jsonify({'error': '项目不存在或您没有权限修改'}), 404
        
        # 构建更新后的项目数据
        updated_project_data = {
            'name': project_name,
            'description': project_description,
            'steps': project_steps if project_steps else user_projects[project_id]['data']['steps']
        }
        
        # 保存到数据库
        success = db_manager.save_user_project(user_id, project_id, updated_project_data)
        
        if success:
            # 也更新内存中的项目（如果存在）
            if project_id in USER_CREATED_PROJECTS:
                USER_CREATED_PROJECTS[project_id] = updated_project_data
            
            return jsonify({
                'success': True,
                'message': '项目更新成功',
                'project': updated_project_data
            })
        else:
            return jsonify({'error': '更新项目失败'}), 500
            
    except Exception as e:
        return jsonify({'error': f'更新项目失败: {str(e)}'}), 500

@app.route('/api/user/project/<project_id>/duplicate', methods=['POST'])
@require_auth
def duplicate_user_project(project_id):
    """复制用户项目"""
    try:
        current_user = get_current_user()
        user_id = current_user['id']
        
        # 获取原项目数据（可以是模板项目或用户项目）
        original_project = None
        
        # 首先检查是否是模板项目
        if project_id in PROJECT_TEMPLATES:
            original_project = PROJECT_TEMPLATES[project_id]
        else:
            # 检查用户项目
            user_projects = db_manager.get_user_projects(user_id)
            if project_id in user_projects:
                original_project = user_projects[project_id]['data']
            elif project_id in USER_CREATED_PROJECTS:
                original_project = USER_CREATED_PROJECTS[project_id]
        
        if not original_project:
            return jsonify({'error': '原项目不存在'}), 404
        
        # 创建新的项目ID
        import uuid
        new_project_id = f"user_{user_id}_copy_{str(uuid.uuid4())[:8]}"
        
        # 复制项目数据
        new_project_data = {
            'name': f"{original_project['name']} (副本)",
            'description': original_project['description'],
            'steps': original_project['steps'].copy()
        }
        
        # 保存新项目
        success = db_manager.save_user_project(user_id, new_project_id, new_project_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': '项目复制成功',
                'new_project_id': new_project_id,
                'project': new_project_data
            })
        else:
            return jsonify({'error': '复制项目失败'}), 500
            
    except Exception as e:
        return jsonify({'error': f'复制项目失败: {str(e)}'}), 500

@app.route('/api/user/project/<project_id>/share', methods=['POST'])
@require_auth
def share_user_project(project_id):
    """生成项目分享链接（简单实现）"""
    try:
        current_user = get_current_user()
        user_id = current_user['id']
        
        # 检查项目是否属于当前用户
        user_projects = db_manager.get_user_projects(user_id)
        if project_id not in user_projects:
            return jsonify({'error': '项目不存在或您没有权限分享'}), 404
        
        # 生成分享信息（简单实现，实际应用中可能需要更复杂的分享机制）
        project_data = user_projects[project_id]['data']
        share_info = {
            'project_name': project_data['name'],
            'project_description': project_data['description'],
            'total_steps': len(project_data['steps']),
            'created_by': current_user['username'],
            'share_url': f"/shared_project/{project_id}",  # 这个URL需要额外实现
            'share_code': project_id  # 可以用于分享代码功能
        }
        
        return jsonify({
            'success': True,
            'share_info': share_info,
            'message': '分享链接生成成功'
        })
            
    except Exception as e:
        return jsonify({'error': f'生成分享链接失败: {str(e)}'}), 500

# ================================
# 用户笔记相关路由
# ================================

@app.route('/api/notes', methods=['GET'])
@require_auth
def get_notes():
    """获取用户笔记列表"""
    try:
        current_user = get_current_user()
        user_id = current_user['id']
        
        notes = db_manager.get_user_notes(user_id)
        
        return jsonify({
            'success': True,
            'notes': notes
        })
        
    except Exception as e:
        return jsonify({'error': f'获取笔记失败: {str(e)}'}), 500

@app.route('/api/notes', methods=['POST'])
@require_auth
def create_note():
    """创建新笔记"""
    try:
        current_user = get_current_user()
        user_id = current_user['id']
        
        data = request.get_json()
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        topic = data.get('topic')
        
        if not title or not content:
            return jsonify({'error': '标题和内容不能为空'}), 400
        
        note_id = db_manager.save_user_note(
            user_id=user_id,
            title=title,
            content=content,
            topic=topic
        )
        
        if note_id:
            return jsonify({
                'success': True,
                'message': '笔记创建成功',
                'note_id': note_id
            })
        else:
            return jsonify({'error': '保存笔记失败'}), 500
            
    except Exception as e:
        return jsonify({'error': f'创建笔记失败: {str(e)}'}), 500

@app.route('/api/notes/<int:note_id>', methods=['PUT'])
@require_auth
def update_note(note_id):
    """更新笔记"""
    try:
        current_user = get_current_user()
        user_id = current_user['id']
        
        data = request.get_json()
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        topic = data.get('topic')
        
        if not title or not content:
            return jsonify({'error': '标题和内容不能为空'}), 400
        
        success = db_manager.save_user_note(
            user_id=user_id,
            title=title,
            content=content,
            topic=topic,
            note_id=note_id
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': '笔记更新成功'
            })
        else:
            return jsonify({'error': '更新笔记失败'}), 500
            
    except Exception as e:
        return jsonify({'error': f'更新笔记失败: {str(e)}'}), 500

@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
@require_auth
def delete_note(note_id):
    """删除笔记"""
    try:
        current_user = get_current_user()
        user_id = current_user['id']
        
        success = db_manager.delete_user_note(user_id, note_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': '笔记删除成功'
            })
        else:
            return jsonify({'error': '删除笔记失败'}), 404
            
    except Exception as e:
        return jsonify({'error': f'删除笔记失败: {str(e)}'}), 500

# ============ MISSING API ENDPOINTS FOR LEARNING CHATBOT ============

@app.route('/api/step_guidance', methods=['POST'])
@optional_auth
def get_step_guidance():
    """Get AI guidance for a specific project step"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        project_id = data.get('project_id')
        step_num = data.get('step_num')
        
        if not project_id or not step_num:
            return jsonify({'success': False, 'error': 'Missing project_id or step_num'}), 400
        
        # Get project and step info
        try:
            # Check if it's a template project
            if project_id in PROJECT_TEMPLATES:
                project = PROJECT_TEMPLATES[project_id]
                if step_num <= len(project['steps']):
                    step_info = project['steps'][step_num - 1]
                    project_name = project['name']
                else:
                    return jsonify({'success': False, 'error': 'Invalid step number'}), 400
            else:
                # Check user-created projects
                current_user = get_current_user()
                if current_user:
                    user_id = current_user['id']
                    user_projects = db_manager.get_user_projects(user_id)
                    
                    if project_id in user_projects:
                        project = user_projects[project_id]['data']
                        if step_num <= len(project['steps']):
                            step_info = project['steps'][step_num - 1]
                            project_name = project['name']
                        else:
                            return jsonify({'success': False, 'error': 'Invalid step number'}), 400
                    else:
                        # 兼容性：检查内存中的项目
                        if project_id in USER_CREATED_PROJECTS:
                            project = USER_CREATED_PROJECTS[project_id]
                            if step_num <= len(project['steps']):
                                step_info = project['steps'][step_num - 1]
                                project_name = project['name']
                            else:
                                return jsonify({'success': False, 'error': 'Invalid step number'}), 400
                        else:
                            return jsonify({'success': False, 'error': 'Project not found or access denied'}), 404
                else:
                    # User not authenticated, check memory-based projects only
                    if project_id in USER_CREATED_PROJECTS:
                        project = USER_CREATED_PROJECTS[project_id]
                        if step_num <= len(project['steps']):
                            step_info = project['steps'][step_num - 1]
                            project_name = project['name']
                        else:
                            return jsonify({'success': False, 'error': 'Invalid step number'}), 400
                    else:
                        return jsonify({'success': False, 'error': 'Project not found or access denied'}), 404
        except Exception as e:
            return jsonify({'success': False, 'error': f'Error accessing project: {str(e)}'}), 500
        
        # Generate guidance using AI if available
        if API_AVAILABLE and client:
            try:
                # Get step guidance prompt - Fix parameter structure
                prompt = get_step_explanation_prompt(
                    project_name=project_name,
                    step_info={
                        'step': step_num,
                        'title': step_info['title'],
                        'description': step_info['description'],
                        'concepts': step_info.get('concepts', [])
                    },
                    student_level="beginner"
                )
                
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1500,
                    temperature=0.7
                )
                
                guidance = response.choices[0].message.content
                formatted_guidance = format_response(guidance, "STEP_GUIDANCE")
                
                return jsonify({
                    'success': True,
                    'guidance': formatted_guidance,
                    'step_info': step_info,
                    'project_name': project_name
                })
                
            except Exception as e:
                print(f"AI guidance error: {str(e)}")
                # Fall back to basic guidance
                pass
        
        # Fallback guidance
        basic_guidance = f"""
        ## 🎯 Step {step_num}: {step_info['title']}
        
        ### 📋 What you'll learn:
        {step_info['description']}
        
        ### 🔑 Key concepts:
        {', '.join(step_info.get('concepts', []))}
        
        ### 💡 Getting Started:
        1. Review the step description carefully
        2. Think about how this relates to what you've learned
        3. Start with small pieces of code
        4. Test your code frequently
        5. Ask for help if you get stuck!
        
        Ready to dive in? I'm here to help guide you through this step!
        """
        
        formatted_guidance = format_response(basic_guidance, "STEP_GUIDANCE")
        
        return jsonify({
            'success': True,
            'guidance': formatted_guidance,
            'step_info': step_info,
            'project_name': project_name
        })
        
    except Exception as e:
        print(f"Step guidance error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to generate step guidance'}), 500


@app.route('/api/submit_code', methods=['POST'])
@optional_auth
def submit_code():
    """Submit code for review and feedback"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        code = data.get('code', '').strip()
        project_id = data.get('project_id')
        step_num = data.get('step_num')
        
        if not code:
            return jsonify({'success': False, 'error': 'No code provided'}), 400
        
        # Validate code and get suggestions for fixes
        issues, suggestions = validate_and_suggest_code_fixes(code)
        
        # Determine overall code status
        has_syntax_errors = any('Syntax error' in issue for issue in issues)
        has_undefined_vars = any('undefined' in issue.lower() for issue in issues)
        has_issues = len(issues) > 0
        
        # Generate code review using AI if available
        if API_AVAILABLE and client:
            try:
                # Enhanced prompt with clear status requirement
                context_info = ""
                if issues or suggestions:
                    context_info = f"\n\nCode Analysis Results:\nIssues found: {issues}\nSuggestions: {[s['description'] for s in suggestions]}"
                
                enhanced_prompt = f"""You are a Python programming tutor. Review the submitted code and provide feedback.

IMPORTANT: Start your response with a clear status indicator:
- If the code has no errors: "✅ **CODE STATUS: WORKING** - Your code looks good!"
- If the code has minor issues: "⚠️ **CODE STATUS: NEEDS MINOR FIXES** - Your code has small issues that can be easily fixed."
- If the code has major errors: "❌ **CODE STATUS: HAS ERRORS** - Your code has errors that need to be fixed."

Then provide detailed analysis following this structure:
1. Brief explanation of what the code does (or tries to do)
2. Issues found (if any)
3. Suggestions for improvement
4. Encouragement and next steps

Student Code:
{code}
{context_info}

Project Context: {f"Project: {project_id}, Step: {step_num}" if project_id else "General code review"}
"""
                
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": enhanced_prompt}],
                    max_tokens=1500,
                    temperature=0.7
                )
                
                review = response.choices[0].message.content
                formatted_review = format_response(review, "CODE_REVIEW")
                
                return jsonify({
                    'success': True,
                    'review': formatted_review,
                    'issues': issues,
                    'suggestions': suggestions,
                    'code_status': 'working' if not has_issues else ('minor_issues' if not has_syntax_errors else 'has_errors')
                })
                
            except Exception as e:
                print(f"AI code review error: {str(e)}")
                # Fall back to basic review
                pass
        
        # Enhanced basic code analysis with clear status
        # Determine status message
        if not has_issues:
            status_header = "✅ **CODE STATUS: WORKING** - Your code looks good!"
            status_emoji = "✅"
            status_class = "working"
        elif has_syntax_errors:
            status_header = "❌ **CODE STATUS: HAS ERRORS** - Your code has errors that need to be fixed."
            status_emoji = "❌"
            status_class = "has_errors"
        else:
            status_header = "⚠️ **CODE STATUS: NEEDS MINOR FIXES** - Your code has small issues that can be easily fixed."
            status_emoji = "⚠️"
            status_class = "minor_issues"
        
        basic_review_parts = [
            "## 🔍 Code Review",
            "",
            f"### {status_emoji} Code Status",
            status_header,
            "",
            "### 📝 Your Code:",
            "```python",
            code,
            "```"
        ]
        
        # Add code analysis section
        if not has_issues:
            basic_review_parts.extend([
                "",
                "### 🎉 Analysis:",
                "Great job! Your code appears to be syntactically correct and should run without errors.",
                "",
                "### ✅ What's working well:",
                "- No syntax errors detected",
                "- All variables appear to be properly defined",
                "- Code structure looks good"
            ])
        else:
            basic_review_parts.extend([
                "",
                "### 🔍 What I found:",
            ])
            
            if has_syntax_errors:
                basic_review_parts.append("**Syntax Errors Detected:** Your code has formatting or syntax issues that prevent it from running.")
            elif has_undefined_vars:
                basic_review_parts.append("**Variable Issues:** Some variables are used before being defined.")
            else:
                basic_review_parts.append("**Minor Issues:** Small problems that are easy to fix.")
        
        if issues:
            basic_review_parts.extend([
                "",
                "### ⚠️ Specific Issues Found:",
            ])
            for issue in issues:
                basic_review_parts.append(f"- {issue}")
        
        if suggestions:
            basic_review_parts.extend([
                "",
                "### 🔧 How to Fix:",
            ])
            for suggestion in suggestions:
                basic_review_parts.append(f"**{suggestion['description']}**")
                if 'fixed_code' in suggestion:
                    basic_review_parts.extend([
                        "",
                        "Fixed version:",
                        "```python",
                        suggestion['fixed_code'],
                        "```",
                        ""
                    ])
                elif 'example' in suggestion:
                    basic_review_parts.extend([
                        "",
                        "Example:",
                        "```python",
                        suggestion['example'],
                        "```",
                        ""
                    ])
        
        # Add encouragement and next steps
        if not has_issues:
            basic_review_parts.extend([
                "",
                "### 🚀 Next Steps:",
                "- Your code is ready to run! Try executing it to see the results.",
                "- Consider adding comments to explain what your code does.",
                "- Think about testing with different inputs.",
                "",
                "Excellent work! Keep coding! 🎉"
            ])
        elif has_syntax_errors:
            basic_review_parts.extend([
                "",
                "### 🚀 Next Steps:",
                "- Fix the syntax errors shown above",
                "- Check your indentation carefully",
                "- Make sure all parentheses and quotes are properly closed",
                "- Test your code again after making fixes",
                "",
                "Don't worry - syntax errors are common when learning! You're doing great! 💪"
            ])
        else:
            basic_review_parts.extend([
                "",
                "### 🚀 Next Steps:",
                "- Address the issues mentioned above",
                "- Make sure all variables are defined before use",
                "- Test your code with different inputs",
                "",
                "You're on the right track! Small fixes will make your code perfect! 🌟"
            ])
        
        basic_review = "\n".join(basic_review_parts)
        formatted_review = format_response(basic_review, "CODE_REVIEW")
        
        return jsonify({
            'success': True,
            'review': formatted_review,
            'issues': issues,
            'suggestions': suggestions,
            'code_status': status_class
        })
        
    except Exception as e:
        print(f"Code submission error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to review code'}), 500


@app.route('/api/hint_chat', methods=['POST'])
@optional_auth
def hint_chat():
    """Provide hints and help for learning"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        message = data.get('message', '').strip()
        error_context = data.get('error_context', '')
        student_progress = data.get('student_progress', '')
        response_type = data.get('response_type', 'direct')
        
        if not message:
            return jsonify({'success': False, 'error': 'No message provided'}), 400
        
        # Generate hint using AI if available
        if API_AVAILABLE and client:
            try:
                prompt = get_adaptive_hint_prompt(
                    difficulty_level="basic",  # Could be enhanced to determine actual level
                    error_context=error_context,
                    student_progress=student_progress
                )
                
                max_tokens = 2000 if response_type == 'detailed' else 800
                
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0.7
                )
                
                hint = response.choices[0].message.content
                formatted_hint = format_response(hint, "HINT")
                
                return jsonify({
                    'success': True,
                    'response': formatted_hint
                })
                
            except Exception as e:
                print(f"AI hint error: {str(e)}")
                # Fall back to basic hint
                pass
        
        # Basic hint fallback
        basic_hint = f"""
        ## 💡 Here's a hint for you!
        
        ### 🤔 Your question:
        {message}
        
        ### 💭 Think about this:
        - Break down the problem into smaller parts
        - What do you already know that might help?
        - Have you seen similar problems before?
        - Try writing out the steps in plain English first
        
        ### 🔍 Debugging tips:
        - Print out variables to see their values
        - Check for typos in variable names
        - Make sure indentation is correct
        - Read error messages carefully
        
        ### 🚀 Next steps:
        Try implementing one small piece at a time. You've got this! 💪
        """
        
        formatted_hint = format_response(basic_hint, "HINT")
        
        return jsonify({
            'success': True,
            'response': formatted_hint
        })
        
    except Exception as e:
        print(f"Hint chat error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to generate hint'}), 500


@app.route('/api/reflection_chat', methods=['POST'])
@optional_auth
def reflection_chat():
    """Handle reflection and metacognitive learning"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        message = data.get('message', '').strip()
        session_summary = data.get('session_summary', '')
        concepts_covered = data.get('concepts_covered', [])
        response_type = data.get('response_type', 'direct')
        
        if not message:
            return jsonify({'success': False, 'error': 'No message provided'}), 400
        
        # Generate reflection using AI if available
        if API_AVAILABLE and client:
            try:
                prompt = get_reflection_prompt_enhanced(
                    learning_session_summary=session_summary,
                    concepts_covered=concepts_covered
                )
                
                max_tokens = 2000 if response_type == 'detailed' else 800
                
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0.7
                )
                
                reflection = response.choices[0].message.content
                formatted_reflection = format_response(reflection, "REFLECTION")
                
                return jsonify({
                    'success': True,
                    'response': formatted_reflection
                })
                
            except Exception as e:
                print(f"AI reflection error: {str(e)}")
                # Fall back to basic reflection
                pass
        
        # Basic reflection fallback
        basic_reflection = f"""
        ## 🤔 Great reflection question!
        
        ### 💭 Your thought:
        {message}
        
        ### 🧠 Let's think deeper:
        - What patterns do you notice in your learning?
        - Which concepts are clicking for you?
        - What challenges are you facing?
        - How does this connect to what you already know?
        
        ### 📈 Learning progress:
        Reflection is a powerful tool for learning! By thinking about your thinking, you're developing metacognitive skills that will help you become a better programmer.
        
        ### 🎯 Keep growing:
        - Celebrate your successes
        - Learn from your mistakes
        - Ask questions when you're curious
        - Practice regularly
        
        What insights are you gaining about your learning journey? 🚀
        """
        
        formatted_reflection = format_response(basic_reflection, "REFLECTION")
        
        return jsonify({
            'success': True,
            'response': formatted_reflection
        })
        
    except Exception as e:
        print(f"Reflection chat error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to generate reflection'}), 500


# Additional helper endpoints that might be called
@app.route('/api/reflection_prompt', methods=['POST'])
@optional_auth
def get_reflection_prompt():
    """Generate a reflection prompt for the user"""
    try:
        data = request.get_json()
        session_summary = data.get('session_summary', 'Python learning session')
        concepts_covered = data.get('concepts_covered', [])
        
        reflection_prompts = [
            f"What was the most challenging concept you encountered in {session_summary}?",
            f"How do the concepts {', '.join(concepts_covered[:3])} relate to each other?",
            "What programming problem would you like to solve with what you've learned?",
            "What questions do you still have about today's topics?",
            "How has your understanding of Python grown through this session?"
        ]
        
        import random
        selected_prompt = random.choice(reflection_prompts)
        
        reflection_text = f"""
        ## 🤔 Time to Reflect
        
        Take a moment to think about your learning journey:
        
        ### 💭 Reflection Question:
        {selected_prompt}
        
        ### 🎯 Why reflect?
        Reflection helps you:
        - Consolidate your learning
        - Identify knowledge gaps
        - Make connections between concepts
        - Plan your next learning steps
        
        Share your thoughts below! 💡
        """
        
        return jsonify({
            'success': True,
            'reflection': reflection_text
        })
        
    except Exception as e:
        print(f"Reflection prompt error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to generate reflection prompt'}), 500


@app.route('/api/get_hint', methods=['POST'])
@optional_auth
def get_hint():
    """Generate a general hint for the current learning context"""
    try:
        data = request.get_json()
        error_context = data.get('error_context', 'Python learning')
        student_progress = data.get('student_progress', 'Beginning learner')
        
        general_hints = [
            "Remember to read error messages carefully - they often tell you exactly what's wrong!",
            "Try breaking your problem into smaller, manageable pieces.",
            "Use print() statements to debug and see what your variables contain.",
            "Check your indentation - Python is very particular about spacing!",
            "Don't forget to test your code with different inputs to make sure it works correctly.",
            "When stuck, try explaining your code out loud or to someone else - it often helps clarify your thinking!"
        ]
        
        import random
        selected_hint = random.choice(general_hints)
        
        hint_text = f"""
        ## 💡 Here's a helpful hint!
        
        ### 🎯 Tip:
        {selected_hint}
        
        ### 📝 Context:
        {error_context}
        
        ### 🚀 Keep going!
        Every programmer gets stuck sometimes. The key is to keep trying different approaches and learning from each attempt.
        
        You're doing great! 💪
        """
        
        return jsonify({
            'success': True,
            'hint': hint_text
        })
        
    except Exception as e:
        print(f"Get hint error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to generate hint'}), 500

def fix_code_indentation(code):
    """Fix common indentation errors in Python code"""
    lines = code.split('\n')
    fixed_lines = []
    
    # Track if we're in a code block that should be indented
    in_indented_block = False
    
    for i, line in enumerate(lines):
        # Skip empty lines
        if not line.strip():
            fixed_lines.append(line)
            continue
            
        stripped_line = line.strip()
        
        # Check if this line starts a new indented block
        if (stripped_line.endswith(':') and 
            any(stripped_line.startswith(keyword) for keyword in 
                ['if ', 'for ', 'while ', 'def ', 'class ', 'try:', 'except', 'else:', 'elif ', 'with '])):
            in_indented_block = True
            fixed_lines.append(line)
            continue
        
        # Check if this line ends an indented block
        if (in_indented_block and not line.startswith(' ') and not line.startswith('\t') and 
            stripped_line and not stripped_line.startswith('#')):
            in_indented_block = False
        
        # If we're not supposed to be in an indented block, fix wrong indentation
        if not in_indented_block and (line.startswith('    ') or line.startswith('\t')):
            # Check if previous line was a simple statement (not ending with :)
            if i > 0:
                prev_line = lines[i-1].strip()
                if (prev_line and not prev_line.endswith(':') and 
                    not prev_line.startswith('def ') and not prev_line.startswith('class ') and
                    not prev_line.startswith('if ') and not prev_line.startswith('for ') and
                    not prev_line.startswith('while ') and not prev_line.startswith('with ') and
                    not prev_line.startswith('try:') and not prev_line.startswith('except') and
                    not prev_line.startswith('else:') and not prev_line.startswith('elif ')):
                    
                    # This line should not be indented
                    fixed_lines.append(stripped_line)
                    continue
        
        # If we should be in an indented block but the line isn't indented, add indentation
        if (in_indented_block and not line.startswith(' ') and not line.startswith('\t') and 
            stripped_line and not stripped_line.startswith('#') and
            not any(stripped_line.startswith(keyword) for keyword in ['else:', 'elif ', 'except', 'finally:'])):
            fixed_lines.append('    ' + stripped_line)
            continue
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def validate_and_suggest_code_fixes(code):
    """Validate code and suggest fixes for common issues"""
    issues = []
    suggestions = []
    
    # Try to parse the code to find syntax errors
    try:
        ast.parse(code)
    except SyntaxError as e:
        issues.append(f"Syntax error on line {e.lineno}: {e.msg}")
        
        # Try to fix common indentation issues
        fixed_code = fix_code_indentation(code)
        try:
            ast.parse(fixed_code)
            suggestions.append({
                'type': 'indentation_fix',
                'description': 'Fixed indentation errors',
                'fixed_code': fixed_code
            })
        except SyntaxError:
            pass
    
    # Check for undefined variables
    lines = code.split('\n')
    defined_vars = set()
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        # Check for variable assignments
        if '=' in line and not line.endswith(':'):
            parts = line.split('=')
            if len(parts) == 2:
                var_name = parts[0].strip()
                if var_name.isidentifier():
                    defined_vars.add(var_name)
        
        # Check for undefined variables in print statements
        if line.startswith('print(') and line.endswith(')'):
            content = line[6:-1]  # Remove print( and )
            if content.isidentifier() and content not in defined_vars:
                issues.append(f"Line {line_num}: Variable '{content}' is used but not defined")
                suggestions.append({
                    'type': 'undefined_variable',
                    'description': f"Define variable '{content}' before using it",
                    'example': f"{content} = 'some_value'  # Define {content} first"
                })
    
    return issues, suggestions

# Vercel需要的app变量导出
# 移除本地运行的代码，因为Vercel不需要
# if __name__ == '__main__': 部分已被移除

# 确保应用可以被Vercel导入
application = app

@app.route('/api/rename/<int:file_id>', methods=['PUT'])
@require_auth
def rename_file(file_id):
    """重命名文件"""
    try:
        # 获取当前用户
        current_user = get_current_user()
        user_id = current_user['id']
        
        # 获取请求数据
        data = request.get_json()
        new_name = data.get('new_name', '').strip()
        
        if not new_name:
            return jsonify({'success': False, 'error': 'File name cannot be empty'}), 400
        
        # 验证文件名长度
        if len(new_name) > 255:
            return jsonify({'success': False, 'error': 'File name too long'}), 400
        
        # 获取用户文件列表
        user_files = db_manager.get_user_files(user_id)
        
        # 查找指定文件
        target_file = None
        for file_info in user_files:
            if file_info['id'] == file_id:
                target_file = file_info
                break
        
        if not target_file:
            return jsonify({'success': False, 'error': 'File not found or access denied'}), 404
        
        # 更新数据库中的original_filename
        conn = sqlite3.connect(db_manager.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE user_files SET original_filename = ? WHERE id = ? AND user_id = ?', 
                      (new_name, file_id, user_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'error': 'File not found or no changes made'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'File renamed to "{new_name}" successfully',
            'new_name': new_name
        })
        
    except Exception as e:
        error_msg = f'Rename failed: {str(e)}'
        print(f"Rename error: {error_msg}")
        return jsonify({'success': False, 'error': error_msg}), 500