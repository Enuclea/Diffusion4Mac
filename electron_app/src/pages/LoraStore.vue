<template>
    <div class="main_container">
        <h1>LoRA Store</h1>
        <p class="subtitle">Download and toggle custom LoRA layers to enhance your image generations. Only one LoRA can be active per model family at a time by default, or enable stacking in Settings.</p>
        <br>

        <h2>FLUX.1-schnell Enhancements</h2>
        <div class="icon_container">
            <div v-for="lora in active_schnell_loras" :key="lora.id" class="model_card">
                <div class="model_card_image" v-bind:style="{ 'background-image': `url('${lora.img_url}')` }"></div>
                <div class="card_desc">
                    <div class="card_text">
                        <h2>{{ lora.title }}</h2>
                        <p>{{ lora.description }}</p>
                        <p style="zoom:0.75; opacity: 0.6; margin-top: 4px;">Designed for FLUX.1-schnell</p>
                        <p v-if="lora.keyword" style="zoom:0.85; opacity: 0.9; margin-top: 4px; font-weight: 500;">Keyword: <span style="color: #3E7BFA;">{{ lora.keyword }}</span></p>
                    </div>

                    <div class="lora_action_area">
                        <!-- If downloaded, show toggle switch -->
                        <div v-if="is_downloaded(lora.id)" class="toggle_container">
                            <span class="status_label" :class="{ active: is_enabled(lora.id) }">
                                {{ is_enabled(lora.id) ? 'Active' : 'Inactive' }}
                            </span>
                            <label class="switch">
                                <input type="checkbox" :checked="is_enabled(lora.id)" @change="toggleLora(lora.id, 'flux_schnell')">
                                <span class="toggle round"></span>
                            </label>
                        </div>
                        
                        <!-- If active, show weight/strength slider -->
                        <div v-if="is_downloaded(lora.id) && is_enabled(lora.id)" class="slider_container" style="margin-top: 8px;">
                            <div style="display: flex; justify-content: space-between; font-size: 0.75rem; opacity: 0.9; margin-bottom: 2px;">
                                <span>Strength:</span>
                                <span style="font-weight: bold; color: #3E7BFA;">{{ get_strength(lora.id) }}</span>
                            </div>
                            <input type="range" :min="lora.min_weight !== undefined ? lora.min_weight : -2.0" :max="lora.max_weight !== undefined ? lora.max_weight : 2.0" step="0.1" :value="get_strength(lora.id)" @input="update_strength(lora.id, $event.target.value)" style="width: 100%; height: 4px; border-radius: 2px; outline: none; background: #555; accent-color: #3E7BFA; cursor: pointer;">
                        </div>
                        
                        <!-- If not downloaded, show download button -->
                        <DownloadButton v-else :app="app" :asset_details="lora"></DownloadButton>

                        <!-- If custom, show remove option -->
                        <div v-if="lora.is_custom" style="margin-top: 8px; text-align: right;">
                            <a href="#" @click.prevent="removeCustomLora(lora.id)" style="color: #ff5252; font-size: 0.8rem; text-decoration: none; font-weight: 500;">Remove LoRA</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <br>
        <h2>FLUX.2 [klein] Enhancements</h2>
        <div class="icon_container">
            <div v-for="lora in active_klein_loras" :key="lora.id" class="model_card">
                <div class="model_card_image" v-bind:style="{ 'background-image': `url('${lora.img_url}')` }"></div>
                <div class="card_desc">
                    <div class="card_text">
                        <h2>{{ lora.title }}</h2>
                        <p>{{ lora.description }}</p>
                        <p style="zoom:0.75; opacity: 0.6; margin-top: 4px;">Designed for FLUX.2 [klein]</p>
                        <p v-if="lora.keyword" style="zoom:0.85; opacity: 0.9; margin-top: 4px; font-weight: 500;">Keyword: <span style="color: #3E7BFA;">{{ lora.keyword }}</span></p>
                    </div>

                    <div class="lora_action_area">
                        <!-- If incompatible with active model size -->
                        <div v-if="lora.incompatible" style="background: rgba(233, 64, 87, 0.1); border: 1px solid rgba(233, 64, 87, 0.2); padding: 8px 12px; border-radius: 8px; font-size: 0.8rem; color: #ff6b8b; margin-top: 8px; display: flex; align-items: center; gap: 6px; box-sizing: border-box; width: 100%;">
                            <span>⚠️ {{ lora.incompatible_reason }}</span>
                        </div>

                        <!-- Otherwise show normal actions -->
                        <template v-else>
                            <!-- If downloaded, show toggle switch -->
                            <div v-if="is_downloaded(lora.id)" class="toggle_container">
                                <span class="status_label" :class="{ active: is_enabled(lora.id) }">
                                    {{ is_enabled(lora.id) ? 'Active' : 'Inactive' }}
                                </span>
                                <label class="switch">
                                    <input type="checkbox" :checked="is_enabled(lora.id)" @change="toggleLora(lora.id, 'flux_klein')">
                                    <span class="toggle round"></span>
                                </label>
                            </div>
                            
                            <!-- If active, show weight/strength slider -->
                            <div v-if="is_downloaded(lora.id) && is_enabled(lora.id)" class="slider_container" style="margin-top: 8px;">
                                <div style="display: flex; justify-content: space-between; font-size: 0.75rem; opacity: 0.9; margin-bottom: 2px;">
                                    <span>Strength:</span>
                                    <span style="font-weight: bold; color: #3E7BFA;">{{ get_strength(lora.id) }}</span>
                                </div>
                                <input type="range" :min="lora.min_weight !== undefined ? lora.min_weight : -2.0" :max="lora.max_weight !== undefined ? lora.max_weight : 2.0" step="0.1" :value="get_strength(lora.id)" @input="update_strength(lora.id, $event.target.value)" style="width: 100%; height: 4px; border-radius: 2px; outline: none; background: #555; accent-color: #3E7BFA; cursor: pointer;">
                            </div>
                            
                            <!-- If not downloaded, show download button -->
                            <DownloadButton v-else :app="app" :asset_details="lora"></DownloadButton>
                        </template>

                        <!-- If custom, show remove option -->
                        <div v-if="lora.is_custom" style="margin-top: 8px; text-align: right;">
                            <a href="#" @click.prevent="removeCustomLora(lora.id)" style="color: #ff5252; font-size: 0.8rem; text-decoration: none; font-weight: 500;">Remove LoRA</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <br>
        <hr style="opacity: 0.15;">
        <br>
        <h2>Import Custom LoRA (.safetensors)</h2>
        <div class="import_section">
            <div class="import_card">
                <div class="form_group">
                    <label>LoRA Title</label>
                    <input type="text" v-model="import_form.title" placeholder="e.g. Aesthetic Anime" class="form_input">
                </div>
                <div class="form_group">
                    <label>Works with Model Family</label>
                    <select v-model="import_form.family" class="form_input">
                        <option value="flux_schnell">FLUX.1-schnell</option>
                        <option value="flux_klein">FLUX.2 [klein]</option>
                    </select>
                </div>
                <div class="form_group">
                    <label>Trigger Keyword (Optional)</label>
                    <input type="text" v-model="import_form.keyword" placeholder="e.g. anime (leave blank if none/slider)" class="form_input">
                </div>
                <div class="form_group" style="display: flex; gap: 15px;">
                    <div style="flex: 1;">
                        <label>Min Weight</label>
                        <input type="number" step="0.1" v-model.number="import_form.min_weight" class="form_input">
                    </div>
                    <div style="flex: 1;">
                        <label>Max Weight</label>
                        <input type="number" step="0.1" v-model.number="import_form.max_weight" class="form_input">
                    </div>
                </div>
                <div class="form_group">
                    <label>File Path (.safetensors)</label>
                    <div style="display: flex; gap: 8px;">
                        <input type="text" v-model="import_form.asset_path" placeholder="Select your LoRA file..." class="form_input" style="flex: 1;" readonly>
                        <button @click="browseLoraFile" class="btn_browse">Browse...</button>
                    </div>
                </div>
                <button @click="submitImport" class="btn_import">Import LoRA</button>
                <p v-if="import_error" class="import_error">{{ import_error }}</p>
            </div>
        </div>
    </div>
