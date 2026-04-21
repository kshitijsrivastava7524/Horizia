const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  syncData: () => ipcRenderer.invoke('sync-data')
});