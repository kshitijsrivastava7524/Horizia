const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const chokidar = require('chokidar');
const fs = require('fs');

let mainWindow;
const syncingSites = new Set(); //  track per-site instead of one global flag
const SYNC_TIMEOUT_MS = 5 * 60 * 1000;
const VALID_SITES = ['site1', 'site2', 'site3', 'site4'];

// ---------------- WINDOW ----------------
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    show: false,
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true
    }
  });

  mainWindow.loadFile(path.join(__dirname, '../frontend/index-testing.html'));

  const watcher = chokidar.watch(path.join(__dirname, '../frontend')).on('change', () => {
    console.log("Reloading frontend...");
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.reload();
    }
  });

  mainWindow.on('closed', () => {
    watcher.close();
    mainWindow = null;
  });

  mainWindow.maximize();
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

// ---------------- CONFIG ----------------
const PYTHON_PATH = process.env.PYTHON_PATH || 'python';
// const PYTHON_PATH = process.env.PYTHON_PATH || '../.venv/bin/python';
//   'C:\\Users\\kshit\\miniconda3\\envs\\horizia\\python.exe' ||
  

const SCRIPT_PATH = path.join(__dirname, '../backend/sync_pipeline.py');



// ---------------- SYNC HANDLER ----------------
ipcMain.handle('sync-data', async (_, site) => {

  // Validate site
  if (!VALID_SITES.includes(site)) {
    return { status: 'error', message: `Invalid site: ${site}` };
  }

  // Per-site busy check
  if (syncingSites.has(site)) {
    return { status: 'busy', message: `${site} sync already running` };
  }

  syncingSites.add(site);

  return new Promise((resolve) => {
    // Pass site as argument to Python
    const py = spawn(PYTHON_PATH, [SCRIPT_PATH, site]);

    let logs = [];
    let errors = [];
    let resolved = false;

    const resolveOnce = (value) => {
      if (!resolved) {
        resolved = true;
        resolve(value);
      }
    };

    const sendToFrontend = (channel, msg) => {
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send(channel, { site, msg });
      }
    };

    const timeout = setTimeout(() => {
      console.error(`Sync timed out for ${site}`);
      py.kill();
      syncingSites.delete(site);
      resolveOnce({ status: 'error', site, message: 'Sync timed out' });
    }, SYNC_TIMEOUT_MS);

    py.stdout.on('data', (data) => {
      const msg = data.toString();
      console.log(`[PYTHON ${site}]: ${msg}`);
      logs.push(msg);
      sendToFrontend('sync-log', msg);
    });

    py.stderr.on('data', (data) => {
      const err = data.toString();
      const isWarning =
        err.includes('FutureWarning') ||
        err.includes('warnings.warn') ||
        err.includes('DeprecationWarning') ||
        err.includes('UserWarning');

      if (isWarning) {
        console.warn(`[PYTHON WARNING ${site}]: ${err}`);
      } else {
        console.error(`[PYTHON ERROR ${site}]: ${err}`);
        errors.push(err);
        sendToFrontend('sync-error', err);
      }
    });

    py.on('close', (code) => {
      clearTimeout(timeout);
      syncingSites.delete(site);
      console.log(`Python exited for ${site} with code ${code}`);

      if (code === 0) {
        resolveOnce({ status: 'success', site, message: `${site} sync completed`, logs });
      } else {
        resolveOnce({ status: 'error', site, message: `${site} failed with code ${code}`, errors, logs });
      }
    });

    py.on('error', (err) => {
      clearTimeout(timeout);
      syncingSites.delete(site);
      console.error(`Failed to start Python for ${site}:`, err);
      resolveOnce({ status: 'error', site, message: 'Failed to start Python', error: err.message });
    });
  });
});





//---------get dates---------
ipcMain.handle('get-dates', (event, site) => {
  const basePath = path.join(__dirname, '../data/output/images', site);

  if (!fs.existsSync(basePath)) return [];

  return fs.readdirSync(basePath).filter(name => {
    return fs.statSync(path.join(basePath, name)).isDirectory();
  });
});

//---------get image paths---------
ipcMain.handle('get-image-path', (event, site, date, type) => {
  const fileMap = {
    rgb: 'rgb.png',
    prob: 'prob.png',
    overlay: 'rgb-mask.png',
    contour: 'contour-overlay.png'
  };

  return path.join(
    __dirname,
    '../data/output/images',
    site,
    date,
    fileMap[type]
  );
});


//---------get image paths---------
ipcMain.handle('get-metrics', (event, site, date) => {
  const filePath = path.join(
    __dirname,
    '../data/history',
    site,
    `${date}.json`
  );

  if (!fs.existsSync(filePath)) return null;

  return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
});