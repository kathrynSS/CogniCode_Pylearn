import os
import io
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload, MediaIoBaseUpload
from googleapiclient.errors import HttpError
import mimetypes
from datetime import datetime

class GoogleDriveService:
    def __init__(self, credentials_path=None, credentials_json=None, resources_folder_id=None):
        """
        初始化Google Drive服务
        
        Args:
            credentials_path: 服务账号JSON文件路径
            credentials_json: 服务账号JSON字符串（用于环境变量）
            resources_folder_id: 指定的Resources文件夹ID（可选）
        """
        self.SCOPES = ['https://www.googleapis.com/auth/drive']
        self.service = None
        # 使用指定的文件夹ID，如果没有提供则自动创建
        self.specified_folder_id = resources_folder_id or "1UbGiexxrOamAhGe8zQU-m4Kqyk9j99-2"
        self.resources_folder_id = None
        
        try:
            # 优先使用环境变量中的凭据
            if credentials_json:
                credentials_info = json.loads(credentials_json)
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_info, scopes=self.SCOPES
                )
            elif credentials_path and os.path.exists(credentials_path):
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_path, scopes=self.SCOPES
                )
            else:
                raise ValueError("No valid credentials provided")
                
            self.service = build('drive', 'v3', credentials=credentials)
            self._ensure_resources_folder()
            print("✅ Google Drive service initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize Google Drive service: {str(e)}")
            raise
    
    def _ensure_resources_folder(self):
        """确保Resources文件夹存在，优先使用指定的文件夹ID"""
        try:
            # 如果指定了文件夹ID，先尝试验证其存在性
            if self.specified_folder_id:
                try:
                    folder_info = self.service.files().get(
                        fileId=self.specified_folder_id,
                        fields='id,name,mimeType'
                    ).execute()
                    
                    if folder_info.get('mimeType') == 'application/vnd.google-apps.folder':
                        self.resources_folder_id = self.specified_folder_id
                        print(f"✅ Using specified Resources folder: {self.resources_folder_id}")
                        print(f"📁 Folder name: {folder_info.get('name', 'Unknown')}")
                        return
                    else:
                        print(f"⚠️  Specified ID is not a folder, falling back to search/create")
                        
                except HttpError as e:
                    if e.resp.status == 404:
                        print(f"⚠️  Specified folder ID not found or no access: {self.specified_folder_id}")
                        print("🔄 Falling back to search/create Resources folder")
                    else:
                        print(f"⚠️  Error accessing specified folder: {str(e)}")
                        print("🔄 Falling back to search/create Resources folder")
            
            # 搜索名为"Resources"的文件夹
            query = "name='Resources' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(q=query, spaces='drive').execute()
            items = results.get('files', [])
            
            if items:
                self.resources_folder_id = items[0]['id']
                print(f"📁 Found existing Resources folder: {self.resources_folder_id}")
            else:
                # 创建Resources文件夹
                folder_metadata = {
                    'name': 'Resources',
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = self.service.files().create(body=folder_metadata, fields='id').execute()
                self.resources_folder_id = folder.get('id')
                print(f"📁 Created new Resources folder: {self.resources_folder_id}")
                
        except HttpError as e:
            print(f"❌ Error managing Resources folder: {str(e)}")
            raise
    
    def _ensure_user_folder(self, user_id):
        """确保用户文件夹存在"""
        try:
            folder_name = f"user_{user_id}"
            
            # 在Resources文件夹中搜索用户文件夹
            query = f"name='{folder_name}' and parents in '{self.resources_folder_id}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(q=query, spaces='drive').execute()
            items = results.get('files', [])
            
            if items:
                return items[0]['id']
            else:
                # 创建用户文件夹
                folder_metadata = {
                    'name': folder_name,
                    'parents': [self.resources_folder_id],
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = self.service.files().create(body=folder_metadata, fields='id').execute()
                user_folder_id = folder.get('id')
                print(f"📁 Created user folder for user_{user_id}: {user_folder_id}")
                return user_folder_id
                
        except HttpError as e:
            print(f"❌ Error managing user folder: {str(e)}")
            raise
    
    def upload_file(self, file_path, original_filename, user_id, mime_type=None):
        """
        上传文件到Google Drive
        
        Args:
            file_path: 本地文件路径
            original_filename: 原始文件名
            user_id: 用户ID
            mime_type: 文件MIME类型
            
        Returns:
            dict: 包含文件信息的字典
        """
        try:
            # 确保用户文件夹存在
            user_folder_id = self._ensure_user_folder(user_id)
            
            # 生成唯一文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name, ext = os.path.splitext(original_filename)
            unique_filename = f"user_{user_id}_{name}_{timestamp}{ext}"
            
            # 确定MIME类型
            if not mime_type:
                mime_type, _ = mimetypes.guess_type(original_filename)
                if not mime_type:
                    mime_type = 'application/octet-stream'
            
            # 准备文件元数据
            file_metadata = {
                'name': unique_filename,
                'parents': [user_folder_id],
                'description': f'Uploaded by user {user_id} on {datetime.now().isoformat()}'
            }
            
            # 上传文件
            media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,size,mimeType,createdTime,webViewLink'
            ).execute()
            
            print(f"✅ File uploaded successfully: {file.get('name')} (ID: {file.get('id')})")
            
            return {
                'id': file.get('id'),
                'name': unique_filename,
                'original_name': original_filename,
                'size': int(file.get('size', 0)),
                'mime_type': file.get('mimeType'),
                'created_time': file.get('createdTime'),
                'web_view_link': file.get('webViewLink'),
                'drive_folder_id': user_folder_id
            }
            
        except HttpError as e:
            print(f"❌ Error uploading file: {str(e)}")
            raise
        except Exception as e:
            print(f"❌ Unexpected error uploading file: {str(e)}")
            raise
    
    def upload_file_from_memory(self, file_data, original_filename, user_id, mime_type=None):
        """
        从内存中的文件数据上传到Google Drive
        
        Args:
            file_data: 文件数据（bytes）
            original_filename: 原始文件名
            user_id: 用户ID
            mime_type: 文件MIME类型
            
        Returns:
            dict: 包含文件信息的字典
        """
        try:
            # 确保用户文件夹存在
            user_folder_id = self._ensure_user_folder(user_id)
            
            # 生成唯一文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name, ext = os.path.splitext(original_filename)
            unique_filename = f"user_{user_id}_{name}_{timestamp}{ext}"
            
            # 确定MIME类型
            if not mime_type:
                mime_type, _ = mimetypes.guess_type(original_filename)
                if not mime_type:
                    mime_type = 'application/octet-stream'
            
            # 准备文件元数据
            file_metadata = {
                'name': unique_filename,
                'parents': [user_folder_id],
                'description': f'Uploaded by user {user_id} on {datetime.now().isoformat()}'
            }
            
            # 创建内存文件对象
            file_io = io.BytesIO(file_data)
            
            # 上传文件
            media = MediaIoBaseUpload(file_io, mimetype=mime_type, resumable=True)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,size,mimeType,createdTime,webViewLink'
            ).execute()
            
            print(f"✅ File uploaded from memory: {file.get('name')} (ID: {file.get('id')})")
            
            return {
                'id': file.get('id'),
                'name': unique_filename,
                'original_name': original_filename,
                'size': int(file.get('size', 0)),
                'mime_type': file.get('mimeType'),
                'created_time': file.get('createdTime'),
                'web_view_link': file.get('webViewLink'),
                'drive_folder_id': user_folder_id
            }
            
        except HttpError as e:
            print(f"❌ Error uploading file from memory: {str(e)}")
            raise
        except Exception as e:
            print(f"❌ Unexpected error uploading file from memory: {str(e)}")
            raise
    
    def download_file(self, file_id):
        """
        从Google Drive下载文件
        
        Args:
            file_id: Google Drive文件ID
            
        Returns:
            bytes: 文件数据
        """
        try:
            request = self.service.files().get_media(fileId=file_id)
            file_io = io.BytesIO()
            downloader = MediaIoBaseDownload(file_io, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                
            file_data = file_io.getvalue()
            print(f"✅ File downloaded successfully: {file_id}")
            return file_data
            
        except HttpError as e:
            print(f"❌ Error downloading file: {str(e)}")
            raise
        except Exception as e:
            print(f"❌ Unexpected error downloading file: {str(e)}")
            raise
    
    def delete_file(self, file_id):
        """
        从Google Drive删除文件
        
        Args:
            file_id: Google Drive文件ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            self.service.files().delete(fileId=file_id).execute()
            print(f"✅ File deleted successfully: {file_id}")
            return True
            
        except HttpError as e:
            print(f"❌ Error deleting file: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error deleting file: {str(e)}")
            return False
    
    def get_file_info(self, file_id):
        """
        获取文件信息
        
        Args:
            file_id: Google Drive文件ID
            
        Returns:
            dict: 文件信息
        """
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='id,name,size,mimeType,createdTime,modifiedTime,webViewLink'
            ).execute()
            
            return {
                'id': file.get('id'),
                'name': file.get('name'),
                'size': int(file.get('size', 0)),
                'mime_type': file.get('mimeType'),
                'created_time': file.get('createdTime'),
                'modified_time': file.get('modifiedTime'),
                'web_view_link': file.get('webViewLink')
            }
            
        except HttpError as e:
            print(f"❌ Error getting file info: {str(e)}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error getting file info: {str(e)}")
            return None
    
    def list_user_files(self, user_id):
        """
        列出用户的所有文件
        
        Args:
            user_id: 用户ID
            
        Returns:
            list: 文件列表
        """
        try:
            # 获取用户文件夹ID
            user_folder_id = self._ensure_user_folder(user_id)
            
            # 查询用户文件夹中的所有文件
            query = f"parents in '{user_folder_id}' and trashed=false"
            results = self.service.files().list(
                q=query,
                fields='files(id,name,size,mimeType,createdTime,modifiedTime,webViewLink)'
            ).execute()
            
            files = []
            for item in results.get('files', []):
                files.append({
                    'id': item.get('id'),
                    'name': item.get('name'),
                    'size': int(item.get('size', 0)),
                    'mime_type': item.get('mimeType'),
                    'created_time': item.get('createdTime'),
                    'modified_time': item.get('modifiedTime'),
                    'web_view_link': item.get('webViewLink')
                })
            
            return files
            
        except HttpError as e:
            print(f"❌ Error listing user files: {str(e)}")
            return []
        except Exception as e:
            print(f"❌ Unexpected error listing user files: {str(e)}")
            return [] 