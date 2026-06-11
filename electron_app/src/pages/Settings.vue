<template>
    <div class="main_container">
        <h1>Settings</h1>
        <p class="subtitle">Configure application settings, API keys, and model preferences.</p>
        <br>

        <!-- System Auto-Optimizer Banner -->
        <div class="optimizer_panel" v-if="system_info">
            <div class="optimizer_left">
                <div class="optimizer_header">
                    <span class="optimizer_title_icon">⚡</span>
                    <h2>System Auto-Optimizer</h2>
                    <span :class="['profile_pill', current_profile.toLowerCase().replace('-', '_') + '_profile']">
                        {{ current_profile }}
                    </span>
                </div>
                <p class="optimizer_description" v-html="system_description"></p>
            </div>
            <div class="optimizer_actions">
                <button class="opt_btn speed_btn" @click="apply_speed_profile">
                    <span class="btn_icon">⚡</span>
                    <div class="btn_text_group">
                        <span class="btn_title">Optimize for Speed</span>
                        <span class="btn_subtitle">Fast 4B model & low latency</span>
                    </div>
                </button>
                <button class="opt_btn quality_btn" @click="apply_quality_profile">
                    <span class="btn_icon">✨</span>
                    <div class="btn_text_group">
                        <span class="btn_title">Optimize for Quality</span>
                        <span class="btn_subtitle">Detailed 9B model & high fidelity</span>
                    </div>
                </button>
            </div>
        </div>
        <br v-if="system_info">

        <div class="settings_grid">
            <!-- Card 1: Notification Sound -->
            <div class="setting_card">
                <div class="card_hero hero_blue">
                    <span class="hero_icon">🔔</span>
                </div>
                <div class="card_body">
                    <h3>Notification Sound</h3>
                    <p>Play a sound notification when image generation is completed.</p>
                </div>
                <div class="card_footer">
                    <label class="switch">
                        <input type="checkbox" v-model="app.app_state.app_data.settings.notification_sound" checked>
                        <span class="toggle round"></span>
                    </label>
                </div>
            </div>

            <!-- Card 2: Hugging Face Token -->
            <div class="setting_card">
                <div class="card_hero hero_cyan">
                    <span class="hero_icon">🔑</span>
                </div>
                <div class="card_body">
                    <h3>Hugging Face Token</h3>
                    <p>Access Token (read permission) to download gated models like FLUX.2 [klein].</p>
                </div>
                <div class="card_footer">
                    <input 
                        type="password" 
                        v-model="app.app_state.app_data.settings.hf_token" 
                        placeholder="hf_..." 
                        class="form_input" 
                    />
                </div>
            </div>

            <!-- Card 3: Preferred Gemma Model -->
            <div class="setting_card">
                <div class="card_hero hero_purple">
                    <span class="hero_icon">🤖</span>
                </div>
                <div class="card_body">
                    <h3>Preferred Gemma Model</h3>
                    <p>Choose the model used for AI Assist rewrite and image prompt description.</p>
                </div>
                <div class="card_footer">
                    <select 
                        v-model="app.app_state.app_data.settings.gemma_preferred_model" 
                        class="form_input select_input"
                    >
                        <option value="gemma4:e4b">Gemma 4 [e4b] (4B)</option>
                        <option value="gemma4:e2b">Gemma 4 [e2b] (2B)</option>
                    </select>
                </div>
            </div>

            <!-- Card 4: Allow LoRA Stacking -->
            <div class="setting_card">
                <div class="card_hero hero_orange">
                    <span class="hero_icon">🥞</span>
                </div>
                <div class="card_body">
                    <h3>Allow LoRA Stacking</h3>
                    <p>Enable stacking multiple LoRAs. Caution: may degrade quality if they conflict.</p>
                </div>
                <div class="card_footer">
                    <label class="switch">
                        <input type="checkbox" v-model="app.app_state.app_data.settings.lora_stacking">
                        <span class="toggle round"></span>
                    </label>
                </div>
            </div>

            <!-- Card 5: Save Metadata to EXIF -->
            <div class="setting_card">
                <div class="card_hero hero_green">
                    <span class="hero_icon">🏷️</span>
                </div>
                <div class="card_body">
                    <h3>Save Metadata to EXIF</h3>
                    <p>Save prompt, seed, model, and active LoRAs directly inside the image's EXIF data.</p>
                </div>
                <div class="card_footer">
                    <label class="switch">
                        <input type="checkbox" v-model="app.app_state.app_data.settings.save_exif_meta">
                        <span class="toggle round"></span>
                    </label>
                </div>
            </div>

            <!-- Card 6: Gemini API Key -->
            <div class="setting_card">
                <div class="card_hero hero_red">
                    <span class="hero_icon">🔑</span>
                </div>
                <div class="card_body">
                    <h3>Gemini API Key</h3>
                    <p>Enter your Gemini API Key to enable Gemini Studio cloud generation (Imagen 3).</p>
                </div>
                <div class="card_footer">
                    <input 
                        type="password" 
                        v-model="app.app_state.app_data.settings.gemini_api_key" 
                        placeholder="AIzaSy..." 
                        class="form_input" 
                    />
                </div>
            </div>

            <!-- Card 7: Preferred FLUX.2 [klein] Size -->
            <div class="setting_card">
                <div class="card_hero hero_blue">
                    <span class="hero_icon">📏</span>
                </div>
                <div class="card_body">
                    <h3>Preferred FLUX.2 [klein] Size</h3>
                    <p>Choose between the 9B model or the lightweight 4B model (recommended for faster generation on low-end systems).</p>
                </div>
                <div class="card_footer">
                    <select 
                        v-model="app.app_state.app_data.settings.flux_klein_size" 
                        class="form_input select_input"
                    >
                        <option value="9B">9B (Default / High Detail)</option>
                        <option value="4B">4B (Lightweight / Fast)</option>
                    </select>
                </div>
            </div>

            <!-- Card 8: Sequential CPU Offloading -->
            <div class="setting_card">
                <div class="card_hero hero_orange">
                    <span class="hero_icon">💾</span>
                </div>
                <div class="card_body">
                    <h3>Sequential CPU Offloading</h3>
                    <p>Offloads layers to CPU one by one. Drastically reduces memory usage (down to ~4GB) but slows down generation.</p>
                </div>
                <div class="card_footer">
                    <label class="switch">
                        <input type="checkbox" v-model="app.app_state.app_data.settings.flux_sequential_cpu_offload">
                        <span class="toggle round"></span>
                    </label>
                </div>
            </div>

            <!-- Card 9: VAE Slicing -->
            <div class="setting_card">
                <div class="card_hero hero_cyan">
                    <span class="hero_icon">🍰</span>
                </div>
                <div class="card_body">
                    <h3>VAE Slicing</h3>
                    <p>Decodes images in slices. Highly recommended for 8GB/16GB Macs to prevent memory crashes during decoding.</p>
                </div>
                <div class="card_footer">
                    <label class="switch">
                        <input type="checkbox" v-model="app.app_state.app_data.settings.flux_vae_slicing">
                        <span class="toggle round"></span>
                    </label>
                </div>
            </div>

            <!-- Card 10: Attention Slicing -->
            <div class="setting_card">
                <div class="card_hero hero_green">
                    <span class="hero_icon">⚡</span>
                </div>
                <div class="card_body">
                    <h3>Attention Slicing</h3>
                    <p>Slices attention computation to reduce memory usage during generation at a small speed cost.</p>
                </div>
                <div class="card_footer">
                    <label class="switch">
                        <input type="checkbox" v-model="app.app_state.app_data.settings.flux_attention_slicing">
                        <span class="toggle round"></span>
                    </label>
                </div>
            </div>

            <!-- Card 11: VAE Tiling -->
            <div class="setting_card">
                <div class="card_hero hero_purple">
                    <span class="hero_icon">🧱</span>
                </div>
                <div class="card_body">
                    <h3>VAE Tiling</h3>
                    <p>Processes VAE decoding in overlapping tiles. Saves memory when generating larger images.</p>
                </div>
                <div class="card_footer">
                    <label class="switch">
                        <input type="checkbox" v-model="app.app_state.app_data.settings.flux_vae_tiling">
                        <span class="toggle round"></span>
                    </label>
                </div>
            </div>

            <!-- Card 12: FP8 (8-bit) Quantization -->
            <div class="setting_card">
                <div class="card_hero hero_blue">
                    <span class="hero_icon">⚖️</span>
                </div>
                <div class="card_body">
                    <h3>FP8 (8-bit) Quantization</h3>
                    <p>Loads Flux model weights in FP8 format. Drastically reduces memory footprint by up to 10GB, allowing large models to run smoothly on lower-RAM Macs.</p>
                </div>
                <div class="card_footer">
                    <label class="switch">
                        <input type="checkbox" v-model="app.app_state.app_data.settings.flux_fp8">
                        <span class="toggle round"></span>
                    </label>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
