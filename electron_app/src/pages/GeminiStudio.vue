<template>
    <div class="gemini_studio_container">
        <!-- Left Pane: Controls -->
        <div class="studio_controls">
            <div class="controls_header">
                <h2>Gemini Studio</h2>
                <span class="badge_not_local">☁️ Not Local / Cloud API</span>
            </div>
            <p class="studio_intro">
                Generate high-fidelity images using Google's <strong>Imagen 3</strong> model and enhance prompts with <strong>Gemini 2.5 Flash</strong>.
            </p>
            
            <div class="form_group">
                <label>Text Prompt</label>
                <textarea 
                    v-model="prompt" 
                    placeholder="Describe the image you want to generate in detail..." 
                    class="form_textarea"
                    rows="4"
                    :disabled="loading"
                ></textarea>
            </div>
            
            <div class="form_group inline_toggle">
                <label class="switch_container">
                    <input type="checkbox" v-model="enhancePromptFlag" :disabled="loading">
                    <span class="slider_switch round"></span>
                </label>
                <div class="toggle_label">
                    <h4>Enhance Prompt with Gemini AI</h4>
                    <p>Automatically rewrite into a detailed, visually descriptive prompt</p>
                </div>
            </div>
            
            <div class="form_group">
                <label>Imagen Model</label>
                <select v-model="selectedModel" class="form_select" :disabled="loading">
                    <option v-for="model in availableModels" :key="model.name" :value="model.name">
                        {{ model.displayName }}
                    </option>
                </select>
            </div>
            
            <div class="form_group">
                <label>Aspect Ratio</label>
                <div class="aspect_ratio_selector">
                    <div 
                        v-for="ratio in aspectRatios" 
                        :key="ratio.value" 
                        class="ratio_card" 
                        :class="{ active: selectedRatio === ratio.value }"
                        @click="selectRatio(ratio.value)"
                    >
                        <div class="ratio_preview" :class="'preview_' + ratio.value.replace(':', '_')"></div>
                        <span class="ratio_label">{{ ratio.label }}</span>
                    </div>
                </div>
            </div>
            
            <button 
                @click="generate" 
                class="btn_generate" 
                :disabled="loading || !prompt.trim()"
            >
                <span v-if="loading" class="spinner_inline"></span>
                <span>{{ loading ? 'Generating...' : 'Generate with Gemini' }}</span>
            </button>
        </div>
        
        <!-- Right Pane: Workspace / Output -->
        <div class="studio_workspace">
            <!-- Loading State -->
            <div v-if="loading" class="workspace_loading">
                <div class="loader_glow"></div>
                <div class="loader_spinner"></div>
                <h3 class="loader_title">{{ loadingTitle }}</h3>
                <p class="loader_desc">{{ loadingDesc }}</p>
            </div>
            
            <!-- Result State -->
            <div v-else-if="imageSrc" class="workspace_result">
                <div class="result_image_container">
                    <img :src="imageSrc" alt="Generated Image" class="result_image" />
                </div>
                
                <div class="action_bar">
                    <button @click="useInImg2Img" class="btn_action">
                        <span>🖼️ Send to Img2Img</span>
                    </button>
                    <button @click="useInTxt2Img" class="btn_action">
                        <span>🎯 Use as Txt2Img Reference</span>
                    </button>
                    <button @click="downloadImage" class="btn_action btn_download">
                        <span>💾 Save Image</span>
                    </button>
                </div>
            </div>
            
            <!-- Empty State -->
            <div v-else class="workspace_empty">
                <div class="gemini_logo_container">
                    <div class="gemini_glow"></div>
                    <div class="gemini_symbol">☁️</div>
                </div>
                <h3>Cloud Image Generation</h3>
                <p>Enter a description and click generate to invoke Google Imagen. Generations require an active internet connection.</p>
                <div class="disclaimer_card">
                    <p>⚠️ <strong>Direct Connection:</strong> Calls are made directly to Google AI Studio REST endpoints using the Gemini API Key saved in your local settings.</p>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import Vue from 'vue';

