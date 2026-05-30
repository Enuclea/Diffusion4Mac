<template>
    <SDImageGenerationApplet 
        ref="sd_applet"   
        name="img2img" :form_data="form_data" :form_tags="[  'img2img']" :app="app" 
        :check_options_input_fn="check_options_input_fn"
        :postprocess_form_options_fn="postprocess_form_options_fn"> </SDImageGenerationApplet>
</template>
<script>


import SDImageGenerationApplet from "../components/SDImageGenerationApplet.vue"
import Vue from 'vue'


const Img2Img = {
    name: 'Img2Img',
    props: {
        app:Object, 
    },
    components: {SDImageGenerationApplet},
    mounted() {
        this.app.functions.send_to_img2img = this.send_to_img2img; 
    },
    data() {
        let form_data = require("../forms/sd_options_adv.json")
        
        return {
            form_data:form_data, 
        };
    },
    methods: {
       send_to_img2img(im_path, params ){
          Vue.set( this.$refs.sd_applet.sd_options , "input_img" ,  im_path );
          if(params){
             params = JSON.parse(JSON.stringify(params))
             params.input_img = undefined
             params.seed = undefined
             if(params.raw_form_options) {
                params.raw_form_options.input_img = undefined
                params.raw_form_options.seed = undefined
             }
             this.$refs.sd_applet.load_options(params)
          }
          this.app.functions.switch_page("Img2Img")

       }, 

       check_options_input_fn(){
            if((!this.$refs.sd_applet.sd_options.input_img) || this.$refs.sd_applet.sd_options.input_img=="" ){
                this.app.show_toast("You need to specify an input image")
                return false
            } else {
                return true
            }
       }, 

       postprocess_form_options_fn(options){
            let w = options.img_width || this.$refs.sd_applet.sd_options.input_img__AUX__width || 1024;
            let h = options.img_height || this.$refs.sd_applet.sd_options.input_img__AUX__height || 1024;

            const max_dim = 1024;
            if (w > max_dim || h > max_dim) {
                if (w > h) {
                    h = Math.round(h * (max_dim / w));
                    w = max_dim;
                } else {
                    w = Math.round(w * (max_dim / h));
                    h = max_dim;
                }
            }

            // Ensure dimensions are multiples of 16
            options.img_width = Math.round(w / 16) * 16;
            options.img_height = Math.round(h / 16) * 16;

            return options
       }
    },
}

export default Img2Img;
Img2Img.title = "Image to image"
Img2Img.description = "Transform images with text descriptions"
Img2Img.icon = "images"
Img2Img.img_icon = require("../assets/imgs/page_icon_imgs/img2img.png")
Img2Img.home_category = "main"
Img2Img.sidebar_show = "always"

</script>
<style>
</style>
<style scoped>
</style>