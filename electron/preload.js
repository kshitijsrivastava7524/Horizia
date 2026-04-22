const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {

  // ✅ accepts site name
  syncData: (site) => ipcRenderer.invoke('sync-data', site),

  onLog: (callback) => {
    ipcRenderer.removeAllListeners('sync-log');
    ipcRenderer.on('sync-log', (_, payload) => callback(payload));
  },

  onError: (callback) => {
    ipcRenderer.removeAllListeners('sync-error');
    ipcRenderer.on('sync-error', (_, payload) => callback(payload));
  },

  removeListeners: () => {
    ipcRenderer.removeAllListeners('sync-log');
    ipcRenderer.removeAllListeners('sync-error');
  }

});