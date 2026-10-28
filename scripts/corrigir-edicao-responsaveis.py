#!/usr/bin/env python3
"""Editar fatura, mover para Lixo, eliminar responsáveis não associados e persistência."""
from pathlib import Path
root=Path('webapp/src')
def edit(relative, fn):
    p=root/relative
    old=p.read_text(encoding='utf-8')
    new=fn(old)
    assert new!=old, relative
    p.write_text(new,encoding='utf-8')
    print('Atualizado:',relative)
def once(s,old,new):
    assert s.count(old)==1,(old[:95],s.count(old))
    return s.replace(old,new)

def signers(s):
    s=once(s,"  ShieldAlert,\n","  ShieldAlert,\n  Trash2,\n")
    s=once(s,"  onSaveSigner: (signer: Signer) => Promise<void>;",
      "  onSaveSigner: (signer: Signer) => Promise<void>;\n  onDeleteSigner: (signer: Signer) => Promise<void>;")
    s=once(s,"  onSaveSigner,\n  onFilterSignerInvoices,",
      "  onSaveSigner,\n  onDeleteSigner,\n  onFilterSignerInvoices,")
    marker="                  <button\n                    type=\"button\"\n                    onClick={() => handleToggleActive(s)}"
    ui="""                  <button
                    type="button"
                    onClick={() => {
                      if (window.confirm('Eliminar o responsável ' + s.name + '? Só é permitido se não tiver faturas associadas.')) {
                        void onDeleteSigner(s).catch(() => window.alert('Não foi possível eliminar o responsável.'));
                      }
                    }}
                    className="p-1.5 text-rose-700 hover:bg-rose-50 rounded"
                    title="Eliminar responsável sem histórico associado"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>

"""
    s=once(s,marker,ui+marker)
    marker="      <div className=\"p-4 bg-white rounded-xl border border-[#B8DBFA] text-xs text-[#64788B] space-y-1\">"
    s=once(s,marker,
      """      <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-900">
        Foram desativados os dados de demonstração automáticos. Os responsáveis já existentes
        não são alterados nem apagados. Pode eliminar individualmente nomes fictícios sem faturas associadas;
        nos restantes casos, utilize Desativar para manter o histórico.
      </div>
""" + marker)
    return s
edit('components/SignersView.tsx',signers)

def settings(s):
    s=once(s,"  const [savedSuccess, setSavedSuccess] = useState(false);",
      """  const [savedSuccess, setSavedSuccess] = useState(false);
  const [persistentState, setPersistentState] = useState<boolean | null>(null);
  const [persistMessage, setPersistMessage] = useState('');""")
    s=once(s,"    loadSuppliers();\n",
      "    loadSuppliers();\n    void storage.isPersistentStorage().then(setPersistentState);\n")
    s=once(s,"    const updated: AppSettings = {\n      warningDaysThreshold:",
      "    const updated: AppSettings = {\n      ...settings,\n      warningDaysThreshold:")
    marker="          {/* Salvaguarda administrativa e restauro */}"
    snippet="""          <div className="bg-white rounded-xl border border-[#B8DBFA] p-5 space-y-2">
            <h2 className="font-bold text-[#253B53] text-sm">Gravação persistente no computador</h2>
            <p className="text-xs text-[#64788B]">
              Os registos são guardados na base local IndexedDB desta aplicação, neste navegador e neste computador.
              A persistência reduz o risco de remoção automática pelo navegador, mas não substitui cópias de segurança.
            </p>
            <p className="text-xs font-bold">
              {persistentState === true ? 'Persistência do armazenamento concedida'
                : persistentState === false ? 'Persistência ainda não concedida'
                : 'Este navegador não informa o estado da persistência'}
            </p>
            <button type="button"
              className="px-4 py-2 bg-[#287DBB] text-white font-bold text-xs rounded-lg"
              onClick={async () => {
                try {
                  const granted = await storage.requestPersistentStorage();
                  setPersistentState(granted);
                  setPersistMessage(granted
                    ? 'Gravação persistente ativada. Continue a fazer cópias de segurança.'
                    : 'O navegador não concedeu persistência. Guarde as cópias JSON numa pasta segura.');
                } catch {
                  setPersistMessage('Não foi possível pedir armazenamento persistente.');
                }
              }}>Ativar persistência local</button>
            {persistMessage && <p className="text-xs text-[#64788B]">{persistMessage}</p>}
          </div>

"""
    s=once(s,marker,snippet+marker)
    return s
edit('components/SettingsView.tsx',settings)

