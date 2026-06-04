# Diffusion4Mac - Stable Diffusion GUI App for MacOS

### Diffusion4Mac is an easy, premium way to run Stable Diffusion locally on MacOS. Comes with a simple installer. No dependencies or technical knowledge needed.

* Runs locally on your computer, with optional cloud-based frontier power via Google Gemini and Imagen 3.
* Supports FLUX.1-schnell, FLUX.2 [klein] (9B & 4B variants), cloud-based Imagen 3 and Gemini 2.5 Flash, local Gemma LLM vision and prompt assistance, custom LoRAs, and multiple LoRA stacking.

## Features
* Full data privacy for local generations.
* Optional **Gemini Studio** tab for cloud-based generation using Google **Imagen 3** (`imagen-3.0-generate-002`) and prompt enhancement using **Gemini 2.5 Flash** (requires Gemini API Key).
* Clean, premium, and easy to use UI.
* Image to image & Text to image generation.
* Custom CDN Mirror: pre-configured models download directly from our high-speed Cloudflare mirror, completely bypassing the need for Hugging Face API keys or registration.
* Gemma-based vision prompt designer.
* Gemma-based AI Assist prompt rewriter.
* Custom LoRA imports with required keyword validation.
* LoRA stacking setting (multiple active LoRAs).
* History, Upscaling, and Inpainting support.

## Models & CDN Mirror
By default, Diffusion4Mac hosts and mirrors its core assets on a custom high-speed CDN. You can download the following local models directly inside the app without needing a Hugging Face account or requesting gated access:
* **FLUX.1-schnell** (Fast, local 4-step generation)
* **FLUX.2 [klein] (4B)** (Optimized for speed and lower-memory Apple Silicon Macs)
* **FLUX.2 [klein] (9B)** (High-fidelity local model)

## Requirements
* Mac with Apple Silicon (M1/M2/M3/M4/M5) or Intel CPU. (Note: Starting with v2.7.0-beta, macOS builds are compiled natively for Apple Silicon `arm64` by default for maximum performance and to avoid Rosetta translation warnings).
* macOS 12.3 or later

## License & Attribution
- This application is a modified derivative work based on [DiffusionBee](https://github.com/divamgupta/diffusionbee-stable-diffusion-ui) (original copyright owner Divam Gupta).
- This project is licensed under the GNU Affero General Public License Version 3 (AGPL-3.0), in compliance with the original licensing terms.
- All terms of Stable Diffusion apply to the output images.

## References
1) [DiffusionBee original repository](https://github.com/divamgupta/diffusionbee-stable-diffusion-ui)
2) [Hugging Face Diffusers library](https://github.com/huggingface/diffusers)
