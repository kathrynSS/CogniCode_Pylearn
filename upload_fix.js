// Upload Fix Script - Ensures file upload functionality works correctly
console.log('Upload Fix Script Loading...');

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Upload Fix: DOM Content Loaded');
    
    // Wait a bit more to ensure all other scripts have run
    setTimeout(function() {
        console.log('Upload Fix: Initializing...');
        
        // Get elements
        const fileInput = document.getElementById('file-upload');
        const uploadButton = document.getElementById('upload-button');
        const selectedFileName = document.getElementById('selected-file-name');
        
        console.log('Upload Fix: Elements found:', {
            fileInput: !!fileInput,
            uploadButton: !!uploadButton,
            selectedFileName: !!selectedFileName
        });
        
        if (!fileInput || !uploadButton || !selectedFileName) {
            console.error('Upload Fix: Required elements not found!');
            return;
        }
        
        // Clear any existing event listeners by cloning elements
        const newFileInput = fileInput.cloneNode(true);
        const newUploadButton = uploadButton.cloneNode(true);
        
        fileInput.parentNode.replaceChild(newFileInput, fileInput);
        uploadButton.parentNode.replaceChild(newUploadButton, uploadButton);
        
        console.log('Upload Fix: Elements cloned and replaced');
        
        // Add fresh event listeners
        newFileInput.addEventListener('change', function(e) {
            console.log('Upload Fix: File input changed');
            const file = e.target.files[0];
            
            if (file) {
                console.log('Upload Fix: File selected:', {
                    name: file.name,
                    size: file.size,
                    type: file.type
                });
                
                // Update UI
                selectedFileName.textContent = file.name;
                selectedFileName.style.color = '#2c3e50';
                selectedFileName.style.fontWeight = 'bold';
                
                // Check file size (16MB limit)
                const maxSize = 16 * 1024 * 1024;
                if (file.size > maxSize) {
                    alert('File too large! Please select a file smaller than 16MB.');
                    newFileInput.value = '';
                    selectedFileName.textContent = 'No file selected';
                    selectedFileName.style.color = '#6c757d';
                    selectedFileName.style.fontWeight = 'normal';
                    newUploadButton.disabled = true;
                    newUploadButton.classList.remove('active');
                    return;
                }
                
                // Check file type
                const allowedTypes = ['.pdf', '.doc', '.docx', '.txt'];
                const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
                if (!allowedTypes.includes(fileExtension)) {
                    alert('Unsupported file type! Please select a PDF, Word document, or text file.');
                    newFileInput.value = '';
                    selectedFileName.textContent = 'No file selected';
                    selectedFileName.style.color = '#6c757d';
                    selectedFileName.style.fontWeight = 'normal';
                    newUploadButton.disabled = true;
                    newUploadButton.classList.remove('active');
                    return;
                }
                
                // Enable upload button with visual feedback
                newUploadButton.disabled = false;
                newUploadButton.classList.add('active');
                newUploadButton.style.backgroundColor = '#2196F3 !important';
                newUploadButton.style.color = 'white !important';
                newUploadButton.style.opacity = '1 !important';
                newUploadButton.style.cursor = 'pointer !important';
                newUploadButton.style.pointerEvents = 'auto !important';
                
                // Add visual indicator
                newUploadButton.innerHTML = '<i class="fas fa-upload"></i> Upload (Click to start upload)';
                
                console.log('Upload Fix: Upload button enabled');
                
                // Show notification
                // if (window.showNotification) {
                //     showNotification(`File selected: ${file.name}, click "Upload" button to start upload`, 3000);
                // }
                
            } else {
                console.log('Upload Fix: No file selected');
                selectedFileName.textContent = 'No file selected';
                selectedFileName.style.color = '#6c757d';
                selectedFileName.style.fontWeight = 'normal';
                newUploadButton.disabled = true;
                newUploadButton.classList.remove('active');
                newUploadButton.innerHTML = '<i class="fas fa-upload"></i> Upload';
                newUploadButton.style.backgroundColor = '';
                newUploadButton.style.color = '';
                newUploadButton.style.opacity = '';
                newUploadButton.style.cursor = '';
                newUploadButton.style.pointerEvents = '';
            }
        });
        
        // Upload button click handler
        newUploadButton.addEventListener('click', function(e) {
            console.log('Upload Fix: Upload button clicked!');
            e.preventDefault();
            e.stopPropagation();
            
            if (this.disabled) {
                console.log('Upload Fix: Button is disabled, ignoring click');
                return;
            }
            
            const file = newFileInput.files[0];
            if (!file) {
                alert('Please select a file first');
                console.log('Upload Fix: No file selected');
                return;
            }
            
            console.log('Upload Fix: Starting upload for file:', file.name);
            
            // Show loading state
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';
            this.disabled = true;
            this.style.backgroundColor = '#6c757d';
            
            // Create form data
            const formData = new FormData();
            formData.append('file', file);
            
            console.log('Upload Fix: Sending upload request...');
            
            // Upload file
            fetch('/api/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                console.log('Upload Fix: Response status:', response.status);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Upload Fix: Response data:', data);
                if (data.success) {
                    alert(`File uploaded successfully!\nFile name: ${data.file.original_name}\nSize: ${(data.file.size / 1024).toFixed(2)} KB`);
                    
                    // Reset form
                    newFileInput.value = '';
                    selectedFileName.textContent = 'No file selected';
                    selectedFileName.style.color = '#6c757d';
                    selectedFileName.style.fontWeight = 'normal';
                    this.innerHTML = originalText;
                    this.disabled = true;
                    this.classList.remove('active');
                    this.style.backgroundColor = '';
                    this.style.color = '';
                    this.style.opacity = '';
                    this.style.cursor = '';
                    this.style.pointerEvents = '';
                    
                    // Reload file list
                    console.log('Upload Fix: Reloading file list...');
                    if (window.loadFileList) {
                        loadFileList();
                    }
                    
                    // Show success notification
                    // if (window.showNotification) {
                    //     showNotification(`File "${data.file.original_name}" uploaded successfully!`, 3000);
                    // }
                } else {
                    console.error('Upload Fix: Upload failed:', data.error);
                    alert('Upload failed: ' + (data.error || 'Unknown error'));
                    this.innerHTML = originalText;
                    this.disabled = false;
                    this.style.backgroundColor = '#2196F3';
                }
            })
            .catch(error => {
                console.error('Upload Fix: Upload error:', error);
                alert('Upload error: ' + error.message);
                this.innerHTML = originalText;
                this.disabled = false;
                this.style.backgroundColor = '#2196F3';
            });
        });
        
        console.log('Upload Fix: Event listeners attached successfully');
        
    }, 1000); // Wait 1 second to ensure all other scripts have run
});

console.log('Upload Fix Script Loaded'); 