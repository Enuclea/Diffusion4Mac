<template>
    <div class="main_container">
        <h1>Prompt Designer</h1>
        <p class="subtitle">Upload an image and let Gemma analyze its content to generate a detailed prompt for Stable Diffusion.</p>
        <br>

        <div class="designer_layout">
            <!-- Left panel: Image input and status -->
            <div class="left_panel">
                <div 
                    class="image_dropzone" 
                    @drop.prevent="onDragFile" 
                    @dragover.prevent 
                    @click="triggerFileInput"
                    :class="{ has_image: imageSrc }"
                >
                    <input 
                        type="file" 
                        ref="fileInput" 
                        @change="onFileSelected" 
                        accept="image/*" 
                        style="display: none;" 
                    />
                    
                    <div v-if="imageSrc" class="image_preview_container">
                        <img :src="imageSrc" class="image_preview" />
                        <div class="image_overlay">
                            <span class="change_txt">Click or drag to change image</span>
                        </div>
                    </div>
                    
                    <div v-else class="dropzone_placeholder">
                        <span class="icon">🖼️</span>
                        <p>Click or drag-and-drop an image here</p>
                        <span class="subtext">Supports PNG, JPG, JPEG</span>
                    </div>
                </div>

                <div v-if="imageSrc" class="image_actions">
                    <div @click="clearImage" class="l_button">Clear Image</div>
                    <div 
                        @click="describeImage" 
                        class="l_button button_colored" 
                        :class="{ button_disabled: analyzing }"
                        style="display: flex; align-items: center; justify-content: center; gap: 6px;"
                    >
                        <span v-if="analyzing" class="ai_spinner"></span>
                        <span v-else>✨</span>
                        {{ analyzing ? 'Analyzing Image...' : 'Describe Image with AI' }}
                    </div>
                </div>
            </div>

            <!-- Right panel: AI Prompt Result -->
            <div class="right_panel">
                <h3>Generated Prompt</h3>
                <p style="opacity: 0.7; font-size: 0.85rem; margin-bottom: 8px;">Gemma's sight description optimized for stable diffusion:</p>
                
                <textarea 
                    v-model="resultPrompt" 
                    placeholder="The generated prompt will appear here..." 
                    class="form-control result_textarea"
                    rows="8"
                ></textarea>

                <div class="action_buttons_row" v-if="resultPrompt">
                    <div @click="useInTxt2Img" class="l_button button_colored">Use in Text-to-Image</div>
                    <div @click="useInImg2Img" class="l_button button_colored" v-if="imagePath">Use in Image-to-Image</div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import Vue from 'vue';

const PromptDesigner = {
    name: 'PromptDesigner',
    props: {
        app: Object,
    },
    data() {
        return {
            imageSrc: '',
            imagePath: '',
            base64Data: '',
            resultPrompt: '',
            analyzing: false,
        };
    },
    methods: {
        triggerFileInput() {
            this.$refs.fileInput.click();
        },
        onFileSelected(event) {
            const file = event.target.files[0];
            if (file) {
                this.processFile(file);
            }
        },
        onDragFile(event) {
            const file = event.dataTransfer.files[0];
            if (file && file.type.startsWith('image/')) {
                this.processFile(file);
            }
        },
        async processFile(file) {
            // Keep absolute path for Img2Img routing
            this.imagePath = file.path || '';
            
            // Resize and convert to base64
            try {
                const resized = await this.resizeAndEncodeImage(file);
                this.imageSrc = resized.dataUrl;
                this.base64Data = resized.base64;
            } catch (err) {
                console.error("Error processing file:", err);
                alert("Failed to process image file.");
            }
        },
        resizeAndEncodeImage(file) {
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const img = new Image();
                    img.onload = () => {
                        const maxDim = 1024;
                        let width = img.width;
                        let height = img.height;
                        
                        if (width > maxDim || height > maxDim) {
                            if (width > height) {
                                height = Math.round((height * maxDim) / width);
                                width = maxDim;
                            } else {
                                width = Math.round((width * maxDim) / height);
                                height = maxDim;
                            }
                        }
                        
                        const canvas = document.createElement('canvas');
                        canvas.width = width;
                        canvas.height = height;
                        const ctx = canvas.getContext('2d');
                        ctx.drawImage(img, 0, 0, width, height);
                        
                        const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
                        const base64 = dataUrl.split(',')[1];
                        resolve({ base64, dataUrl });
                    };
                    img.onerror = reject;
                    img.src = e.target.result;
                };
                reader.onerror = reject;
                reader.readAsDataURL(file);
            });
        },
        clearImage() {
            this.imageSrc = '';
            this.imagePath = '';
            this.base64Data = '';
            this.resultPrompt = '';
        },
        async describeImage() {
            if (!this.base64Data) {
                alert("Please add an image first.");
                return;
            }
            
            this.analyzing = true;
            try {
                const tagsResponse = await fetch("http://127.0.0.1:11435/api/tags").catch(() => null);
                if (!tagsResponse) {
                    alert("Ollama is not running. Please make sure Ollama is active on port 11435.");
                    this.analyzing = false;
                    return;
                }
                const tagsData = await tagsResponse.json();
                const downloadedModels = tagsData.models ? tagsData.models.map(m => m.name) : [];
                
                let preferredModel = "gemma4:e4b";
                if (this.app && this.app.app_state && this.app.app_state.app_data && this.app.app_state.app_data.settings) {
                    preferredModel = this.app.app_state.app_data.settings.gemma_preferred_model || "gemma4:e4b";
                }
                
                if (!downloadedModels.includes(preferredModel)) {
                    const otherModel = preferredModel === "gemma4:e4b" ? "gemma4:e2b" : "gemma4:e4b";
                    if (downloadedModels.includes(otherModel)) {
                        preferredModel = otherModel;
                    } else {
                        alert("Please download Gemma 4 [e2b] or [e4b] in the Model Store to use image description.");
                        this.analyzing = false;
                        return;
                    }
                }
                
                const response = await fetch("http://127.0.0.1:11435/api/chat", {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        model: preferredModel,
                        messages: [
                            {
                                role: 'user',
                                content: 'Describe this image in detail. Focus on the main subject, style, composition, colors, lighting, and mood. Format the description as a detailed, visually rich Stable Diffusion text-to-image prompt (just the descriptive text, under 75 words, no introductory phrasing).',
                                images: [this.base64Data]
                            }
                        ],
                        stream: false
                    })
                });
                
                if (!response.ok) {
                    throw new Error("HTTP error " + response.status);
                }
                
                const data = await response.json();
                if (data.message && data.message.content) {
                    this.resultPrompt = data.message.content.trim();
                } else {
                    throw new Error("Invalid response format from Ollama");
                }
            } catch (e) {
                console.error("AI Describe error:", e);
                alert("Error during image analysis: " + e.message);
            } finally {
                this.analyzing = false;
            }
        },
        useInTxt2Img() {
            if (!this.resultPrompt) return;
            
            // Switch page
            this.app.functions.switch_page("Txt2Img");
            
            // Populate prompt options
            Vue.nextTick(() => {
                const txt2img = this.app.$refs.router.$refs['Txt2Img'];
                if (txt2img && txt2img[0] && txt2img[0].$refs.sd_applet) {
                    Vue.set(txt2img[0].$refs.sd_applet.sd_options, 'prompt', this.resultPrompt);
                }
            });
        },
        useInImg2Img() {
            if (!this.resultPrompt || !this.imagePath) return;
            
            // Switch page
            this.app.functions.switch_page("Img2Img");
            
            // Populate prompt and image options
            Vue.nextTick(() => {
                const img2img = this.app.$refs.router.$refs['Img2Img'];
                if (img2img && img2img[0] && img2img[0].$refs.sd_applet) {
                    Vue.set(img2img[0].$refs.sd_applet.sd_options, 'prompt', this.resultPrompt);
                    Vue.set(img2img[0].$refs.sd_applet.sd_options, 'input_img', this.imagePath);
                }
            });
        }
    }
};

