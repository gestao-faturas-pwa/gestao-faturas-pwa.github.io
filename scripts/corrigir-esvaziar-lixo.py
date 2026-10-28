#!/usr/bin/env python3
"""Eliminação definitiva apenas a pedido do utilizador, com backup prévio.
Não elimina faturas ativas, não limpa outros anos, não altera armazenamento.
"""
from pathlib import Path
p=Path("webapp/src/App.tsx")
s=p.read_text(encoding="utf-8")

def once(old,new):
    global s
    n=s.count(old)
    if n!=1: raise RuntimeError(f"Esperado 1 ocorrência ({n}): {old[:110]!r}")
    s=s.replace(old,new)

once("  const [showTrash, setShowTrash] = useState(false);",
     "  const [showTrash, setShowTrash] = useState(false);\n"
     "  const [isPurgingTrash, setIsPurgingTrash] = useState(false);")

anchor="  const handleDeleteSigner = async (signer: Signer) => {"
addition=r"""  // Fazer download de uma cópia datada ANTES de eliminar definitivamente.
  // Esta cópia fica sob responsabilidade do utilizador (dados confidenciais).
  const downloadBackupBeforePurge = async (): Promise<boolean> => {
    try {
      const content = await storage.exportFullBackup();
      const blob = new Blob([content], { type: 'application/json;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      const stamp = new Date().toISOString().replace(/[:.]/g, '-');
      anchor.href = url;
      anchor.download = 'Backup_Antes_Esvaziar_Lixo_' + stamp + '.json';
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      setTimeout(() => URL.revokeObjectURL(url), 30_000);
      return true;
    } catch (error) {
      console.error('Não foi possível preparar cópia antes da eliminação:', error);
      window.alert('Não foi possível preparar a cópia de segurança. NENHUMA fatura foi eliminada.');
      return false;
    }
  };

  const permanentlyDeleteInvoice = async (target: InvoiceRecord) => {
    // Revalidar a partir do estado atual; nunca apagar uma fatura ativa.
    const stored = invoices.find(i => i.id === target.id);
    if (!stored?.deletedAt || stored.documentDate?.slice(0, 4) !== String(activeFiscalYear)) {
      window.alert('Esta fatura não está no Lixo do ano selecionado. Nada foi eliminado.');
      return;
    }
    if (!window.confirm(
      'Eliminar DEFINITIVAMENTE esta fatura do Lixo?\n' +
      stored.documentNumber + ' — ' + stored.supplier +
      '\nEsta ação não pode ser desfeita pela aplicação. Será descarregada uma cópia de segurança antes.'
    )) return;
    if (window.prompt('Para confirmar a eliminação definitiva, escreva ELIMINAR:') !== 'ELIMINAR') return;
    setIsPurgingTrash(true);
    try {
      if (!(await downloadBackupBeforePurge())) return;
      await storage.deleteInvoice(stored.id);
      // Documentos antigos podem ter ficheiros anexados: só os eliminar
      // quando nenhum outro registo guardar uma referência ao mesmo ficheiro.
      if (stored.fileId && !invoices.some(i => i.id !== stored.id && i.fileId === stored.fileId)) {
        try { await storage.deleteFile(stored.fileId); }
        catch (error) { console.warn('Ficheiro antigo não removido:', error); }
      }
      setInvoices(prev => prev.filter(i => i.id !== stored.id));
      showToast('Fatura eliminada definitivamente. A cópia de segurança foi transferida.', 'info');
    } catch (error) {
      console.error('Falha na eliminação definitiva:', error);
      window.alert('Não foi possível concluir a eliminação. Confirme os registos antes de repetir.');
    } finally { setIsPurgingTrash(false); }
  };

  const emptyYearTrash = async () => {
    // A seleção deriva SEMPRE das faturas no Lixo do ano, não de todas as faturas.
    const targets = invoices.filter(i => Boolean(i.deletedAt)
      && i.documentDate?.slice(0, 4) === String(activeFiscalYear));
    if (!targets.length) return;
    if (!window.confirm(
      'ESVAZIAR o Lixo de ' + activeFiscalYear + '?\n' +
      'Serão eliminadas DEFINITIVAMENTE ' + targets.length + ' faturas do Lixo.\n' +
      'Faturas ativas e registos de outros anos ficam intactos.'
    )) return;
    const code = 'ESVAZIAR ' + activeFiscalYear;
    if (window.prompt('Para confirmar, escreva exatamente: ' + code) !== code) return;
    setIsPurgingTrash(true);
    try {
      if (!(await downloadBackupBeforePurge())) return;
      let deleted = 0;
      for (const target of targets) {
        // Confirmação de estado antes de cada operação.
        if (!target.deletedAt || target.documentDate?.slice(0, 4) !== String(activeFiscalYear)) continue;
        await storage.deleteInvoice(target.id);
        deleted += 1;
        setInvoices(prev => prev.filter(i => i.id !== target.id));
        if (target.fileId && !invoices.some(i => i.id !== target.id && i.fileId === target.fileId)) {
          try { await storage.deleteFile(target.fileId); }
          catch (error) { console.warn('Anexo legado não eliminado:', error); }
        }
      }
      showToast(deleted + ' faturas eliminadas definitivamente do Lixo de ' + activeFiscalYear + '.', 'info');
    } catch (error) {
      console.error('Falha ao esvaziar Lixo:', error);
      window.alert('A eliminação foi interrompida. Algumas faturas podem ter sido removidas. Verifique o Lixo e a cópia de segurança.');
    } finally { setIsPurgingTrash(false); }
  };

"""
once(anchor,addition+anchor)

# O botão de esvaziar é visível APENAS na vista do Lixo.
old="""                <h2 className="font-bold text-[#253B53]">Lixo — {activeFiscalYear}</h2>"""
new="""                <div className="flex flex-wrap gap-3 items-center justify-between">
                  <h2 className="font-bold text-[#253B53]">Lixo — {activeFiscalYear}</h2>
                  {trashedInvoices.length > 0 && (
                    <button type="button" disabled={isPurgingTrash}
                      onClick={() => void emptyYearTrash()}
                      className="rounded-lg bg-rose-100 text-rose-800 px-3 py-2 text-xs font-bold disabled:opacity-50">
                      Esvaziar Lixo deste ano ({trashedInvoices.length})
                    </button>
                  )}
                </div>"""
once(old,new)
old="""                    <button type="button" onClick={() => void handleRestoreInvoice(i)}
                      className="bg-[#DCEEFF] text-[#287DBB] font-bold rounded-lg px-3 py-2">Restaurar</button>"""
new="""                    <div className="flex items-center gap-2">
                      <button type="button" disabled={isPurgingTrash}
                        onClick={() => void handleRestoreInvoice(i)}
                        className="bg-[#DCEEFF] text-[#287DBB] font-bold rounded-lg px-3 py-2 disabled:opacity-50">Restaurar</button>
                      <button type="button" disabled={isPurgingTrash}
                        onClick={() => void permanentlyDeleteInvoice(i)}
                        className="bg-rose-100 text-rose-800 font-bold rounded-lg px-3 py-2 disabled:opacity-50">
                        Eliminar definitivamente
                      </button>
                    </div>"""
once(old,new)
p.write_text(s,encoding="utf-8")
print("Ações seguras do Lixo adicionadas: confirmação dupla, backup prévio, só o ano selecionado.")
