import { initSvgIcons } from './global.js';
import { EXPIRY_TIMES, BURN_TIMES, FONT_SIZES } from './constants.js';
import { $ } from './utils/dom.js';
import { setupSlider, updateCharCounter, toggleVisibility } from './utils/ui.js';

class MessageCreator {
    constructor() {
        initSvgIcons();
        
        this.messageInput = $('#messageContent');
        this.dropZone = $('#dropZone');
        this.fileInput = $('#fileInput');
        this.imagePreviews = $('#imagePreviews');
        this.createBtn = $('#createBtn');
        
        this.images = new Set();
        this.MAX_IMAGES = 1;
        this.MAX_IMAGE_SIZE = 3 * 1024 * 1024; // 3MB
        this.ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/gif'];
        this.MAX_MESSAGE_LENGTH = 2000;
        
        this.customTokenBtn = $('#customTokenBtn');
        this.tokenInputContainer = $('#tokenInputContainer');
        this.customToken = $('#customToken');
        this.tokenCounter = $('#tokenCounter');
        this.tokenHint = $('#tokenHint');
        this.hintCounter = $('#hintCounter');
        
        this.MIN_TOKEN_LENGTH = 6;
        this.MAX_TOKEN_LENGTH = 70;
        
        // Characters chosen for readability (no I,l,0,O etc.)
        this.TOKEN_CHARS = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789';
        this.TOKEN_LENGTH = 8;
        
        this.setupEventListeners();
        this.setupCharCounter();
        this.setupExpirySlider();
        this.setupBurnTimeSlider();
        this.setupTokenInput();
        this.setupTokenGenerator();
        this.setupFontSizeControls();
    }
    
