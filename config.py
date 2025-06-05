import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    # Google Drive API配置
    GOOGLE_DRIVE_API_KEY = os.getenv('GOOGLE_DRIVE_API_KEY', 'd9c4291725fb8dd81de139b2d6d2b3883babfb8c')
    GOOGLE_DRIVE_CREDENTIALS_PATH = os.getenv('GOOGLE_DRIVE_CREDENTIALS_PATH', 'google_drive_credentials.json')
    
    # 文件上传配置
    UPLOAD_FOLDER = 'Resources'
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
    
    # Google Drive服务配置
    GOOGLE_DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive.file']
    GOOGLE_DRIVE_ROOT_FOLDER = 'Resources'
    
    @staticmethod
    def init_app(app):
        # 确保上传文件夹存在
        if not os.path.exists(Config.UPLOAD_FOLDER):
            os.makedirs(Config.UPLOAD_FOLDER)
            
        # 设置文件上传配置
        app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
        app.config['MAX_CONTENT_LENGTH'] = Config.MAX_FILE_SIZE 