const GeminiStudio = {
    name: 'GeminiStudio',
    props: {
        app: Object
    },
    data() {
        return {
            prompt: "",
            enhancePromptFlag: false,
            selectedRatio: "1:1",
            selectedModel: "imagen-3.0-generate-002",
            availableModels: [
                { displayName: "Imagen 4 Generate (Standard)", name: "imagen-4.0-generate-001" },
                { displayName: "Imagen 4 Ultra Generate", name: "imagen-4.0-ultra-generate-001" },
                { displayName: "Imagen 4 Fast Generate", name: "imagen-4.0-fast-generate-001" },
                { displayName: "Imagen 3 Generate (Legacy)", name: "imagen-3.0-generate-002" }
            ],
            loading: false,
            loadingTitle: "",
            loadingDesc: "",
            imageSrc: "",
            savedImagePath: "",
            aspectRatios: [
                { label: 'Square (1:1)', value: '1:1' },
                { label: 'Landscape (16:9)', value: '16:9' },
                { label: 'Portrait (9:16)', value: '9:16' },
                { label: 'Standard (4:3)', value: '4:3' },
                { label: 'Classic (3:4)', value: '3:4' }
            ]
        };
    },
    computed: {
        apiKey() {
            return this.app?.app_state?.app_data?.settings?.gemini_api_key || "";
        }
    },
    watch: {
        apiKey: {
            handler(newVal) {
                if (newVal) {
                    this.fetchAvailableModels();
                }
            },
            immediate: true
        }
    },
    methods: {
        async fetchAvailableModels() {
            if (!this.apiKey || !this.apiKey.trim()) return;
            try {
                const url = `https://generativelanguage.googleapis.com/v1beta/models?key=${this.apiKey.trim()}`;
                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error(`HTTP error ${response.status}`);
                }
                const data = await response.json();
                if (data.models && Array.isArray(data.models)) {
                    const imagenModels = data.models.filter(m => 
                        m.name && m.name.toLowerCase().includes('imagen')
                    );
                    
                    if (imagenModels.length > 0) {
                        const formatted = imagenModels.map(m => {
                            const shortName = m.name.replace('models/', '');
                            let displayName = m.displayName || shortName;
                            return {
                                name: shortName,
                                displayName: displayName
                            };
                        });
                        
                        this.availableModels = formatted;
                        
                        // If current selectedModel is not in the fetched list, select standard one or the first one
                        const exists = this.availableModels.some(m => m.name === this.selectedModel);
                        if (!exists) {
                            const standard = this.availableModels.find(m => m.name.includes('generate-001') || m.name.includes('generate-002'));
                            this.selectedModel = standard ? standard.name : this.availableModels[0].name;
                        }
                    }
                }
            } catch (err) {
                console.error("Error fetching available models:", err);
            }
        },
        async generate() {
            if (!this.prompt.trim()) {
                this.app.show_toast("Please enter a prompt");
                return;
            }
            if (!this.apiKey.trim()) {
                this.app.show_toast("Gemini API Key is not set in Settings");
                return;
            }
            
            this.loading = true;
            this.imageSrc = "";
            this.savedImagePath = "";
            
            try {
                let finalPrompt = this.prompt;
                
                if (this.enhancePromptFlag) {
                    this.loadingTitle = "Enhancing prompt...";
                    this.loadingDesc = "Using Gemini 2.5 Flash to optimize prompt details";
                    finalPrompt = await this.enhancePromptCall(this.prompt, this.apiKey);
                }
                
                this.loadingTitle = "Generating image...";
                this.loadingDesc = "Imagen is generating your cloud image";
                
                const b64Data = await this.generateImageCall(finalPrompt, this.selectedRatio, this.apiKey);
                
                this.loadingTitle = "Saving image...";
                this.loadingDesc = "Saving generated image to local disk";
                
                // Save image via Electron IPC
                const savedPath = window.ipcRenderer.sendSync('save_b64_image', b64Data, false);
                if (savedPath) {
                    this.savedImagePath = savedPath;
                    this.imageSrc = 'file://' + savedPath;
                } else {
                    throw new Error("Failed to save image locally");
                }
                
                this.app.show_toast("Image generated successfully!");
            } catch (err) {
                console.error(err);
                this.app.show_toast("Failed to generate: " + err.message);
            } finally {
                this.loading = false;
            }
        },
        async enhancePromptCall(userPrompt, apiKey) {
            const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`;
            const payload = {
                contents: [{
                    parts: [{
                        text: "You are an expert prompt engineer for Imagen 3 image generation. " +
                              "Rewrite the following prompt into a highly descriptive, detailed prompt optimized for image generation. " +
                              "Focus on style, lighting, composition, mood, and visual details. " +
                              "Do NOT include any introduction, explanation, or conversational text. Output ONLY the enhanced prompt. " +
                              "Here is the prompt to enhance:\n\n" + userPrompt
                    }]
                }]
            };
            
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) {
                const errText = await response.text();
                throw new Error(`Gemini API error: ${response.status} - ${errText}`);
            }
            
            const data = await response.json();
            if (data.candidates && data.candidates[0] && data.candidates[0].content && data.candidates[0].content.parts && data.candidates[0].content.parts[0]) {
                return data.candidates[0].content.parts[0].text.trim();
            } else {
                throw new Error("Invalid response format from Gemini API");
            }
        },
        async generateImageCall(prompt, aspectRatio, apiKey) {
            const url = `https://generativelanguage.googleapis.com/v1beta/models/${this.selectedModel}:predict?key=${apiKey}`;
            const payload = {
                instances: [
                    {
                        prompt: prompt
                    }
                ],
                parameters: {
                    numberOfImages: 1,
                    outputMimeType: "image/png",
                    aspectRatio: aspectRatio
                }
            };
            
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) {
                const errText = await response.text();
                throw new Error(`Imagen API error: ${response.status} - ${errText}`);
            }
            
            const data = await response.json();
            if (data.predictions && data.predictions[0] && data.predictions[0].bytesBase64Encoded) {
                return data.predictions[0].bytesBase64Encoded;
            } else {
                throw new Error("Invalid response format from Imagen API");
            }
        },
        useInTxt2Img() {
            if (!this.savedImagePath) return;
            
            // Switch page
            this.app.functions.switch_page("Txt2Img");
            
            // Populate options
            Vue.nextTick(() => {
                const txt2img = this.app.$refs.router.$refs['Txt2Img'];
                if (txt2img && txt2img[0] && txt2img[0].$refs.sd_applet) {
                    Vue.set(txt2img[0].$refs.sd_applet.sd_options, 'model_selection', 'Flux Klein');
                    Vue.set(txt2img[0].$refs.sd_applet.sd_options, 'is_adv_mode', true);
                    Vue.set(txt2img[0].$refs.sd_applet.sd_options, 'guide_img_1', this.savedImagePath);
                    if (this.prompt) {
                        Vue.set(txt2img[0].$refs.sd_applet.sd_options, 'prompt', this.prompt);
                    }
                }
            });
        },
        useInImg2Img() {
            if (!this.savedImagePath) return;
            
            if (this.app.functions.send_to_img2img) {
                this.app.functions.send_to_img2img(this.imageSrc, { prompt: this.prompt });
            } else {
                // fallback
                this.app.functions.switch_page("Img2Img");
                Vue.nextTick(() => {
                    const img2img = this.app.$refs.router.$refs['Img2Img'];
                    if (img2img && img2img[0] && img2img[0].$refs.sd_applet) {
                        Vue.set(img2img[0].$refs.sd_applet.sd_options, 'input_img', this.imageSrc);
                        if (this.prompt) {
                            Vue.set(img2img[0].$refs.sd_applet.sd_options, 'prompt', this.prompt);
                        }
                    }
                });
            }
        },
        downloadImage() {
            if (!this.savedImagePath) return;
            
            const suggested_fname = "GeminiStudio_" + Date.now();
            const out_path = window.ipcRenderer.sendSync('save_dialog', suggested_fname);
            if (!out_path) return;
            
            const org_path = this.savedImagePath;
            window.ipcRenderer.sendSync('save_file', org_path + "||" + out_path);
            this.app.show_toast("Image saved successfully");
        },
        selectRatio(ratioVal) {
            if (!this.loading) {
                this.selectedRatio = ratioVal;
            }
        }
    }
};

