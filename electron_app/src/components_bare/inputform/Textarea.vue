<template>
   <div style="position: relative; width: 100%;"> 
         <textarea 
             v-model="form_values[config.id]" 
             style="border-radius: 5px; width: 100%; resize: none; padding-bottom: 40px;" 
             class="form-control"  
             :placeholder="config.placeholder || '' " 
             :rows="config.is_small? 3 : 7"></textarea>
          
          <button 
              v-if="config.id === 'prompt'" 
              @click="rewritePrompt" 
              class="ai_assist_btn" 
              :disabled="rewriting"
          >
              <span v-if="rewriting" class="ai_spinner"></span>
              <span v-else style="margin-right: 4px;">✨</span>
              {{ rewriting ? 'Rewriting...' : 'AI Assist' }}
          </button>
   </div> 
</template>
<script>

import FormInputMixin from "./FormInputMixin.vue"
import { icon_library } from "../icon_library.js"
import Vue from 'vue'

export default {
    name: 'Textarea',
    mixins: [FormInputMixin],
    props: {
         config: Object , 
        form_values: Object,
    },
    components: {},
    mounted() {
        if(this.form_values[this.config.id] === undefined && this.config.default_value != undefined ){
            Vue.set( this.form_values  , this.config.id  , this.config.default_value  )
        } 
    },
    data() {
        return {
            icon_library:icon_library,
            rewriting: false
        };
    },
    methods: {
        async rewritePrompt() {
            const currentPrompt = this.form_values[this.config.id];
            if (!currentPrompt || !currentPrompt.trim()) {
                alert("Please enter a basic prompt first before using AI Assist.");
                return;
            }
            
            this.rewriting = true;
            try {
                const tagsResponse = await fetch("http://127.0.0.1:11435/api/tags").catch(() => null);
                if (!tagsResponse) {
                    alert("Ollama is not running. Please make sure Ollama is active on port 11435.");
                    this.rewriting = false;
                    return;
                }
                const tagsData = await tagsResponse.json();
                const downloadedModels = tagsData.models ? tagsData.models.map(m => m.name) : [];
                
                let preferredModel = "gemma4:e4b";
                if (window.app && window.app.app_state && window.app.app_state.app_data && window.app.app_state.app_data.settings) {
                    preferredModel = window.app.app_state.app_data.settings.gemma_preferred_model || "gemma4:e4b";
                }
                
                if (!downloadedModels.includes(preferredModel)) {
                    const otherModel = preferredModel === "gemma4:e4b" ? "gemma4:e2b" : "gemma4:e4b";
                    if (downloadedModels.includes(otherModel)) {
                        preferredModel = otherModel;
                    } else {
                        alert("Please download Gemma 4 [e2b] or [e4b] in the Model Store to use AI Assist.");
                        this.rewriting = false;
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
                                role: 'system', 
                                content: 'You are a Stable Diffusion prompt engineering expert. Rewrite the user\'s input prompt to be more detailed, visually rich, and optimized for high-quality image generation. Keep it under 75 words. Do not include any introductory or concluding text, markdown formatting, quotes, or explanations. Only return the rewritten prompt.' 
                            },
                            { role: 'user', content: currentPrompt }
                        ],
                        stream: false
                    })
                });
                
                if (!response.ok) {
                    throw new Error("HTTP error " + response.status);
                }
                
                const data = await response.json();
                if (data.message && data.message.content) {
                    const rewritten = data.message.content.trim();
                    Vue.set(this.form_values, this.config.id, rewritten);
                } else {
                    throw new Error("Invalid response format from Ollama");
                }
            } catch (e) {
                console.error("AI Assist rewrite error:", e);
                alert("Error during prompt rewrite: " + e.message);
            } finally {
                this.rewriting = false;
            }
        }
    },
}
</script>
<style>
</style>
<style scoped>
.ai_assist_btn {
    position: absolute;
    bottom: 8px;
    right: 8px;
    background: linear-gradient(135deg, #6366f1, #a855f7);
    color: white;
    border: none;
    border-radius: 6px;
    padding: 5px 12px;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    box-shadow: 0 2px 8px rgba(168, 85, 247, 0.4);
    transition: all 0.2s ease;
    z-index: 10;
}

.ai_assist_btn:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(168, 85, 247, 0.6);
    filter: brightness(1.1);
}

.ai_assist_btn:disabled {
    opacity: 0.7;
    cursor: not-allowed;
    background: #4b5563;
    box-shadow: none;
}

.ai_spinner {
    width: 12px;
    height: 12px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    border-top-color: white;
    animation: ai_spin 0.8s linear infinite;
    margin-right: 6px;
}

@keyframes ai_spin {
    to { transform: rotate(360deg); }
}
</style>