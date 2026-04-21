const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true
    }
  });

  win.loadFile(path.join(__dirname, '../frontend/index.html'));
}

app.whenReady().then(createWindow);


// 🔥 Sync trigger
ipcMain.handle('sync-data', async () => {
  return new Promise((resolve, reject) => {

    const py = spawn(
      'C:\\Users\\kshit\\miniconda3\\envs\\horizia\\python.exe',
      ['D:\\project\\Horizia\\backend\\sync_pipeline.py']
    );

    py.on('close', (code) => {
      if (code === 0) resolve("Done");
      else reject("Error");
    });
  });
});