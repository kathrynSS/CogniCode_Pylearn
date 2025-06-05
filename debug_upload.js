// Debug Upload Functionality
// This script provides debugging capabilities for the file upload system

console.log('Debug Upload script loaded');

// Debug function to monitor upload events
function debugUpload() {
    console.log('=== Upload Debug Information ===');
    
    // Check if upload elements exist - FIXED IDs
    const fileUploadInput = document.getElementById('file-upload');
    const uploadButton = document.getElementById('upload-button');
    const selectedFileName = document.getElementById('selected-file-name');
    
    console.log('Upload Elements Status:', {
        fileUploadInput: fileUploadInput ? 'Found' : 'Missing',
        uploadButton: uploadButton ? 'Found' : 'Missing',
        selectedFileName: selectedFileName ? 'Found' : 'Missing'
    });
    
    // Monitor file selection
    if (fileUploadInput) {
        fileUploadInput.addEventListener('change', function(e) {
            console.log('File selected:', {
                fileName: e.target.files[0]?.name,
                fileSize: e.target.files[0]?.size,
                fileType: e.target.files[0]?.type
            });
        });
    }
    
    // Monitor upload button clicks
    if (uploadButton) {
        uploadButton.addEventListener('click', function(e) {
            console.log('Upload button clicked');
            console.log('Current file input value:', fileUploadInput?.value);
        });
    }
}

// Initialize debug functionality when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', debugUpload);
} else {
    debugUpload();
}

// Global debug functions for manual testing
window.debugUploadStatus = function() {
    debugUpload();
};

window.testUploadEndpoint = async function() {
    console.log('Testing upload endpoint...');
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ test: true })
        });
        console.log('Upload endpoint response:', response.status, response.statusText);
        const data = await response.json();
        console.log('Upload endpoint data:', data);
    } catch (error) {
        console.error('Upload endpoint test failed:', error);
    }
};

console.log('Debug upload functions available: debugUploadStatus(), testUploadEndpoint()'); 