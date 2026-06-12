<template>
    <div class="ideogram_studio_container">
        <!-- Left Pane: Controls -->
        <div class="studio_controls">
            <div class="controls_header">
                <h2>Ideogram Studio</h2>
                <div class="mode_tabs">
                    <button 
                        class="mode_tab" 
                        :class="{ active: mode === 'cloud' }"
                        @click="setMode('cloud')"
                        :disabled="loading"
                    >
                        ☁️ Cloud API
                    </button>
                    <button 
                        class="mode_tab" 
                        :class="{ active: mode === 'local' }"
                        @click="setMode('local')"
                        :disabled="loading"
                    >
                        💻 Local (Offline)
                    </button>
                </div>
            </div>

            <!-- Cloud Mode Interface -->
            <div v-if="mode === 'cloud'" class="mode_content">
                <p class="studio_intro">
                    Generate high-fidelity text-heavy images using Ideogram's Cloud API.
                </p>

                <div v-if="!apiKey.trim()" class="api_warning_card">
                    <p>⚠️ <strong>Ideogram API Key is required.</strong> Please go to Settings to configure your API key first.</p>
                    <button @click="goToSettings" class="btn_settings_redirect">Go to Settings</button>
                </div>

                <div v-else>
                    <div class="form_group">
                        <label>Text Prompt</label>
                        <textarea 
                            v-model="prompt" 
                            placeholder="Describe the image you want to generate (e.g. A typographic poster reading 'Diffusion4Mac' in neon colors)..." 
                            class="form_textarea"
                            rows="4"
                            :disabled="loading"
                        ></textarea>
                    </div>

                    <div class="form_group">
                        <label>Magic Prompt Option</label>
                        <select v-model="cloudMagicPrompt" class="form_select" :disabled="loading">
                            <option value="AUTO">AUTO (Optimize if long)</option>
                            <option value="ON">ON (Always enhance)</option>
                            <option value="OFF">OFF (Keep raw prompt)</option>
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
                        @click="generateCloud" 
                        class="btn_generate" 
                        :disabled="loading || !prompt.trim()"
                    >
                        <span v-if="loading" class="spinner_inline"></span>
                        <span>{{ loading ? 'Generating...' : 'Generate with Cloud API' }}</span>
                    </button>
                </div>
            </div>

            <!-- Local Mode Interface -->
            <div v-else class="mode_content">
                <p class="studio_intro">
                    Run the quantized 9.3B parameter Ideogram 4.0 model locally on your Apple Silicon hardware.
                </p>

                <!-- Model Downloading State -->
                <div v-if="isDownloading" class="model_download_card">
                    <h3>Downloading Ideogram 4.0 Model</h3>
                    <p>Fetching quantized model weights. This might take a while.</p>
                    <div class="progress_container">
                        <div class="progress_bar" :style="{ width: downloadProgress + '%' }"></div>
                    </div>
                    <span class="progress_text">{{ downloadProgress }}% Complete</span>
                </div>

                <!-- Model Not Downloaded State -->
                <div v-else-if="!isDownloaded" class="model_download_card">
                    <h3>Local Model Required</h3>
                    <p>The quantized Ideogram 4.0 weights must be downloaded to enable offline generation.</p>
                    <button @click="downloadLocalModel" class="btn_download_model">
                        📥 Download Model weights
                    </button>
                </div>

                <!-- Model Ready / Control State -->
                <div v-else>
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

                    <div class="form_group">
                        <label>Inference Steps (Quality)</label>
                        <div class="slider_container">
                            <input 
                                type="range" 
                                min="10" 
                                max="100" 
                                v-model="localSteps" 
                                class="form_slider"
                                :disabled="loading"
                            />
                            <span class="slider_value">{{ localSteps }} steps</span>
                        </div>
                    </div>

                    <div class="form_group">
                        <label>Guidance Scale (Prompt Adherence)</label>
                        <div class="slider_container">
                            <input 
                                type="range" 
                                min="1.0" 
                                max="20.0" 
                                step="0.5"
                                v-model="localGuidance" 
                                class="form_slider"
                                :disabled="loading"
                            />
                            <span class="slider_value">{{ localGuidance }}</span>
                        </div>
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
                        @click="generateLocal" 
                        class="btn_generate" 
                        :disabled="loading || !prompt.trim()"
                    >
                        <span v-if="loading" class="spinner_inline"></span>
                        <span>{{ loading ? 'Generating...' : 'Generate Locally' }}</span>
                    </button>
                </div>
            </div>
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
                <div class="ideogram_logo_container">
                    <div class="ideogram_glow"></div>
                    <div class="ideogram_symbol">🎨</div>
                </div>
                <h3>Ideogram Studio</h3>
                <p>Select cloud or local mode, write a descriptive prompt, and generate beautiful images with crisp typographic rendering.</p>
            </div>
        </div>
    </div>
