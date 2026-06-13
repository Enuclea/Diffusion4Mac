import sys
sys.modules['tensorflow'] = None
sys.modules['keras'] = None

# Monkeypatch bitsandbytes quantizer environment validation check and device map for Apple Silicon / MPS compatibility
try:
    from diffusers.quantizers.bitsandbytes.bnb_quantizer import BnB4BitDiffusersQuantizer, BnB8BitDiffusersQuantizer
    BnB4BitDiffusersQuantizer.validate_environment = lambda *args, **kwargs: None
    BnB8BitDiffusersQuantizer.validate_environment = lambda *args, **kwargs: None
    BnB4BitDiffusersQuantizer.update_device_map = lambda self, device_map: {"": "cpu"} if device_map is None else device_map
    BnB8BitDiffusersQuantizer.update_device_map = lambda self, device_map: {"": "cpu"} if device_map is None else device_map
except ImportError:
    pass

# Monkeypatch Qwen2Tokenizer to Qwen2TokenizerFast to allow loading from tokenizer.json only
try:
    import transformers
    import transformers.models.qwen2.tokenization_qwen2
    import transformers.models.qwen2
    transformers.models.qwen2.tokenization_qwen2.Qwen2Tokenizer = transformers.Qwen2TokenizerFast
    transformers.models.qwen2.Qwen2Tokenizer = transformers.Qwen2TokenizerFast
    transformers.Qwen2Tokenizer = transformers.Qwen2TokenizerFast
except ImportError:
    pass

# Monkeypatch Qwen3VLTextRotaryEmbedding to handle missing rope_scaling config
try:
    import transformers.models.qwen3_vl.modeling_qwen3_vl as qwen3_module
    orig_qwen3_init = qwen3_module.Qwen3VLTextRotaryEmbedding.__init__
    def patched_qwen3_init(self, *args, **kwargs):
        config = kwargs.get("config", args[0] if args else None)
        if config is not None:
            if getattr(config, "rope_scaling", None) is None:
                config.rope_scaling = {}
        return orig_qwen3_init(self, *args, **kwargs)
    qwen3_module.Qwen3VLTextRotaryEmbedding.__init__ = patched_qwen3_init
except Exception:
    pass

# Monkeypatch PreTrainedTokenizerBase._set_model_specific_special_tokens to handle list types safely
try:
    from transformers.tokenization_utils_base import PreTrainedTokenizerBase
    orig_set_tokens = PreTrainedTokenizerBase._set_model_specific_special_tokens
    def patched_set_tokens(self, special_tokens):
        if not isinstance(special_tokens, dict):
            special_tokens = {}
        return orig_set_tokens(self, special_tokens)
    PreTrainedTokenizerBase._set_model_specific_special_tokens = patched_set_tokens
except Exception:
    pass

# Monkeypatch create_causal_mask to handle inputs_embeds and missing cache_position
try:
    import transformers.masking_utils
    orig_create_causal_mask = transformers.masking_utils.create_causal_mask
    def patched_create_causal_mask(*args, **kwargs):
        if "inputs_embeds" in kwargs:
            kwargs["input_embeds"] = kwargs.pop("inputs_embeds")
        input_embeds = kwargs.get("input_embeds", None)
        if input_embeds is None and len(args) > 1:
            input_embeds = args[1]
        has_cache_position = "cache_position" in kwargs or len(args) > 3
        if not has_cache_position and input_embeds is not None:
            import torch
            query_length = input_embeds.shape[1]
            kwargs["cache_position"] = torch.arange(query_length, device=input_embeds.device)
        return orig_create_causal_mask(*args, **kwargs)
    transformers.masking_utils.create_causal_mask = patched_create_causal_mask
except Exception:
    pass

# Monkeypatch diffusers.utils.torch_utils.randn_tensor to always generate on CPU when device is MPS
try:
    import diffusers.utils.torch_utils
    orig_randn_tensor = diffusers.utils.torch_utils.randn_tensor
    def patched_randn_tensor(shape, generator=None, device=None, dtype=None, layout=None):
        import torch
        target_device = device
        if isinstance(target_device, str):
            target_device = torch.device(target_device)
        elif target_device is None:
            target_device = torch.device("cpu")
            
        if target_device.type == "mps":
            cpu_generator = None
            if generator is not None:
                if isinstance(generator, list):
                    cpu_generator = []
                    for g in generator:
                        if g.device.type == "mps":
                            cg = torch.Generator(device="cpu")
                            cg.set_state(g.get_state())
                            cpu_generator.append(cg)
                        else:
                            cpu_generator.append(g)
                elif generator.device.type == "mps":
                    cpu_generator = torch.Generator(device="cpu")
                    cpu_generator.set_state(generator.get_state())
                else:
                    cpu_generator = generator
            res = orig_randn_tensor(shape, generator=cpu_generator, device=torch.device("cpu"), dtype=dtype, layout=layout)
            return res.to(target_device)
        return orig_randn_tensor(shape, generator=generator, device=device, dtype=dtype, layout=layout)
    diffusers.utils.torch_utils.randn_tensor = patched_randn_tensor
except Exception:
    pass

# Apply PyTorch 2.4 compatibility monkeypatch for macOS x86_64 PyTorch 2.2.2
import importlib.metadata
orig_metadata_version = importlib.metadata.version
importlib.metadata.version = lambda name: "2.4.0" if name == "torch" else orig_metadata_version(name)

import types
import torch
import torch.nn

if not hasattr(torch.nn, "RMSNorm"):
    import numbers
    class DummyRMSNorm(torch.nn.Module):
        def __init__(self, normalized_shape, eps=1e-05, elementwise_affine=True, device=None, dtype=None):
            super().__init__()
            self.eps = eps
            self.elementwise_affine = elementwise_affine
            if isinstance(normalized_shape, numbers.Integral):
                normalized_shape = (normalized_shape,)
            self.normalized_shape = tuple(normalized_shape)
            if elementwise_affine:
                self.weight = torch.nn.Parameter(torch.ones(self.normalized_shape, device=device, dtype=dtype))
            else:
                self.register_parameter('weight', None)

        def forward(self, x):
            input_dtype = x.dtype
            dims = tuple(range(-len(self.normalized_shape), 0))
            variance = x.to(torch.float32).pow(2).mean(dim=dims, keepdim=True)
            norm_x = x * torch.rsqrt(variance + self.eps)
            if self.elementwise_affine:
                if self.weight.dtype in [torch.float16, torch.bfloat16]:
                    norm_x = norm_x.to(self.weight.dtype)
                return norm_x * self.weight
            return norm_x.to(input_dtype)

    torch.nn.RMSNorm = DummyRMSNorm

