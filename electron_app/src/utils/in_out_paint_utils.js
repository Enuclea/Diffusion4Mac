function inpaint_assets(self , mode ){
    // Avoid unused variables lint errors
    if (self && mode) { /* no-op */ }
    return [];
}

function prep_sd_optins(self , sd_options_object, mode , img_mask_url){
    if (self && mode) { /* no-op */ }
    if(!sd_options_object.num_imgs)
        sd_options_object.num_imgs = 1

    sd_options_object.mask_image_path = img_mask_url
    sd_options_object.sd_mode_override = "txt2img"
}

export { prep_sd_optins ,  inpaint_assets }