PromptDesigner.title = "Prompt Designer";
PromptDesigner.icon = "magic";
PromptDesigner.description = "Design stable diffusion prompts using AI vision";
PromptDesigner.img_icon = require("../assets/imgs/page_icon_imgs/prompt_designer.png");
PromptDesigner.home_category = "main";
PromptDesigner.sidebar_show = "always";

export default PromptDesigner;
</script>

<style scoped>
.main_container {
    padding: 20px;
    width: 100%;
    height: 100%;
    overflow: auto;
}

.subtitle {
    opacity: 0.7;
    margin-top: -10px;
    font-size: 0.95rem;
}

.designer_layout {
    display: flex;
    gap: 30px;
    margin-top: 15px;
    flex-wrap: wrap;
}

.left_panel {
    flex: 1;
    min-width: 320px;
    max-width: 480px;
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.right_panel {
    flex: 1.2;
    min-width: 360px;
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.image_dropzone {
    width: 100%;
    height: 320px;
    border: 2px dashed rgba(255, 255, 255, 0.15);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    background-color: var(--sidebar-color, #1e1e1e);
    overflow: hidden;
    position: relative;
    transition: border-color 0.2s, background-color 0.2s;
}

.image_dropzone:hover {
    border-color: rgba(168, 85, 247, 0.5);
    background-color: rgba(255, 255, 255, 0.02);
}

.image_dropzone.has_image {
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.dropzone_placeholder {
    text-align: center;
    padding: 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
}

.dropzone_placeholder .icon {
    font-size: 3rem;
}

.dropzone_placeholder p {
    font-weight: 500;
    margin: 0;
}

.dropzone_placeholder .subtext {
    font-size: 0.8rem;
    opacity: 0.5;
}

.image_preview_container {
    width: 100%;
    height: 100%;
    position: relative;
}

.image_preview {
    width: 100%;
    height: 100%;
    object-fit: contain;
    background-color: #0b0b0b;
}

.image_overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    opacity: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: opacity 0.25s ease;
}

.image_preview_container:hover .image_overlay {
    opacity: 1;
}

.change_txt {
    color: white;
    font-weight: 500;
    font-size: 0.9rem;
    background: rgba(0, 0, 0, 0.6);
    padding: 6px 12px;
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.2);
}

.image_actions {
    display: flex;
    gap: 10px;
    justify-content: space-between;
}

.result_textarea {
    width: 100%;
    resize: none;
    font-family: inherit;
    font-size: 0.95rem;
    line-height: 1.5;
    background-color: var(--input-bg-color, #1e1e1e);
    color: var(--text-color, white);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 12px;
    box-sizing: border-box;
}

.action_buttons_row {
    display: flex;
    gap: 12px;
    margin-top: 10px;
}

.button_disabled {
    opacity: 0.5;
    cursor: not-allowed !important;
    pointer-events: none;
}

.ai_spinner {
    width: 14px;
    height: 14px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    border-top-color: white;
    animation: ai_spin 0.8s linear infinite;
}

@keyframes ai_spin {
    to { transform: rotate(360deg); }
}
</style>
