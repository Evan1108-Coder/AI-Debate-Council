const { app, BrowserWindow, dialog, shell, Menu } = require("electron");
const { spawn, execFileSync } = require("child_process");
const path = require("path");
const fs = require("fs");
const net = require("net");
const http = require("http");

const BACKEND_PORT = 8000;
const FRONTEND_PORT = 6001;

let mainWindow = null;
let backendProcess = null;
let frontendProcess = null;
let splashWindow = null;

const projectRoot = app.isPackaged
  ? path.join(process.resourcesPath, "app-content")
  : path.resolve(__dirname, "..");

function getDataDir() {
  return path.join(app.getPath("userData"), "backend-env");
}

function getVenvDir() {
  if (app.isPackaged) {
    return path.join(getDataDir(), ".venv");
  }
  const dotVenv = path.join(projectRoot, ".venv");
  if (fs.existsSync(dotVenv)) return dotVenv;
  const plainVenv = path.join(projectRoot, "venv");
  if (fs.existsSync(plainVenv)) return plainVenv;
  return dotVenv;
}

function getVenvPython() {
  const venvDir = getVenvDir();
  if (process.platform === "win32") {
    return path.join(venvDir, "Scripts", "python.exe");
  }
  return path.join(venvDir, "bin", "python");
}

function findSystemPython() {
  const candidates =
    process.platform === "win32"
      ? ["python3", "python"]
      : ["python3.14", "python3.13", "python3.12", "python3.11", "python3"];

  const env = getEnhancedEnv();
  for (const cmd of candidates) {
    try {
      const ver = execFileSync(cmd, ["--version"], {
        env,
        timeout: 5000,
        encoding: "utf8",
        windowsHide: true,
      }).trim();
      const match = ver.match(/Python (\d+)\.(\d+)/);
      if (match && Number(match[1]) >= 3 && Number(match[2]) >= 10) {
        return cmd;
      }
    } catch (_) {}
  }
  return null;
}

function getEnhancedEnv() {
  const env = { ...process.env };
  if (process.platform === "darwin") {
    const extraPaths = [
      "/opt/homebrew/bin",
      "/opt/homebrew/sbin",
      "/usr/local/bin",
      "/usr/local/sbin",
      "/usr/bin",
      "/bin",
      "/usr/sbin",
      "/sbin",
    ];
    const nvmDir = path.join(process.env.HOME || "", ".nvm/versions/node");
    try {
      const versions = fs.readdirSync(nvmDir);
      if (versions.length > 0) {
        versions.sort().reverse();
        extraPaths.unshift(path.join(nvmDir, versions[0], "bin"));
      }
    } catch (_) {}
    const currentPath = env.PATH || "/usr/bin:/bin:/usr/sbin:/sbin";
    const pathSet = new Set(currentPath.split(":"));
    for (const p of extraPaths) {
      pathSet.add(p);
    }
    env.PATH = Array.from(pathSet).join(":");
  }
  return env;
}

function isPortInUse(port) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.once("error", () => resolve(true));
    server.once("listening", () => {
      server.close();
      resolve(false);
    });
    server.listen(port, "127.0.0.1");
  });
}

function waitForServer(url, timeoutMs = 60000) {
  const start = Date.now();
  return new Promise((resolve, reject) => {
    const check = () => {
      if (Date.now() - start > timeoutMs) {
        reject(
          new Error(
            `Server at ${url} did not start within ${timeoutMs / 1000}s`
          )
        );
        return;
      }
      http
        .get(url, (res) => {
          if (res.statusCode === 200) {
            resolve();
          } else {
            setTimeout(check, 500);
          }
        })
        .on("error", () => {
          setTimeout(check, 500);
        });
    };
    check();
  });
}

function updateSplashStatus(text) {
  if (!splashWindow || splashWindow.isDestroyed()) return;
  splashWindow.webContents
    .executeJavaScript(
      `document.querySelector('.status').textContent = ${JSON.stringify(text)}`
    )
    .catch(() => {});
}

function closeSplash() {
  if (splashWindow && !splashWindow.isDestroyed()) {
    splashWindow.close();
    splashWindow = null;
  }
}

