const { app, BrowserWindow, dialog, shell, Menu } = require("electron");
const { spawn } = require("child_process");
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

function getVenvPython() {
  if (process.platform === "win32") {
    return path.join(projectRoot, ".venv", "Scripts", "python.exe");
  }
  return path.join(projectRoot, ".venv", "bin", "python");
}

function getNpmCommand() {
  return process.platform === "win32" ? "npm.cmd" : "npm";
}

function getEnhancedEnv() {
  const env = { ...process.env };
  if (process.platform === "darwin") {
    const extraPaths = [
      "/opt/homebrew/bin",
      "/opt/homebrew/sbin",
      "/usr/local/bin",
      "/usr/local/sbin",
      path.join(process.env.HOME || "", ".nvm/versions/node"),
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
        reject(new Error(`Server at ${url} did not start within ${timeoutMs / 1000}s`));
        return;
      }
      http.get(url, (res) => {
        if (res.statusCode === 200) {
          resolve();
        } else {
          setTimeout(check, 500);
        }
      }).on("error", () => {
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

  splashWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(splashHtml)}`);
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
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.close();
      splashWindow = null;
    }
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

async function startBackend() {
  const python = getVenvPython();

  if (!fs.existsSync(python)) {
    await dialog.showMessageBox({
      type: "error",
      title: "Python Environment Not Found",
      message:
        "The Python virtual environment (.venv) was not found.\n\n" +
        "Please run the setup instructions from SETUP.md first:\n\n" +
        "python3.13 -m venv .venv\n" +
        "source .venv/bin/activate\n" +
        "pip install -r backend/requirements.txt",
      buttons: ["Quit"],
    });
    app.quit();
    return;
  }

  const inUse = await isPortInUse(BACKEND_PORT);
  if (inUse) {
    console.log(`Backend port ${BACKEND_PORT} already in use, assuming backend is running`);
    return;
  }

  const env = { ...getEnhancedEnv(), PYTHONUNBUFFERED: "1" };

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
    { cwd: projectRoot, env, stdio: ["ignore", "pipe", "pipe"], windowsHide: true }
  );

  backendProcess.stdout.on("data", (data) => {
    process.stdout.write(`[backend] ${data}`);
  });

  backendProcess.stderr.on("data", (data) => {
    process.stderr.write(`[backend] ${data}`);
  });

  backendProcess.on("exit", (code) => {
    console.log(`Backend exited with code ${code}`);
    backendProcess = null;
  });
}

async function startFrontend() {
  const inUse = await isPortInUse(FRONTEND_PORT);
  if (inUse) {
    console.log(`Frontend port ${FRONTEND_PORT} already in use, assuming frontend is running`);
    return;
  }

  const npm = getNpmCommand();
  const frontendDir = path.join(projectRoot, "frontend");

  const env = getEnhancedEnv();

  if (!fs.existsSync(path.join(frontendDir, "node_modules"))) {
    console.log("Installing frontend dependencies...");
    updateSplashStatus("Installing frontend dependencies\u2026");
    const install = spawn(npm, ["install"], {
      cwd: frontendDir,
      env,
      stdio: ["ignore", "pipe", "pipe"],
      shell: true,
      windowsHide: true,
    });
    install.stdout.on("data", (data) => {
      process.stdout.write(`[npm] ${data}`);
    });
    install.stderr.on("data", (data) => {
      process.stderr.write(`[npm] ${data}`);
    });
    await new Promise((resolve, reject) => {
      install.on("exit", (code) => {
        if (code === 0) resolve();
        else reject(new Error(`npm install exited with code ${code}`));
      });
    });
  }

  const nextBin = path.join(frontendDir, "node_modules", ".bin", "next");
  const builtDir = path.join(frontendDir, ".next");

  if (fs.existsSync(builtDir)) {
    frontendProcess = spawn(nextBin, ["start", "-p", String(FRONTEND_PORT)], {
      cwd: frontendDir,
      env,
      stdio: ["ignore", "pipe", "pipe"],
      shell: process.platform === "win32",
      windowsHide: true,
    });
  } else {
    frontendProcess = spawn(nextBin, ["dev", "-p", String(FRONTEND_PORT)], {
      cwd: frontendDir,
      env,
      stdio: ["ignore", "pipe", "pipe"],
      shell: process.platform === "win32",
      windowsHide: true,
    });
  }

  frontendProcess.stdout.on("data", (data) => {
    process.stdout.write(`[frontend] ${data}`);
  });

  frontendProcess.stderr.on("data", (data) => {
    process.stderr.write(`[frontend] ${data}`);
  });

  frontendProcess.on("exit", (code) => {
    console.log(`Frontend exited with code ${code}`);
    frontendProcess = null;
  });
}

function stopProcess(proc) {
  if (!proc || proc.killed) return;
  try {
    if (process.platform === "win32") {
      spawn("taskkill", ["/pid", String(proc.pid), "/f", "/t"], { windowsHide: true });
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
    updateSplashStatus("Starting backend and frontend\u2026");
    await Promise.all([startBackend(), startFrontend()]);

    updateSplashStatus("Waiting for backend\u2026");
    await waitForServer(`http://127.0.0.1:${BACKEND_PORT}/health`, 120000);
    console.log("Backend is ready.");

    updateSplashStatus("Waiting for frontend\u2026");
    await waitForServer(`http://127.0.0.1:${FRONTEND_PORT}`, 120000);
    console.log("Frontend is ready.");

    updateSplashStatus("Loading app\u2026");
    createMainWindow();
  } catch (err) {
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.close();
      splashWindow = null;
    }
    await dialog.showMessageBox({
      type: "error",
      title: "Startup Error",
      message: `Failed to start AI Debate Council:\n\n${err.message}`,
      buttons: ["Quit"],
    });
    cleanup();
    app.quit();
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
