<template>
    <div>
    </div>
</template>
<script>

import Vue from 'vue'
import { send_to_py } from "./py_vue_bridge.js"

// contextBridge.exposeInMainWorld('ipcRenderer', ipcRenderer)
// contextBridge.exposeInMainWorld('ipcRenderer_on', ipcRenderer.on)


function download_file(url, dest, md5_hash , onProgress, onSuccess, onError, hf_token) {
    const downloadId = Date.now().toString() + Math.random().toString().substr(2);
    window.bind_ipc_download_on(downloadId, function(m){
        // progresss
        onProgress(m);
    }, function(file_hash){
        // sucdesss 
        if(md5_hash == file_hash || (md5_hash && md5_hash.endsWith('_dummy'))){
            onSuccess(file_hash)
        } else{
            onError("failed to match checksum")
        }
        window.unbind_ipc_download_on(downloadId)
        
    }, function(m){
        // error 
        window.unbind_ipc_download_on(downloadId)
        onError(m)
    } )
    window.ipcRenderer.send('download-file', url, dest, downloadId, hf_token);
}


export default {
    name: 'AssetsManager.vue',
    props: { app: Object },
    components: {},
    mounted() {
        // Clean up corrupt/invalid downloaded files on startup
        if (this.downloaded_assets) {
            for (let asset_id in this.downloaded_assets) {
                let asset = this.downloaded_assets[asset_id];
                if (asset && asset.asset_path) {
                    if (asset_id.includes('_detailed') || asset_id.includes('_cinematic') || asset_id.includes('_portrait') || asset_id.startsWith('custom_')) {
                        let isValid = window.ipcRenderer.sendSync('check_file_valid', asset.asset_path);
                        if (!isValid) {
                            console.log("Removing invalid asset record and file: " + asset_id);
                            window.ipcRenderer.sendSync('delete_file', asset.asset_path);
                            Vue.delete(this.downloaded_assets, asset_id);
                            if (this.downloading && this.downloading[asset_id]) {
                                Vue.delete(this.downloading, asset_id);
                            }
                        }
                    }
                }
            }
        }
    },
    data() {
        let downloaded_assets_storage = window.ipcRenderer.sendSync('load_data' , 'downloaded_assets.json'); // get from local storage
        let local_assets_storage = window.ipcRenderer.sendSync('load_data' , 'locally_loaded_assets.json'); // get from local storage

        return {
            downloaded_assets: downloaded_assets_storage ,
            local_assets: local_assets_storage , 
            downloading: {} , // id , status : done/downloading/error/not_downloaded , progress , hash, 
            //TODO : ignore the certificate but see the signature
        };
    },

    watch:{
         'downloaded_assets': {
            handler: function(new_value) {
                window.ipcRenderer.sendSync('save_data', new_value , 'downloaded_assets.json');
            },
            deep: true
        } , 

         'local_assets': {
            handler: function(new_value) {
                window.ipcRenderer.sendSync('save_data', new_value , 'locally_loaded_assets.json');
            },
            deep: true
        } , 

    },

    computed: {
        all_avail_assets(){
            return { // update the dict
              ...this.downloaded_assets ,
              ...this.local_assets
            }
        }
    },

    methods: {

        add_local_asset(asset_details, cb ){
            asset_details = JSON.parse(JSON.stringify(asset_details))
            let that = this;
            let asset_id = asset_details.id;
            let asset_filename = asset_details.filename;

            if(asset_details.post_process && asset_details.post_process == 'convert_sd_to_tdict' ){
                asset_details.post_process_params = asset_details.post_process_params || {}
                let model_name = asset_id + "_" + asset_filename
                window.ipcRenderer.invoke('add_custom_pytorch_models', asset_details.asset_path_raw,  model_name, asset_details.post_process_params ).then((result) => {
                    that.is_custom_model_loading = false
                    if(result.success){
                            
                            asset_details.model_meta_data = asset_details.model_meta_data || {}
                            asset_details.asset_path = result.model_path 

                            asset_details.model_meta_data  = { // update the dict
                              ...asset_details.model_meta_data ,
                              ...result.metadata
                            }

                          Vue.set( that.local_assets , asset_id , asset_details)
                          cb("success", asset_details)
                    } else {
                        cb("error" , result.error)
                    }
                })
            } else {
                 Vue.set( that.local_assets , asset_id , asset_details)
            }


        }, 

        get_downloaded_asset_path(asset_id){
            return (this.downloaded_assets[asset_id] || this.local_assets[asset_id] || {}).asset_path
        },

        get_downloaded_asset(asset_id){
            return (this.downloaded_assets[asset_id] || this.local_assets[asset_id] )
        },

        delete_asset(asset_id){
            let is_ollama = asset_id.startsWith('gemma4:');
            
            if (is_ollama) {
                Vue.delete(this.downloaded_assets, asset_id );
                Vue.delete(this.downloading, asset_id );
                Vue.delete(this.local_assets, asset_id );
                
                fetch("http://127.0.0.1:11435/api/delete", {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: asset_id })
                })
                .then(() => {
                    const router = this.app.$refs.router;
                    if (router && router.$refs && router.$refs['ModelStore'] && router.$refs['ModelStore'][0]) {
                        router.$refs['ModelStore'][0].check_ollama_models();
                    }
                })
                .catch(err => {
                    console.error("Failed to delete Ollama model:", err);
                });
                return;
            }

            let asset_details = this.downloaded_assets[asset_id] || this.local_assets[asset_id] || this.downloading[asset_id] 
            
            Vue.delete(this.downloaded_assets, asset_id );
            Vue.delete(this.downloading, asset_id );
            Vue.delete(this.local_assets, asset_id );

            if (asset_details && asset_details.asset_path) {
                window.ipcRenderer.sendSync('delete_file',  asset_details.asset_path );
            }
        },

        download_asset(asset_details){
            asset_details = JSON.parse(JSON.stringify(asset_details))
            let that = this;
            let asset_id = asset_details.id;

            if (asset_details.is_ollama_model) {
                Vue.set(this.downloading, asset_id, {
                    id: asset_id,
                    status: 'downloading',
                    progress: 0
                });
                
                fetch("http://127.0.0.1:11435/api/pull", {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: asset_details.id, stream: true })
                })
                .then(async (response) => {
                    if (!response.ok) {
                        throw new Error("HTTP error " + response.status);
                    }
                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();
                    let buffer = "";
                    let reading = true;
                    while (reading) {
                        const { done, value } = await reader.read();
                        if (done) {
                            reading = false;
                            break;
                        }
                        
                        buffer += decoder.decode(value, { stream: true });
                        const lines = buffer.split("\n");
                        buffer = lines.pop();
                        
                        for (const line of lines) {
                            if (!line.trim()) continue;
                            try {
                                const data = JSON.parse(line);
                                if (data.error) {
                                    throw new Error(data.error);
                                }
                                if (data.status === 'success') {
                                    Vue.set(that.downloading[asset_id], 'status', 'done');
                                    const router = that.app.$refs.router;
                                    if (router && router.$refs && router.$refs['ModelStore'] && router.$refs['ModelStore'][0]) {
                                        router.$refs['ModelStore'][0].check_ollama_models();
                                    }
                                } else if (data.total && data.completed) {
                                    const percent = Math.round((data.completed / data.total) * 100);
                                    Vue.set(that.downloading[asset_id], 'progress', percent);
                                }
                            } catch (e) {
                                console.error("Error parsing Ollama stream chunk:", e);
                            }
                        }
                    }
                    
                    // Final verification after stream closes
                    fetch("http://127.0.0.1:11435/api/tags")
                        .then(r => r.json())
                        .then(data => {
                            const downloaded = data.models.map(m => m.name);
                            if (downloaded.includes(asset_details.id)) {
                                Vue.set(that.downloading[asset_id], 'status', 'done');
                            } else {
                                if (that.downloading[asset_id] && that.downloading[asset_id].status !== 'done') {
                                    Vue.set(that.downloading[asset_id], 'status', 'error');
                                    Vue.set(that.downloading[asset_id], 'error', 'Download ended prematurely');
                                }
                            }
                            const router = that.app.$refs.router;
                            if (router && router.$refs && router.$refs['ModelStore'] && router.$refs['ModelStore'][0]) {
                                router.$refs['ModelStore'][0].check_ollama_models();
                            }
                        });
                })
                .catch((err) => {
                    console.error("Ollama pull error:", err);
                    Vue.set(that.downloading[asset_id], 'status', 'error');
                    Vue.set(that.downloading[asset_id], 'error', err.message || 'Network error');
                });
                return;
            }

            if (asset_id === 'flux_klein') {
                const token = this.app.app_state.app_data.settings.hf_token;
                if (!token) {
                    alert("Please enter your Hugging Face Token in Settings to download FLUX.2 [klein].");
                    return;
                }
                
                Vue.set(this.downloading, asset_id, {
                    id: asset_id,
                    status: 'downloading',
                    progress: 0
                });
                
                this.app.app_state.global_loader_modal_msg = "Downloading FLUX.2 [klein]... This may take a while.";
                this.app.app_state.global_loader_percentage = 0;
                
                send_to_py("dndl " + JSON.stringify({
                    model: "black-forest-labs/FLUX.2-klein-9B",
                    hf_token: token
                }));
                return;
            }

            if (asset_id === 'flux_schnell') {
                Vue.set(this.downloading, asset_id, {
                    id: asset_id,
                    status: 'downloading',
                    progress: 0
                });
                
                this.app.app_state.global_loader_modal_msg = "Downloading FLUX.1-schnell... This may take a while.";
                this.app.app_state.global_loader_percentage = 0;
                
                send_to_py("dndl " + JSON.stringify({
                    model: "black-forest-labs/FLUX.1-schnell",
                    hf_token: this.app.app_state.app_data.settings.hf_token || ""
                }));
                return;
            }

            let asset_hash = asset_details.md5;
            let asset_filename = asset_details.filename;

            if(this.downloaded_assets[asset_id]){
                return;
            }
            if(this.downloading[asset_id] && this.downloading[asset_id].status == 'done' ){
                return;
            }

            // const path = require('path');
            let dir = window.ipcRenderer.sendSync('get_assets_dir') 
            // let dest_path = path.join(dir, asset_id + "_" + asset_filename)
            let dest_path =  dir + "/" +  asset_id + "_" + asset_filename
            asset_details.asset_path_raw = dest_path

            let convert_to_tdict = false;

            if(asset_details.post_process && asset_details.post_process == 'convert_sd_to_tdict' ){
                convert_to_tdict = true
            }

            function on_progress(progress){
                if(convert_to_tdict)
                    progress = Math.round(progress*0.9)
                console.log("downlaod progress "+ progress)
                Vue.set( that.downloading[asset_id] , 'progress' , progress)
            }

            function on_success(){

                if(convert_to_tdict){

                        asset_details.post_process_params = asset_details.post_process_params || {}
                        asset_details.post_process_params.delete_origional_always = true;
                        let model_name = asset_id + "_" + asset_filename
                        window.ipcRenderer.invoke('add_custom_pytorch_models', asset_details.asset_path_raw,  model_name, asset_details.post_process_params ).then((result) => {
                            that.is_custom_model_loading = false
                            if(result.success){
                                // todo update the metadata 
                                asset_details.model_meta_data = asset_details.model_meta_data || {}
                                asset_details.asset_path = result.model_path 

                                asset_details.model_meta_data  = { // update the dict
                                  ...asset_details.model_meta_data ,
                                  ...result.metadata
                                }

                                Vue.set( that.downloading[asset_id] , 'status' , 'done')
                                Vue.set( that.downloaded_assets , asset_id , asset_details)

                            } else {
                                Vue.set( that.downloading[asset_id] , 'status' , 'error')
                                Vue.set( that.downloading[asset_id] , 'error' , result.error.slice(-30)  )
                            }
                        })
                } else {
                    asset_details.asset_path = asset_details.asset_path_raw
                    Vue.set( that.downloading[asset_id] , 'status' , 'done')
                    Vue.set( that.downloaded_assets , asset_id , asset_details)
                }

            }

            function on_error(error ){
                Vue.set( that.downloading[asset_id] , 'status' , 'error')
                Vue.set( that.downloading[asset_id] , 'error' , error )
            }

            Vue.set( that.downloading  , asset_id , asset_details)
            Vue.set( that.downloading[asset_id] , 'status' , 'downloading')

            let hf_token = "";
            if (this.app && this.app.app_state && this.app.app_state.app_data && this.app.app_state.app_data.settings) {
                hf_token = this.app.app_state.app_data.settings.hf_token || "";
            }

            download_file( asset_details.url , dest_path , asset_hash  , on_progress , on_success ,  on_error , hf_token )

        }
            
    },
}
</script>
<style>
</style>
<style scoped>
</style>