if not hasattr(torch, "get_default_device"):
    def _get_default_device():
        try:
            return torch.device(torch._C._get_default_device())
        except Exception:
            return torch.device("cpu")
    torch.get_default_device = _get_default_device

orig_is_autocast_enabled = torch.is_autocast_enabled
def new_is_autocast_enabled(device_type="cuda"):
    if device_type == "cpu":
        return torch.is_autocast_cpu_enabled()
    elif device_type == "cuda":
        return orig_is_autocast_enabled()
    else:
        return False
torch.is_autocast_enabled = new_is_autocast_enabled

try:
    from torch.torch_version import TorchVersion
    torch.__version__ = TorchVersion("2.4.0")
except ImportError:
    torch.__version__ = "2.4.0"
torch.uint16 = torch.int16
torch.uint32 = torch.int32
torch.uint64 = torch.int64

# Monkeypatch torch.Tensor.to to convert float8 to float16 when moving to MPS
orig_to = torch.Tensor.to
def patched_to(self, *args, **kwargs):
    device = None
    try:
        if args and args[0] is not None:
            if isinstance(args[0], (str, torch.device)):
                device = torch.device(args[0])
        if "device" in kwargs and kwargs["device"] is not None:
            device = torch.device(kwargs["device"])
    except Exception:
        pass
        
    if device is None:
        try:
            device = self.device
        except Exception:
            pass
        
    float8_dtypes = []
    if hasattr(torch, "float8_e4m3fn"):
        float8_dtypes.append(torch.float8_e4m3fn)
    if hasattr(torch, "float8_e5m2"):
        float8_dtypes.append(torch.float8_e5m2)

    if device is not None and device.type == "mps":
        new_args = list(args)
        new_kwargs = dict(kwargs)
        has_float8_target = False
        
        if "dtype" in new_kwargs and new_kwargs["dtype"] in float8_dtypes:
            new_kwargs["dtype"] = torch.float16
            has_float8_target = True
            
        for idx, arg in enumerate(new_args):
            if arg in float8_dtypes:
                new_args[idx] = torch.float16
                has_float8_target = True
                
        if self.dtype in float8_dtypes:
            # Convert float8 to float16 on CPU first, then transfer to MPS
            cpu_fp16 = orig_to(self, device="cpu", dtype=torch.float16)
            return orig_to(cpu_fp16, *new_args, **new_kwargs)
            
        if has_float8_target:
            return orig_to(self, *new_args, **new_kwargs)

    return orig_to(self, *args, **kwargs)
torch.Tensor.to = patched_to

# Monkeypatch torch.nn.functional.linear to align input/bias dtypes to weight.dtype on MPS, avoiding device mismatch crashes
import torch.nn.functional as F
orig_linear = F.linear
def patched_linear(input, weight, bias=None):
    if input.device.type == "mps" or weight.device.type == "mps":
        target_dtype = torch.float16
        float8_dtypes = []
        if hasattr(torch, "float8_e4m3fn"):
            float8_dtypes.append(torch.float8_e4m3fn)
        if hasattr(torch, "float8_e5m2"):
            float8_dtypes.append(torch.float8_e5m2)
            
        if input.dtype in float8_dtypes:
            input = input.to(target_dtype)
        if weight.dtype in float8_dtypes:
            weight = weight.to(target_dtype)
        if bias is not None and bias.dtype in float8_dtypes:
            bias = bias.to(target_dtype)
            
        # Match input and bias dtypes to weight.dtype to avoid MPS NDArray datatype mismatch crash
        if input.dtype != weight.dtype:
            input = input.to(weight.dtype)
        if bias is not None and bias.dtype != weight.dtype:
            bias = bias.to(weight.dtype)
    return orig_linear(input, weight, bias)
F.linear = patched_linear


if not hasattr(torch, "xpu"):
    class DummyXPUMetaclass(type):
        def __getattr__(cls, name):
            if name in ('device', 'Event', 'Stream'):
                return type(name, (), {})
            return lambda *a, **k: False

    class DummyXPU(metaclass=DummyXPUMetaclass):
        pass

    torch.xpu = DummyXPU

def dummy_decorator(*args, **kwargs):
    if len(args) == 1 and not kwargs and callable(args[0]):
        return args[0]
    return lambda f: f

# Conditional compiler mock
if not hasattr(torch, "compiler"):
    compiler_mod = types.ModuleType("torch.compiler")
    compiler_mod.is_compiling = lambda: False
    compiler_mod.disable = dummy_decorator
    compiler_mod.allow_in_graph = dummy_decorator
    compiler_mod.assume_constant_result = dummy_decorator
    torch.compiler = compiler_mod
    sys.modules["torch.compiler"] = compiler_mod
else:
    import torch.compiler
    if not hasattr(torch.compiler, "is_compiling"):
        torch.compiler.is_compiling = lambda: False
    if not hasattr(torch.compiler, "disable"):
        torch.compiler.disable = dummy_decorator
    if not hasattr(torch.compiler, "allow_in_graph"):
        torch.compiler.allow_in_graph = dummy_decorator
    if not hasattr(torch.compiler, "assume_constant_result"):
        torch.compiler.assume_constant_result = dummy_decorator

# Conditional library mock
if not hasattr(torch, "library"):
    library_mod = types.ModuleType("torch.library")
    torch.library = library_mod
    sys.modules["torch.library"] = library_mod

if not hasattr(torch.library, "custom_op"):
    torch.library.custom_op = dummy_decorator
if not hasattr(torch.library, "register_fake"):
    torch.library.register_fake = dummy_decorator
if not hasattr(torch.library, "register_autograd"):
    torch.library.register_autograd = dummy_decorator

# Conditional distributed / device_mesh mock
try:
    import torch.distributed.device_mesh
except ImportError:
    DummyDeviceMesh = type("DeviceMesh", (), {})
    devmesh_mod = types.ModuleType("torch.distributed.device_mesh")
    devmesh_mod.DeviceMesh = DummyDeviceMesh
    sys.modules["torch.distributed.device_mesh"] = devmesh_mod
    import torch.distributed
    torch.distributed.device_mesh = devmesh_mod

# Conditional distributed / tensor mock
try:
    import torch.distributed.tensor
except ImportError:
    tensor_mod = types.ModuleType("torch.distributed.tensor")
    sys.modules["torch.distributed.tensor"] = tensor_mod
    torch.distributed.tensor = tensor_mod
    
    td_mesh_mod = types.ModuleType("torch.distributed.tensor.device_mesh")
    td_mesh_mod.DeviceMesh = DummyDeviceMesh
    sys.modules["torch.distributed.tensor.device_mesh"] = td_mesh_mod
    torch.distributed.tensor.device_mesh = td_mesh_mod