GeminiStudio.title = "Gemini Studio";
GeminiStudio.icon = "cloud";
GeminiStudio.description = "Frontier AI image generation (Not Local)";
GeminiStudio.img_icon = require("../assets/imgs/page_icon_imgs/default.png");
GeminiStudio.home_category = "main";
GeminiStudio.sidebar_show = "never"; // Toggled dynamically by router

export default GeminiStudio;
</script>

<style scoped>
.gemini_studio_container {
    display: flex;
    padding: 20px;
    height: 100%;
    width: 100%;
    box-sizing: border-box;
    overflow: hidden;
}

/* Left controls panel */
.studio_controls {
    width: 360px;
    background-color: var(--sidebar-color);
    border: 1px solid var(--border-color-invert-extralight);
    border-radius: 12px;
    padding: 20px;
    display: flex;
    flex-direction: column;
    overflow-y: auto;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.controls_header {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-bottom: 12px;
}

.controls_header h2 {
    font-size: 1.5rem;
    margin: 0;
    font-weight: 600;
}

.badge_not_local {
    font-size: 0.75rem;
    background-color: rgba(255, 65, 108, 0.15);
    color: #FF416C;
    padding: 3px 8px;
    border-radius: 20px;
    font-weight: 600;
    width: fit-content;
    border: 1px solid rgba(255, 65, 108, 0.2);
}

.studio_intro {
    font-size: 0.85rem;
    opacity: 0.75;
    line-height: 1.4;
    margin: 0 0 20px 0;
}

.form_group {
    margin-bottom: 20px;
    display: flex;
    flex-direction: column;
}

.form_group label {
    font-size: 0.85rem;
    font-weight: 600;
    margin-bottom: 8px;
    opacity: 0.9;
}

.form_textarea {
    width: 100%;
    background-color: var(--options-input-bg);
    color: var(--text-color-solid);
    border: 1px solid var(--border-color-invert);
    border-radius: 8px;
    padding: 10px;
    font-size: 0.9rem;
    outline: none;
    resize: none;
    box-sizing: border-box;
    transition: border-color 0.2s;
    font-family: inherit;
}

.form_textarea:focus {
    border-color: #3E7BFA;
}

.form_select {
    width: 100%;
    background-color: var(--options-input-bg);
    color: var(--text-color-solid);
    border: 1px solid var(--border-color-invert);
    border-radius: 8px;
    padding: 10px;
    font-size: 0.9rem;
    outline: none;
    box-sizing: border-box;
    transition: border-color 0.2s;
    font-family: inherit;
    cursor: pointer;
}

.form_select:focus {
    border-color: #3E7BFA;
}

/* Inline toggle */
.inline_toggle {
    flex-direction: row;
    align-items: flex-start;
    gap: 12px;
}

.toggle_label {
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.toggle_label h4 {
    margin: 0;
    font-size: 0.85rem;
    font-weight: 600;
}

.toggle_label p {
    margin: 0;
    font-size: 0.75rem;
    opacity: 0.6;
    line-height: 1.3;
}

/* Switch styling */
.switch_container {
    position: relative;
    display: inline-block;
    width: 42px;
    height: 22px;
    margin: 0;
    flex-shrink: 0;
}

.switch_container input {
    opacity: 0;
    width: 0;
    height: 0;
}

.slider_switch {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #555;
    transition: .3s;
}

.slider_switch:before {
    position: absolute;
    content: "";
    height: 14px;
    width: 14px;
    left: 4px;
    bottom: 4px;
    background-color: white;
    transition: .3s;
}

input:checked + .slider_switch {
    background-color: #3E7BFA;
}

input:checked + .slider_switch:before {
    transform: translateX(20px);
}

.slider_switch.round {
    border-radius: 34px;
}

.slider_switch.round:before {
    border-radius: 50%;
}

/* Aspect ratio selector */
.aspect_ratio_selector {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 6px;
}

.ratio_card {
    background-color: var(--options-input-bg);
    border: 1px solid var(--border-color-invert);
    border-radius: 8px;
    padding: 8px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s ease;
}

.ratio_card:hover {
    background-color: var(--button-highlight-one);
    border-color: var(--text-color-solid);
}

.ratio_card.active {
    background-color: rgba(62, 123, 250, 0.12);
    border-color: #3E7BFA;
}

.ratio_preview {
    background-color: var(--text-color-solid);
    opacity: 0.3;
    border-radius: 2px;
    margin-bottom: 4px;
    transition: opacity 0.2s;
}

.ratio_card.active .ratio_preview {
    opacity: 0.8;
    background-color: #3E7BFA;
}

.preview_1_1 { width: 14px; height: 14px; }
.preview_16_9 { width: 20px; height: 11px; }
.preview_9_16 { width: 11px; height: 20px; }
.preview_4_3 { width: 18px; height: 13px; }
.preview_3_4 { width: 13px; height: 18px; }

.ratio_label {
    font-size: 0.7rem;
    font-weight: 500;
}

/* Generate button */
.btn_generate {
    width: 100%;
    background: linear-gradient(135deg, #FF416C, #FF4B2B);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 12px;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    margin-top: 10px;
    box-shadow: 0 4px 12px rgba(255, 65, 108, 0.25);
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
}

.btn_generate:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(255, 65, 108, 0.4);
    background: linear-gradient(135deg, #FF4B2B, #FF5E3A);
}

.btn_generate:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    box-shadow: none;
    background: #444;
}

/* Inline Spinner */
.spinner_inline {
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255, 255, 255, 0.2);
    border-top: 2px solid white;
    border-radius: 50%;
    animation: spin 0.8s infinite linear;
}

/* Right workspace panel */
.studio_workspace {
    flex: 1;
    margin-left: 20px;
    background-color: var(--options-input-bg);
    border: 1px solid var(--border-color-invert-extralight);
    border-radius: 12px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    position: relative;
    box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.1);
}

