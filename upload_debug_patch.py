"""
Enhanced Upload Endpoint with Detailed Error Logging
Replace the existing upload_file function with this version for debugging
"""

@app.route('/api/upload', methods=['POST'])
@require_auth
def upload_file():
    """Handle file upload - Enhanced with detailed error logging"""
    error_context = "Unknown"
    try:
        print("=" * 50)
        print("🔥 File upload request received")
        print("=" * 50)
        
        error_context = "Authentication"
        # 获取当前用户
        current_user = get_current_user()
        user_id = current_user['id']
        print(f"✅ User authenticated: ID={user_id}")
        
        error_context = "Request validation"
        # Check if the post request has the file part
        if 'file' not in request.files:
            error_msg = "No file part in request"
            print(f"❌ {error_msg}")
            print(f"Available form keys: {list(request.files.keys())}")
            print(f"Request content type: {request.content_type}")
            return jsonify({'success': False, 'error': 'No file selected'})
        
        file = request.files['file']
        print(f"✅ File found in request: {file.filename}")
        
        # If user does not select file, browser also submits an empty part without filename
        if file.filename == '':
            error_msg = "No file selected (empty filename)"
            print(f"❌ {error_msg}")
            return jsonify({'success': False, 'error': 'No file selected'})
        
        error_context = "File size validation"
        # Check file size
        content_length = request.content_length or 0
        print(f"📏 Content length: {content_length} bytes")
        if content_length > MAX_FILE_SIZE:
            error_msg = f"File too large: {content_length} bytes (max: {MAX_FILE_SIZE})"
            print(f"❌ {error_msg}")
            return jsonify({'success': False, 'error': f'File size exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit'})
        
        error_context = "File type validation"
        if file and allowed_file(file.filename):
            print(f"✅ File type allowed: {file.filename}")
            original_filename = secure_filename(file.filename)
            print(f"✅ Secured filename: {original_filename}")
            
            error_context = "MIME type detection"
            # 获取MIME类型
            import mimetypes
            mime_type, _ = mimetypes.guess_type(original_filename)
            print(f"📋 MIME type: {mime_type}")
            
            error_context = "Tag generation"
            # 生成标签
            tags = generate_file_tags(original_filename)
            print(f"🏷️  Generated tags: {tags}")
            
            error_context = "Google Drive service check"
            if drive_service:
                print("☁️  Using Google Drive storage")
                # 使用Google Drive存储
                try:
                    error_context = "File data reading"
                    # 读取文件数据到内存
                    file_data = file.read()
                    file_size = len(file_data)
                    print(f"📖 File data read: {file_size} bytes")
                    
                    error_context = "Google Drive upload"
                    # 上传到Google Drive
                    print("☁️  Uploading to Google Drive...")
                    drive_result = drive_service.upload_file_from_memory(
                        file_data=file_data,
                        original_filename=original_filename,
                        user_id=user_id,
                        mime_type=mime_type
                    )
                    print(f"✅ Google Drive upload successful: {drive_result}")
                    
                    error_context = "Database save (Google Drive)"
                    # 保存文件信息到数据库
                    print("💾 Saving file info to database...")
                    file_id = db_manager.save_user_file(
                        user_id=user_id,
                        filename=drive_result['name'],
                        original_filename=original_filename,
                        file_path=None,  # 不使用本地路径
                        file_size=file_size,
                        mime_type=mime_type,
                        tags=tags,
                        drive_file_id=drive_result['id'],
                        drive_folder_id=drive_result['drive_folder_id'],
                        storage_type='drive'
                    )
                    
                    if not file_id:
                        error_msg = "Failed to save file information to database"
                        print(f"❌ {error_msg}")
                        # 如果数据库保存失败，删除Google Drive上的文件
                        print("🗑️  Cleaning up Google Drive file...")
                        drive_service.delete_file(drive_result['id'])
                        return jsonify({'success': False, 'error': error_msg}), 500
                    
                    file_info = {
                        'id': file_id,
                        'filename': drive_result['name'],
                        'original_name': original_filename,
                        'size': file_size,
                        'upload_date': drive_result['created_time'],
                        'tags': tags,
                        'icon': get_file_icon(original_filename),
                        'mime_type': mime_type,
                        'drive_file_id': drive_result['id'],
                        'storage_type': 'drive'
                    }
                    
                    print(f"🎉 File uploaded to Google Drive successfully: {file_info}")
                    
                    return jsonify({
                        'success': True, 
                        'message': f'File "{original_filename}" uploaded to Google Drive successfully!',
                        'file': file_info
                    })
                    
                except Exception as e:
                    error_msg = f"Google Drive upload error: {str(e)}"
                    print(f"❌ {error_msg}")
                    print("📋 Google Drive error traceback:")
                    print(traceback.format_exc())
                    return jsonify({'success': False, 'error': f'Google Drive upload failed: {str(e)}'}), 500
            
            else:
                print("💾 Using local storage (Google Drive not available)")
                error_context = "Local storage setup"
                # 回退到本地存储
                # Generate unique filename with timestamp and user ID
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                name, ext = os.path.splitext(original_filename)
                unique_filename = f"user_{user_id}_{name}_{timestamp}{ext}"
                print(f"📝 Generated unique filename: {unique_filename}")
                
                # Create user-specific upload directory
                user_upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], f'user_{user_id}')
                print(f"📁 User upload directory: {user_upload_dir}")
                
                error_context = "Directory creation"
                if not os.path.exists(user_upload_dir):
                    print("📁 Creating user upload directory...")
                    os.makedirs(user_upload_dir)
                    print("✅ Directory created successfully")
                
                # Save file
                file_path = os.path.join(user_upload_dir, unique_filename)
                print(f"💾 Saving file to local storage: {file_path}")
                
                error_context = "File save"
                file.save(file_path)
                print("✅ File saved successfully")
                
                error_context = "File info retrieval"
                # Get file info
                file_size = os.path.getsize(file_path)
                upload_date = datetime.datetime.now().isoformat()
                print(f"📏 File size: {file_size} bytes")
                print(f"📅 Upload date: {upload_date}")
                
                error_context = "Database save (local)"
                # 保存文件信息到数据库
                print("💾 Saving file info to database...")
                file_id = db_manager.save_user_file(
                    user_id=user_id,
                    filename=unique_filename,
                    original_filename=original_filename,
                    file_path=file_path,
                    file_size=file_size,
                    mime_type=mime_type,
                    tags=tags,
                    storage_type='local'
                )
                
                if not file_id:
                    error_msg = "Failed to save file information to database"
                    print(f"❌ {error_msg}")
                    # 如果数据库保存失败，删除已上传的文件
                    try:
                        print("🗑️  Cleaning up uploaded file...")
                        os.remove(file_path)
                        print("✅ File cleanup successful")
                    except Exception as cleanup_error:
                        print(f"⚠️  File cleanup failed: {cleanup_error}")
                    return jsonify({'success': False, 'error': error_msg}), 500
                
                file_info = {
                    'id': file_id,
                    'filename': unique_filename,
                    'original_name': original_filename,
                    'size': file_size,
                    'upload_date': upload_date,
                    'tags': tags,
                    'icon': get_file_icon(original_filename),
                    'path': file_path,
                    'mime_type': mime_type,
                    'storage_type': 'local'
                }
                
                print(f"🎉 File uploaded to local storage successfully: {file_info}")
                
                return jsonify({
                    'success': True, 
                    'message': f'File "{original_filename}" uploaded successfully!',
                    'file': file_info
                })
        else:
            error_context = "File type rejection"
            allowed_exts = ', '.join(ALLOWED_EXTENSIONS)
            error_msg = f'Invalid file type. Allowed types: {allowed_exts}'
            print(f"❌ {error_msg} - File: {file.filename if file else 'None'}")
            return jsonify({'success': False, 'error': error_msg})
            
    except Exception as e:
        error_msg = f'Upload failed at {error_context}: {str(e)}'
        print("=" * 50)
        print(f"💥 UPLOAD ERROR: {error_msg}")
        print("=" * 50)
        print("📋 Full traceback:")
        print(traceback.format_exc())
        print("=" * 50)
        print("🔍 Debug info:")
        print(f"   Request method: {request.method}")
        print(f"   Content type: {request.content_type}")
        print(f"   Content length: {request.content_length}")
        print(f"   Form keys: {list(request.form.keys()) if request.form else 'None'}")
        print(f"   File keys: {list(request.files.keys()) if request.files else 'None'}")
        print(f"   Error context: {error_context}")
        print("=" * 50)
        
        return jsonify({'success': False, 'error': error_msg}), 500 