import torch.amp
try:
    from torch.cuda.amp import GradScaler
    torch.amp.GradScaler = GradScaler
except ImportError:
    pass


import json
import os

def emit_progress(percent):
    """Write progress directly to fd 1 (stdout) bypassing Python buffering."""
    msg = f"sdbk mlpr {percent}\n"
    try:
        os.write(1, msg.encode("utf-8"))
    except Exception:
        pass

# Global tracking variables for tqdm monkey patch
hf_downloaded_bytes = 0
hf_total_repo_size = 0
hf_last_pct_emitted = -1

# --- Monkey patch huggingface_hub tqdm to enable real-time progress updates ---
try:
    import huggingface_hub.utils
    import huggingface_hub.constants
    
    # 1. Force smaller chunks for more frequent progress updates (1MB chunks)
    huggingface_hub.constants.DOWNLOAD_CHUNK_SIZE = 1024 * 1024
    
    # 2. Keep track of original tqdm methods
    _original_tqdm_init = huggingface_hub.utils.tqdm.__init__
    _original_tqdm_update = huggingface_hub.utils.tqdm.update

    def patched_tqdm_init(self, *args, **kwargs):
        # Force progress bar to be enabled even in non-TTY/background subprocesses
        kwargs["disable"] = False
        _original_tqdm_init(self, *args, **kwargs)

    def patched_tqdm_update(self, n=1):
        global hf_downloaded_bytes, hf_total_repo_size, hf_last_pct_emitted
        res = _original_tqdm_update(self, n)
        
        if hf_total_repo_size > 0:
            effective = hf_downloaded_bytes + self.n
            pct = min(99, int(effective / hf_total_repo_size * 100))
            if pct > hf_last_pct_emitted:
                hf_last_pct_emitted = pct
                emit_progress(pct)
        return res

    huggingface_hub.utils.tqdm.__init__ = patched_tqdm_init
    huggingface_hub.utils.tqdm.update = patched_tqdm_update
except Exception as e:
    import sys
    sys.stderr.write(f"[D4M] Failed to patch huggingface_hub tqdm: {e}\n")
    sys.stderr.flush()

# Load environment variables from .env if present in CWD or parent dir
for env_path in (".env", "../.env"):
    if os.path.exists(env_path):
        try:
            with open(env_path, "r") as f:
                for line in f:
                    if "=" in line and not line.strip().startswith("#"):
                        k, v = line.strip().split("=", 1)
                        os.environ[k.strip()] = v.strip()
        except Exception:
            pass
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_NO_TF"] = "1"
import random
import traceback
from pathlib import Path
from PIL import Image, ImageOps
import torch
from diffusers import FluxPipeline, FluxImg2ImgPipeline, FluxInpaintPipeline

try:
    try:
        from pipeline_flux2_klein import Flux2KleinPipeline
        from pipeline_flux2_klein_inpaint import Flux2KleinInpaintPipeline
        print("sdbk info Imported Flux2KleinPipeline directly")
    except ImportError:
        from backends.stable_diffusion.pipeline_flux2_klein import Flux2KleinPipeline
        from backends.stable_diffusion.pipeline_flux2_klein_inpaint import Flux2KleinInpaintPipeline
        print("sdbk info Imported Flux2KleinPipeline via backends.stable_diffusion package")
except Exception as e:
    print(f"sdbk errr Failed to import Flux2KleinPipeline: {e}")
    import traceback
    traceback.print_exc()

# Apply transformers.masking_utils.sdpa_mask monkeypatch for Apple Silicon (MPS) compatibility
# This avoids a PyTorch vmap/comparison compilation bug on MPS that triggers "RuntimeError: Invalid buffer size"
import transformers.masking_utils

def dummy_sdpa_mask(
    batch_size,
    cache_position,
    kv_length,
    kv_offset=0,
    mask_function=None,
    attention_mask=None,
    allow_is_causal_skip=True,
    **kwargs
):
    q_idx = (cache_position.cpu() + kv_offset).view(-1, 1)
    kv_idx = torch.arange(kv_length, device="cpu").view(1, -1)
    causal_mask = kv_idx <= q_idx
    causal_mask = causal_mask.unsqueeze(0).unsqueeze(0).expand(batch_size, 1, -1, -1)
    if attention_mask is not None:
        causal_mask = causal_mask & attention_mask.cpu().view(batch_size, 1, 1, kv_length).to(torch.bool)
    return causal_mask.contiguous().to(cache_position.device)

transformers.masking_utils.sdpa_mask = dummy_sdpa_mask

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

def resolve_hf_url(url, token=None):
    if not url:
        return None
    if not isinstance(url, str):
        return url
    if not (url.startswith("http://") or url.startswith("https://")) or "huggingface.co" not in url:
        return url
    
    try:
        import urllib.parse
        from huggingface_hub import hf_hub_download
        
        parsed = urllib.parse.urlparse(url)
        # path parts: split by '/'
        path_decoded = urllib.parse.unquote(parsed.path)
        parts = [p for p in path_decoded.split('/') if p]
        
        # Hugging Face URL structure:
        # Model: https://huggingface.co/owner/repo/resolve/branch/filename
        # Dataset: https://huggingface.co/datasets/owner/repo/resolve/branch/filename
        # Space: https://huggingface.co/spaces/owner/repo/resolve/branch/filename
        
        repo_type = "model"
        if parts and parts[0] == "datasets":
            repo_type = "dataset"
            parts = parts[1:]
        elif parts and parts[0] == "spaces":
            repo_type = "space"
            parts = parts[1:]
            
        if len(parts) >= 5 and parts[2] == "resolve":
            repo_id = f"{parts[0]}/{parts[1]}"
            revision = parts[3]
            filename = "/".join(parts[4:])
            
            print(f"sdbk mltl Downloading asset:{filename}")
            sys.stdout.flush()
            
            import huggingface_hub.utils
            orig_init = huggingface_hub.utils.tqdm.__init__
            orig_update = huggingface_hub.utils.tqdm.update

            def custom_init(self, *args, **kwargs):
                kwargs['disable'] = False
                orig_init(self, *args, **kwargs)
                self._last_printed = -1

            def custom_update(self, n=1):
                orig_update(self, n)
                if self.total:
                    percent = int((self.n / self.total) * 100)
                    if percent > getattr(self, '_last_printed', -1):
                        self._last_printed = percent
                        print(f"sdbk mlpr {percent}")
                        sys.stdout.flush()

            huggingface_hub.utils.tqdm.__init__ = custom_init
            huggingface_hub.utils.tqdm.update = custom_update
            
            try:
                local_path = hf_hub_download(
                    repo_id=repo_id,
                    filename=filename,
                    revision=revision,
                    repo_type=repo_type,
                    token=token
                )
            finally:
                huggingface_hub.utils.tqdm.__init__ = orig_init
                huggingface_hub.utils.tqdm.update = orig_update
                
            print(f"sdbk resolved: Downloaded successfully to {local_path}")
            sys.stdout.flush()
            return local_path
    except Exception as e:
        print(f"Error resolving HF URL {url} via hf_hub_download: {e}")
    return url