</template>

<script>
import Vue from 'vue';

const IdeogramStudio = {
    name: 'IdeogramStudio',
    props: {
        app: Object
    },
    data() {
        return {
            mode: "cloud", // cloud or local
            prompt: "",
            cloudMagicPrompt: "AUTO",
            selectedRatio: "1:1",
            localSteps: 48,
            localGuidance: 7.0,
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
            return this.app?.app_state?.app_data?.settings?.ideogram_api_key || "";
        },
        isDownloaded() {
            if (!this.app?.app_state?.downloaded_assets) return false;
            const model = this.app.app_state.downloaded_assets['ideogram_4_nf4'] || 
                          (this.app.assets_manager && this.app.assets_manager.local_assets && this.app.assets_manager.local_assets['ideogram_4_nf4']);
            return model && model.status === 'done';
        },
        isDownloading() {
            if (!this.app?.app_state?.downloading) return false;
            const model = this.app.app_state.downloading['ideogram_4_nf4'];
            return model && model.status === 'downloading';
        },
        downloadProgress() {
            if (!this.app?.app_state?.downloading) return 0;
            const model = this.app.app_state.downloading['ideogram_4_nf4'];
            return model ? (model.progress || 0) : 0;
        }
    },
    methods: {
        setMode(m) {
            this.mode = m;
        },
        goToSettings() {
            this.app.functions.switch_page("Settings");
        },
        selectRatio(ratioVal) {
            if (!this.loading) {
                this.selectedRatio = ratioVal;
            }
        },
        downloadLocalModel() {
            const asset_details = {
                id: "ideogram_4_nf4",
                title: "Ideogram 4.0 (Offline/Local)",
                description: "High-fidelity text rendering and composition model with 9.3B parameters, quantized in NF4 for local systems.",
                md5: "ideogram_4_nf4_dummy",
                filename: "Ideogram-4.0-NF4",
                model_meta_data: {
                    sd_type: "Ideogram 4",
                    float_type: "nf4"
                }
            };
            if (this.app?.assets_manager) {
                this.app.assets_manager.download_asset(asset_details);
            }
        },
        async generateCloud() {
            if (!this.prompt.trim()) {
                this.app.show_toast("Please enter a prompt");
                return;
            }
            if (!this.apiKey.trim()) {
                this.app.show_toast("Ideogram API Key is not set in Settings");
                return;
            }

            this.loading = true;
            this.imageSrc = "";
            this.savedImagePath = "";
            this.loadingTitle = "Generating cloud image...";
            this.loadingDesc = "Requesting image generation from Ideogram API";

            try {
                const url = "https://api.ideogram.ai/v1/ideogram-v4/generate";
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Api-Key': this.apiKey.trim(),
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        text_prompt: this.prompt,
                        aspect_ratio: this.selectedRatio.replace(':', 'x'),
                        magic_prompt_option: this.cloudMagicPrompt
                    })
                });

                if (!response.ok) {
                    const errText = await response.text();
                    throw new Error(`API error ${response.status}: ${errText}`);
                }

                const respJson = await response.json();
                if (respJson.data && respJson.data[0] && respJson.data[0].url) {
                    const imageUrl = respJson.data[0].url;
                    this.loadingTitle = "Saving image...";
                    this.loadingDesc = "Downloading the generated image to local disk";
                    const savedPath = await this.downloadAndSaveImage(imageUrl);
                    if (savedPath) {
                        this.savedImagePath = savedPath;
                        this.imageSrc = 'file://' + savedPath;
                        this.app.show_toast("Image generated successfully!");
                    } else {
                        throw new Error("Failed to save image locally");
                    }
                } else {
                    throw new Error("No image URL returned in response");
                }
            } catch (err) {
                console.error(err);
                this.app.show_toast("Generation failed: " + err.message);
            } finally {
                this.loading = false;
            }
        },
        downloadAndSaveImage(url) {
            return fetch(url)
                .then(res => {
                    if (!res.ok) {
                        throw new Error(`HTTP error! status: ${res.status}`);
                    }
                    return res.blob();
                })
                .then(blob => {
                    return new Promise((resolve, reject) => {
                        const reader = new FileReader();
                        reader.onloadend = () => {
                            try {
                                const b64Data = reader.result;
                                const savedPath = window.ipcRenderer.sendSync('save_b64_image', b64Data, false);
                                resolve(savedPath);
                            } catch (e) {
                                reject(e);
                            }
                        };
                        reader.onerror = () => reject(reader.error || new Error("FileReader error"));
                        reader.readAsDataURL(blob);
                    });
                });
        },
        generateLocal() {
            if (!this.prompt.trim()) {
                this.app.show_toast("Please enter a prompt");
                return;
            }

            this.loading = true;
            this.imageSrc = "";
            this.savedImagePath = "";
            this.loadingTitle = "Initializing weights...";
            this.loadingDesc = "Loading Ideogram 4.0 model locally";

            // Resolve width and height from aspect ratio
            let width = 1024;
            let height = 1024;
            if (this.selectedRatio === "16:9") {
                width = 1024;
                height = 576;
            } else if (this.selectedRatio === "9:16") {
                width = 576;
                height = 1024;
            } else if (this.selectedRatio === "4:3") {
                width = 1024;
                height = 768;
            } else if (this.selectedRatio === "3:4") {
                width = 768;
                height = 1024;
            }

            const prompt_params = {
                prompt: this.prompt,
                seed: -1, // Random
                ddim_steps: Number(this.localSteps),
                img_width: width,
                img_height: height,
                guidance_scale: Number(this.localGuidance),
                raw_form_options: {
                    model_selection: "Ideogram Local",
                    seed: -1
                }
            };

            const self = this;
            const callbacks = {
                on_img(img) {
                    self.loading = false;
                    if (img && img.generated_img_path) {
                        self.savedImagePath = img.generated_img_path;
                        self.imageSrc = 'file://' + img.generated_img_path;
                        self.app.show_toast("Image generated successfully!");
                    } else {
                        self.app.show_toast("Failed to generate image.");
                    }
                },
                on_progress(p, iter_time) {
                    self.loadingTitle = `Generating image locally...`;
                    self.loadingDesc = `Progress: ${p}% complete ${iter_time ? '(' + (iter_time / 1000).toFixed(1) + 's/it)' : ''}`;
                },
                on_err(err) {
                    self.loading = false;
                    self.app.show_toast("Local generation failed: " + err);
                }
            };

            this.app.stable_diffusion.text_to_img(prompt_params, callbacks, 'ideogram_local');
        },
        useInTxt2Img() {
            if (!this.savedImagePath) return;
            
            this.app.functions.switch_page("Txt2Img");
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
                this.app.functions.send_to_img2img(this.savedImagePath, { prompt: this.prompt });
            } else {
                this.app.functions.switch_page("Img2Img");
                Vue.nextTick(() => {
                    const img2img = this.app.$refs.router.$refs['Img2Img'];
                    if (img2img && img2img[0] && img2img[0].$refs.sd_applet) {
                        Vue.set(img2img[0].$refs.sd_applet.sd_options, 'input_img', this.savedImagePath);
                        if (this.prompt) {
                            Vue.set(img2img[0].$refs.sd_applet.sd_options, 'prompt', this.prompt);
                        }
                    }
                });
            }
        },
        downloadImage() {
            if (!this.savedImagePath) return;
            
            const suggested_fname = "Ideogram_" + Date.now();
            const out_path = window.ipcRenderer.sendSync('save_dialog', suggested_fname);
            if (!out_path) return;
            
            const org_path = this.savedImagePath;
            window.ipcRenderer.sendSync('save_file', org_path + "||" + out_path);
            this.app.show_toast("Image saved successfully");
        }
    }
};