/* Empty Workspace State */
.workspace_empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 40px;
    max-width: 420px;
}

.gemini_logo_container {
    position: relative;
    width: 100px;
    height: 100px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 15px;
}

.gemini_glow {
    position: absolute;
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(138, 180, 248, 0.5) 0%, rgba(248, 138, 180, 0.3) 50%, transparent 100%);
    filter: blur(15px);
    animation: pulse 3s infinite alternate;
}

.gemini_symbol {
    font-size: 3rem;
    z-index: 1;
}

.workspace_empty h3 {
    font-size: 1.25rem;
    margin: 0 0 10px 0;
    font-weight: 600;
}

.workspace_empty p {
    font-size: 0.85rem;
    opacity: 0.7;
    line-height: 1.4;
    margin: 0 0 20px 0;
}

.disclaimer_card {
    background-color: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--border-color-invert);
    border-radius: 8px;
    padding: 10px 15px;
}

.disclaimer_card p {
    font-size: 0.75rem;
    margin: 0;
    line-height: 1.35;
    opacity: 0.8;
}

/* Loading State */
.workspace_loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 2;
    text-align: center;
    padding: 40px;
}

.loader_glow {
    position: absolute;
    width: 180px;
    height: 180px;
    background: radial-gradient(circle, rgba(62, 123, 250, 0.25) 0%, rgba(255, 65, 108, 0.15) 50%, transparent 100%);
    filter: blur(20px);
    animation: pulse 4s infinite alternate;
}