def make_progress_callback(num_steps):
    def progress_callback(pipe_self, step_index, timestep, callback_kwargs):
        percent = int((step_index + 1) / max(1, num_steps) * 100)
        percent = min(100, max(0, percent))
        print(f"sdbk dnpr {percent}")
        sys.stdout.flush()
        return callback_kwargs
    return progress_callback

def patch_vae_for_mps(pipeline):
    if not pipeline or not hasattr(pipeline, "vae") or pipeline.vae is None:
        return
    
    # 1. Ensure VAE is in float32 on MPS
    pipeline.vae.to(dtype=torch.float32)
    
    # 2. Monkeypatch vae.decode to force input latents to float32
    if hasattr(pipeline.vae, "decode"):
        orig_decode = pipeline.vae.decode
        def patched_decode(latents, *args, **kwargs):
            if isinstance(latents, torch.Tensor):
                latents = latents.to(torch.float32)
            return orig_decode(latents, *args, **kwargs)
        pipeline.vae.decode = patched_decode
        
    # 3. Monkeypatch vae.encode to force input image to float32
    if hasattr(pipeline.vae, "encode"):
        orig_encode = pipeline.vae.encode
        def patched_encode(x, *args, **kwargs):
            if isinstance(x, torch.Tensor):
                x = x.to(torch.float32)
            return orig_encode(x, *args, **kwargs)
        pipeline.vae.encode = patched_encode

def flush_mps_cache():
    import gc
    gc.collect()
    if hasattr(torch, "mps") and hasattr(torch.mps, "empty_cache"):
        try:
            torch.mps.empty_cache()
        except Exception: pass
    if hasattr(torch, "mps") and hasattr(torch.mps, "synchronize"):
        try:
            torch.mps.synchronize()
        except Exception: pass