const Settings = {
    name: 'Settings',
    props: { app: Object },
    components: {},
    mounted() {
        try {
            this.system_info = window.ipcRenderer.sendSync('get_system_info');
        } catch (err) {
            console.error("Failed to load system info", err);
        }
    },
    data() {
        return {
            system_info: null
        };
    },
    computed: {
        current_profile() {
            if (!this.system_info || !this.app || !this.app.app_state || !this.app.app_state.app_data) return 'Custom';
            const settings = this.app.app_state.app_data.settings;
            const ram = this.system_info.total_ram_gb;

            const speed_match = 
                settings.flux_klein_size === '4B' &&
                settings.flux_sequential_cpu_offload === (ram <= 8.5) &&
                settings.flux_vae_slicing === true &&
                settings.flux_vae_tiling === false &&
                settings.flux_attention_slicing === (ram <= 8.5) &&
                settings.flux_fp8 === (ram <= 16.5);

            const quality_match = 
                settings.flux_klein_size === '9B' &&
                settings.flux_sequential_cpu_offload === (ram <= 16.5) &&
                settings.flux_vae_slicing === true &&
                settings.flux_vae_tiling === (ram <= 8.5) &&
                settings.flux_attention_slicing === (ram <= 16.5) &&
                settings.flux_fp8 === (ram <= 16.5);

            if (speed_match) return 'Speed-Optimized';
            if (quality_match) return 'Quality-Optimized';
            return 'Custom';
        },
        system_description() {
            if (!this.system_info) return 'Loading system specifications...';
            const model = this.system_info.cpu_model;
            const ram = this.system_info.total_ram_gb;
            
            let desc = `Detected <strong>${model}</strong> with <strong>${ram} GB RAM</strong>. `;
            
            if (ram <= 8.5) {
                desc += "This is a low-memory system. We highly recommend the <strong>Speed-Optimized</strong> profile to ensure stable image generation using the lightweight 4B model.";
            } else if (ram <= 16.5) {
                desc += "Your system has a solid memory capacity. The <strong>Speed-Optimized</strong> profile will generate images in seconds, while the <strong>Quality-Optimized</strong> profile will deliver maximum detail with moderate offloading.";
            } else {
                desc += "You have a high-memory system! You can run both Speed and Quality profiles fully in unified memory with sequential offloading disabled for maximum performance.";
            }
            return desc;
        }
    },
    methods: {
        apply_speed_profile() {
            if (!this.system_info || !this.app || !this.app.app_state || !this.app.app_state.app_data) return;
            const ram = this.system_info.total_ram_gb;
            const settings = this.app.app_state.app_data.settings;

            settings.flux_klein_size = "4B";
            settings.flux_sequential_cpu_offload = ram <= 8.5;
            settings.flux_vae_slicing = true;
            settings.flux_vae_tiling = false;
            settings.flux_attention_slicing = ram <= 8.5;
            settings.flux_fp8 = ram <= 16.5;

            this.app.show_toast("Optimized for Speed! ⚡");
        },
        apply_quality_profile() {
            if (!this.system_info || !this.app || !this.app.app_state || !this.app.app_state.app_data) return;
            const ram = this.system_info.total_ram_gb;
            const settings = this.app.app_state.app_data.settings;

            settings.flux_klein_size = "9B";
            settings.flux_sequential_cpu_offload = ram <= 16.5;
            settings.flux_vae_slicing = true;
            settings.flux_vae_tiling = ram <= 8.5;
            settings.flux_attention_slicing = ram <= 16.5;
            settings.flux_fp8 = ram <= 16.5;

            this.app.show_toast("Optimized for Quality! ✨");
        }
    }
}

