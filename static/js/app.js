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
            
            if (status.demo_mode) {
                this.showInfo('Running in demo mode - ML dependencies not installed. Interface functionality is demonstrated with mock results.');
            } else if (!status.model_loaded) {
                this.showError('FIBO model not loaded. Please check the server logs.');
            }
        } catch (error) {
            console.error('Failed to check status:', error);
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

        this.showGenerationStatus();
        this.updateProgress(0, 'Preparing generation...');

        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.success) {
                this.currentResultId = result.result_id;
                this.displayResults(result);
                this.hideGenerationStatus();
                
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
        const files = result.files;

        // Display HDRI if generated
        if (files.hdri) {
            this.displayHDRI(files.hdri);
        }

        // Display textures if generated
        if (files.textures) {
            this.displayTextures(files.textures);
        }

        // Show package download if available
        if (files.package) {
            document.getElementById('packageCard').classList.remove('d-none');
        }
    }

    displayHDRI(hdriPath) {
        const preview = document.getElementById('hdriPreview');
        const download = document.getElementById('hdriDownload');

        // Create preview (simplified - in real implementation, you'd show a proper HDRI preview)
        preview.innerHTML = `
            <div class="text-center">
                <i class="fas fa-globe text-success fa-4x mb-2"></i>
                <h6>HDRI Generated</h6>
                <p class="text-muted small">${hdriPath.split('/').pop()}</p>
            </div>
        `;

        download.classList.remove('d-none');
    }

    displayTextures(textures) {
        const preview = document.getElementById('texturePreview');
        const downloads = document.getElementById('textureDownloads');

        // Create texture grid preview
        const textureGrid = Object.keys(textures).map(type => `
            <div class="col-6 mb-2">
                <div class="text-center p-2 border rounded">
                    <i class="fas fa-layer-group text-primary"></i>
                    <small class="d-block">${type.charAt(0).toUpperCase() + type.slice(1)}</small>
                </div>
            </div>
        `).join('');

        preview.innerHTML = `
            <div class="row">
                ${textureGrid}
            </div>
        `;

        // Create download buttons
        const downloadButtons = Object.keys(textures).map(type => `
            <button class="btn btn-outline-success btn-sm me-2 mb-2 download-btn" data-type="${type}">
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
        // Simple error display - in production, use a proper toast/modal system
        alert(`Error: ${message}`);
    }

    showInfo(message) {
        // Simple info display
        console.log(`Info: ${message}`);
        // You could also show this in a banner on the page
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new FIBOStudio();
});