def main():
    home_path = os.path.expanduser("~")
    print("sdbk mdld") # notify UI model logic is ready to load/run

    current_model = None
    current_sequential_offload = None
    current_fp8 = None
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
            sys.stdout.flush()
            try:
                json_str = inp_str.replace("b2py dndl", "").strip()
                data = json.loads(json_str)
                token = data.get("hf_token", None)
                if token == "":
                    token = None
                
                # set token in env globally too just in case
                if token:
                    os.environ["HF_TOKEN"] = token
                    os.environ["HUGGING_FACE_HUB_TOKEN"] = token

                def emit_progress(percent):
                    """Write progress directly to fd 1 (stdout) bypassing Python buffering."""
                    msg = f"sdbk mlpr {percent}\n"
                    os.write(1, msg.encode("utf-8"))

                model_url = data.get("model_url", None)
                sys.stderr.write(f"[D4M] dndl handler: model_url={model_url is not None}, data keys={list(data.keys())}\n")
                sys.stderr.flush()
                if model_url:
                    # --- SINGLE FILE DOWNLOAD (LoRAs) ---
                    dest_path = data.get("dest_path")
                    asset_id = data.get("asset_id", "lora")
                    
                    # Skip if file already exists
                    if dest_path and os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000:
                        sys.stderr.write(f"[D4M] LoRA {asset_id} already exists at {dest_path}, skipping download\n")
                        sys.stderr.flush()
                        emit_progress(100)
                        print("sdbk mdld")
                        sys.stdout.flush()
                        continue
                    
                    print(f"sdbk mltl Downloading asset:{asset_id}")
                    sys.stdout.flush()
                    
                    import requests as dl_requests
                    import urllib.parse
                    
                    # 1. Look up R2 key in registry.json for this asset_id
                    r2_key = None
                    for reg_path in ("../cdn_mirror/registry.json", "cdn_mirror/registry.json", "backends/stable_diffusion/registry.json", "registry.json"):
                        if os.path.exists(reg_path):
                            try:
                                with open(reg_path, "r") as rf:
                                    registry_data = json.load(rf)
                                    loras_dict = registry_data.get("loras", {})
                                    if asset_id in loras_dict:
                                        r2_key = loras_dict[asset_id].get("r2_key")
                                    break
                            except Exception:
                                pass

                    # 2. If cloudflare_id and r2_key are present, construct the CDN URL
                    cloudflare_id = os.environ.get("cloudflare_id")
                    cloudflare_token = os.environ.get("cloudflare_token")
                    
                    cdn_url = None
                    if cloudflare_id and r2_key:
                        cdn_base = os.environ.get("cdn_base_url")
                        if cdn_base:
                            cdn_url = f"{cdn_base.rstrip('/')}/{r2_key}"
                        else:
                            cdn_url = f"https://cdn.diffusion4mac.com/{r2_key}"

                    # 3. Request URL resolution: try CDN first, fallback to Hugging Face
                    response = None
                    if cdn_url:
                        sys.stderr.write(f"[D4M] Attempting download from CDN: {cdn_url[:80]}...\n")
                        sys.stderr.flush()
                        
                        # Use the User-Agent and/or the read-only client key (X-D4M-Client-Key)
                        # to authorize the request on the Cloudflare CDN side and prevent third-party hotlinking.
                        # This client-side token is read-only and does not possess write privileges.
                        cdn_headers = {"User-Agent": "Diffusion4Mac"}
                        if cloudflare_token:
                            cdn_headers["X-D4M-Client-Key"] = cloudflare_token
                        
                        try:
                            # Workers might redirect to R2 internally, but let's check
                            r = dl_requests.get(cdn_url, headers=cdn_headers, stream=True, allow_redirects=True, timeout=60)
                            if r.status_code in (200, 206):
                                response = r
                                sys.stderr.write(f"[D4M] CDN download started successfully (status={r.status_code})\n")
                                sys.stderr.flush()
                            else:
                                sys.stderr.write(f"[D4M] CDN returned status {r.status_code}, falling back to Hugging Face\n")
                                sys.stderr.flush()
                        except Exception as e:
                            sys.stderr.write(f"[D4M] CDN connection failed: {e}, falling back to Hugging Face\n")
                            sys.stderr.flush()

                    if not response:
                        # Fallback: Build Hugging Face auth header
                        headers = {}
                        if token:
                            headers["Authorization"] = f"Bearer {token}"
                        
                        current_url = model_url
                        max_redirects = 10
                        for redirect_step in range(max_redirects):
                            sys.stderr.write(f"[D4M] HF Fallback: Requesting {current_url[:120]} (step {redirect_step})...\n")
                            sys.stderr.flush()
                            
                            r = dl_requests.get(current_url, headers=headers, stream=True, allow_redirects=False, timeout=60)
                            
                            if r.status_code in (301, 302, 303, 307, 308):
                                location = r.headers.get("Location")
                                if not location:
                                    response = r
                                    break
                                
                                next_url = urllib.parse.urljoin(current_url, location)
                                parsed_current = urllib.parse.urlparse(current_url)
                                parsed_next = urllib.parse.urlparse(next_url)
                                
                                if parsed_next.netloc != parsed_current.netloc:
                                    sys.stderr.write(f"[D4M] Host changed from {parsed_current.netloc} to {parsed_next.netloc}. Stripping Authorization header.\n")
                                    sys.stderr.flush()
                                    headers = {k: v for k, v in headers.items() if k.lower() != 'authorization'}
                                
                                current_url = next_url
                            else:
                                response = r
                                break
                        
                        if not response:
                            raise Exception("Failed to establish redirect connection")
                    
                    response.raise_for_status()
                    
                    total_size = int(response.headers.get("content-length", 0))
                    sys.stderr.write(f"[D4M] LoRA: content-length={total_size}, status={response.status_code}\n")
                    sys.stderr.flush()
                    downloaded = 0
                    last_percent = -1
                    
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    with open(dest_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=256 * 1024):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                if total_size > 0:
                                    percent = min(99, int(downloaded / total_size * 100))
                                    if percent > last_percent:
                                        last_percent = percent
                                        emit_progress(percent)
                    
                    emit_progress(100)
                    print("sdbk mdld")
                    sys.stdout.flush()
                else:
                    # --- FULL REPO DOWNLOAD (base models) ---
                    model_name = data.get("model", "black-forest-labs/FLUX.2-klein-9B")
                    
                    # Fast local cache check — avoid download modal if already cached
                    repo_folder_name = "models--" + model_name.replace("/", "--")
                    cache_dir = os.path.expanduser(f"~/.cache/huggingface/hub/{repo_folder_name}")
                    ref_path = os.path.join(cache_dir, "refs", "main")
                    is_cached = False
                    if os.path.exists(ref_path):
                        try:
                            with open(ref_path) as rf:
                                commit = rf.read().strip()
                            snapshot_dir = os.path.join(cache_dir, "snapshots", commit)
                            if os.path.isdir(snapshot_dir) and len(os.listdir(snapshot_dir)) > 5:
                                is_cached = True
                        except Exception:
                            pass
                    
                    if is_cached:
                        sys.stderr.write(f"[D4M] Model {model_name} already cached, skipping download\n")
                        sys.stderr.flush()
                        emit_progress(100)
                        print("sdbk mdld")
                        sys.stdout.flush()
                        continue
                    
                    print("sdbk mltl Downloading " + model_name)
                    sys.stdout.flush()
                    
                    # Emit 0% immediately so UI switches from spinner to progress bar
                    emit_progress(0)

                    # Look up in registry
                    model_info = None
                    # Load registry if needed
                    registry_data = {}
                    for reg_path in ("../cdn_mirror/registry.json", "cdn_mirror/registry.json", "backends/stable_diffusion/registry.json", "registry.json"):
                        if os.path.exists(reg_path):
                            try:
                                with open(reg_path, "r") as rf:
                                    registry_data = json.load(rf)
                                break
                            except Exception: pass
                    
                    for m_id, m_info in registry_data.get("models", {}).items():
                        if m_info.get("huggingface_repo") == model_name or m_info.get("id") == model_name:
                            model_info = m_info
                            break

                    downloaded_from_cdn = False
                    cloudflare_id = os.environ.get("cloudflare_id")
                    cloudflare_token = os.environ.get("cloudflare_token")
                    home_path = os.path.expanduser("~")
                    import requests as dl_requests

                    if cloudflare_id and model_info and model_info.get("r2_key"):
                        r2_key = model_info.get("r2_key") + ".zip"
                        cdn_base = os.environ.get("cdn_base_url")
                        if cdn_base:
                            cdn_url = f"{cdn_base.rstrip('/')}/{r2_key}"
                        else:
                            cdn_url = f"https://cdn.diffusion4mac.com/{r2_key}"

                        sys.stderr.write(f"[D4M] Attempting base model download from CDN: {cdn_url[:80]}...\n")
                        sys.stderr.flush()
                        
                        # Use the User-Agent and/or the read-only client key (X-D4M-Client-Key)
                        # to authorize the request on the Cloudflare CDN side and prevent third-party hotlinking.
                        # This client-side token is read-only and does not possess write privileges.
                        cdn_headers = {"User-Agent": "Diffusion4Mac"}
                        if cloudflare_token:
                            cdn_headers["X-D4M-Client-Key"] = cloudflare_token
                        
                        try:
                            # 1. Get remote file size using HEAD
                            head_headers = cdn_headers.copy()
                            try:
                                h = dl_requests.head(cdn_url, headers=head_headers, allow_redirects=True, timeout=15)
                                h.raise_for_status()
                                total_size = int(h.headers.get("content-length", 0))
                            except Exception as e:
                                sys.stderr.write(f"[D4M] CDN HEAD request failed: {e}. Trying GET directly...\n")
                                sys.stderr.flush()
                                total_size = 0

                            temp_zip = os.path.join(home_path, ".diffusionbee", f"temp_{model_info['id']}.zip")
                            os.makedirs(os.path.dirname(temp_zip), exist_ok=True)
                            
                            downloaded = 0
                            if os.path.exists(temp_zip) and total_size > 0:
                                local_size = os.path.getsize(temp_zip)
                                if local_size < total_size:
                                    downloaded = local_size
                                    sys.stderr.write(f"[D4M] Local partial zip found ({downloaded / (1024*1024*1024):.2f} GB). Resuming download...\n")
                                    sys.stderr.flush()
                                elif local_size == total_size:
                                    downloaded = total_size
                                    sys.stderr.write(f"[D4M] Local zip is already fully downloaded. Proceeding to extract...\n")
                                    sys.stderr.flush()
                                else:
                                    # Local file is larger (corrupted?), reset
                                    try: os.remove(temp_zip)
                                    except Exception: pass
                            else:
                                if os.path.exists(temp_zip):
                                    try: os.remove(temp_zip)
                                    except Exception: pass

                            max_retries = 20
                            retry_delay = 5
                            import time
                            
                            download_success = False
                            if downloaded >= total_size and total_size > 0:
                                download_success = True
                                
                            while downloaded < total_size or (total_size == 0 and not download_success):
                                req_headers = cdn_headers.copy()
                                if downloaded > 0:
                                    req_headers["Range"] = f"bytes={downloaded}-"
                                    write_mode = "ab"
                                else:
                                    write_mode = "wb"
                                    
                                try:
                                    r = dl_requests.get(cdn_url, headers=req_headers, stream=True, allow_redirects=True, timeout=30)
                                    if r.status_code == 200:
                                        write_mode = "wb"
                                        downloaded = 0
                                        if total_size == 0:
                                            total_size = int(r.headers.get("content-length", 0))
                                    elif r.status_code == 206:
                                        pass
                                    else:
                                        r.raise_for_status()
                                        
                                    last_percent = -1
                                    with open(temp_zip, write_mode) as f:
                                        for chunk in r.iter_content(chunk_size=1024 * 1024):
                                            if chunk:
                                                f.write(chunk)
                                                downloaded += len(chunk)
                                                if total_size > 0:
                                                    percent = min(99, int(downloaded / total_size * 100))
                                                    if percent > last_percent:
                                                        last_percent = percent
                                                        emit_progress(percent)
                                                        
                                    if total_size > 0 and downloaded >= total_size:
                                        download_success = True
                                        break
                                    elif total_size == 0:
                                        download_success = True
                                        break
                                except Exception as e:
                                    sys.stderr.write(f"[D4M] CDN download connection interrupted: {e}. Retrying in {retry_delay}s...\n")
                                    sys.stderr.flush()
                                    max_retries -= 1
                                    if max_retries <= 0:
                                        raise Exception(f"CDN download failed after max retries: {e}")
                                    time.sleep(retry_delay)
                                    if os.path.exists(temp_zip):
                                        downloaded = os.path.getsize(temp_zip)

                            if download_success:
                                emit_progress(99)
                                sys.stderr.write(f"[D4M] CDN download complete. Extracting zip archive...\n")
                                sys.stderr.flush()
                                
                                # Unzip to target directory
                                dest_dir = os.path.join(home_path, ".diffusionbee", "downloaded_assets", "models", model_info["id"])
                                os.makedirs(dest_dir, exist_ok=True)
                                
                                import zipfile
                                with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                                    zip_ref.extractall(dest_dir)
                                
                                # Cleanup
                                os.remove(temp_zip)
                                
                                downloaded_from_cdn = True
                                emit_progress(100)
                                print("sdbk mdld")
                                sys.stdout.flush()
                                sys.stderr.write("[D4M] Model successfully deployed from CDN!\n")
                                sys.stderr.flush()
                            else:
                                raise Exception("Download loop finished without success.")
                        except Exception as e:
                            sys.stderr.write(f"[D4M] CDN download failed: {e}, falling back to Hugging Face\n")
                            sys.stderr.flush()
                            # Clean up if download wasn't successful to prevent corruption later
                            if not download_success:
                                temp_zip = os.path.join(home_path, ".diffusionbee", f"temp_{model_info['id']}.zip")
                                if os.path.exists(temp_zip):
                                    try: os.remove(temp_zip)
                                    except Exception: pass

                    if not downloaded_from_cdn:
                        from huggingface_hub import hf_hub_download, list_repo_tree
                        import threading

                        # Single API call: get file list AND total size
                        repo_files = []
                        total_repo_size = 0
                        try:
                            for f in list_repo_tree(model_name, token=token, recursive=True):
                                if hasattr(f, 'rfilename') and f.rfilename:
                                    repo_files.append(f)
                                    if hasattr(f, 'size') and f.size is not None:
                                        total_repo_size += f.size
                        except Exception:
                            pass

                        sys.stderr.write(f"[D4M] Repo {model_name}: {len(repo_files)} files, {total_repo_size} bytes\n")
                        sys.stderr.flush()

                        # Initialize global progress tracking for tqdm patch
                        global hf_downloaded_bytes, hf_total_repo_size, hf_last_pct_emitted
                        hf_downloaded_bytes = 0
                        hf_total_repo_size = total_repo_size
                        hf_last_pct_emitted = -1

                        try:
                            for idx, f in enumerate(repo_files):
                                file_expected = getattr(f, 'size', 0) or 0
                                
                                try:
                                    local_path = hf_hub_download(
                                        repo_id=model_name,
                                        filename=f.rfilename,
                                        token=token
                                    )
                                    try:
                                        file_size = os.path.getsize(local_path)
                                    except OSError:
                                        file_size = file_expected
                                    hf_downloaded_bytes += file_size
                                except Exception as e:
                                    sys.stderr.write(f"[D4M] Error downloading {f.rfilename}: {e}\n")
                                    sys.stderr.flush()
                                    hf_downloaded_bytes += file_expected
                                
                                # Emit progress: prefer byte-based, fallback to file-count
                                if hf_total_repo_size > 0:
                                    pct = min(99, int(hf_downloaded_bytes / hf_total_repo_size * 100))
                                else:
                                    pct = min(99, int((idx + 1) / max(len(repo_files), 1) * 100))
                                if pct > hf_last_pct_emitted:
                                    hf_last_pct_emitted = pct
                                    emit_progress(pct)
                            
                            emit_progress(100)
                            print("sdbk mdld")
                            sys.stdout.flush()
                            sys.stderr.write("[D4M] Download complete\n")
                            sys.stderr.flush()
                        except Exception as inner_e:
                            raise inner_e
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
            
            # Low-end system optimization parameters
            flux_vae_slicing = data.get("flux_vae_slicing", False)
            flux_vae_tiling = data.get("flux_vae_tiling", False)
            flux_attention_slicing = data.get("flux_attention_slicing", False)
            flux_sequential_cpu_offload = data.get("flux_sequential_cpu_offload", False)
            flux_klein_size = data.get("flux_klein_size", "9B")
            flux_fp8 = data.get("flux_fp8", False)
            
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
            try:
                target_width = int(data.get("img_width", 1024) or 1024)
            except Exception:
                target_width = 1024
            try:
                target_height = int(data.get("img_height", 1024) or 1024)
            except Exception:
                target_height = 1024
            
            # Cap target dimensions to a maximum of 1024 to prevent RAM runaway
            MAX_DIMENSION = 1024
            if target_width > MAX_DIMENSION or target_height > MAX_DIMENSION:
                if target_width > target_height:
                    target_height = int(target_height * (MAX_DIMENSION / target_width))
                    target_width = MAX_DIMENSION
                else:
                    target_width = int(target_width * (MAX_DIMENSION / target_height))
                    target_height = MAX_DIMENSION
            
            target_width = max(16, (target_width // 16) * 16)
            target_height = max(16, (target_height // 16) * 16)
            
            data["img_width"] = target_width
            data["img_height"] = target_height
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
                        resample_filter = getattr(Image, "Resampling", Image).LANCZOS
                        img = ImageOps.fit(img, (target_width, target_height), method=resample_filter)
                        guide_images.append(img)

            # Handle parsed options
            print(f"Backend options: model_selection={model_selection}, input_image_path={input_image_path}")
            print(f"Loaded {len(guide_images)} guide images.")
            
            # Resolve model ID or local directory
            model_key = "flux_schnell"
            if model_selection == "Flux Klein":
                if flux_klein_size == "4B":
                    model_key = "flux_klein_4b"
                else:
                    model_key = "flux_klein"
            elif model_selection == "Ideogram Local":
                model_key = "ideogram_4_nf4"
            
            # Check if local model directory exists
            local_model_dir = os.path.join(str(home_path), ".diffusionbee", "downloaded_assets", "models", model_key)
            if os.path.isdir(local_model_dir):
                model_id = local_model_dir
            else:
                if model_selection == "Ideogram Local":
                    model_id = "ideogram-ai/ideogram-4-nf4-diffusers"
                elif model_selection == "Flux Klein":
                    if flux_klein_size == "4B":
                        model_id = "black-forest-labs/FLUX.2-klein-4B"
                    else:
                        model_id = "black-forest-labs/FLUX.2-klein-9B"
                else:
                    model_id = "black-forest-labs/FLUX.1-schnell"

            device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
            dtype = torch.float16 if device == "mps" else torch.bfloat16            # Setup pipeline if model changed, sequential offload state changed, FP8 state changed, or uninitialized
            if current_model != model_id or current_sequential_offload != flux_sequential_cpu_offload or current_fp8 != flux_fp8:
                print(f"sdbk mdld Loading model weights (model_id={model_id}, sequential_offload={flux_sequential_cpu_offload}, FP8={flux_fp8})...")
                
                if pipe is not None:
                    del pipe
                if pipe_img2img is not None:
                    del pipe_img2img
                if pipe_kv is not None:
                    del pipe_kv
                pipe_inpaint = None
                flush_mps_cache()

                if model_selection == "Ideogram Local":
                    from diffusers import Ideogram4Pipeline
                    print(f"sdbk info Loading Ideogram Local Pipeline (model_id={model_id})...")
                    pipe = Ideogram4Pipeline.from_pretrained(
                        model_id,
                        torch_dtype=dtype,
                        token=hf_token
                    )
                    if device == "mps":
                        patch_vae_for_mps(pipe)
                    print(f"sdbk info Moving Ideogram pipeline to {device}...")
                    pipe.to(device)
                elif model_selection == "Flux Klein" and "Flux2KleinPipeline" in globals():
                    # use standard pipeline for klein multi-image editing or standard text2img
                    if flux_fp8:
                        from diffusers.models import Flux2Transformer2DModel
                        print("sdbk info Loading Klein Transformer in float8_e4m3fn...")
                        try:
                            transformer = Flux2Transformer2DModel.from_pretrained(
                                model_id,
                                subfolder="transformer",
                                torch_dtype=torch.float8_e4m3fn,
                                token=hf_token
                            )
                            pipe = Flux2KleinPipeline.from_pretrained(
                                model_id,
                                transformer=transformer,
                                torch_dtype=dtype,
                                token=hf_token,
                                low_cpu_mem_usage=False
                            )
                        except Exception as e:
                            print(f"sdbk warn Failed to load float8 transformer: {e}. Falling back to default dtype...")
                            pipe = Flux2KleinPipeline.from_pretrained(model_id, torch_dtype=dtype, token=hf_token, low_cpu_mem_usage=False)
                    else:
                        pipe = Flux2KleinPipeline.from_pretrained(model_id, torch_dtype=dtype, token=hf_token, low_cpu_mem_usage=False)

                    if device == "mps":
                        patch_vae_for_mps(pipe)
                    import psutil
                    total_ram_gb = psutil.virtual_memory().total / (1024 ** 3)
                    force_sequential = total_ram_gb <= 12.0
                    if (flux_sequential_cpu_offload or force_sequential) and hasattr(pipe, "enable_sequential_cpu_offload"):
                        print(f"sdbk info Enabling sequential CPU offload (force={force_sequential}, total_ram={total_ram_gb:.1f}GB)...")
                        try:
                            pipe.enable_sequential_cpu_offload(device=device)
                        except Exception as e:
                            print(f"sdbk warn Sequential CPU offload failed: {e}")
                            if hasattr(pipe, "enable_model_cpu_offload"):
                                    pipe.enable_model_cpu_offload(device=device)
                            else:
                                pipe.to(device)
                    elif hasattr(pipe, "enable_model_cpu_offload"):
                        try:
                            pipe.enable_model_cpu_offload(device=device)
                        except Exception as e:
                            print(f"sdbk warn CPU offload failed: {e}")
                            pipe.to(device)
                    else:
                        pipe.to(device)
                    if "Flux2KleinInpaintPipeline" in globals():
                        pipe_inpaint = Flux2KleinInpaintPipeline(**pipe.components)
                        if device == "mps":
                            patch_vae_for_mps(pipe_inpaint)
                else:
                    # Schnell or standard Klein
                    if flux_fp8:
                        from diffusers import FluxTransformer2DModel
                        print("sdbk info Loading Flux Transformer in float8_e4m3fn...")
                        try:
                            transformer = FluxTransformer2DModel.from_pretrained(
                                model_id,
                                subfolder="transformer",
                                torch_dtype=torch.float8_e4m3fn,
                                token=hf_token
                            )
                            pipe = FluxPipeline.from_pretrained(
                                model_id,
                                transformer=transformer,
                                torch_dtype=dtype,
                                token=hf_token
                            )
                        except Exception as e:
                            print(f"sdbk warn Failed to load float8 transformer: {e}. Falling back to default dtype...")
                            pipe = FluxPipeline.from_pretrained(model_id, torch_dtype=dtype, token=hf_token)
                    else:
                        pipe = FluxPipeline.from_pretrained(model_id, torch_dtype=dtype, token=hf_token)

                    if device == "mps":
                        patch_vae_for_mps(pipe)
                    import psutil
                    total_ram_gb = psutil.virtual_memory().total / (1024 ** 3)
                    force_sequential = total_ram_gb <= 12.0
                    if (flux_sequential_cpu_offload or force_sequential) and hasattr(pipe, "enable_sequential_cpu_offload"):
                        print(f"sdbk info Enabling sequential CPU offload (force={force_sequential}, total_ram={total_ram_gb:.1f}GB)...")
                        try:
                            pipe.enable_sequential_cpu_offload(device=device)
                        except Exception as e:
                            print(f"sdbk warn Sequential CPU offload failed: {e}")
                            if hasattr(pipe, "enable_model_cpu_offload"):
                                 pipe.enable_model_cpu_offload(device=device)
                            else:
                                pipe.to(device)
                    elif hasattr(pipe, "enable_model_cpu_offload"):
                        try:
                            pipe.enable_model_cpu_offload(device=device)
                        except Exception as e:
                            print(f"sdbk warn CPU offload failed: {e}")
                            pipe.to(device)
                    else:
                        pipe.to(device)
                    pipe_img2img = FluxImg2ImgPipeline(**pipe.components)
                    if device == "mps":
                        patch_vae_for_mps(pipe_img2img)
                    if "FluxInpaintPipeline" in globals():
                        pipe_inpaint = FluxInpaintPipeline(**pipe.components)
                        if device == "mps":
                            patch_vae_for_mps(pipe_inpaint)

                current_model = model_id
                current_sequential_offload = flux_sequential_cpu_offload
                current_fp8 = flux_fp8
                flush_mps_cache()

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
                    if not path:
                        continue
                    
                    # Resolve Hugging Face URL if path is a URL
                    if path.startswith("http://") or path.startswith("https://"):
                        resolved_path = resolve_hf_url(path, token=hf_token)
                        if resolved_path and os.path.exists(resolved_path):
                            path = resolved_path
                        else:
                            print(f"Skipping LoRA URL {path} as it could not be resolved/downloaded.")
                            continue

                    if not os.path.exists(path):
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
                                if os.path.exists(path) and os.path.getsize(path) < 1024 * 1024:
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
                                        if os.path.exists(path) and os.path.getsize(path) < 1024 * 1024:
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
                resample_filter = getattr(Image, "Resampling", Image).LANCZOS
                input_image = ImageOps.fit(input_image, (target_width, target_height), method=resample_filter)

            mask_image_path = data.get("mask_image_path", None)
            mask_image = load_image(mask_image_path) if mask_image_path else None

            # Setup active pipeline reference
            active_pipe = pipe
            if model_selection == "Ideogram Local":
                active_pipe = pipe
            elif mask_image and input_image:
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

            # Apply VAE/Attention optimizations on active pipeline
            if active_pipe is not None:
                if flux_vae_slicing and hasattr(active_pipe, "enable_vae_slicing"):
                    try:
                        active_pipe.enable_vae_slicing()
                    except Exception as e:
                        print(f"sdbk warn enable_vae_slicing failed: {e}")
                elif hasattr(active_pipe, "disable_vae_slicing"):
                    try:
                        active_pipe.disable_vae_slicing()
                    except Exception:
                        pass

                if flux_vae_tiling and hasattr(active_pipe, "enable_vae_tiling"):
                    try:
                        active_pipe.enable_vae_tiling()
                    except Exception as e:
                        print(f"sdbk warn enable_vae_tiling failed: {e}")
                elif hasattr(active_pipe, "disable_vae_tiling"):
                    try:
                        active_pipe.disable_vae_tiling()
                    except Exception:
                        pass

                if flux_attention_slicing and hasattr(active_pipe, "enable_attention_slicing"):
                    try:
                        active_pipe.enable_attention_slicing()
                    except Exception as e:
                        print(f"sdbk warn enable_attention_slicing failed: {e}")
                elif hasattr(active_pipe, "disable_attention_slicing"):
                    try:
                        active_pipe.disable_attention_slicing()
                    except Exception:
                        pass

            apply_loras(active_pipe, lora_paths, lora_weights)

            # Aggressive memory cleanup before generation to prevent MPS OOM
            flush_mps_cache()

            generator = torch.Generator(device="cpu").manual_seed(seed)

            if mask_image and input_image:
                if mask_image.size != input_image.size:
                    mask_image = mask_image.resize(input_image.size)

            for i in range(num_imgs):
                print("sdbk dnpr 0")
                sys.stdout.flush()

                progress_cb = make_progress_callback(num_steps)

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
                                generator=generator,
                                callback_on_step_end=progress_cb
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
                                generator=generator,
                                callback_on_step_end=progress_cb
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
                                generator=generator,
                                height=data.get("img_height", 1024),
                                width=data.get("img_width", 1024),
                                callback_on_step_end=progress_cb
                            )
                    else:
                        print("Running Flux2KleinPipeline as Text2Img")
                        with torch.inference_mode():
                            out = pipe(
                                prompt=prompt,
                                num_inference_steps=num_steps,
                                generator=generator,
                                height=data.get("img_height", 1024),
                                width=data.get("img_width", 1024),
                                callback_on_step_end=progress_cb
                            )
                elif model_selection == "Ideogram Local":
                    print("Running Ideogram Local Text2Img")
                    step_count = 0
                    orig_scheduler_step = pipe.scheduler.step
                    def patched_scheduler_step(*args, **kwargs):
                        nonlocal step_count
                        res = orig_scheduler_step(*args, **kwargs)
                        percent = int((step_count + 1) / max(1, num_steps) * 100)
                        percent = min(100, max(0, percent))
                        print(f"sdbk dnpr {percent}")
                        sys.stdout.flush()
                        step_count += 1
                        return res
                    pipe.scheduler.step = patched_scheduler_step
                    try:
                        with torch.inference_mode():
                            out = pipe(
                                prompt=prompt,
                                num_inference_steps=num_steps,
                                guidance_scale=guidance_scale,
                                guidance_schedule=None,
                                generator=generator,
                                height=data.get("img_height", 1024),
                                width=data.get("img_width", 1024),
                                callback_on_step_end=None,
                                max_sequence_length=256
                            )
                    finally:
                        pipe.scheduler.step = orig_scheduler_step
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
                                strength=strength,
                                callback_on_step_end=progress_cb
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
                                width=data.get("img_width", 1024),
                                callback_on_step_end=progress_cb
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
                flush_mps_cache()

        except Exception as e:
            print(f"sdbk errr {str(e)}")
            sys.stdout.flush()
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
            flush_mps_cache()

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    import traceback
    try:
        main()
    except Exception as e:
        traceback.print_exc()
