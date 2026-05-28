<template>
    <div class="main_container">
        <h1>Settings</h1>
        <p class="subtitle">Configure application settings, API keys, and model preferences.</p>
        <br>

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
        </div>
    </div>
</template>

<script>
const Settings = {
    name: 'Settings',
    props: { app: Object },
    components: {},
    mounted() {},
    data() {
        return {};
    },
    methods: {},
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
</style>