</template>

<script>
import DownloadButton from "../components/DownloadButton.vue";
import Vue from "vue";

const LoraStore = {
    name: 'LoraStore',
    props: {
        app: Object,
    },
    components: {
        DownloadButton
    },
    data() {
        return {
            schnell_loras: [
                {
                    id: "flux_schnell_detailed",
                    title: "Detailed Enhancer",
                    description: "Brings out intricate textures, microscopic details, and hyper-realistic surfaces.",
                    md5: "flux_schnell_detailed_dummy",
                    filename: "flux_schnell_detailed.safetensors",
                    url: "https://huggingface.co/Shakker-Labs/FLUX.1-dev-LoRA-add-details/resolve/main/FLUX-dev-lora-add_details.safetensors",
                    img_url: require("../assets/imgs/page_icon_imgs/lora_detailed.png"),
                    keyword: "",
                    min_weight: 0.0,
                    max_weight: 1.5,
                    default_weight: 0.8,
                    model_meta_data: {
                        type: "lora"
                    }
                },
                {
                    id: "flux_schnell_cinematic",
                    title: "Cinematic Film",
                    description: "Adds film grain, reversal film photography tones, and vintage cinematic color grading.",
                    md5: "flux_schnell_cinematic_dummy",
                    filename: "flux_schnell_cinematic.safetensors",
                    url: "https://huggingface.co/Shakker-Labs/FilmPortrait/resolve/main/filmfotos.safetensors",
                    img_url: require("../assets/imgs/page_icon_imgs/lora_cinematic.png"),
                    keyword: "filmfotos, film grain",
                    min_weight: 0.0,
                    max_weight: 1.5,
                    default_weight: 0.8,
                    model_meta_data: {
                        type: "lora"
                    }
                },
                {
                    id: "flux_schnell_portrait",
                    title: "Portrait Engine",
                    description: "Enhances facial structures, eyes, hair fidelity, and realistic skin tone textures.",
                    md5: "flux_schnell_portrait_dummy",
                    filename: "flux_schnell_portrait.safetensors",
                    url: "https://huggingface.co/strangerzonehf/Flux-Super-Portrait-LoRA/resolve/main/Super-Portrait.safetensors",
                    img_url: require("../assets/imgs/page_icon_imgs/lora_portrait.png"),
                    keyword: "Super Portrait",
                    min_weight: 0.0,
                    max_weight: 1.5,
                    default_weight: 0.8,
                    model_meta_data: {
                        type: "lora"
                    }
                }
            ],
            klein_loras: [
                {
                    id: "flux_klein_detailed",
                    title: "Detailed Enhancer",
                    description: "Enhances skin texture, fabric weave, and micro-detail sharpness for photorealism on Flux 2.",
                    md5: "flux_klein_detailed_dummy",
                    filename: "flux_klein_detailed.safetensors",
                    url: "https://huggingface.co/dx8152/Flux2-Klein-9B-Enhanced-Details/resolve/main/realistic.safetensors",
                    img_url: require("../assets/imgs/page_icon_imgs/lora_detailed.png"),
                    keyword: "",
                    min_weight: 0.0,
                    max_weight: 1.0,
                    default_weight: 0.65,
                    model_meta_data: {
                        type: "lora"
                    }
                },
                {
                    id: "flux_klein_cinematic",
                    title: "Cinematic Film",
                    description: "Adds dramatic volume rays, natural light leak glows, and stylized cinematic colors on Flux 2.",
                    md5: "flux_klein_cinematic_dummy",
                    filename: "flux_klein_cinematic.safetensors",
                    url: "https://huggingface.co/artificialguybr/CINEMATIC-FILMSTILL-REDMOND-FLUXKLEIN9B/resolve/main/%5BFLUX.2.Klein%5DFilmStill_Redmond.safetensors",
                    img_url: require("../assets/imgs/page_icon_imgs/lora_cinematic.png"),
                    keyword: "Cinematic, Film Still",
                    min_weight: 0.0,
                    max_weight: 1.5,
                    default_weight: 0.8,
                    model_meta_data: {
                        type: "lora"
                    }
                },
                {
                    id: "flux_klein_portrait",
                    title: "Portrait Engine",
                    description: "Studio-quality relighting and facial enhancement while preserving identity on Flux 2.",
                    md5: "flux_klein_portrait_dummy",
                    filename: "flux_klein_portrait.safetensors",
                    url: "https://huggingface.co/linoyts/Flux2-Klein-Delight-LoRA/resolve/main/pytorch_lora_weights.safetensors",
                    img_url: require("../assets/imgs/page_icon_imgs/lora_portrait.png"),
                    keyword: "",
                    min_weight: 0.0,
                    max_weight: 1.0,
                    default_weight: 0.7,
                    model_meta_data: {
                        type: "lora"
                    }
                }
            ],
            import_form: {
                title: "",
                family: "flux_schnell",
                keyword: "",
                asset_path: "",
                min_weight: -2.0,
                max_weight: 2.0
            },
            import_error: ""
        };
    },
    computed: {
        active_schnell_loras() {
            if (!this.app.is_mounted || !this.app.app_state.app_data.settings) return this.schnell_loras;
            const custom = (this.app.app_state.app_data.settings.custom_loras || [])
                .filter(x => x.family === 'flux_schnell');
            return [...this.schnell_loras, ...custom];
        },
        active_klein_loras() {
            if (!this.app.is_mounted || !this.app.app_state.app_data.settings) return this.klein_loras;
            const is_4b = this.app.app_state.app_data.settings.flux_klein_size === '4B';
            const mapped = this.klein_loras.map(lora => {
                let copy = JSON.parse(JSON.stringify(lora));
                if (is_4b) {
                    if (copy.id === 'flux_klein_detailed') {
                        copy.id = 'flux_klein_detailed_4b';
                        copy.filename = 'f2k_4B_consist_20260314.safetensors';
                        copy.url = 'https://huggingface.co/lrzjason/Consistance_Edit_Lora/resolve/main/f2k_4B_consist_20260314.safetensors';
                        copy.md5 = 'flux_klein_detailed_4b_dummy';
                        copy.title = 'Detailed Enhancer (4B)';
                        copy.description = 'Enhances structure and consistency specifically for the 4B model.';
                        copy.default_weight = 0.65;
                    } else if (copy.id === 'flux_klein_cinematic') {
                        // Map to 4B-compatible adapter with cinematic-tuned weight
                        copy.id = 'flux_klein_cinematic_4b';
                        copy.filename = 'f2k_4B_consist_20260314.safetensors';
                        copy.url = 'https://huggingface.co/lrzjason/Consistance_Edit_Lora/resolve/main/f2k_4B_consist_20260314.safetensors';
                        copy.md5 = 'flux_klein_cinematic_4b_dummy';
                        copy.title = 'Cinematic Film (4B)';
                        copy.description = 'Adds dramatic tones and stylized cinematic color grading on 4B. Use keyword for best effect.';
                        copy.default_weight = 0.45;
                        copy.keyword = 'Cinematic, Film Still';
                    } else if (copy.id === 'flux_klein_portrait') {
                        // Map to 4B-compatible adapter with portrait-tuned weight
                        copy.id = 'flux_klein_portrait_4b';
                        copy.filename = 'f2k_4B_consist_20260314.safetensors';
                        copy.url = 'https://huggingface.co/lrzjason/Consistance_Edit_Lora/resolve/main/f2k_4B_consist_20260314.safetensors';
                        copy.md5 = 'flux_klein_portrait_4b_dummy';
                        copy.title = 'Portrait Engine (4B)';
                        copy.description = 'Enhances facial structures and realistic skin textures on 4B.';
                        copy.default_weight = 0.55;
                    }
                }
                return copy;
            });
            const custom = (this.app.app_state.app_data.settings.custom_loras || [])
                .filter(x => x.family === 'flux_klein');
            return [...mapped, ...custom];
        }
    },
    methods: {
        is_downloaded(lora_id) {
            if (!this.app.is_mounted) return false;
            if (lora_id.startsWith("custom_")) {
                return true;
            }
            let asset = this.app.app_state.downloaded_assets[lora_id];
            if (asset && asset.status === 'done') {
                return true;
            }
            let downloadingAsset = this.app.app_state.downloading[lora_id];
            if (downloadingAsset && downloadingAsset.status === 'done') {
                return true;
            }
            return false;
        },
        is_enabled(lora_id) {
            if (!this.app.is_mounted || !this.app.app_state.app_data.settings.loras) return false;
            return !!this.app.app_state.app_data.settings.loras[lora_id];
        },
        toggleLora(lora_id, family) {
            const currentVal = this.is_enabled(lora_id);
            const lora_settings = this.app.app_state.app_data.settings.loras;
            const stacking = this.app.app_state.app_data.settings.lora_stacking;
            
            if (!currentVal) {
                if (!stacking) {
                    // Stacking disabled: turn OFF all other LoRAs in the same family first.
                    const family_loras = family === 'flux_schnell' 
                        ? this.active_schnell_loras
                        : this.active_klein_loras;
                    
                    for (let lora of family_loras) {
                        Vue.set(lora_settings, lora.id, false);
                    }
                }
                Vue.set(lora_settings, lora_id, true);
                
                // Set default weight if not already set
                let strengths = this.app.app_state.app_data.settings.lora_strengths;
                if (strengths && strengths[lora_id] === undefined) {
                    let lora_def = this.find_lora_def(lora_id);
                    let default_w = (lora_def && lora_def.default_weight !== undefined) ? lora_def.default_weight : 1.0;
                    Vue.set(strengths, lora_id, default_w);
                }
            } else {
                Vue.set(lora_settings, lora_id, false);
            }
        },
        browseLoraFile() {
            let file_path = window.ipcRenderer.sendSync('file_dialog', 'weights_file');
            if (file_path && file_path !== "NULL") {
                this.import_form.asset_path = file_path;
            }
        },
        find_lora_def(lora_id) {
            let all = [...this.active_schnell_loras, ...this.active_klein_loras];
            return all.find(l => l.id === lora_id) || null;
        },
        get_strength(lora_id) {
            if (!this.app.is_mounted || !this.app.app_state.app_data.settings.lora_strengths) {
                let lora_def = this.find_lora_def(lora_id);
                return (lora_def && lora_def.default_weight !== undefined) ? lora_def.default_weight : 1.0;
            }
            const str = this.app.app_state.app_data.settings.lora_strengths[lora_id];
            if (str !== undefined) return str;
            let lora_def = this.find_lora_def(lora_id);
            return (lora_def && lora_def.default_weight !== undefined) ? lora_def.default_weight : 1.0;
        },
        update_strength(lora_id, value) {
            if (this.app.is_mounted && this.app.app_state.app_data.settings.lora_strengths) {
                Vue.set(this.app.app_state.app_data.settings.lora_strengths, lora_id, parseFloat(value));
            }
        },
        submitImport() {
            this.import_error = "";
            const form = this.import_form;
            if (!form.title.trim()) {
                this.import_error = "LoRA Title is required.";
                return;
            }
            if (!form.asset_path.trim()) {
                this.import_error = "File Path is required. Please browse and select a file.";
                return;
            }
            
            const kw = form.keyword.trim();
            const new_id = "custom_" + Date.now() + "_" + Math.random().toString(36).substr(2, 9);
            const new_lora = {
                id: new_id,
                title: form.title.trim(),
                description: kw ? `Custom LoRA triggered by "${kw}"` : `Custom Slider LoRA`,
                filename: form.asset_path.split(/[/\\]/).pop(),
                asset_path: form.asset_path,
                img_url: require("../assets/imgs/page_icon_imgs/default.png"),
                keyword: kw,
                family: form.family,
                status: 'done',
                is_custom: true,
                min_weight: typeof form.min_weight === 'number' && !isNaN(form.min_weight) ? form.min_weight : -2.0,
                max_weight: typeof form.max_weight === 'number' && !isNaN(form.max_weight) ? form.max_weight : 2.0
            };
            
            if (!this.app.app_state.app_data.settings.custom_loras) {
                Vue.set(this.app.app_state.app_data.settings, 'custom_loras', []);
            }
            
            this.app.app_state.app_data.settings.custom_loras.push(new_lora);
            
            // Reset form
            this.import_form.title = "";
            this.import_form.keyword = "";
            this.import_form.asset_path = "";
            this.import_form.min_weight = -2.0;
            this.import_form.max_weight = 2.0;
        },
        removeCustomLora(lora_id) {
            // Turn off setting first
            if (this.app.app_state.app_data.settings.loras) {
                Vue.set(this.app.app_state.app_data.settings.loras, lora_id, false);
            }
            if (this.app.app_state.app_data.settings.lora_strengths) {
                Vue.delete(this.app.app_state.app_data.settings.lora_strengths, lora_id);
            }
            
            const custom_loras = this.app.app_state.app_data.settings.custom_loras || [];
            const idx = custom_loras.findIndex(x => x.id === lora_id);
            if (idx > -1) {
                custom_loras.splice(idx, 1);
            }
        }
    }
};

