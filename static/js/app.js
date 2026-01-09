/**
 * Word to PDF Converter - Frontend Application
 * 
 * Handles file upload, drag & drop, conversion progress, and download.
 */

class WordToPdfConverter {
    constructor() {
        // DOM Elements
        this.uploadState = document.getElementById('upload-state');
        this.convertingState = document.getElementById('converting-state');
        this.completeState = document.getElementById('complete-state');
        this.errorState = document.getElementById('error-state');
        
        this.uploadZone = document.getElementById('upload-zone');
        this.fileInput = document.getElementById('file-input');
        this.browseBtn = document.getElementById('browse-btn');
        
        this.fileNameDisplay = document.getElementById('file-name-display');
        this.progressFill = document.getElementById('progress-fill');
        this.progressText = document.getElementById('progress-text');
        
        this.convertedFileName = document.getElementById('converted-file-name');
        this.conversionTime = document.getElementById('conversion-time');
        this.downloadBtn = document.getElementById('download-btn');
        this.convertAnotherBtn = document.getElementById('convert-another-btn');
        
        this.errorMessage = document.getElementById('error-message');
        this.tryAgainBtn = document.getElementById('try-again-btn');
        
        // State
        this.currentFile = null;
        
        // Initialize
        this.init();
    }
    
    init() {
        this.bindEvents();
    }
    
    bindEvents() {
        // Browse button click
        this.browseBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.fileInput.click();
        });
        
        // Upload zone click
        this.uploadZone.addEventListener('click', () => {
            this.fileInput.click();
        });
        
        // File input change
        this.fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFile(e.target.files[0]);
            }
        });
        
        // Drag and drop events
        this.uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.uploadZone.classList.add('dragover');
        });
        
        this.uploadZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.uploadZone.classList.remove('dragover');
        });
        
        this.uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.uploadZone.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFile(files[0]);
            }
        });
        
        // Prevent default drag behavior on document
        document.addEventListener('dragover', (e) => e.preventDefault());
        document.addEventListener('drop', (e) => e.preventDefault());
        
        // Convert another button
        this.convertAnotherBtn.addEventListener('click', () => {
            this.reset();
        });
        
        // Try again button
        this.tryAgainBtn.addEventListener('click', () => {
            this.reset();
        });
    }
    
    handleFile(file) {
        // Validate file type
        const validTypes = [
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword'
        ];
        const validExtensions = ['.docx', '.doc'];
        
        const extension = '.' + file.name.split('.').pop().toLowerCase();
        
        if (!validTypes.includes(file.type) && !validExtensions.includes(extension)) {
            this.showError('Invalid file type. Please upload a .docx or .doc file.');
            return;
        }
        
        // Check file size (100 MB limit)
        const maxSize = 100 * 1024 * 1024;
        if (file.size > maxSize) {
            this.showError('File too large. Maximum size is 100 MB.');
            return;
        }
        
        this.currentFile = file;
        this.uploadFile(file);
    }
    
    async uploadFile(file) {
        // Show converting state
        this.showState('converting');
        this.fileNameDisplay.textContent = file.name;
        this.updateProgress(0, 'Uploading...');
        
        // Create form data
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            // Simulate initial progress
            this.updateProgress(20, 'Uploading file...');
            
            // Upload and convert
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            this.updateProgress(60, 'Converting...');
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Conversion failed');
            }
            
            const result = await response.json();
            
            this.updateProgress(100, 'Complete!');
            
            // Small delay before showing complete state
            setTimeout(() => {
                this.showComplete(result);
            }, 500);
            
        } catch (error) {
            console.error('Conversion error:', error);
            this.showError(error.message || 'An error occurred during conversion.');
        }
    }
    
    updateProgress(percent, text) {
        this.progressFill.style.width = `${percent}%`;
        this.progressText.textContent = text;
    }
    
    showComplete(result) {
        this.showState('complete');
        this.convertedFileName.textContent = result.filename;
        this.conversionTime.textContent = `Converted in ${result.elapsed_time} seconds`;
        
        // Set download link
        this.downloadBtn.href = result.download_url;
        this.downloadBtn.download = result.filename;
    }
    
    showError(message) {
        this.showState('error');
        this.errorMessage.textContent = message;
    }
    
    showState(state) {
        // Hide all states
        this.uploadState.classList.remove('active');
        this.convertingState.classList.remove('active');
        this.completeState.classList.remove('active');
        this.errorState.classList.remove('active');
        
        // Show requested state
        switch (state) {
            case 'upload':
                this.uploadState.classList.add('active');
                break;
            case 'converting':
                this.convertingState.classList.add('active');
                break;
            case 'complete':
                this.completeState.classList.add('active');
                break;
            case 'error':
                this.errorState.classList.add('active');
                break;
        }
    }
    
    reset() {
        this.currentFile = null;
        this.fileInput.value = '';
        this.updateProgress(0, 'Processing...');
        this.showState('upload');
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.converter = new WordToPdfConverter();
});
