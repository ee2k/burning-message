import { initSvgIcons } from './global.js';

class MessageCreator {
    constructor() {
        initSvgIcons();
        
        this.messageInput = document.getElementById('messageContent');
        this.dropZone = document.getElementById('dropZone');
        this.fileInput = document.getElementById('fileInput');
        this.imagePreviews = document.getElementById('imagePreviews');
        this.createBtn = document.getElementById('createBtn');
        
        this.images = new Set();
        this.MAX_IMAGES = 1;
        this.MAX_IMAGE_SIZE = 3 * 1024 * 1024; // 3MB
        this.ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/gif'];
        this.MAX_MESSAGE_LENGTH = 2000;
        
        this.expiryTimes = [
            { value: 1, label: '1 min' },
            { value: 5, label: '5 min' },
            { value: 30, label: '30 min' },
            { value: 60, label: '1 hour' },
            { value: 720, label: '12 hours' },
            { value: 1440, label: '1 day' },
            { value: 4320, label: '3 days' }
        ];
        
        this.burnTimes = [
            { value: 0.1, label: '0.1 second' },
            { value: 1, label: '1 second' },
            { value: 3, label: '3 seconds' },
            { value: 7, label: '7 seconds' },
            { value: 180, label: '3 minutes' },
            { value: 600, label: '10 minutes' },
            { value: Infinity, label: 'Never' }
        ];
        
        this.setupEventListeners();
        this.setupCharCounter();
        this.setupSlider();
        this.setupBurnTimeSlider();
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
        counter.style.display = 'none';  // Hide by default
        this.messageInput.parentNode.insertBefore(counter, this.messageInput.nextSibling);
        
        this.messageInput.addEventListener('input', () => {
            const remaining = this.MAX_MESSAGE_LENGTH - this.messageInput.value.length;
            
            // Only show counter when approaching limit (last 100 chars) or exceeding
            if (remaining <= 100) {
                counter.textContent = `${remaining}`;
                counter.style.display = 'block';
                
                if (remaining < 0) {
                    counter.classList.add('error');
                    counter.classList.remove('warning');
                    this.messageInput.classList.add('error');
                    this.messageInput.classList.remove('near-limit');
                    this.createBtn.disabled = true;
                } else {
                    counter.classList.add('warning');
                    counter.classList.remove('error');
                    this.messageInput.classList.add('near-limit');
                    this.messageInput.classList.remove('error');
                    this.createBtn.disabled = false;
                }
            } else {
                counter.style.display = 'none';
                counter.classList.remove('warning', 'error');
                this.messageInput.classList.remove('near-limit', 'error');
                this.createBtn.disabled = false;
            }
        });
    }
    
    setupSlider() {
        const slider = document.getElementById('expiryTime');
        const value = slider.parentElement.querySelector('.slider-value');
        
        const updateSliderProgress = () => {
            const progress = (slider.value / slider.max) * 100;
            slider.style.setProperty('--slider-progress', `${progress}%`);
        };
        
        const updateSliderValue = () => {
            const time = this.expiryTimes[slider.value];
            value.textContent = time.label;
            updateSliderProgress();
        };
        
        slider.addEventListener('input', updateSliderValue);
        updateSliderValue(); // Set initial value
    }
    
    setupBurnTimeSlider() {
        const slider = document.getElementById('burnTime');
        const value = slider.parentElement.querySelector('.slider-value');
        
        const updateSliderProgress = () => {
            const progress = (slider.value / slider.max) * 100;
            slider.style.setProperty('--slider-progress', `${progress}%`);
        };
        
        const updateSliderValue = () => {
            const time = this.burnTimes[slider.value];
            value.textContent = time.label;
            updateSliderProgress();
        };
        
        slider.addEventListener('input', updateSliderValue);
        updateSliderValue(); // Set initial value
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
        formData.append('expiry', this.expiryTimes[document.getElementById('expiryTime').value].value);
        formData.append('burnTime', this.burnTimes[document.getElementById('burnTime').value].value);
        this.images.forEach(file => formData.append('images', file));
        
        try {
            const response = await fetch('/api/create', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                window.location.href = `/success?id=${data.id}`;
            } else {
                throw new Error('Failed to create message');
            }
        } catch (error) {
            alert('Error creating message: ' + error.message);
        }
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    new MessageCreator();
});
