<template>
    <div></div>
</template>
<script>

import Vue from 'vue'
import { send_to_py } from "./py_vue_bridge.js"
import {get_tokens} from './clip_tokeniser/clip_encoder.js'
import {compute_time_remaining} from "./utils.js"
const moment = require('moment')

let notification_sound = new Audio(require('@/assets/notification.mp3'))

function remove_non_ascii(str) {
  
  if ((str===null) || (str===''))
       return false;
 else
   str = str.toString();
  
  return str.replace(/[^\x20-\x7E]/g, '');
}

export default {
    name: 'StableDiffusion',
    props: {},
    components: {},
    mounted() {

    },
    data() {
        return {
            is_stopping: false,
            is_backend_loaded : false,
            is_model_downloading: false, 
            downloading_model_id: null,
            downloading_asset_ids: null,
            is_input_avail : false,
            model_loading_msg : "",
            model_loading_title : "",
            loading_percentage : -1 , 
            generation_state_msg : "",
            remaining_times: "",
            attached_cbs : undefined,
            model_version : "",
            nb_its: 0,
            iter_times: [],
            generation_loop: undefined
        };
    },
    methods: {
        state_msg(msg){
            let msg_code = msg.substring(0, 4);
            if(msg_code == "mdld"){
                console.log("[SD] mdld received. downloading_asset_ids:", this.downloading_asset_ids, "downloading_model_id:", this.downloading_model_id);
                this.is_backend_loaded = true;
                this.is_model_downloading = false;
                this.loading_percentage = -1;
                if (this.$parent.app_state) {
                    this.$parent.app_state.global_loader_percentage = -1;
                }
                
                let completed_model_id = this.downloading_model_id;
                let completed_asset_ids = this.downloading_asset_ids || (completed_model_id ? [completed_model_id] : []);
                if (completed_asset_ids.length === 0 && this.$parent.assets_manager) {
                    if (this.$parent.assets_manager.downloading['flux_klein'] && this.$parent.assets_manager.downloading['flux_klein'].status === 'downloading') {
                        completed_asset_ids = ['flux_klein'];
                    } else if (this.$parent.assets_manager.downloading['flux_schnell'] && this.$parent.assets_manager.downloading['flux_schnell'].status === 'downloading') {
                        completed_asset_ids = ['flux_schnell'];
                    }
                }
                
                if (this.$parent.assets_manager) {
                    let is_base = false;
                    for (let tid of completed_asset_ids) {
                        if (tid === 'flux_klein' || tid === 'flux_schnell') {
                            is_base = true;
                            Vue.set(this.$parent.assets_manager.downloading[tid], 'status', 'done');
                            Vue.set(this.$parent.assets_manager.downloading[tid], 'progress', 100);
                        }
                    }
                    if (!is_base) {
                        for (let tid of completed_asset_ids) {
                            let asset_details = this.$parent.assets_manager.downloading[tid] || {};
                            asset_details.status = 'done';
                            asset_details.progress = 100;
                            // Ensure asset_path is set from asset_path_raw for HF downloads
                            if (!asset_details.asset_path && asset_details.asset_path_raw) {
                                asset_details.asset_path = asset_details.asset_path_raw;
                            }
                            Vue.set(this.$parent.assets_manager.downloaded_assets, tid, asset_details);
                        }
                    }
                }
                
                this.downloading_model_id = null;
                this.downloading_asset_ids = null;
                this.$parent.app_state.global_loader_modal_msg = "";
            }
            if(msg_code == "mldn"){
                this.is_model_downloading = false;
                this.loading_percentage = -1;
                if (this.$parent.app_state) {
                    this.$parent.app_state.global_loader_percentage = -1;
                }
                this.downloading_model_id = null;
                this.downloading_asset_ids = null;
            }
            if(msg_code == "inrd"){
                console.log("cps unset inrd ")
                this.is_stopping = false
                this.is_input_avail = true; // note : is_input_avail can be watched so set this at last pls
            }
            if(msg_code == "inwk"){
                this.is_input_avail = false;
            }

            if(msg_code == "nwim"){
                if (this.$parent.app_state.app_data.settings.notification_sound == true) {
                    notification_sound.play();
                }
                let img = msg.substring(5).trim()
                img = JSON.parse(img)
                if(this.attached_cbs){
                    if(this.attached_cbs.on_img)
                        this.attached_cbs.on_img(img);
                } else {
                    console.log("got new img but cbs none")
                }
            }

            if(msg_code == "mdvr"){
                this.model_version = msg.substring(5).trim()
            }

            if(msg_code == "mlpr"){
                let p = Number(msg.substring(5).trim());
                console.log("[SD] mlpr received:", p, "downloading_asset_ids:", this.downloading_asset_ids);
                this.loading_percentage = p;
                if (this.$parent.app_state) {
                    this.$parent.app_state.global_loader_percentage = p;
                }
                if (this.$parent.assets_manager) {
                    let tids = this.downloading_asset_ids || (this.downloading_model_id ? [this.downloading_model_id] : []);
                    for (let tid of tids) {
                        if (this.$parent.assets_manager.downloading[tid]) {
                            Vue.set(this.$parent.assets_manager.downloading[tid], 'progress', p);
                        }
                    }
                    if (this.$parent.assets_manager.downloading['flux_klein']) {
                        Vue.set(this.$parent.assets_manager.downloading['flux_klein'], 'progress', p);
                    }
                    if (this.$parent.assets_manager.downloading['flux_schnell']) {
                        Vue.set(this.$parent.assets_manager.downloading['flux_schnell'], 'progress', p);
                    }
                }
            }
            if(msg_code == "mlms"){
                let p = (msg.substring(5).trim());
                this.model_loading_msg = p;
            }
            if(msg_code == "gnms"){
                let p = (msg.substring(5).trim());
                this.generation_state_msg = p;
            }

            if(msg_code == "mltl"){
                let p = (msg.substring(5).trim());

                if( p.startsWith("Downloading asset:") ){
                    this.is_model_downloading = true;
                    let asset_id = p.replace("Downloading asset:", "").trim();
                    console.log("[SD] mltl Downloading asset received, asset_id:", asset_id);
                    
                    // Map filename or asset ID to default stock LoRA IDs case-insensitively
                    let target_ids = [];
                    let asset_id_lower = asset_id.toLowerCase();
                    if (asset_id_lower === "flux_schnell_detailed" || asset_id_lower === "flux_klein_detailed") {
                        target_ids = [asset_id_lower];
                    } else if (asset_id_lower.includes("flux-dev-lora-add_details")) {
                        target_ids = ["flux_schnell_detailed"];
                    } else if (asset_id_lower.includes("realistic") && asset_id_lower.includes("klein")) {
                        target_ids = ["flux_klein_detailed"];
                    } else if (asset_id_lower === "flux_schnell_cinematic" || asset_id_lower === "flux_klein_cinematic") {
                        target_ids = [asset_id_lower];
                    } else if (asset_id_lower.includes("filmfotos") || asset_id_lower.includes("filmportrait")) {
                        target_ids = ["flux_schnell_cinematic"];
                    } else if (asset_id_lower.includes("filmstill_redmond") || asset_id_lower.includes("fluxklein")) {
                        target_ids = ["flux_klein_cinematic"];
                    } else if (asset_id_lower === "flux_schnell_portrait" || asset_id_lower === "flux_klein_portrait") {
                        target_ids = [asset_id_lower];
                    } else if (asset_id_lower.includes("super-portrait") || asset_id_lower.includes("super_portrait")) {
                        target_ids = ["flux_schnell_portrait"];
                    } else if (asset_id_lower.includes("delight") || asset_id_lower.includes("pytorch_lora_weights")) {
                        target_ids = ["flux_klein_portrait"];
                    } else if (asset_id_lower.includes("detailed")) {
                        target_ids = [asset_id_lower];
                    } else if (asset_id_lower.includes("cinematic")) {
                        target_ids = [asset_id_lower];
                    } else if (asset_id_lower.includes("portrait")) {
                        target_ids = [asset_id_lower];
                    } else {
                        target_ids = [asset_id];
                    }
                    
                    this.downloading_model_id = target_ids[0];
                    this.downloading_asset_ids = target_ids;
                    
                    if (this.$parent.assets_manager) {
                        for (let tid of target_ids) {
                            let orig_asset = this.$parent.assets_manager.downloading[tid] || {};
                            Vue.set(this.$parent.assets_manager.downloading, tid, {
                                ...orig_asset,
                                id: tid,
                                status: 'downloading',
                                progress: 0
                            });
                        }
                    }
                    this.$parent.app_state.global_loader_modal_msg = "Downloading asset... This may take a while.";
                    this.$parent.app_state.global_loader_percentage = 0;
                } else if( p.includes("Downloading") ){
                    this.is_model_downloading = true;
                    let model_id = null;
                    if (p.includes("FLUX.2-klein-9B") || p.includes("flux_klein")) {
                        model_id = "flux_klein";
                    } else if (p.includes("FLUX.1-schnell") || p.includes("flux_schnell")) {
                        model_id = "flux_schnell";
                    }
                    if (model_id) {
                        this.downloading_model_id = model_id;
                        this.downloading_asset_ids = [model_id];
                        if (this.$parent.assets_manager) {
                            if (!this.$parent.assets_manager.downloading[model_id]) {
                                Vue.set(this.$parent.assets_manager.downloading, model_id, {
                                    id: model_id,
                                    status: 'downloading',
                                    progress: 0
                                });
                            } else {
                                Vue.set(this.$parent.assets_manager.downloading[model_id], 'status', 'downloading');
                            }
                        }
                        let model_title = model_id === "flux_klein" ? "FLUX.2 [klein]" : "FLUX.1-schnell";
                        this.$parent.app_state.global_loader_modal_msg = "Downloading " + model_title + "... This may take a while.";
                        this.$parent.app_state.global_loader_percentage = 0;
                    }
                }

                this.model_loading_title = p;
            }


            if(msg_code == "errr"){
                this.is_model_downloading = false;
                this.loading_percentage = -1;
                if (this.$parent.app_state) {
                    this.$parent.app_state.global_loader_percentage = -1;
                }
                let error = msg.substring(5).trim()
                
                let failed_model_id = this.downloading_model_id;
                let failed_asset_ids = this.downloading_asset_ids || (failed_model_id ? [failed_model_id] : []);
                if (failed_asset_ids.length === 0 && this.$parent.assets_manager) {
                    // Check for any in-progress downloads (base models or LoRAs)
                    for (let key in this.$parent.assets_manager.downloading) {
                        if (this.$parent.assets_manager.downloading[key] && this.$parent.assets_manager.downloading[key].status === 'downloading') {
                            failed_asset_ids.push(key);
                        }
                    }
                }
                
                if (this.$parent.assets_manager) {
                    for (let tid of failed_asset_ids) {
                        if (!this.$parent.assets_manager.downloading[tid]) {
                            Vue.set(this.$parent.assets_manager.downloading, tid, {
                                id: tid,
                                status: 'error',
                                error: error.slice(-30),
                                progress: 0
                            });
                        } else {
                            Vue.set(this.$parent.assets_manager.downloading[tid], 'status', 'error');
                            Vue.set(this.$parent.assets_manager.downloading[tid], 'error', error.slice(-30));
                        }
                    }
                }
                
                this.downloading_model_id = null;
                this.downloading_asset_ids = null;
                this.$parent.app_state.global_loader_modal_msg = "";
                if(this.attached_cbs){
                    if(this.attached_cbs.on_err)
                        this.attached_cbs.on_err(error);
                }

            }

            if(msg_code == "dnpr"){
                this.is_model_downloading = false;
                let p = Number(msg.substring(5).trim());
                let iter_time =  Date.now()  -this.last_iter_t;
                this.last_iter_t  = Date.now();
                if(this.attached_cbs){
                    if(this.attached_cbs.on_progress){
                        if(p >= 0 ){
                            this.generation_state_msg = iter_time/1000 + " s/it";
                            this.iter_times.push(iter_time);
                            let median = this.iter_times.sort((a, b) => a - b)[Math.floor(this.iter_times.length / 2)];
                            let time_remaining = moment.duration(median*((100-p)*this.nb_its/100));
                              
                            this.remaining_times = compute_time_remaining(time_remaining);
                            clearInterval(this.generation_loop);
                            this.generation_loop = setInterval(() => {
                                if(this.attached_cbs == undefined){
                                    return clearInterval(this.generation_loop);
                                }
                                time_remaining.subtract(1, 'seconds');
                                this.remaining_times = compute_time_remaining(time_remaining);
                            }, 1000);
    
                        }
                        this.attached_cbs.on_progress(p, iter_time);
                    }
                        
                } else {
                    console.log("got new msg but cbs none")
                }

            }


        } ,

        interupt(){
            send_to_py("t2im __stop__")
            console.log("cps unset st ")
            this.is_stopping = true
            this.attached_cbs = undefined;
        },

        is_ready(){
            if(this.is_model_downloading)
                return false 
            return this.is_backend_loaded
        },

        run_applet(applet_name , params , callbacks ){


            if(!this.is_input_avail)
                return;
            
            this.is_stopping = false

            this.generated_by = applet_name;
            this.attached_cbs = callbacks;

            this.generation_state_msg = "Running " + applet_name

            const settings = this.$parent.app_state.app_data.settings;
            if (settings) {
                params.save_exif_meta = !!settings.save_exif_meta;
                if (settings.hf_token) {
                    params.hf_token = settings.hf_token;
                }
            }

            send_to_py("rapp " + applet_name + " " + JSON.stringify(params)) 
            
        },

        text_to_img(prompt_params, callbacks, generated_by){
            if(!this.is_input_avail)
                return;
            this.is_stopping = false
            let tokens = [49406].concat((get_tokens(prompt_params.prompt))).concat([49407])
            tokens.filter(n => n != null && n != undefined)
            prompt_params.prompt_tokens = tokens;

            if(prompt_params.negative_prompt)
            {
                let tokens2 = [49406].concat((get_tokens(prompt_params.negative_prompt))).concat([49407])
                tokens2.filter(n => n != null && n != undefined)
                prompt_params.negative_prompt_tokens = tokens2
            }

            prompt_params.seed = Number(prompt_params.seed) || 0 

            if(prompt_params.prompt){
                prompt_params.prompt = remove_non_ascii(prompt_params.prompt)
            }

            if(prompt_params.negative_prompt){
                prompt_params.negative_prompt = remove_non_ascii(prompt_params.negative_prompt)
            }                

            this.last_iter_t = Date.now()
            this.generated_by = generated_by;
            this.attached_cbs = callbacks;
            console.log("cps set ")
            this.generation_state_msg = ""
            this.remaining_times = ""
            this.iter_times = []
            this.nb_its = prompt_params.ddim_steps||25
            
            const settings = this.$parent.app_state.app_data.settings;
            if (settings) {
                if (settings.hf_token) {
                    prompt_params.hf_token = settings.hf_token;
                }
                prompt_params.save_exif_meta = !!settings.save_exif_meta;
            }

            send_to_py("t2im " + JSON.stringify(prompt_params)) 
        }

    },
}
</script>
<style>
</style>
<style scoped>
</style>