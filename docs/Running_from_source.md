## How to run Diffusion4Mac from source 

### Prerequisites
Install the following:
- Conda (Miniforge recommended)
- Node.js (v16 or higher)

### 1. Clone the repository: 
```bash
git clone https://github.com/enuclea/Diffusion4Mac
```

### 2. Create the conda environment and activate it:
```bash
conda create -n diffusion4mac_env python=3.9.10
conda activate diffusion4mac_env
```

### 3. Install Python dependencies:
```bash
cd Diffusion4Mac/backends/stable_diffusion
pip install -r requirements.txt
```

### 4. Install Frontend dependencies:
```bash
cd ../../electron_app
npm install
```

### 5. Run the application in development mode:
```bash
npm run electron:serve
```