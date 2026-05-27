import sys
import json
import os
import random
from pathlib import Path
from PIL import Image
import torch
from diffusers import FluxPipeline, FluxImg2ImgPipeline

try:
    from diffusers import Flux2KleinKVPipeline
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

def main():
    print("sdbk mdld") # notify UI model logic is ready to load/run

    current_model = None
    pipe = None
    pipe_img2img = None
    pipe_kv = None

    while True:
        print("sdbk inrd") # input ready

        inp_str = get_input()
        if inp_str.strip() == "":
            continue

        if "__stop__" in inp_str:
            break

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

            if seed == -1:
                seed = random.randint(0, 2147483647)

            input_image_path = data.get("input_image", None)

            # advanced custom form tags
            raw_form_options = data.get("raw_form_options", {})
            model_selection = raw_form_options.get("model_selection", "Flux Schnell")
            guide_img_1_path = raw_form_options.get("guide_img_1", None)
            lora_path = raw_form_options.get("lora_path", None)

            model_id = "black-forest-labs/FLUX.1-schnell"
            if model_selection == "Flux Klein":
                model_id = "black-forest-labs/FLUX.1-schnell" # fall back to standard model if custom gated pipeline not installed

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
                torch.cuda.empty_cache() if torch.cuda.is_available() else None

                if model_selection == "Flux Klein" and "Flux2KleinKVPipeline" in globals():
                    # use KV pipeline for klein multi-image editing or standard text2img
                    pipe = Flux2KleinKVPipeline.from_pretrained(model_id, torch_dtype=dtype)
                    pipe.to(device)
                else:
                    # Schnell or standard Klein
                    pipe = FluxPipeline.from_pretrained(model_id, torch_dtype=dtype)
                    pipe.to(device)
                    pipe_img2img = FluxImg2ImgPipeline.from_pretrained(model_id, torch_dtype=dtype)
                    pipe_img2img.to(device)

                current_model = model_id

            if lora_path and os.path.exists(lora_path):
                pipe.load_lora_weights(lora_path)
                if pipe_img2img:
                    pipe_img2img.load_lora_weights(lora_path)

            generator = torch.Generator(device=device).manual_seed(seed)

            input_image = load_image(input_image_path)
            guide_image = load_image(guide_img_1_path)

            for i in range(num_imgs):
                print(f"sdbk dnpr {i}/{num_imgs}")

                if model_selection == "Flux Klein":
                    if guide_image:
                        # multi reference KV editing
                        # diffusers API for KV pipeline usually accepts reference_images list
                        out = pipe(
                            prompt=prompt,
                            reference_images=[guide_image] + ([input_image] if input_image else []),
                            guidance_scale=guidance_scale,
                            num_inference_steps=num_steps,
                            generator=generator
                        )
                    else:
                        # basic T2I with Klein KV pipeline handles standard inputs too usually
                        # or fallback to FluxPipeline if needed
                        out = pipe(
                            prompt=prompt,
                            guidance_scale=guidance_scale,
                            num_inference_steps=num_steps,
                            generator=generator,
                            height=data.get("img_height", 1024),
                            width=data.get("img_width", 1024)
                        )
                else:
                    if input_image:
                        out = pipe_img2img(
                            prompt=prompt,
                            image=input_image,
                            guidance_scale=guidance_scale,
                            num_inference_steps=num_steps,
                            generator=generator,
                            strength=0.8
                        )
                    else:
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
                img.save(fpath)

                ret_dict = {"generated_img_path": fpath}
                print("sdbk nwim %s" % (json.dumps(ret_dict)))

        except Exception as e:
            print(f"Error processing: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    import traceback
    try:
        main()
    except Exception as e:
        traceback.print_exc()