.loader_spinner {
    width: 44px;
    height: 44px;
    border: 3px solid var(--border-color-invert);
    border-top: 3px solid #3E7BFA;
    border-radius: 50%;
    animation: spin 1s infinite linear;
    margin-bottom: 20px;
    z-index: 1;
}

.loader_title {
    font-size: 1.15rem;
    font-weight: 600;
    margin: 0 0 6px 0;
    z-index: 1;
}

.loader_desc {
    font-size: 0.85rem;
    opacity: 0.7;
    margin: 0;
    max-width: 280px;
    z-index: 1;
}

/* Result State */
.workspace_result {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    padding: 20px;
    box-sizing: border-box;
}

.result_image_container {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    background-color: rgba(0, 0, 0, 0.2);
    border-radius: 8px;
    border: 1px solid var(--border-color-invert);
}

.result_image {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
    border-radius: 4px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.3);
}

.action_bar {
    display: flex;
    gap: 10px;
    margin-top: 15px;
}

.btn_action {
    flex: 1;
    background-color: var(--sidebar-color);
    border: 1px solid var(--border-color-invert);
    color: var(--text-color-solid);
    border-radius: 6px;
    padding: 10px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
}

.btn_action:hover {
    background-color: var(--button-highlight-one);
    border-color: var(--text-color-solid);
}

.btn_download {
    background-color: #3E7BFA;
    color: white;
    border: none;
}

.btn_download:hover {
    background-color: #2b66e3;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

@keyframes pulse {
    0% { transform: scale(0.9); opacity: 0.7; }
    100% { transform: scale(1.1); opacity: 1; }
}
</style>
