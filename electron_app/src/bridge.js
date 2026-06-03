import { ipcMain, dialog, app } from 'electron'

var win;
var python;
var ollama_proc;

var py_buffer = "";
var is_app_closing = false;

var last_few_err = ""

let RESTART_BACKEND_ON_CLOSE = true

const path = require('path');

function start_bridge() {

    console.log("starting bridge")
    const fs = require('fs')

    // Start Ollama on port 11435 using the bundled binary
    console.log("starting ollama on port 11435")
    let custom_path = process.env.PATH || '';
    if (!custom_path.includes('/usr/local/bin')) custom_path = '/usr/local/bin:' + custom_path;
    if (!custom_path.includes('/opt/homebrew/bin')) custom_path = '/opt/homebrew/bin:' + custom_path;
    
    // Resolve bundled Ollama binary path
    // Dev: ../backends/ollama/ollama (relative to CWD which is electron_app/)
    // Prod: core/ollama (extraResources)
    let ollama_bin = null;
    const ollama_candidates = [
        path.resolve('..', 'backends', 'ollama', 'ollama'),           // dev: from electron_app/
        path.resolve('../backends/ollama/ollama'),                     // dev: alternate
        path.join(path.dirname(__dirname), 'core', 'ollama'),          // prod: extraResources
        path.resolve(__dirname, '..', '..', 'backends', 'ollama', 'ollama'), // dev: from dist_electron/
    ];
    for (const candidate of ollama_candidates) {
        if (fs.existsSync(candidate)) {
            ollama_bin = candidate;
            break;
        }
    }
    if (!ollama_bin) {
        console.log("Bundled Ollama not found at any candidate path, falling back to system ollama");
        console.log("Searched:", ollama_candidates);
        ollama_bin = 'ollama';
    } else {
        console.log("Using bundled Ollama:", ollama_bin);
    }
    
    // Set DYLD_LIBRARY_PATH so ollama can find its companion .dylib/.so files
    let ollama_dir = path.dirname(ollama_bin);
    let ollama_env = Object.assign({}, process.env, {
        OLLAMA_HOST: '127.0.0.1:11435',
        PATH: custom_path,
        DYLD_LIBRARY_PATH: ollama_dir + ':' + (process.env.DYLD_LIBRARY_PATH || ''),
        DYLD_FALLBACK_LIBRARY_PATH: ollama_dir
    })
    try {
        ollama_proc = require('child_process').spawn(ollama_bin, ['serve'], { env: ollama_env })
        ollama_proc.stderr.on('data', (data) => {
            console.log("Ollama stderr:", data.toString())
        })
        ollama_proc.stdout.on('data', (data) => {
            console.log("Ollama stdout:", data.toString())
        })
        ollama_proc.on('error', (err) => {
            console.error("Failed to spawn Ollama:", err)
        })
    } catch(e) {
        console.error("Error starting Ollama serve:", e)
    }

    let script_path = process.env.PY_SCRIPT || "../backends/stable_diffusion/diffusionbee_backend.py"; 
    let bin_path =  process.env.BIN_PATH;

    let is_apple_silicon = false;
    let use_arm64_arch = false;
    if (process.platform === 'darwin') {
        try {
            is_apple_silicon = require('child_process').execSync('sysctl -n hw.optional.arm64').toString().trim() === '1';
            if (is_apple_silicon) {
                try {
                    require('child_process').execSync('arch -arm64 python3 --version');
                    use_arm64_arch = true;
                } catch (e) {
                    console.log("arch -arm64 python3 is not supported or failed (e.g. running under x86_64 venv on Apple Silicon)");
                }
            }
        } catch (e) {
            // ignore
        }
    }

    if(bin_path && (fs.existsSync(script_path))){
        python = require('child_process').spawn( bin_path );
    }
    else if (fs.existsSync(script_path)) {
        if (use_arm64_arch) {
            python = require('child_process').spawn('arch', ['-arm64', 'python3', '-u', script_path]);
        } else {
            python = require('child_process').spawn('python3', ['-u', script_path]);
        }
    }
    else{
        const path = require('path');
        let backend_path =  path.join(path.dirname(__dirname), 'core' , 'diffusionbee_backend' );
        if (is_apple_silicon) {
            python = require('child_process').spawn('arch', ['-arm64', backend_path]);
        } else {
            python = require('child_process').spawn( backend_path  );
        }
    }

    if (python) {
        python.on('error', (err) => {
            console.error("Failed to spawn Python backend process:", err);
            if (win) {
                win.webContents.send('to_renderer', 'adlg Failed to spawn Python backend process: ' + err.message);
            }
        });
    }
    
   
    python.stdin.setEncoding('utf-8');

    python.stdout.on('data', function(data) {
        console.log("Python response: ", data.toString('utf8'));


        if(! data.toString().includes("sdbk ")){
            if(win && !is_app_closing )
                win.webContents.send('to_renderer', 'adlg ' + data.toString('utf8'));
        }
           
        

        if (win) {

            py_buffer += data.toString('utf8');

            let splitted = py_buffer.split("\n")

            if( splitted.length > 1 ){
                for (var i = 0; i < splitted.length -1 ; i++) {
                    if (splitted[i].length > 0) {
                        if(win && !is_app_closing )
                            win.webContents.send('to_renderer', 'py2b ' + splitted[i]);
                        
                        // Direct progress channel: parse mlpr messages and send as dedicated IPC
                        // This bypasses the py_vue_bridge -> StableDiffusion.state_msg chain
                        if (splitted[i].startsWith('sdbk mlpr ')) {
                            let pct = parseInt(splitted[i].substring(10), 10);
                            if (!isNaN(pct)) {
                                console.log("[BRIDGE] Sending direct download_progress IPC:", pct);
                                win.webContents.send('download_progress', pct);
                            }
                        }
                    }
                }
            }

            py_buffer = splitted[ splitted.length - 1  ];

        } else {
            console.log("window not binded yet, got from py : " + data.toString('utf8'))
        }

    });

    python.stderr.on('data', (data) => {
        console.error(`stderr: ${data}`);
        last_few_err = last_few_err + data.toString();
        last_few_err = last_few_err.slice(-300);
        if(win && !is_app_closing )
             win.webContents.send('to_renderer', 'adlg ' + data.toString('utf8') );
    });

    python.on('close', (code) => {
        // if( code != 0 )
        // {
        // 	dialog.showMessageBox("Backend quit unexpectedly")
        // }

        if(is_app_closing){
            if (win){
                 app.exit(1);
            }
            return;
        }

        


        if(RESTART_BACKEND_ON_CLOSE){
            // Filter out harmless semaphore warnings from error display
            let display_err = last_few_err.replace(/resource_tracker:.*?at shutdown\n?/gs, '').trim();
            if (display_err) {
                dialog.showMessageBox({ message: "Backend crashed and is restarting.\n\n" + display_err });
            }
            // Notify renderer that backend is restarting
            if (win && !is_app_closing) {
                win.webContents.send('to_renderer', 'py2b sdbk errr Backend crashed - restarting...');
            }
            last_few_err = "";
            return start_bridge()
        }
        else{

            dialog.showMessageBox({ message: "Backend quit unexpectedly. " + last_few_err });

            if (win)
            {
                is_app_closing = true;
                app.exit(1);
            }
        }
        
            

    });

}


ipcMain.on('to_python_sync', (event, arg) => {
    if (python) {
        event.returnValue = "ok";
        // console("sending to py from  main " + arg )
        python.stdin.write("b2py " + arg.toString() + "\n")

    } else {
        console.log("Python not binded yet!");
        event.returnValue = "not_ok";
    }
})


ipcMain.on('to_python_async', (event, arg) => {
    if (python) {
        python.stdin.write("b2py " + arg.toString() + "\n")
    }
})







app.on('window-all-closed', () => {
    if(python){
        is_app_closing = true;
        python.kill();
    }
    if (ollama_proc) {
        ollama_proc.kill();
    }
})



function bind_window_bridge(w) {
    console.log("browser object binded")
    win = w;
}


export { start_bridge, bind_window_bridge }