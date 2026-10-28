#!/usr/bin/env python3
"""Cópia administrativa automática para pasta escolhida pelo utilizador.
Nunca guarda PDFs, texto OCR integral ou documentos; só JSON de registos.
O navegador só escreve após consentimento e permissão de escrita.
"""
from pathlib import Path
p=Path('webapp/src/services/storage.ts')
s=p.read_text(encoding='utf-8')
old="  private dbPromise: Promise<IDBDatabase> | null = null;"
assert s.count(old)==1
s=s.replace(old,"""  private dbPromise: Promise<IDBDatabase> | null = null;
  private autoBackupTimer: ReturnType<typeof setTimeout> | null = null;

  // File System Access API: disponível em alguns navegadores baseados em Chromium.
  // O diretório é sempre escolhido pelo utilizador, sem acesso livre ao disco.
  private async getBackupDirectory(): Promise<any | null> {
    const db = await this.getDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('settings', 'readonly');
      const request = tx.objectStore('settings').get('backup_directory_handle');
      request.onsuccess = () => resolve(request.result?.value || null);
      request.onerror = () => reject(request.error);
    });
  }

  async getBackupDirectoryStatus(): Promise<{
    supported: boolean; configured: boolean; granted: boolean; name?: string;
  }> {
    const supported = typeof window !== 'undefined' && 'showDirectoryPicker' in window;
    if (!supported) return { supported, configured: false, granted: false };
    try {
      const dir = await this.getBackupDirectory();
      if (!dir) return { supported, configured: false, granted: false };
      const permission = await dir.queryPermission({ mode: 'readwrite' });
      return { supported, configured: true, granted: permission === 'granted', name: dir.name };
    } catch {
      return { supported, configured: false, granted: false };
    }
  }

  async chooseBackupDirectory(): Promise<boolean> {
    const picker = (window as unknown as {
      showDirectoryPicker?: (options?: { mode?: string }) => Promise<any>;
    }).showDirectoryPicker;
    if (!picker) throw new Error('Este navegador não permite escolher uma pasta.');
    const dir = await picker({ mode: 'readwrite' });
    const db = await this.getDB();
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction('settings', 'readwrite');
      tx.objectStore('settings').put({ key: 'backup_directory_handle', value: dir });
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
      tx.onabort = () => reject(tx.error || new Error('A pasta não foi autorizada.'));
    });
    return await this.writeBackupToDirectory();
  }

  async writeBackupToDirectory(): Promise<boolean> {
    const dir = await this.getBackupDirectory();
    if (!dir) return false;
    if (await dir.queryPermission({ mode: 'readwrite' }) !== 'granted') return false;
    const json = await this.exportFullBackup();
    const file = await dir.getFileHandle('Gestao_Faturas_Backup_Automatico.json', { create: true });
    const writer = await file.createWritable();
    try {
      await writer.write(json);
      await writer.close();
    } catch (error) {
      await writer.abort?.().catch(() => undefined);
      throw error;
    }
    return true;
  }

  private scheduleAutoBackup(): void {
    if (this.autoBackupTimer) clearTimeout(this.autoBackupTimer);
    this.autoBackupTimer = setTimeout(() => {
      this.autoBackupTimer = null;
      void this.writeBackupToDirectory().catch(err =>
        console.warn('Não foi possível atualizar o backup na pasta escolhida:', err)
      );
    }, 700);
  }
""")
# A transação primária deve concluir antes do backup; se o backup falhar,
# a transação primária mantém-se. Sem alterar/anular faturas existentes.
old="tx.oncomplete = () => resolve();"
assert s.count(old)>=5,(s.count(old))
s=s.replace(old,"tx.oncomplete = () => { this.scheduleAutoBackup(); resolve(); };")
p.write_text(s,encoding='utf-8')

p=Path('webapp/src/components/SettingsView.tsx')
s=p.read_text(encoding='utf-8')
old="  const [persistMessage, setPersistMessage] = useState('');"
assert s.count(old)==1
s=s.replace(old,old+"""
  const [backupFolder, setBackupFolder] = useState<{
    supported: boolean; configured: boolean; granted: boolean; name?: string;
  } | null>(null);
  const [folderStatusMessage, setFolderStatusMessage] = useState('');
""")
old="    void storage.isPersistentStorage().then(setPersistentState);"
assert s.count(old)==1
s=s.replace(old,old+"\n    void storage.getBackupDirectoryStatus().then(setBackupFolder);")
marker="          {/* Salvaguarda administrativa e restauro */}"
assert s.count(marker)==1
ui="""          <div className="bg-white rounded-xl border border-[#B8DBFA] p-5 space-y-3">
            <h2 className="text-sm font-bold text-[#253B53]">Pasta de segurança no computador</h2>
            <p className="text-xs text-[#64788B]">
              Opcional: escolhe uma pasta do PC para manter automaticamente uma cópia
              administrativa JSON após as alterações. Nunca são exportados PDFs nem texto OCR bruto.
              Guarda esta pasta num local seguro, pois contém dados contabilísticos.
            </p>
            <p className="text-xs font-semibold text-[#253B53]">
              {!backupFolder?.supported ? 'Seleção de pasta indisponível neste navegador'
                : !backupFolder.configured ? 'Nenhuma pasta selecionada'
                : backupFolder.granted ? 'Cópia automática ativa: ' + backupFolder.name
                : 'Pasta associada, mas sem permissão de escrita ativa'}
            </p>
            <div className="flex flex-wrap gap-2">
              <button type="button" onClick={async () => {
                try {
                  const success = await storage.chooseBackupDirectory();
                  setBackupFolder(await storage.getBackupDirectoryStatus());
                  setFolderStatusMessage(success
                    ? 'Cópia inicial guardada. Novas alterações serão exportadas automaticamente.'
                    : 'A pasta foi selecionada, mas não foi possível escrever. Reveja as permissões.');
                } catch (error: any) {
                  if (error?.name !== 'AbortError') setFolderStatusMessage('Erro ao selecionar pasta: ' + (error?.message || 'Desconhecido'));
                }
              }} disabled={!backupFolder?.supported}
                className="px-3 py-2 rounded-lg bg-[#287DBB] text-white text-xs font-bold disabled:opacity-50">
                Escolher pasta para backup automático
              </button>
              {backupFolder?.granted && (
                <button type="button" onClick={async () => {
                  try {
                    const result = await storage.writeBackupToDirectory();
                    setFolderStatusMessage(result ? 'Cópia de segurança atualizada.' : 'Permissão não concedida.');
                  } catch {
                    setFolderStatusMessage('Não foi possível gravar. Verifique a pasta e as permissões.');
                  }
                }} className="px-3 py-2 rounded-lg border border-[#B8DBFA] text-xs font-bold">
                  Guardar cópia agora
                </button>
              )}
            </div>
            {folderStatusMessage && <p className="text-xs text-[#287DBB]">{folderStatusMessage}</p>}
          </div>

"""
s=s.replace(marker,ui+marker)
p.write_text(s,encoding='utf-8')
print('Pasta de backup opcional adicionada sem alterar a base de dados nem os registos.')