def modal(s):
    s=once(s,"import React, { useState } from 'react';",
      "import React, { useState } from 'react';")
    s=once(s,"  onUpdateInvoice: (updated: InvoiceRecord) => void;",
      "  onUpdateInvoice: (updated: InvoiceRecord) => Promise<void>;\n  onTrashInvoice: (invoice: InvoiceRecord) => Promise<void>;")
    s=once(s,"  onUpdateInvoice,\n}) => {",
      "  onUpdateInvoice,\n  onTrashInvoice,\n}) => {")
    s=once(s,"  const [copiedText, setCopiedText] = useState(false);",
      """  const [copiedText, setCopiedText] = useState(false);
  const [isEditingRecord, setIsEditingRecord] = useState(false);
  const [editForm, setEditForm] = useState<InvoiceRecord | null>(null);
  const [savingEdit, setSavingEdit] = useState(false);

  const beginEdit = () => {
    if (invoice) { setEditForm({ ...invoice }); setIsEditingRecord(true); }
  };
  const saveEdit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!editForm || !invoice) return;
    if (!editForm.documentDate || !editForm.documentNumber.trim() || !editForm.supplier.trim()
      || !Number.isFinite(editForm.amount)) {
      window.alert('Preencha data, número, fornecedor e valor válido.'); return;
    }
    const now = new Date().toISOString();
    const status = editForm.returnDate ? 'DEVOLVIDA'
      : editForm.deliveryDate && editForm.assignedTo ? 'EM_ASSINATURA' : 'POR_ENTREGAR';
    setSavingEdit(true);
    try {
      await onUpdateInvoice({
        ...editForm, status, updatedAt: now,
        history: [...(invoice.history || []), {
          id: 'evt-edit-' + Date.now(), timestamp: now, effectiveDate: now.slice(0,10),
          type: 'EDICAO', description: 'Dados administrativos corrigidos manualmente.',
          author: 'Departamento de Contabilidade'
        }]
      });
      setIsEditingRecord(false);
    } catch {
      window.alert('Não foi possível guardar a correção na base local.');
    } finally { setSavingEdit(false); }
  };
""")
    marker="          <div className=\"flex items-center gap-2\">\n            {invoice.status === 'EM_ASSINATURA'"
    buttons="""          <div className="flex items-center gap-2">
            <button type="button" onClick={beginEdit}
              className="rounded-lg px-3 py-1.5 bg-white text-[#287DBB] hover:bg-[#DCEEFF] font-bold text-xs">
              Editar
            </button>
            <button type="button" onClick={() => {
              if (window.confirm('Mover a fatura ' + invoice.documentNumber + ' para o Lixo? Pode restaurá-la posteriormente.')) {
                void onTrashInvoice(invoice).catch(() => window.alert('Falha ao guardar a eliminação.'));
              }
            }}
              className="rounded-lg px-3 py-1.5 bg-rose-100 text-rose-800 hover:bg-rose-200 font-bold text-xs">
              Eliminar
            </button>
            {invoice.status === 'EM_ASSINATURA'"""
    s=once(s,marker,buttons)
    marker='          {/* Faixa Resumo de Circulação Física */}'
    form="""          {isEditingRecord && editForm && (
            <form onSubmit={saveEdit} className="space-y-3 bg-[#F3F9FF] border border-[#B8DBFA] rounded-xl p-4">
              <h3 className="font-bold text-[#253B53]">Corrigir dados desta fatura</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {([
                  ['documentDate','Data do documento','date'],
                  ['documentNumber','N.º documento','text'],
                  ['supplier','Fornecedor','text'],
                  ['amount','Valor (€)','number'],
                  ['deliveryDate','Data de entrega','date'],
                  ['returnDate','Data de devolução','date'],
                ] as const).map(([field,label,type]) => (
                  <label key={field} className="text-xs font-bold text-[#253B53]">
                    {label}
                    <input type={type} step={type === 'number' ? '0.01' : undefined}
                      required={['documentDate','documentNumber','supplier','amount'].includes(field)}
                      value={editForm[field] ?? ''}
                      onChange={event => setEditForm(prev => prev ? {
                        ...prev, [field]: field === 'amount' ? Number(event.target.value) : event.target.value
                      } : null)}
                      className="mt-1 w-full rounded-lg border border-[#B8DBFA] bg-white p-2 text-xs" />
                  </label>
                ))}
                <label className="text-xs font-bold text-[#253B53]">
                  Responsável
                  <select value={editForm.assignedTo || ''}
                    onChange={event => setEditForm(prev => prev ? {...prev,assignedTo:event.target.value || undefined} : null)}
                    className="mt-1 w-full rounded-lg border border-[#B8DBFA] p-2 bg-white text-xs">
                    <option value="">Por atribuir</option>
                    {signers.map(s => <option key={s.id} value={s.name}>{s.name}</option>)}
                  </select>
                </label>
                <label className="text-xs font-bold text-[#253B53]">
                  Observações
                  <textarea value={editForm.notes || ''}
                    onChange={event => setEditForm(prev => prev ? {...prev,notes:event.target.value} : null)}
                    className="mt-1 w-full rounded-lg border border-[#B8DBFA] p-2 bg-white text-xs" />
                </label>
              </div>
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => setIsEditingRecord(false)}
                  className="px-3 py-2 rounded-lg border bg-white text-xs">Cancelar</button>
                <button type="submit" disabled={savingEdit}
                  className="px-4 py-2 rounded-lg bg-[#287DBB] text-white text-xs font-bold">
                  {savingEdit ? 'A guardar...' : 'Guardar correções'}
                </button>
              </div>
            </form>
          )}

"""
    s=once(s,marker,form+marker)
    return s
edit('components/InvoiceDetailModal.tsx',modal)
print('Editar, Eliminar para o Lixo, gestão de responsáveis e persistência adicionados.')