export default Settings;
Settings.title = "Settings"
Settings.icon = "tools"
Settings.img_icon = require("../assets/imgs/page_icon_imgs/settings.png")
Settings.home_category = "pages"
Settings.sidebar_show = "always"
</script>

<style scoped>
.main_container {
    padding: 20px;
    width: 100%;
    height: 100%;
    overflow: auto;
    box-sizing: border-box;
}

.subtitle {
    opacity: 0.7;
    margin-top: -10px;
    font-size: 0.95rem;
}

.settings_grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 20px;
    margin-top: 15px;
}

.setting_card {
    background-color: var(--sidebar-color, #1e1e1e);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    height: 300px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.setting_card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
    border-color: rgba(255, 255, 255, 0.15);
}

/* Card hero header */
.card_hero {
    height: 90px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
}

.hero_icon {
    font-size: 2.3rem;
}

/* Gradient themes */
.hero_blue {
    background: linear-gradient(135deg, #3a7bd5, #3a6073);
}

.hero_cyan {
    background: linear-gradient(135deg, #02aab0, #00cdac);
}

.hero_purple {
    background: linear-gradient(135deg, #8a2387, #e94057);
}

.hero_orange {
    background: linear-gradient(135deg, #f12711, #f5af19);
}

.hero_green {
    background: linear-gradient(135deg, #11998e, #38ef7d);
}

.hero_red {
    background: linear-gradient(135deg, #FF416C, #FF4B2B);
}

/* Card body text */
.card_body {
    padding: 15px;
    flex: 1;
}

.card_body h3 {
    font-size: 1.05rem;
    font-weight: 600;
    margin: 0 0 6px 0;
    color: var(--text-color, #ffffff);
}

.card_body p {
    font-size: 0.85rem;
    line-height: 1.4;
    opacity: 0.7;
    margin: 0;
}

/* Card footer inputs */
.card_footer {
    padding: 12px 15px 15px 15px;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
    display: flex;
    align-items: center;
    justify-content: flex-end;
}

/* Controls */
.form_input {
    width: 100%;
    background-color: var(--input-bg-color, #2b2b2b);
    color: var(--text-color, #ffffff);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 0.9rem;
    outline: none;
    box-sizing: border-box;
}

.select_input {
    cursor: pointer;
}

.select_input option {
    background-color: #1e1e1e;
    color: #ffffff;
}

/* Switch Styles */
.switch {
  position: relative;
  display: inline-block;
  width: 54px;
  height: 28px;
}

.switch input { 
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #444;
  transition: .4s;
}

.toggle:before {
  position: absolute;
  content: "";
  height: 20px;
  width: 20px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  transition: .4s;
}

input:checked + .toggle {
  background-color: #3E7BFA;
}

input:checked + .toggle:before {
  transform: translateX(26px);
}

.toggle.round {
  border-radius: 34px;
}

.toggle.round:before {
  border-radius: 50%;
}

/* Auto-Optimizer Panel Styles */
.optimizer_panel {
    background: linear-gradient(135deg, rgba(30, 30, 32, 0.7) 0%, rgba(20, 20, 22, 0.8) 100%);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 30px;
    margin-bottom: 10px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
    position: relative;
    overflow: hidden;
}

/* Add a subtle top-lighting border effect for glassmorphism */
.optimizer_panel::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.15), transparent);
}

.optimizer_left {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.optimizer_header {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}

.optimizer_title_icon {
    font-size: 1.8rem;
}

.optimizer_header h2 {
    font-size: 1.4rem;
    font-weight: 700;
    margin: 0;
    color: #ffffff;
    background: linear-gradient(90deg, #ffffff, #dcdcdc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.profile_pill {
    font-size: 0.75rem;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 20px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.speed_optimized_profile {
    background-color: rgba(62, 123, 250, 0.15);
    color: #4da3ff;
    border-color: rgba(62, 123, 250, 0.3);
}

.quality_optimized_profile {
    background-color: rgba(233, 64, 87, 0.15);
    color: #ff6b8b;
    border-color: rgba(233, 64, 87, 0.3);
}

.custom_profile {
    background-color: rgba(255, 255, 255, 0.08);
    color: rgba(255, 255, 255, 0.7);
}

.optimizer_description {
    font-size: 0.9rem;
    line-height: 1.5;
    color: rgba(255, 255, 255, 0.8) !important;
    margin: 0;
}

.optimizer_description strong {
    color: #ffffff;
    font-weight: 600;
}

.optimizer_actions {
    display: flex;
    flex-direction: column;
    gap: 12px;
    min-width: 260px;
}

.opt_btn {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 12px 18px;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: rgba(255, 255, 255, 0.03);
    color: #ffffff;
    cursor: pointer;
    text-align: left;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

.opt_btn::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(120deg, transparent, rgba(255, 255, 255, 0.05), transparent);
    transform: translateX(-100%);
}

.opt_btn:hover::after {
    transform: translateX(100%);
    transition: transform 0.6s ease;
}

.opt_btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
    border-color: rgba(255, 255, 255, 0.2);
}

.speed_btn:hover {
    background: linear-gradient(135deg, rgba(58, 123, 213, 0.15) 0%, rgba(58, 96, 115, 0.15) 100%);
    border-color: rgba(58, 123, 213, 0.4);
}

.quality_btn:hover {
    background: linear-gradient(135deg, rgba(233, 64, 87, 0.15) 0%, rgba(138, 35, 135, 0.15) 100%);
    border-color: rgba(233, 64, 87, 0.4);
}

.btn_icon {
    font-size: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
}

.btn_text_group {
    display: flex;
    flex-direction: column;
}

.btn_title {
    font-weight: 600;
    font-size: 0.95rem;
}

.btn_subtitle {
    font-size: 0.75rem;
    opacity: 0.6;
    margin-top: 2px;
}

@media (max-width: 768px) {
    .optimizer_panel {
        flex-direction: column;
        align-items: stretch;
        padding: 20px;
        gap: 20px;
    }
    
    .optimizer_actions {
        min-width: 100%;
    }
}

@media (prefers-color-scheme: light) {
    .optimizer_panel {
        background: linear-gradient(135deg, rgba(245, 247, 250, 0.8) 0%, rgba(230, 235, 245, 0.9) 100%);
        border: 1px solid rgba(0, 0, 0, 0.08);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
    }
    .optimizer_panel::before {
        background: linear-gradient(90deg, transparent, rgba(0, 0, 0, 0.05), transparent);
    }
    .optimizer_header h2 {
        background: linear-gradient(90deg, #1e1e1e, #555555);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .optimizer_description {
        color: rgba(0, 0, 0, 0.75) !important;
    }
    .optimizer_description strong {
        color: #000000;
    }
    .opt_btn {
        background: rgba(0, 0, 0, 0.02);
        border: 1px solid rgba(0, 0, 0, 0.08);
        color: #333333;
    }
    .opt_btn:hover {
        border-color: rgba(0, 0, 0, 0.15);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
    }
    .speed_btn:hover {
        background: linear-gradient(135deg, rgba(58, 123, 213, 0.08) 0%, rgba(58, 96, 115, 0.08) 100%);
        border-color: rgba(58, 123, 213, 0.25);
        color: #1a5ac7;
    }
    .quality_btn:hover {
        background: linear-gradient(135deg, rgba(233, 64, 87, 0.08) 0%, rgba(138, 35, 135, 0.08) 100%);
        border-color: rgba(233, 64, 87, 0.25);
        color: #c71e43;
    }
    .custom_profile {
        background-color: rgba(0, 0, 0, 0.05);
        color: rgba(0, 0, 0, 0.6);
        border-color: rgba(0, 0, 0, 0.1);
    }
}
</style>