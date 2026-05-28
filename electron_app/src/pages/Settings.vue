<template>
    <div style="width:100%; height:100%; overflow: auto; padding: 20px;">
        
     <h1>Settings</h1>
        <br>
       <h2>General Settings</h2>
        <br>
        <div class="setting_box">
        <div class="settings_left">
        <h3>Notification sound</h3>
        <p>To play a notification sound when generation of an image is completed</p>
        </div>
        
        <div style="float:right;margin-right: 9px;align-self: center;" >
            <label class="switch">
                <input type="checkbox" v-model="app.app_state.app_data.settings.notification_sound" checked>
                <span class="toggle round"></span>
            </label>
        </div>
        </div>
        <hr>

        <div class="setting_box">
            <div class="settings_left">
                <h3>Hugging Face Token</h3>
                <p>Enter your Hugging Face User Access Token (read permission) to download gated models like FLUX.2 [klein].</p>
                <input 
                    type="password" 
                    v-model="app.app_state.app_data.settings.hf_token" 
                    placeholder="hf_..." 
                    class="form-control" 
                    style="max-width: 400px; margin-top: 8px;"
                />
            </div>
        </div>
        <hr>

        <div class="setting_box">
            <div class="settings_left">
                <h3>Preferred Gemma Model</h3>
                <p>Choose the default Gemma model used for AI Assist rewrite and image prompt description.</p>
                <select 
                    v-model="app.app_state.app_data.settings.gemma_preferred_model" 
                    class="form-control" 
                    style="max-width: 400px; margin-top: 8px; background-color: var(--input-bg-color, #2b2b2b); color: var(--text-color, #ffffff); border: 1px solid rgba(255,255,255,0.15); border-radius: 4px; padding: 6px 12px; font-size: 0.9rem; outline: none; cursor: pointer;"
                >
                    <option value="gemma4:e4b" style="background-color: #1e1e1e;">Gemma 4 [e4b] (Recommended - 4B parameters)</option>
                    <option value="gemma4:e2b" style="background-color: #1e1e1e;">Gemma 4 [e2b] (Lighter - 2B parameters)</option>
                </select>
            </div>
        </div>
        <hr>

        <div class="setting_box">
            <div class="settings_left">
                <h3>Allow LoRA Stacking</h3>
                <p>Allow enabling more than one LoRA simultaneously. <span style="color: #ff9800; font-weight: 500;">Caution: Enabling multiple LoRAs simultaneously can degrade image quality or cause conflicts if they are not designed to work together.</span></p>
            </div>
            <div style="float:right;margin-right: 9px;align-self: center;" >
                <label class="switch">
                    <input type="checkbox" v-model="app.app_state.app_data.settings.lora_stacking">
                    <span class="toggle round"></span>
                </label>
            </div>
        </div>
        <hr>

        <div class="setting_box">
            <div class="settings_left">
                <h3>Save Metadata to EXIF</h3>
                <p>Saves all generation metadata (prompt, seed, model, and active LoRAs) as JSON directly inside the exported image's EXIF user description tag.</p>
            </div>
            <div style="float:right;margin-right: 9px;align-self: center;" >
                <label class="switch">
                    <input type="checkbox" v-model="app.app_state.app_data.settings.save_exif_meta">
                    <span class="toggle round"></span>
                </label>
            </div>
        </div>
        <hr>


    </div>
</template>
<script>
const Settings ={
    name: 'Settings',
    props: {app:Object, },
    components: {},
    mounted() {

    },
    data() {
        return {};
    },
    methods: {

    },
}

export default Settings;
Settings.title = "Settings"
Settings.icon = "tools"
Settings.img_icon = require("../assets/imgs/page_icon_imgs/settings.png")
Settings.home_category = "pages"
Settings.sidebar_show = "always"

// add this to the always_on_pages to the PagesRouter

</script>
<style>
</style>
<style scoped>

.setting_box{
    display: flex;
    flex-direction: row;
}

.settings_left{
    flex: 1 1 auto;
}

.switch {
  position: relative;
  display: inline-block;
  width: 60px;
  height: 30px;
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
  background-color: #ccc;
  -webkit-transition: .4s;
  transition: .4s;
}

.toggle:before {
  position: absolute;
  content: "";
  height: 22px;
  width: 23px;
  left: 5px;
  bottom: 4px;
  background-color: white;
  -webkit-transition: .4s;
  transition: .4s;
}

input:checked + .toggle {
  background-color: #3E7BFA;
}


input:checked + .toggle:before {
  transform: translateX(27px);
}

.toggle.round {
  border-radius: 34px;
}

.toggle.round:before {
  border-radius: 50%;
}



</style>