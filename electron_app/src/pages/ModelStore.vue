<template>
    <div class="main_container">

        <h2 v-if="downloaded_models_list.length > 0"> My Models </h2>
        <div v-if="downloaded_models_list.length > 0" class="icon_container">

            <div v-for="model in downloaded_models_list" :key="model.id" class="model_card">
                 <div class="model_card_image" v-bind:style="{ 'background-image': `url('${model.img_url || default_img_url}')` }"></div>
                 <div class="card_desc"> 
                    <div class="card_text">
                        <h2> {{model.title || model.id}} </h2> 
                        <p> {{model.description}} </p> 
                        <p style="zoom:0.7; opacity: 0.6;"> {{ model_metadata_to_str(model) }}</p>
                    </div>
                    <DownloadButton :app=app  :asset_details="model"> </DownloadButton>
                </div> 
            </div>

        </div>

        <br>

        <h2> Available Models </h2>
        <div class="icon_container">

            <div v-for="model in not_downloaded_models_list" :key="model.id" class="model_card">
                 <div class="model_card_image" v-bind:style="{ 'background-image': `url('${model.img_url || default_img_url}')` }"></div>
                 <div class="card_desc"> 
                    <div class="card_text">
                        <h2> {{model.title || model.id}} </h2> 
                        <p> {{model.description}} </p> 
                        <p style="zoom:0.7; opacity: 0.6;"> {{ model_metadata_to_str(model) }}</p>
                    </div>
                    <DownloadButton v-if="!(model.min_version) || model.min_version <= app.current_build_number" :app=app  :asset_details="model"> </DownloadButton>
                    <p  style="color:red" v-if="model.min_version && model.min_version > app.current_build_number"> You need to update the application to use this model</p>
                </div> 
            </div>

        </div>

        <br>

    </div>
</template>
<script>

import DownloadButton from "../components/DownloadButton.vue"
import MoonLoader from 'vue-spinner/src/MoonLoader.vue'

const ModelStore ={
    name: 'ModelStore',
    props: {app:Object, },
    components: {DownloadButton, MoonLoader},
    mounted() {
        this.load_models_list_local_storage()
        this.load_models_list_from_web()
        this.check_ollama_models()
        this.ollama_check_interval = setInterval(this.check_ollama_models, 5000)
    },
    beforeDestroy() {
        if (this.ollama_check_interval) {
            clearInterval(this.ollama_check_interval);
        }
    },
    data() {
        return {
            is_local_model_importing : false, 
            default_img_url : require("../assets/imgs/page_icon_imgs/default.png"),
            ollama_downloaded_models: [],
            models_list : [
                {
                    id: "flux_schnell",
                    title: "FLUX.1-schnell",
                    description: "Compact 12B-parameter model optimized for 1-4 step generation speed and high-quality outputs.",
                    md5: "flux_schnell_dummy",
                    filename: "FLUX.1-schnell",
                    img_url: require("../assets/imgs/page_icon_imgs/flux_schnell.png"),
                    model_meta_data: {
                        sd_type: "Flux 1",
                        float_type: "bf16"
                    }
                },
                {
                    id: "flux_klein",
                    title: "FLUX.2 [klein]",
                    description: "Compact 9B-parameter model optimized for speed, text-to-image, and reference KV-editing. Requires HF token.",
                    md5: "flux_klein_dummy",
                    filename: "FLUX.2-klein-9B",
                    img_url: require("../assets/imgs/page_icon_imgs/flux_klein.png"),
                    model_meta_data: {
                        sd_type: "Flux 2",
                        float_type: "bf16"
                    }
                },
                {
                    id: "gemma4:e2b",
                    title: "Gemma 4 [e2b]",
                    description: "Efficient 2B-parameter Gemma model for text rewriting and prompt description.",
                    md5: "gemma4:e2b",
                    filename: "gemma4:e2b",
                    img_url: require("../assets/imgs/page_icon_imgs/default.png"),
                    model_meta_data: {
                        sd_type: "LLM",
                        float_type: "e2b"
                    },
                    is_ollama_model: true
                },
                {
                    id: "gemma4:e4b",
                    title: "Gemma 4 [e4b]",
                    description: "Highly accurate 4B-parameter Gemma model for high-fidelity prompt generation.",
                    md5: "gemma4:e4b",
                    filename: "gemma4:e4b",
                    img_url: require("../assets/imgs/page_icon_imgs/default.png"),
                    model_meta_data: {
                        sd_type: "LLM",
                        float_type: "e4b"
                    },
                    is_ollama_model: true
                }
            ], 
        };
    },
    computed: {
        downloaded_models_list(){
            if(!this.app.is_mounted)
                return []

            let ret = []
            for(let k in this.app.assets_manager.all_avail_assets){
                if (k === 'flux_klein' || k === 'flux_schnell') {
                    let asset = JSON.parse(JSON.stringify(this.app.assets_manager.all_avail_assets[k]))
                    let static_details = this.models_list.find(x => x.id === k)
                    if (static_details) {
                        asset.img_url = static_details.img_url
                        asset.description = static_details.description
                    }
                    ret.unshift(asset)
                }
            }
            for (let model of this.models_list) {
                if (model.is_ollama_model && this.ollama_downloaded_models.includes(model.id)) {
                    ret.push({
                        ...model,
                        status: 'done',
                        is_locally_imported: true
                    });
                }
            }
            return ret;
        } , 
        not_downloaded_models_list(){
            let that = this
            return this.models_list.filter(model  => {
                if (model.is_ollama_model) {
                    return !that.ollama_downloaded_models.includes(model.id);
                }
                return !(that.app.is_mounted && that.app.assets_manager.downloaded_assets[model.id]);
            })
        }
    },
    methods: {
        check_ollama_models(){
            let that = this;
            fetch("http://127.0.0.1:11435/api/tags")
                .then(response => response.json())
                .then(data => {
                    if (data && data.models) {
                        that.ollama_downloaded_models = data.models.map(m => m.name);
                    }
                })
                .catch(err => {
                    console.log("Ollama tags error:", err);
                });
        },
        load_models_list_from_web(){
            // Statically defined models only
        } ,     

        load_models_list_local_storage(){
            // Statically defined models only
        } , 

        save_models_list_local_storage(){
            // Statically defined models only
        } , 

        model_metadata_to_str(asset_details){
            if(!asset_details.model_meta_data)
                return ""

            let r = ""

            if(asset_details.model_meta_data.sd_type)
                r += " " + asset_details.model_meta_data.sd_type

            if(asset_details.model_meta_data.float_type)
                r += " " + asset_details.model_meta_data.float_type
            
            return r
        }
    },
}

export default ModelStore;
ModelStore.title = "Models"
ModelStore.icon = "cubes"
ModelStore.description = "Download and manage models"
ModelStore.img_icon = require("../assets/imgs/page_icon_imgs/models.png")
ModelStore.home_category = "pages"
ModelStore.sidebar_show = "always"

</script>
<style>
</style>
<style scoped>

.main_container{
    padding: 20px;
    width: 100%;
    height: 100%;
    overflow: auto;
}

.icon_container{
    display: flex;
   flex-wrap: wrap;
}

.model_card{
    width: 230px;
    height: 270px;
    margin: 5px;
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
    height: 130px;
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

@media only screen and (max-width: 1730px) {
  .model_card {
    width : calc(20% - 10px)
  }
}

@media only screen and (max-width: 1430px) {
  .model_card {
    width : calc(25% - 10px)
  }
}

@media only screen and (max-width: 1200px) {
  .model_card {
    width : calc(33% - 10px)
  }
}

</style>