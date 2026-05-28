## How to use Diffusion4Mac

Welcome to the documentation for Diffusion4Mac.

### Installation & Updates

On first launch, Diffusion4Mac will download and initialize additional data for image generation (FLUX models, etc.). When updates are released, your history and local models will be fully preserved in the local database.

---

## Generating Images

### Text to Image
Create an image based on a text prompt description.
- **AI Canvas & Options**:
  - **Steps**: Controls how many sampling steps are used. Setting to a low number is useful for quick drafts.
  - **Seed**: A starting random number for generation. Re-using a seed with the same prompt and settings yields identical output.
  - **AI Assist**: Click the wand icon inside the prompt textarea to leverage the local Gemma model to rewrite and expand a basic phrase into a detailed, high-fidelity prompt.

### Image to Image
Generate a new image using an initial guide image/sketch and a text prompt description.
- **Input Strength**: Determines how closely the generator adheres to the guide image.

### Inpainting
Mask and repaint specific parts of an image. Scribble on the canvas area to define the mask region to be replaced based on the prompt description.

---

## LoRAs (Low-Rank Adaptation)
Diffusion4Mac includes full support for applying LoRA layers to FLUX models:
- **Built-in LoRAs**: Navigate to the **LoRAs** tab to download and toggle the premium built-in enhancements (Detailed Enhancer, Cinematic Lighting, Portrait Engine).
- **Custom LoRAs**: Import your own local `.safetensors` files. A trigger keyword is required during import.
- **LoRA Stacking**: By default, only one LoRA can be active per model family to prevent conflicts. If you enable **Allow LoRA Stacking** in the **Settings** tab, you can toggle multiple LoRAs simultaneously. Active trigger keywords will be automatically prepended to your prompt.

---

## Prompt Designer (Vision)
Analyze existing images to create prompt descriptions:
- Drag and drop or upload any image in the **Prompt Designer** tab.
- Click **Analyze Image** to call local Gemma vision models to describe the image.
- Route the generated prompt description directly to the Text-to-Image or Image-to-Image applets.

---

## Gemini Studio (Cloud-Based Generation)
Diffusion4Mac integrates optional cloud-based image generation:
- **Setup**: Navigate to the **Settings** tab and enter a valid Google Gemini API Key in the **Gemini API Key** card. Once entered, the **Gemini Studio** tab immediately activates on both the sidebar and homepage.
- **Generation (Imagen 3)**: Enter your text prompt, select your target aspect ratio (`1:1`, `16:9`, `9:16`, `4:3`, `3:4`), and click **Generate with Gemini**.
- **AI Prompt Enhancement**: Toggle **Enhance Prompt with Gemini AI** to automatically rewrite and optimize the user prompt with **Gemini 2.5 Flash** before sending it to Imagen 3.
- **Pipeline Routing**: 
  - Click **Send to Img2Img** to preload the generated image in the Image-to-Image editor.
  - Click **Use as Txt2Img Reference** to route the image as a guide reference in Text-to-Image (using Flux Klein).
  - Click **Save Image** to export the result to any directory on your filesystem.

---

## File Directory & Uninstalling

Diffusion4Mac stores generated images, history, and models locally:
- **Mac Directory**: Cache files and local downloads are located in `~/.diffusionbee/`.
- **History and Database**: All configuration and generated history database files are saved inside `~/.diffusionbee/`.
- **Full Uninstall**: To completely remove the application and all cached models/data, drag Diffusion4Mac to the Trash and run:
  ```bash
  rm -r ~/.diffusionbee/
  ```
