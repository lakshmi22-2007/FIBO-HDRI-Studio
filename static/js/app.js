/**
 * FIBO HDRI Studio - Frontend JavaScript
 */

class FIBOStudio {
    constructor() {
        this.currentResultId = null;
        this.presets = {};
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadPresets();
        this.checkStatus();
    }

    setupEventListeners() {
        // Slider updates
        document.getElementById('evValue').addEventListener('input', (e) => {
            document.getElementById('evValueDisplay').textContent = e.target.value;
        });

        document.getElementById('azimuth').addEventListener('input', (e) => {
            document.getElementById('azimuthDisplay').textContent = e.target.value + '°';
        });

        // Texture options toggle
        document.getElementById('generateTextures').addEventListener('change', (e) => {
            document.getElementById('textureOptions').style.display = 
                e.target.checked ? 'block' : 'none';
        });

        // Form submission
        document.getElementById('generationForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.generateAssets();
        });

        // Preset buttons
        document.querySelectorAll('.preset-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const presetName = e.target.dataset.preset;
                this.applyPreset(presetName);
            });
        });

        // Download buttons (delegated event handling)
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('download-btn') || 
                e.target.closest('.download-btn')) {
                const btn = e.target.classList.contains('download-btn') ? 
                           e.target : e.target.closest('.download-btn');
                const fileType = btn.dataset.type;
                this.downloadFile(fileType);
            }
        });
    }

    async loadPresets() {
        try {
            const response = await fetch('/api/presets');
            this.presets = await response.json();
        } catch (error) {
            console.error('Failed to load presets:', error);
        }
    }

    async checkStatus() {
        try {
            const response = await fetch('/api/status');
            const status = await response.json();
            
            console.log('Server status:', status);
            
            if (status.mode === 'demo' || status.status === 'demo_mode') {
                this.showInfo('Running in demo mode - ML dependencies not installed. Interface functionality is demonstrated with mock results.');
            } else if (!status.model_loaded) {
                console.warn('FIBO model not loaded');
            } else {
                console.log('System ready:', status.mode);
            }
        } catch (error) {
            console.error('Failed to check status:', error);
            this.showError('Could not connect to server. Please ensure the Flask app is running.');
        }
    }

    applyPreset(presetName) {
        const preset = this.presets[presetName];
        if (!preset) return;

        document.getElementById('evValue').value = preset.ev_value;
        document.getElementById('evValueDisplay').textContent = preset.ev_value;
        
        document.getElementById('azimuth').value = preset.azimuth;
        document.getElementById('azimuthDisplay').textContent = preset.azimuth + '°';
        
        document.getElementById('colorProfile').value = preset.color_profile;

        // Visual feedback
        document.querySelectorAll('.preset-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-preset="${presetName}"]`).classList.add('active');
    }

    async generateAssets() {
        const formData = this.getFormData();
        
        if (!formData.prompt.trim()) {
            this.showError('Please enter a scene description.');
            return;
        }

        console.log('Starting generation with data:', formData);
        
        this.showGenerationStatus();
        this.updateProgress(10, 'Preparing generation...');

        try {
            this.updateProgress(30, 'Sending request to server...');
            
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            this.updateProgress(60, 'Processing response...');

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log('Generation result:', result);

            if (result.success) {
                this.updateProgress(90, 'Displaying results...');
                this.currentResultId = result.result_id;
                this.displayResults(result);
                this.updateProgress(100, 'Complete!');
                
                setTimeout(() => {
                    this.hideGenerationStatus();
                }, 500);
                
                if (result.demo_mode) {
                    this.showInfo('Demo generation completed! In full mode, actual HDRI and PBR files would be generated.');
                }
            } else {
                throw new Error(result.error || 'Generation failed');
            }

        } catch (error) {
            console.error('Generation error:', error);
            this.showError(`Generation failed: ${error.message}`);
            this.hideGenerationStatus();
        }
    }

    getFormData() {
        const textureTypes = Array.from(document.querySelectorAll('.texture-type:checked'))
                                 .map(cb => cb.value);

        return {
            prompt: document.getElementById('prompt').value,
            ev_value: parseFloat(document.getElementById('evValue').value),
            azimuth: parseFloat(document.getElementById('azimuth').value),
            color_profile: document.getElementById('colorProfile').value,
            generate_hdri: document.getElementById('generateHdri').checked,
            generate_textures: document.getElementById('generateTextures').checked,
            texture_types: textureTypes
        };
    }

    showGenerationStatus() {
        document.getElementById('statusCard').style.display = 'block';
        document.getElementById('resultsGrid').style.opacity = '0.5';
    }

    hideGenerationStatus() {
        document.getElementById('statusCard').style.display = 'none';
        document.getElementById('resultsGrid').style.opacity = '1';
    }

    updateProgress(percent, message) {
        document.getElementById('statusText').textContent = message;
        document.querySelector('.progress-bar').style.width = percent + '%';
    }

    displayResults(result) {
        console.log('Displaying results:', result);
        const files = result.files;
        console.log('Files:', files);

        // Display HDRI if generated
        if (files.hdri) {
            console.log('Displaying HDRI:', files.hdri);
            this.displayHDRI(files.hdri);
        } else {
            console.log('No HDRI file in result');
        }

        // Display textures if generated
        if (files.textures) {
            console.log('Displaying textures:', files.textures);
            this.displayTextures(files.textures);
        } else {
            console.log('No textures in result');
        }

        // Show package download card if any files were generated
        if (files.hdri || files.textures) {
            const packageCard = document.getElementById('packageCard');
            packageCard.classList.remove('d-none');
            packageCard.classList.add('animate-in');
        }
    }

    displayHDRI(hdriPath) {
        const preview = document.getElementById('hdriPreview');
        const download = document.getElementById('hdriDownload');

        // Create enhanced preview with animation
        preview.innerHTML = `
            <div class="text-center animate-in" style="padding: 2rem;">
                <div style="position: relative; display: inline-block;">
                    <i class="fas fa-globe icon-success" style="font-size: 4.5rem; margin-bottom: 1rem;"></i>
                    <i class="fas fa-check-circle" style="position: absolute; top: -5px; right: -5px; color: #00f2fe; font-size: 1.5rem; background: var(--card-bg); border-radius: 50%;"></i>
                </div>
                <h5 class="mb-2" style="color: #4facfe; font-weight: 700;">HDRI Generated!</h5>
                <div class="badge badge-custom mb-2">360° Equirectangular</div>
                <p class="text-secondary small mb-0" style="opacity: 0.7;">${hdriPath.split('/').pop()}</p>
            </div>
        `;

        download.classList.remove('d-none');
        download.classList.add('animate-in');
    }

    displayTextures(textures) {
        const preview = document.getElementById('texturePreview');
        const downloads = document.getElementById('textureDownloads');

        // Create enhanced texture grid preview
        const textureIcons = {
            'albedo': 'fa-fill-drip',
            'normal': 'fa-cube',
            'roughness': 'fa-grip-lines',
            'ao': 'fa-adjust'
        };

        const textureColors = {
            'albedo': '#f5576c',
            'normal': '#4facfe',
            'roughness': '#667eea',
            'ao': '#764ba2'
        };

        const textureGrid = Object.keys(textures).map(type => `
            <div class="texture-item animate-in" style="animation-delay: ${Object.keys(textures).indexOf(type) * 0.1}s;">
                <i class="fas ${textureIcons[type] || 'fa-layer-group'}" style="color: ${textureColors[type] || '#667eea'};"></i>
                <div class="fw-bold mt-2">${type.charAt(0).toUpperCase() + type.slice(1)}</div>
                <small class="text-secondary"><i class="fas fa-check-circle me-1" style="color: #00f2fe;"></i>Ready</small>
            </div>
        `).join('');

        preview.innerHTML = `
            <div class="texture-grid w-100 p-3">
                ${textureGrid}
            </div>
        `;

        // Create enhanced download buttons
        const downloadButtons = Object.keys(textures).map(type => `
            <button class="btn btn-outline-success btn-sm me-2 mb-2 download-btn animate-in" data-type="${type}" style="animation-delay: ${(Object.keys(textures).length + Object.keys(textures).indexOf(type)) * 0.1}s;">
                <i class="fas fa-download me-1"></i>${type.charAt(0).toUpperCase() + type.slice(1)}
            </button>
        `).join('');

        downloads.innerHTML = downloadButtons;
        downloads.classList.remove('d-none');
    }

    async downloadFile(fileType) {
        if (!this.currentResultId) {
            this.showError('No generation result available for download.');
            return;
        }

        try {
            const response = await fetch(`/api/download/${this.currentResultId}/${fileType}`);
            
            if (!response.ok) {
                throw new Error(`Download failed: ${response.status}`);
            }

            // Create download link
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${fileType}_${this.currentResultId}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

        } catch (error) {
            console.error('Download error:', error);
            this.showError(`Download failed: ${error.message}`);
        }
    }

    showError(message) {
        // Enhanced error display with styled alert
        const alertHtml = `
            <div class="alert alert-danger alert-dismissible fade show animate-in" role="alert" style="position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px; background: linear-gradient(135deg, rgba(245, 87, 108, 0.95) 0%, rgba(240, 147, 251, 0.95) 100%); border: none; box-shadow: 0 10px 40px rgba(245, 87, 108, 0.4);">
                <i class="fas fa-exclamation-circle me-2"></i>
                <strong>Error:</strong> ${message}
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="alert"></button>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', alertHtml);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alert = document.querySelector('.alert');
            if (alert) alert.remove();
        }, 5000);
    }

    showInfo(message) {
        // Enhanced info display with styled alert
        const alertHtml = `
            <div class="alert alert-info alert-dismissible fade show animate-in" role="alert" style="position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px; background: linear-gradient(135deg, rgba(79, 172, 254, 0.95) 0%, rgba(0, 242, 254, 0.95) 100%); border: none; box-shadow: 0 10px 40px rgba(79, 172, 254, 0.4); color: white;">
                <i class="fas fa-info-circle me-2"></i>
                ${message}
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="alert"></button>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', alertHtml);
        
        // Auto-dismiss after 7 seconds
        setTimeout(() => {
            const alert = document.querySelector('.alert-info');
            if (alert) alert.remove();
        }, 7000);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new FIBOStudio();
});