LoraStore.title = "LoRAs";
LoraStore.icon = "sliders-h";
LoraStore.description = "Download and apply custom LoRAs";
LoraStore.img_icon = require("../assets/imgs/page_icon_imgs/default.png");
LoraStore.home_category = "pages";
LoraStore.sidebar_show = "always";

export default LoraStore;
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

.icon_container {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.model_card {
    width: 230px;
    height: 350px;
    background-color: var(--sidebar-color);
    position: relative;
    border-radius: 12px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    border: 1px solid rgba(255, 255, 255, 0.08);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.model_card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
    border-color: rgba(255, 255, 255, 0.15);
}

.model_card_image {
    height: 120px;
    width: 100%;
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}

.card_desc {
    padding: 12px 15px;
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.card_text h2 {
    font-size: 1.05rem;
    margin: 0 0 6px 0;
    font-weight: 600;
}

.card_text p {
    font-size: 0.82rem;
    margin: 0 0 4px 0;
    opacity: 0.8;
    line-height: 1.25;
}

.lora_action_area {
    margin-top: 5px;
}

.toggle_container {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.status_label {
    font-size: 0.82rem;
    font-weight: 600;
    opacity: 0.5;
}

.status_label.active {
    color: #3E7BFA;
    opacity: 1;
}

.switch {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 25px;
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
  -webkit-transition: .4s;
  transition: .4s;
}

.toggle:before {
  position: absolute;
  content: "";
  height: 17px;
  width: 17px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  -webkit-transition: .4s;
  transition: .4s;
}

input:checked + .toggle {
  background-color: #3E7BFA;
}

input:checked + .toggle:before {
  transform: translateX(25px);
}

.toggle.round {
  border-radius: 34px;
}

.toggle.round:before {
  border-radius: 50%;
}

/* Import form styles */
.import_section {
    margin-top: 15px;
    max-width: 600px;
}

.import_card {
    background-color: var(--sidebar-color);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 30px;
}

.form_group {
    margin-bottom: 15px;
}

.form_group label {
    display: block;
    font-size: 0.9rem;
    font-weight: 600;
    margin-bottom: 6px;
    color: var(--text-color, #ffffff);
    opacity: 1;
}

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

.form_input option {
    background-color: #2b2b2b;
    color: #ffffff;
}

.form_input[readonly] {
    color: var(--text-color, #ffffff) !important;
    opacity: 1 !important;
    cursor: default;
}

.btn_browse {
    background-color: #444;
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 0.9rem;
    cursor: pointer;
    transition: background 0.2s;
}

.btn_browse:hover {
    background-color: #555;
}

.btn_import {
    background-color: #3E7BFA;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
}

.btn_import:hover {
    background-color: #2b66e3;
}

.import_error {
    color: #ff5252;
    font-size: 0.85rem;
    margin-top: 10px;
}
</style>
