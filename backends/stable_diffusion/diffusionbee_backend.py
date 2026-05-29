import sys
sys.modules['tensorflow'] = None
sys.modules['keras'] = None

import json
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_NO_TF"] = "1"
import random
import traceback
from pathlib import Path
from PIL import Image
import torch
from diffusers import FluxPipeline, FluxImg2ImgPipeline, FluxInpaintPipeline

try:
    from diffusers import Flux2KleinPipeline, Flux2KleinInpaintPipeline
except ImportError:
    pass

print("starting backend")

home_path = Path.home()
projects_root_path = os.path.join(home_path, ".diffusionbee")
default_data_root = os.path.join(projects_root_path, "images")

if not os.path.isdir(default_data_root):
    os.makedirs(default_data_root, exist_ok=True)

class Unbuffered(object):
    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

    def writelines(self, datas):
        self.stream.writelines(datas)
        self.stream.flush()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)

sys.stdout = Unbuffered(sys.stdout)

def get_input():
    return sys.stdin.readline()

def load_image(image_path):
    if not image_path or not os.path.exists(image_path):
        return None
    try:
        return Image.open(image_path).convert("RGB")
    except:
        return None

def resize_image_aspect(img, max_dim=1024):
    if not img:
        return None
    w, h = img.size
    if w <= max_dim and h <= max_dim:
        new_w = (w // 16) * 16
        new_h = (h // 16) * 16
        if new_w == w and new_h == h:
            return img
        resample_filter = getattr(Image, "Resampling", Image).LANCZOS
        return img.resize((new_w, new_h), resample_filter)

    if w > h:
        new_w = max_dim
        new_h = int(h * (max_dim / w))
    else:
        new_h = max_dim
        new_w = int(w * (max_dim / h))

    new_w = max(16, (new_w // 16) * 16)
    new_h = max(16, (new_h // 16) * 16)
    resample_filter = getattr(Image, "Resampling", Image).LANCZOS
    return img.resize((new_w, new_h), resample_filter)

def main():
    print("sdbk mdld") # notify UI model logic is ready to load/run

    current_model = None
    pipe = None
    pipe_img2img = None
    pipe_kv = None
    pipe_inpaint = None

    while True:
        print("sdbk inrd") # input ready

        inp_str = get_input()
        if inp_str.strip() == "":
            continue

        if "__stop__" in inp_str:
            break

        if "b2py dndl" in inp_str:
            print("sdbk inwk")
            try:
                json_str = inp_str.replace("b2py dndl", "").strip()
                data = json.loads(json_str)
                model_name = data.get("model", "black-forest-labs/FLUX.2-klein-9B")
                token = data.get("hf_token", None)
                if token == "":
                    token = None
                
                # set token in env globally too just in case
                if token:
                    os.environ["HF_TOKEN"] = token
                    os.environ["HUGGING_FACE_HUB_TOKEN"] = token

                print("sdbk mltl Downloading " + model_name)
                sys.stdout.flush()

                from huggingface_hub import snapshot_download
                from tqdm.auto import tqdm

                class HuggingFaceDownloadProgress(tqdm):
                    def __init__(self, *args, **kwargs):
                        super().__init__(*args, **kwargs)
                        self._last_printed = -1
                    def update(self, n=1):
                        super().update(n)
                        if self.total:
                            percent = int((self.n / self.total) * 100)
                            if percent > self._last_printed:
                                self._last_printed = percent
                                print(f"sdbk mlpr {percent}")
                                sys.stdout.flush()

                snapshot_download(
                    repo_id=model_name,
                    token=token,
                    tqdm_class=HuggingFaceDownloadProgress
                )
                print("sdbk mdld")
                sys.stdout.flush()
            except Exception as e:
                print(f"sdbk errr {str(e)}")
                sys.stdout.flush()
            continue

        if not "b2py t2im" in inp_str:
            continue

        print("sdbk inwk") # working
        
        try:
            # parse json
            json_str = inp_str.replace("b2py t2im", "").strip()
            data = json.loads(json_str)

            prompt = data.get("prompt", "")
            num_imgs = data.get("num_imgs", 1)
            num_steps = data.get("num_steps", 25)
            guidance_scale = data.get("guidance_scale", 7.5)
            seed = data.get("seed", -1)
            hf_token = data.get("hf_token", None)
            if hf_token == "":
                hf_token = None
            if hf_token:
                os.environ["HF_TOKEN"] = hf_token
                os.environ["HUGGING_FACE_HUB_TOKEN"] = hf_token

            if seed == -1:
                seed = random.randint(0, 2147483647)

            # Resolve input image with fallback keys from UI
            input_image_path = data.get("input_image", None) or data.get("input_img", None) or data.get("input_image_with_mask", None)

            # advanced custom form tags
            raw_form_options = data.get("raw_form_options", {})
            model_selection = raw_form_options.get("model_selection", "Flux Schnell") or data.get("model_selection", "Flux Schnell")
            
            # Retrieve LoRA parameters from root data (injected via LoraStore) or fallback to raw_form_options (advanced UI field)
            lora_path = data.get("lora_path", None) or raw_form_options.get("lora_path", None)
            lora_paths = data.get("lora_paths", []) or raw_form_options.get("lora_paths", [])
            if lora_path and not lora_paths:
                lora_paths = [lora_path]

            lora_weight = data.get("lora_weight", None)
            if lora_weight is None:
                lora_weight = raw_form_options.get("lora_weight", 1.0)
            
            lora_weights = data.get("lora_weights", []) or raw_form_options.get("lora_weights", [])
            if not lora_weights:
                if lora_weight is not None:
                    try:
                        lora_weights = [float(lora_weight)]
                    except Exception:
                        lora_weights = [1.0]
                else:
                    lora_weights = [1.0] * len(lora_paths)

            # Get target image dimensions to resize guide/reference images accordingly
            target_width = data.get("img_width", 1024)
            target_height = data.get("img_height", 1024)
            max_dim = max(target_width, target_height)

            # Load all available guide images and downsize them to target size
            guide_images = []
            guide_image_paths = []
            for key in ["guide_img_1", "guide_img_2", "guide_img_3", "guide_img_4"]:
                path_val = raw_form_options.get(key, None)
                if path_val:
                    guide_image_paths.append((key, path_val))
                    img = load_image(path_val)
                    if img:
                        img = resize_image_aspect(img, max_dim)
                        guide_images.append(img)

            # Handle parsed options
            print(f"Backend options: model_selection={model_selection}, input_image_path={input_image_path}")
            print(f"Loaded {len(guide_images)} guide images.")

            model_id = "black-forest-labs/FLUX.1-schnell"
            if model_selection == "Flux Klein":
                model_id = "black-forest-labs/FLUX.2-klein-9B"

            device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
            dtype = torch.bfloat16

            # Setup pipeline if model changed or uninitialized
            if current_model != model_id:
                print("sdbk mdld Loading model weights...")
                
                if pipe is not None:
                    del pipe
                if pipe_img2img is not None:
                    del pipe_img2img
                if pipe_kv is not None:
                    del pipe_kv
                pipe_inpaint = None
                torch.cuda.empty_cache() if torch.cuda.is_available() else None

                if model_selection == "Flux Klein" and "Flux2KleinPipeline" in globals():
                    # use standard pipeline for klein multi-image editing or standard text2img
                    pipe = Flux2KleinPipeline.from_pretrained(model_id, torch_dtype=dtype, token=hf_token)
                    if hasattr(pipe, "enable_model_cpu_offload"):
                        try:
                            pipe.enable_model_cpu_offload(device=device)
                        except Exception as e:
                            print(f"sdbk warn CPU offload failed: {e}")
                            pipe.to(device)
                    else:
                        pipe.to(device)
                    if "Flux2KleinInpaintPipeline" in globals():
                        pipe_inpaint = Flux2KleinInpaintPipeline(**pipe.components)
                else:
                    # Schnell or standard Klein
                    pipe = FluxPipeline.from_pretrained(model_id, torch_dtype=dtype, token=hf_token)
                    if hasattr(pipe, "enable_model_cpu_offload"):
                        try:
                            pipe.enable_model_cpu_offload(device=device)
                        except Exception as e:
                            print(f"sdbk warn CPU offload failed: {e}")
                            pipe.to(device)
                    else:
                        pipe.to(device)
                    pipe_img2img = FluxImg2ImgPipeline(**pipe.components)
                    if "FluxInpaintPipeline" in globals():
                        pipe_inpaint = FluxInpaintPipeline(**pipe.components)

                current_model = model_id

            # Handle LoRA weights loading/unloading
            def apply_loras(pipeline, paths, weights):
                if not pipeline:
                    return
                # Unload first
                if hasattr(pipeline, "unload_lora_weights"):
                    try:
                        pipeline.unload_lora_weights()
                    except Exception:
                        pass
                if not paths:
                    return
                
                # Load each
                loaded_adapters = []
                loaded_weights = []
                for idx, path in enumerate(paths):
                    if not path or not os.path.exists(path):
                        continue
                    adapter_name = f"lora_{idx}"
                    try:
                        print(f"Loading LoRA {idx}: {path}")
                        pipeline.load_lora_weights(path, adapter_name=adapter_name)
                        loaded_adapters.append(adapter_name)
                        w = 1.0
                        if idx < len(weights):
                            try:
                                w = float(weights[idx])
                            except Exception:
                                pass
                        loaded_weights.append(w)
                    except Exception as e:
                        print(f"Error loading LoRA {path}: {e}")
                        is_corrupt = "checkpoint" in str(e) or "safetensors" in str(e) or "invalid" in str(e).lower()
                        if is_corrupt:
                            try:
                                if os.path.exists(path):
                                    print(f"Removing corrupt LoRA file: {path}")
                                    os.remove(path)
                            except Exception as de:
                                print(f"Failed to remove corrupt LoRA: {de}")
                        else:
                            # Only try fallback if it wasn't deleted as corrupt
                            try:
                                pipeline.load_lora_weights(path)
                            except Exception as e2:
                                print(f"Fallback loading failed: {e2}")
                                if "checkpoint" in str(e2) or "safetensors" in str(e2) or "invalid" in str(e2).lower():
                                    try:
                                        if os.path.exists(path):
                                            print(f"Removing corrupt LoRA file: {path}")
                                            os.remove(path)
                                    except Exception as de:
                                        print(f"Failed to remove corrupt LoRA: {de}")
                
                # Set active adapters
                if loaded_adapters and hasattr(pipeline, "set_adapters"):
                    try:
                        print(f"Setting active adapters: {loaded_adapters} with weights: {loaded_weights}")
                        try:
                            pipeline.set_adapters(loaded_adapters, adapter_weights=loaded_weights)
                        except TypeError:
                            pipeline.set_adapters(loaded_adapters, weights=loaded_weights)
                    except Exception as e:
                        print(f"Error setting active adapters: {e}")

            # Load input image and mask image first to determine the active pipeline
            input_image = load_image(input_image_path)
            if input_image:
                input_image = resize_image_aspect(input_image, max_dim)

            mask_image_path = data.get("mask_image_path", None)
            mask_image = load_image(mask_image_path) if mask_image_path else None

            # Setup active pipeline reference
            active_pipe = pipe
            if mask_image and input_image:
                if pipe_inpaint is None:
                    print("Initializing inpainting pipeline from loaded components...")
                    if model_selection == "Flux Klein" and "Flux2KleinInpaintPipeline" in globals():
                        pipe_inpaint = Flux2KleinInpaintPipeline(**pipe.components)
                    elif "FluxInpaintPipeline" in globals():
                        pipe_inpaint = FluxInpaintPipeline(**pipe.components)
                active_pipe = pipe_inpaint
            elif model_selection == "Flux Klein" and "Flux2KleinPipeline" in globals():
                active_pipe = pipe
            else:
                ref_image = input_image or (guide_images[0] if guide_images else None)
                if ref_image:
                    active_pipe = pipe_img2img
                else:
                    active_pipe = pipe

            apply_loras(active_pipe, lora_paths, lora_weights)

            generator = torch.Generator(device=device).manual_seed(seed)

            if mask_image and input_image:
                if mask_image.size != input_image.size:
                    mask_image = mask_image.resize(input_image.size)

            for i in range(num_imgs):
                print(f"sdbk dnpr {i}/{num_imgs}")

                if mask_image and input_image:
                    w, h = input_image.size
                    inpaint_w = ((w + 8) // 16) * 16
                    inpaint_h = ((h + 8) // 16) * 16

                    log_msg = f"Running Inpainting with input size {input_image.size} (rounded to {inpaint_w}x{inpaint_h}) and mask size {mask_image.size}"
                    print(log_msg)

                    with torch.inference_mode():
                        if model_selection == "Flux Klein" and pipe_inpaint is not None:
                            out = pipe_inpaint(
                                prompt=prompt,
                                image=input_image,
                                mask_image=mask_image,
                                height=inpaint_h,
                                width=inpaint_w,
                                num_inference_steps=num_steps,
                                generator=generator
                            )
                        elif pipe_inpaint is not None:
                            out = pipe_inpaint(
                                prompt=prompt,
                                image=input_image,
                                mask_image=mask_image,
                                height=inpaint_h,
                                width=inpaint_w,
                                guidance_scale=guidance_scale,
                                num_inference_steps=num_steps,
                                generator=generator
                            )
                        else:
                            raise ValueError("Inpainting pipeline is not initialized or not supported.")
                elif model_selection == "Flux Klein" and "Flux2KleinPipeline" in globals():
                    ref_imgs = guide_images + ([input_image] if input_image else [])
                    if ref_imgs:
                        log_msg = f"Running Flux2KleinPipeline with {len(ref_imgs)} reference images: " + ", ".join([str(img.size) for img in ref_imgs])
                        print(log_msg)
                        with torch.inference_mode():
                            out = pipe(
                                prompt=prompt,
                                image=ref_imgs,
                                num_inference_steps=num_steps,
                                generator=generator
                            )
                    else:
                        print("Running Flux2KleinPipeline as Text2Img")
                        with torch.inference_mode():
                            out = pipe(
                                prompt=prompt,
                                num_inference_steps=num_steps,
                                generator=generator,
                                height=data.get("img_height", 1024),
                                width=data.get("img_width", 1024)
                            )
                else:
                    ref_image = input_image or (guide_images[0] if guide_images else None)
                    if ref_image:
                        w, h = ref_image.size
                        img2img_w = ((w + 8) // 16) * 16
                        img2img_h = ((h + 8) // 16) * 16
                        
                        user_strength = data.get("input_image_strength", None)
                        strength = float(user_strength) / 100.0 if user_strength is not None else 0.8
                        
                        print(f"Running FluxImg2ImgPipeline with dimensions {img2img_w}x{img2img_h} and strength {strength}")
                        with torch.inference_mode():
                            out = pipe_img2img(
                                prompt=prompt,
                                image=ref_image,
                                height=img2img_h,
                                width=img2img_w,
                                guidance_scale=guidance_scale,
                                num_inference_steps=num_steps,
                                generator=generator,
                                strength=strength
                            )
                    else:
                        print("Running standard FluxPipeline Text2Img")
                        with torch.inference_mode():
                            out = pipe(
                                prompt=prompt,
                                guidance_scale=guidance_scale,
                                num_inference_steps=num_steps,
                                generator=generator,
                                height=data.get("img_height", 1024),
                                width=data.get("img_width", 1024)
                            )

                img = out.images[0]

                s = ''.join(filter(str.isalnum, prompt[:30]))
                fpath = os.path.join(default_data_root, f"{s}_{random.randint(0,100000000)}.png")
                
                save_exif_meta = data.get("save_exif_meta", False)
                if save_exif_meta:
                    from PIL.PngImagePlugin import PngInfo
                    metadata = PngInfo()
                    meta_to_save = {}
                    for k, v in data.items():
                        if isinstance(v, str) and (v.startswith("data:image") or len(v) > 10000):
                            continue
                        meta_to_save[k] = v
                    metadata.add_text("Description", json.dumps(meta_to_save))
                    metadata.add_text("UserComment", json.dumps(meta_to_save))
                    img.save(fpath, pnginfo=metadata)
                else:
                    img.save(fpath)

                ret_dict = {"generated_img_path": fpath}
                print("sdbk nwim %s" % (json.dumps(ret_dict)))

                # Clean up memory after each image in the batch
                out = None
                img = None
                import gc
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    if hasattr(torch.mps, 'empty_cache'):
                        torch.mps.empty_cache()

        except Exception as e:
            print(f"Exception during message handling: {e}")
            traceback.print_exc()
        finally:
            out = None
            img = None
            input_image = None
            mask_image = None
            ref_image = None
            guide_images = None
            ref_imgs = None
            import gc
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                if hasattr(torch.mps, 'empty_cache'):
                    torch.mps.empty_cache()

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    import traceback
    try:
        main()
    except Exception as e:
        traceback.print_exc()
