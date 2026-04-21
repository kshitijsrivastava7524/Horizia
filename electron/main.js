const { app, BrowserWindow } = require('electron');
const path = require('path');

//autoreload
// const fs = require('fs');
const chokidar = require('chokidar');


function createWindow() {
    const win = new BrowserWindow({
        width: 1200,
        height: 800,
        show: false,
        autoHideMenuBar: true
    });

    win.loadFile(path.join(__dirname, '../frontend/index-testing.html'));
    win.setResizable(true);

    // Watch frontend folder
    chokidar.watch(path.join(__dirname, '../frontend')).on('change', () => {
        console.log("Reloading...");
        win.webContents.reload();
    });


    win.maximize();
    win.once('ready-to-show', () => {
        win.show()
    });
}

app.whenReady().then(createWindow);