IdeogramStudio.title = "Ideogram Studio";
IdeogramStudio.icon = "magic";
IdeogramStudio.description = "Offline local generation and Cloud API powered by Ideogram";
IdeogramStudio.img_icon = require("../assets/imgs/page_icon_imgs/default.png");
IdeogramStudio.home_category = "main";
IdeogramStudio.sidebar_show = "always";

export default IdeogramStudio;
</script>

<style scoped>
.ideogram_studio_container {
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
    gap: 12px;
    margin-bottom: 15px;
}

.controls_header h2 {
    font-size: 1.5rem;
    margin: 0;
    font-weight: 600;
}

.mode_tabs {
    display: flex;
    background-color: var(--options-input-bg);
    border-radius: 8px;
    padding: 4px;
    border: 1px solid var(--border-color-invert);
}

.mode_tab {
    flex: 1;
    background: transparent;
    border: none;
    padding: 8px;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-color-solid);
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
}

.mode_tab.active {
    background-color: var(--button-highlight-one);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.mode_tab:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.mode_content {
    display: flex;
    flex-direction: column;
    flex: 1;
}

.studio_intro {
    font-size: 0.85rem;
    opacity: 0.75;
    line-height: 1.4;
    margin: 0 0 20px 0;
}

.api_warning_card {
    background-color: rgba(255, 65, 108, 0.1);
    border: 1px solid rgba(255, 65, 108, 0.2);
    border-radius: 8px;
    padding: 15px;
    text-align: center;
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.api_warning_card p {
    font-size: 0.85rem;
    margin: 0;
    line-height: 1.4;
    color: var(--text-color-solid);
}

.btn_settings_redirect {
    background-color: #FF416C;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px;
    font-weight: 600;
    font-size: 0.85rem;
    cursor: pointer;
    transition: opacity 0.2s;
}

.btn_settings_redirect:hover {
    opacity: 0.9;
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

/* Slider */
.slider_container {
    display: flex;
    align-items: center;
    gap: 12px;
}

.form_slider {
    flex: 1;
    cursor: pointer;
}

.slider_value {
    font-size: 0.85rem;
    font-weight: 600;
    min-width: 60px;
}

/* Model download card */
.model_download_card {
    background-color: var(--options-input-bg);
    border: 1px solid var(--border-color-invert);
    border-radius: 10px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    margin-top: 10px;
}

.model_download_card h3 {
    margin: 0 0 8px 0;
    font-size: 1.05rem;
    font-weight: 600;
}

.model_download_card p {
    font-size: 0.8rem;
    opacity: 0.7;
    margin: 0 0 15px 0;
    line-height: 1.35;
}

.btn_download_model {
    background-color: #3E7BFA;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 15px;
    font-weight: 600;
    cursor: pointer;
    width: 100%;
}

.progress_container {
    background-color: rgba(255,255,255,0.06);
    border-radius: 20px;
    height: 8px;
    overflow: hidden;
    margin-bottom: 8px;
    border: 1px solid var(--border-color-invert);
}

.progress_bar {
    background: linear-gradient(90deg, #3E7BFA, #FF416C);
    height: 100%;
    border-radius: 20px;
    transition: width 0.3s ease;
}

.progress_text {
    font-size: 0.75rem;
    font-weight: 600;
    opacity: 0.8;
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

.ideogram_logo_container {
    position: relative;
    width: 100px;
    height: 100px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 15px;
}

.ideogram_glow {
    position: absolute;
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(138, 180, 248, 0.5) 0%, rgba(248, 138, 180, 0.3) 50%, transparent 100%);
    filter: blur(15px);
    animation: pulse 3s infinite alternate;
}

.ideogram_symbol {
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
    margin: 0;
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