async function showErrorAndQuit(title, message) {
  closeSplash();
  await dialog.showMessageBox({
    type: "error",
    title,
    message,
    buttons: ["Quit"],
  });
  cleanup();
  app.quit();
}

function createSplashWindow() {
  const isMac = process.platform === "darwin";

  splashWindow = new BrowserWindow({
    width: 420,
    height: 320,
    resizable: false,
    maximizable: false,
    fullscreenable: false,
    alwaysOnTop: true,
    frame: false,
    transparent: true,
    backgroundColor: "#00000000",
    hasShadow: false,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  splashWindow.on("close", () => {
    if (mainWindow === null) {
      cleanup();
      app.quit();
    }
  });

  const splashHtml = `
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          display: flex;
          align-items: center;
          justify-content: center;
          height: 100vh;
          background: transparent;
          -webkit-app-region: drag;
        }
        .splash {
          background: rgba(20, 20, 30, 0.95);
          backdrop-filter: blur(40px) saturate(1.8);
          -webkit-backdrop-filter: blur(40px) saturate(1.8);
          border-radius: 24px;
          padding: 48px 40px 40px;
          text-align: center;
          border: none;
          box-shadow: 0 32px 64px rgba(0, 0, 0, 0.5);
          width: 380px;
          position: relative;
        }
        .close-btn {
          display: flex;
          position: absolute;
          top: 12px;
          ${isMac ? "left: 14px;" : "right: 12px;"}
          width: ${isMac ? "14px" : "28px"};
          height: ${isMac ? "14px" : "28px"};
          align-items: center;
          justify-content: center;
          border-radius: ${isMac ? "50%" : "6px"};
          border: none;
          background: ${isMac ? "rgba(255, 90, 95, 0.85)" : "rgba(255, 255, 255, 0.08)"};
          color: ${isMac ? "transparent" : "rgba(255, 255, 255, 0.6)"};
          font-size: ${isMac ? "10px" : "16px"};
          cursor: pointer;
          -webkit-app-region: no-drag;
          transition: background 0.15s, color 0.15s;
        }
        .close-btn:hover { background: ${isMac ? "rgba(255, 70, 75, 1)" : "rgba(232, 17, 35, 0.9)"}; color: ${isMac ? "rgba(80,0,0,0.7)" : "#fff"}; }
        .icon {
          font-size: 56px;
          margin-bottom: 16px;
          filter: drop-shadow(0 0 20px rgba(100, 150, 255, 0.3));
        }
        h1 {
          color: #fff;
          font-size: 20px;
          font-weight: 600;
          letter-spacing: -0.3px;
          margin-bottom: 8px;
        }
        .status {
          color: rgba(255, 255, 255, 0.5);
          font-size: 13px;
          margin-bottom: 24px;
          transition: opacity 0.2s;
        }
        .loader {
          width: 200px;
          height: 3px;
          background: rgba(255, 255, 255, 0.08);
          border-radius: 2px;
          margin: 0 auto;
          overflow: hidden;
        }
        .loader-bar {
          height: 100%;
          width: 40%;
          background: linear-gradient(90deg, rgba(100, 150, 255, 0.6), rgba(180, 120, 255, 0.6));
          border-radius: 2px;
          animation: slide 1.5s ease-in-out infinite;
        }
        @keyframes slide {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(350%); }
        }
      </style>
    </head>
    <body>
      <div class="splash">
        <button class="close-btn" onclick="window.close()">\u00D7</button>
        <div class="icon">\u{1F3DB}\u{FE0F}</div>
        <h1>AI Debate Council</h1>
        <p class="status">Starting servers\u2026</p>
        <div class="loader"><div class="loader-bar"></div></div>
      </div>
    </body>
    </html>
  `;

  splashWindow.loadURL(
    `data:text/html;charset=utf-8,${encodeURIComponent(splashHtml)}`
  );
}

function createMainWindow() {
  const isMac = process.platform === "darwin";

  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    show: false,
    ...(isMac
      ? { titleBarStyle: "hiddenInset", trafficLightPosition: { x: 16, y: 16 } }
      : {}),
    backgroundColor: "#f5f7f6",
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  mainWindow.loadURL(`http://127.0.0.1:${FRONTEND_PORT}`);

  mainWindow.webContents.once("did-finish-load", () => {
    if (!mainWindow) return;
    closeSplash();
    mainWindow.show();
    mainWindow.focus();
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });
}

function buildAppMenu() {
  const isMac = process.platform === "darwin";
  const template = [
    ...(isMac
      ? [
          {
            label: app.name,
            submenu: [
              { role: "about" },
              { type: "separator" },
              { role: "services" },
              { type: "separator" },
              { role: "hide" },
              { role: "hideOthers" },
              { role: "unhide" },
              { type: "separator" },
              { role: "quit" },
            ],
          },
        ]
      : []),
    {
      label: "Edit",
      submenu: [
        { role: "undo" },
        { role: "redo" },
        { type: "separator" },
        { role: "cut" },
        { role: "copy" },
        { role: "paste" },
        { role: "selectAll" },
      ],
    },
    {
      label: "View",
      submenu: [
        { role: "reload" },
        { role: "forceReload" },
        { role: "toggleDevTools" },
        { type: "separator" },
        { role: "resetZoom" },
        { role: "zoomIn" },
        { role: "zoomOut" },
        { type: "separator" },
        { role: "togglefullscreen" },
      ],
    },
    {
      label: "Window",
      submenu: [
        { role: "minimize" },
        { role: "zoom" },
        ...(isMac
          ? [{ type: "separator" }, { role: "front" }]
          : [{ role: "close" }]),
      ],
    },
  ];

  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

async function ensureBackendVenv() {
  const venvPython = getVenvPython();
  if (fs.existsSync(venvPython)) return;

  if (!app.isPackaged) {
    throw new Error(
      "Python virtual environment (.venv) not found.\n\n" +
        "Run these commands first:\n" +
        "python3 -m venv .venv\n" +
        "source .venv/bin/activate\n" +
        "pip install -r backend/requirements.txt"
    );
  }

  updateSplashStatus("Setting up Python environment\u2026");

  const systemPython = findSystemPython();
  if (!systemPython) {
    throw new Error(
      "Python 3.10 or later is required but was not found.\n\n" +
        "Please install Python from python.org and restart the app."
    );
  }

  const venvDir = getVenvDir();
  const dataDir = getDataDir();
  fs.mkdirSync(dataDir, { recursive: true });

  const env = getEnhancedEnv();

  await runCommand(systemPython, ["-m", "venv", venvDir], {
    env,
    windowsHide: true,
  });

  updateSplashStatus("Installing Python packages (this may take a few minutes)…");

  const pipPython = venvPython;
  const reqFile = path.join(projectRoot, "backend", "requirements.txt");

  const pipArgs = [
    "-m",
    "pip",
    "install",
    "--no-cache-dir",
    "--timeout",
    "60",
    "--retries",
    "3",
    "-r",
    reqFile,
  ];

  const maxAttempts = 2;
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      await runCommand(pipPython, pipArgs, {
        env,
        windowsHide: true,
        onStdout: (line) => {
          const collecting = line.match(/Collecting (\S+)/);
          if (collecting) {
            updateSplashStatus(`Installing ${collecting[1]}…`);
          }
          const downloading = line.match(/Downloading .+?(\d+(?:\.\d+)?\s*[kMG]B)/i);
          if (downloading) {
            updateSplashStatus(`Downloading… ${downloading[1]}`);
          }
          const installing = line.match(/Installing collected packages: (.+)/);
          if (installing) {
            updateSplashStatus("Finalizing packages…");
          }
        },
        onStderr: (line) => {
          const collecting = line.match(/Collecting (\S+)/);
          if (collecting) {
            updateSplashStatus(`Installing ${collecting[1]}…`);
          }
        },
        timeoutMs: 600000,
      });
      return;
    } catch (err) {
      if (attempt < maxAttempts) {
        console.log(`pip install attempt ${attempt} failed, retrying...`);
        updateSplashStatus("Retrying package installation…");
        await new Promise((r) => setTimeout(r, 3000));
      } else {
        throw new Error(
          "Failed to install Python packages.\n\n" +
            "This usually happens when pip cannot reach the internet.\n\n" +
            "Try these fixes:\n" +
            "1. Check your internet connection\n" +
            "2. If you're behind a VPN or proxy, try disconnecting it\n" +
            "3. Close the app and try again\n\n" +
            "Technical details: " +
            err.message
        );
      }
    }
  }
}

function runCommand(cmd, args, opts = {}) {
  const { onStdout, onStderr, timeoutMs, ...spawnOpts } = opts;
  return new Promise((resolve, reject) => {
    let settled = false;
    const settle = (fn, val) => {
      if (settled) return;
      settled = true;
      if (timer) clearTimeout(timer);
      fn(val);
    };

    const proc = spawn(cmd, args, {
      stdio: ["ignore", "pipe", "pipe"],
      ...spawnOpts,
    });

    let timer = null;
    if (timeoutMs) {
      timer = setTimeout(() => {
        try { proc.kill("SIGTERM"); } catch (_) {}
        settle(reject, new Error(`${cmd} timed out after ${Math.round(timeoutMs / 1000)}s`));
      }, timeoutMs);
    }

    let stderr = "";
    let stdoutBuf = "";
    proc.stdout.on("data", (d) => {
      const text = d.toString();
      process.stdout.write(`[setup] ${text}`);
      if (onStdout) {
        stdoutBuf += text;
        const lines = stdoutBuf.split("\n");
        stdoutBuf = lines.pop();
        for (const line of lines) {
          if (line.trim()) onStdout(line);
        }
      }
    });
    let stderrBuf = "";
    proc.stderr.on("data", (d) => {
      const text = d.toString();
      stderr += text;
      process.stderr.write(`[setup] ${text}`);
      if (onStderr) {
        stderrBuf += text;
        const lines = stderrBuf.split("\n");
        stderrBuf = lines.pop();
        for (const line of lines) {
          if (line.trim()) onStderr(line);
        }
      }
    });
    proc.on("error", (err) =>
      settle(reject, new Error(`Failed to run ${cmd}: ${err.message}`))
    );
    proc.on("exit", (code) => {
      if (code === 0) settle(resolve);
      else
        settle(
          reject,
          new Error(`${cmd} exited with code ${code}\n${stderr.slice(-500)}`)
        );
    });
  });
}

async function startBackend() {
  const python = getVenvPython();

  const inUse = await isPortInUse(BACKEND_PORT);
  if (inUse) {
    console.log(
      `Backend port ${BACKEND_PORT} already in use, assuming backend is running`
    );
    return;
  }

  const env = { ...getEnhancedEnv(), PYTHONUNBUFFERED: "1" };

  return new Promise((resolve, reject) => {
    backendProcess = spawn(
      python,
      [
        "-m",
        "uvicorn",
        "backend.app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        String(BACKEND_PORT),
      ],
      {
        cwd: projectRoot,
        env,
        stdio: ["ignore", "pipe", "pipe"],
        windowsHide: true,
      }
    );

    backendProcess.stdout.on("data", (data) => {
      process.stdout.write(`[backend] ${data}`);
    });
    backendProcess.stderr.on("data", (data) => {
      process.stderr.write(`[backend] ${data}`);
    });
    backendProcess.on("error", (err) => {
      reject(new Error(`Backend failed to start: ${err.message}`));
    });
    backendProcess.on("exit", (code) => {
      console.log(`Backend exited with code ${code}`);
      backendProcess = null;
    });

    resolve();
  });
}

async function startFrontend() {
  const inUse = await isPortInUse(FRONTEND_PORT);
  if (inUse) {
    console.log(
      `Frontend port ${FRONTEND_PORT} already in use, assuming frontend is running`
    );
    return;
  }

  const frontendDir = path.join(projectRoot, "frontend");
  const standaloneServer = path.join(
    frontendDir,
    ".next",
    "standalone",
    "server.js"
  );

  if (app.isPackaged && fs.existsSync(standaloneServer)) {
    const electronExe = process.execPath;
    const env = {
      ...getEnhancedEnv(),
      ELECTRON_RUN_AS_NODE: "1",
      PORT: String(FRONTEND_PORT),
      HOSTNAME: "127.0.0.1",
    };

    return new Promise((resolve, reject) => {
      frontendProcess = spawn(electronExe, [standaloneServer], {
        cwd: path.join(frontendDir, ".next", "standalone"),
        env,
        stdio: ["ignore", "pipe", "pipe"],
        windowsHide: true,
      });

      frontendProcess.stdout.on("data", (data) => {
        process.stdout.write(`[frontend] ${data}`);
      });
      frontendProcess.stderr.on("data", (data) => {
        process.stderr.write(`[frontend] ${data}`);
      });
      frontendProcess.on("error", (err) => {
        reject(new Error(`Frontend failed to start: ${err.message}`));
      });
      frontendProcess.on("exit", (code) => {
        console.log(`Frontend exited with code ${code}`);
        frontendProcess = null;
      });

      resolve();
    });
  }

  const env = getEnhancedEnv();

  if (!fs.existsSync(path.join(frontendDir, "node_modules"))) {
    console.log("Installing frontend dependencies...");
    updateSplashStatus("Installing frontend dependencies\u2026");
    const npm = process.platform === "win32" ? "npm.cmd" : "npm";
    await runCommand(npm, ["install"], {
      cwd: frontendDir,
      env,
      shell: true,
      windowsHide: true,
    });
  }

  const nextBin = path.join(frontendDir, "node_modules", ".bin", "next");
  const builtDir = path.join(frontendDir, ".next");
  const cmd = fs.existsSync(builtDir) ? "start" : "dev";

  return new Promise((resolve, reject) => {
    frontendProcess = spawn(nextBin, [cmd, "-p", String(FRONTEND_PORT)], {
      cwd: frontendDir,
      env,
      stdio: ["ignore", "pipe", "pipe"],
      shell: process.platform === "win32",
      windowsHide: true,
    });

    frontendProcess.stdout.on("data", (data) => {
      process.stdout.write(`[frontend] ${data}`);
    });
    frontendProcess.stderr.on("data", (data) => {
      process.stderr.write(`[frontend] ${data}`);
    });
    frontendProcess.on("error", (err) => {
      reject(new Error(`Frontend failed to start: ${err.message}`));
    });
    frontendProcess.on("exit", (code) => {
      console.log(`Frontend exited with code ${code}`);
      frontendProcess = null;
    });

    resolve();
  });
}

function stopProcess(proc) {
  if (!proc || proc.killed) return;
  try {
    if (process.platform === "win32") {
      spawn("taskkill", ["/pid", String(proc.pid), "/f", "/t"], {
        windowsHide: true,
      });
    } else {
      proc.kill("SIGTERM");
    }
  } catch (e) {
    console.error("Error stopping process:", e.message);
  }
}

function cleanup() {
  stopProcess(frontendProcess);
  stopProcess(backendProcess);
}

app.on("ready", async () => {
  buildAppMenu();
  createSplashWindow();

  try {
    updateSplashStatus("Preparing environment\u2026");
    await ensureBackendVenv();

    updateSplashStatus("Starting backend and frontend\u2026");
    await Promise.all([startBackend(), startFrontend()]);

    updateSplashStatus("Waiting for backend\u2026");
    await waitForServer(
      `http://127.0.0.1:${BACKEND_PORT}/health`,
      120000
    );
    console.log("Backend is ready.");

    updateSplashStatus("Waiting for frontend\u2026");
    await waitForServer(`http://127.0.0.1:${FRONTEND_PORT}`, 120000);
    console.log("Frontend is ready.");

    updateSplashStatus("Loading app\u2026");
    createMainWindow();
  } catch (err) {
    console.error("Startup error:", err);
    await showErrorAndQuit(
      "Startup Error",
      `Failed to start AI Debate Council:\n\n${err.message}`
    );
  }
});

app.on("window-all-closed", () => {
  cleanup();
  app.quit();
});

app.on("before-quit", () => {
  cleanup();
});

app.on("activate", () => {
  if (mainWindow === null && backendProcess && frontendProcess) {
    createMainWindow();
  }
});