    setupEventListeners() {
        // Prevent browser from opening dropped files
        document.addEventListener('dragover', (e) => e.preventDefault());
        document.addEventListener('drop', (e) => e.preventDefault());

        // Drag and drop handlers
        this.dropZone.addEventListener('click', () => this.fileInput.click());
        this.dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.dropZone.classList.add('dragover');
        });
        this.dropZone.addEventListener('dragleave', () => {
            this.dropZone.classList.remove('dragover');
        });
        this.dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.dropZone.classList.remove('dragover');
            this.handleFiles(e.dataTransfer.files);
        });
        
        // File input handler
        this.fileInput.addEventListener('change', (e) => {
            this.handleFiles(e.target.files);
        });
        
        // Create button handler
        this.createBtn.addEventListener('click', () => this.createMessage());
    }
    
    setupCharCounter() {
        const counter = document.createElement('div');
        counter.className = 'char-counter';
        counter.style.display = 'none';
        this.messageInput.parentNode.insertBefore(counter, this.messageInput.nextSibling);
        
        this.messageInput.addEventListener('input', () => {
            updateCharCounter(this.messageInput, counter, this.MAX_MESSAGE_LENGTH, {
                warningThreshold: 100,
                onValid: () => {
                    this.messageInput.classList.remove('error', 'near-limit');
                    this.createBtn.disabled = false;
                },
                onInvalid: () => {
                    this.messageInput.classList.add('error');
                    this.messageInput.classList.remove('near-limit');
                    this.createBtn.disabled = true;
                }
            });
        });
    }
    
    setupExpirySlider() {
        const slider = $('#expiryTime');
        const valueDisplay = slider.parentElement.querySelector('.slider-value');
        setupSlider(slider, valueDisplay, EXPIRY_TIMES);
    }
    
    setupBurnTimeSlider() {
        const slider = $('#burnTime');
        const valueDisplay = slider.parentElement.querySelector('.slider-value');
        setupSlider(slider, valueDisplay, BURN_TIMES);
    }
    
    setupTokenInput() {
        this.customTokenBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const isHidden = this.tokenInputContainer.style.display === 'none';
            
            toggleVisibility(this.tokenInputContainer, isHidden);
            this.customTokenBtn.textContent = isHidden ? 'Do not use token' : 'Use access token';
            
            if (isHidden) {
                setTimeout(() => {
                    this.tokenInputContainer.scrollIntoView({ behavior: 'smooth' });
                }, 100);
            } else {
                this.customToken.value = '';
                this.tokenHint.value = '';
            }
        });

        // Token counter
        this.customToken.addEventListener('input', () => {
            const remaining = this.MAX_TOKEN_LENGTH - this.customToken.value.length;
            this.tokenCounter.textContent = remaining.toString();
            
            if (this.customToken.value.length > 0 && this.customToken.value.length < this.MIN_TOKEN_LENGTH) {
                this.tokenCounter.classList.add('error');
                this.createBtn.disabled = true;
            } else {
                this.tokenCounter.classList.remove('error');
                this.createBtn.disabled = false;
            }
        });

        // Hint counter
        this.tokenHint.addEventListener('input', () => {
            const remaining = this.MAX_TOKEN_LENGTH - this.tokenHint.value.length;
            this.hintCounter.textContent = remaining.toString();
        });
    }
    
    setupTokenGenerator() {
        const generateBtn = document.querySelector('.generate-token');
        generateBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const token = this.generateReadableToken();
            this.customToken.value = token;
            // Trigger input event to update character counter
            this.customToken.dispatchEvent(new Event('input'));
        });
    }

    generateReadableToken() {
        let token = '';
        for (let i = 0; i < this.TOKEN_LENGTH; i++) {
            const randomIndex = Math.floor(Math.random() * this.TOKEN_CHARS.length);
            token += this.TOKEN_CHARS[randomIndex];
        }
        return token;
    }
    
    handleFiles(files) {
        if (this.images.size >= this.MAX_IMAGES) {
            alert(`Only ${this.MAX_IMAGES} image allowed. Please remove the existing image first.`);
            this.fileInput.value = '';  // Reset file input after alert
            return;
        }
        
        Array.from(files).slice(0, this.MAX_IMAGES - this.images.size).forEach(file => {
            if (!this.ALLOWED_TYPES.includes(file.type)) {
                alert(`File type ${file.type} not allowed`);
                this.fileInput.value = '';  // Reset file input after type error
                return;
            }
            
            if (file.size > this.MAX_IMAGE_SIZE) {
                alert(`File size exceeds ${this.MAX_IMAGE_SIZE / 1024 / 1024}MB limit`);
                this.fileInput.value = '';  // Reset file input after size error
                return;
            }
            
            this.addImagePreview(file);
        });
    }
    
    addImagePreview(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const preview = document.createElement('div');
            preview.className = 'image-preview';
            preview.innerHTML = `
                <img src="${e.target.result}" alt="Preview">
                <button class="remove-btn">
                    <svg class="icon-primary" width="16" height="16">
                        <use href="static/images/close.svg#icon"></use>
                    </svg>
                </button>
            `;
            
            preview.querySelector('.remove-btn').addEventListener('click', () => {
                this.images.delete(file);
                preview.remove();
                this.fileInput.value = '';  // Reset file input
            });
            
            this.imagePreviews.appendChild(preview);
            this.images.add(file);
        };
        reader.readAsDataURL(file);
    }
    
    async createMessage() {
        const message = this.messageInput.value.trim();
        if (!message && this.images.size === 0) {
            alert('Please enter a message or add images');
            return;
        }
        
        const formData = new FormData();
        formData.append('message', message);
        
        formData.append('expiry_index', $('#expiryTime').value);
        formData.append('burn_index', $('#burnTime').value);
        formData.append('font_size', this.fontSize);
        
        const customToken = this.customToken.value.trim();
        const tokenHint = this.tokenHint.value.trim();

        if (this.tokenInputContainer.style.display !== 'none' && customToken) {
            if (customToken.length < this.MIN_TOKEN_LENGTH) {
                alert(`Password must be at least ${this.MIN_TOKEN_LENGTH} characters`);
                return;
            }
            formData.append('token', customToken);
            if (tokenHint) {
                formData.append('token_hint', tokenHint);
            }
        }

        // Add images
        Array.from(this.images).forEach((file, index) => {
            formData.append(`images`, file);
        });
        
        try {
            // Log initial data
            console.log('Creating message with:', {
                messageLength: message.length,
                imagesCount: this.images.size,
                imageDetails: Array.from(this.images).map(file => ({
                    name: file.name,
                    type: file.type,
                    size: file.size
                }))
            });

            // Disable button during upload
            this.createBtn.disabled = true;
            this.createBtn.textContent = 'Creating...';
            
            const response = await fetch('/api/message/create', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            console.log('Server response:', {
                status: response.status,
                statusText: response.statusText,
                data: data
            });
            
            if (response.ok && data.id) {  // Make sure we have a valid message ID
                // Only store data and redirect on success
                if (customToken) {
                    sessionStorage.setItem(`msg_token_${data.id}`, customToken);
                }
                sessionStorage.setItem('current_message_id', data.id);
                window.location.href = '/success';
            } else {
                if (data.detail?.errors) {
                    const errors = data.detail.errors
                        .map(err => `${err.loc.join('.')}: ${err.msg}`)
                        .join('\n');
                    alert(`Validation errors:\n${errors}`);
                } else if (data.detail?.message) {
                    alert(data.detail.message);
                } else {
                    alert('Failed to create message');
                }
            }
        } catch (error) {
            console.error('Creation error:', error);
            alert('Network error: ' + error.message);
        } finally {
            this.createBtn.disabled = false;
            this.createBtn.textContent = 'Create Burning Message';
        }
    }

    setupFontSizeControls() {
        const textarea = this.messageInput;
        const slider = $('#fontSize');
        
        setupSlider(slider, null, FONT_SIZES, (index) => {
            textarea.style.fontSize = FONT_SIZES[index];
            this.fontSize = index;
        });
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    new MessageCreator();
});
