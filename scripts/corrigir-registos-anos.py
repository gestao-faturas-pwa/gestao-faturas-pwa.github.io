#!/usr/bin/env python3
from pathlib import Path

base=Path('webapp/src')
def edit(path,change):
    p=base/path
    old=p.read_text(encoding='utf-8')
    new=change(old)
    if new==old: raise RuntimeError('Nada mudou em '+path)
    p.write_text(new,encoding='utf-8')
    print('Validado:',path)

def once(s,old,new):
    assert s.count(old)==1,(old[:70],s.count(old))
    return s.replace(old,new)

def storage(s):
    assert s.count('request.onsuccess = () => resolve();')>=6
    s=s.replace('request.onsuccess = () => resolve();',
        "tx.oncomplete = () => resolve();\n      tx.onabort = () => reject(tx.error || new Error('Gravação local cancelada.'));")
    anchor='  // --- FATURAS ---'
    add="""  async isPersistentStorage(): Promise<boolean | null> {
    try {
      return navigator.storage?.persisted ? await navigator.storage.persisted() : null;
    } catch { return null; }
  }

  async requestPersistentStorage(): Promise<boolean> {
    return navigator.storage?.persist ? await navigator.storage.persist() : false;
  }

"""
    return once(s,anchor,add+anchor)
edit('services/storage.ts',storage)

def types(s):
    s=once(s,
        '  isManual?: boolean;       // Marcador de fatura inserida manualmente (sem documento anexo inicial)',
        '  isManual?: boolean;       // Marcador de fatura inserida manualmente (sem documento anexo inicial)\n  deletedAt?: string;       // Eliminação reversível, nunca destrói o registo')
    s=once(s,'  departmentName: string;\n}',
        '  departmentName: string;\n  fiscalYears?: number[];\n  activeFiscalYear?: number;\n}')
    return s
edit('types/index.ts',types)

def app(s):
    s=once(s,"import { seedInitialDemoData, getDelayAlertLevel } from './services/businessRules';",
      "import { getDelayAlertLevel } from './services/businessRules';")
    s=once(s,"      await seedInitialDemoData();",
      "      // Nunca criar ou repor responsáveis e faturas fictícios.")
    s=once(s,"  const [isLoading, setIsLoading] = useState<boolean>(true);",
      """  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [activeFiscalYear, setActiveFiscalYear] = useState(new Date().getFullYear());
  const [showTrash, setShowTrash] = useState(false);""")
    s=once(s,"      setSettings(appSettings);",
      """      setSettings(appSettings);
      setActiveFiscalYear(appSettings.activeFiscalYear || new Date().getFullYear());
      setLoadError(null);""")
    s=once(s,"      console.error('Erro ao carregar dados do IndexedDB:', err);",
      """      console.error('Erro ao carregar dados do IndexedDB:', err);
      setLoadError('Não foi possível consultar os dados locais. Não foram apagados. Evite inserir novos registos até recuperar o acesso.');""")
    s=once(s,
      """  const handleSaveSettings = async (newSettings: AppSettings) => {
    await storage.saveSettings(newSettings);
    setSettings(newSettings);
  };""",
      """  const handleSaveSettings = async (newSettings: AppSettings) => {
    await storage.saveSettings(newSettings);
    setSettings(newSettings);
  };
  const changeFiscalYear = async (year: number, newlyCreated = false) => {
    if (!Number.isInteger(year) || year < 2000 || year > 2100) {
      window.alert('Escolha um ano entre 2000 e 2100.'); return;
    }
    const years = Array.from(new Set([
      ...(settings.fiscalYears || []),
      ...invoices.map(i => Number(i.documentDate?.slice(0, 4))).filter(Number.isInteger),
      new Date().getFullYear(), year
    ])).sort((a,b) => b-a);
    const updated = { ...settings, activeFiscalYear: year, fiscalYears: years };
    try {
      await storage.saveSettings(updated);
      setSettings(updated);
      setActiveFiscalYear(year);
      setShowTrash(false);
      setSelectedInvoice(null);
      if (newlyCreated) showToast('Ano ' + year + ' criado sem alterar faturas anteriores.');
    } catch {
      window.alert('Falha ao guardar a seleção de ano; nada foi eliminado.');
    }
  };
  const addFiscalYear = () => {
    const value = window.prompt('Indique o novo ano:', String(Math.max(...availableFiscalYears) + 1));
    if (value !== null && /^[0-9]{4}$/.test(value.trim())) void changeFiscalYear(Number(value.trim()), true);
  };""")
    anchor='  // Contadores para o Navbar'
    addition="""  const availableFiscalYears = Array.from(new Set([
    new Date().getFullYear(), activeFiscalYear, ...(settings.fiscalYears || []),
    ...invoices.map(i => Number(i.documentDate?.slice(0, 4))).filter(Number.isInteger),
  ])).sort((a,b) => b-a);
  const yearInvoices = invoices.filter(i => i.documentDate?.slice(0,4) === String(activeFiscalYear));
  const visibleInvoices = yearInvoices.filter(i => !i.deletedAt);
  const trashedInvoices = yearInvoices.filter(i => Boolean(i.deletedAt));

  const handleTrashInvoice = async (target: InvoiceRecord) => {
    const now = new Date().toISOString();
    const updated: InvoiceRecord = { ...target, deletedAt: now, updatedAt: now,
      history: [...(target.history || []), {
        id: 'evt-trash-' + Date.now(), timestamp: now, effectiveDate: now.slice(0,10),
        type: 'NOTA', description: 'Fatura movida para o Lixo, recuperação disponível.',
        author: 'Departamento de Contabilidade'
      }] };
    await storage.saveInvoice(updated);
    setInvoices(prev => prev.map(i => i.id === target.id ? updated : i));
    setSelectedInvoice(null);
    showToast('Fatura movida para o Lixo. Pode restaurá-la.', 'info');
  };
  const handleRestoreInvoice = async (target: InvoiceRecord) => {
    const now = new Date().toISOString();
    const updated: InvoiceRecord = { ...target, deletedAt: undefined, updatedAt: now,
      history: [...(target.history || []), {
        id: 'evt-restore-' + Date.now(), timestamp: now, effectiveDate: now.slice(0,10),
        type: 'NOTA', description: 'Fatura restaurada do Lixo.',
        author: 'Departamento de Contabilidade'
      }] };
    await storage.saveInvoice(updated);
    setInvoices(prev => prev.map(i => i.id === target.id ? updated : i));
    showToast('Fatura restaurada.');
  };
  const handleDeleteSigner = async (signer: Signer) => {
    if (invoices.some(i => i.assignedTo === signer.name)) {
      window.alert('O responsável tem faturas associadas. Para preservar o histórico, deve desativá-lo.');
      return;
    }
    await storage.deleteSigner(signer.id);
    setSigners(prev => prev.filter(i => i.id !== signer.id));
    showToast('Responsável removido sem afetar faturas.', 'info');
  };

"""
    s=once(s,anchor,addition+anchor)
    s=s.replace("invoices.filter((inv) => inv.status === 'EM_ASSINATURA')",
                "visibleInvoices.filter((inv) => inv.status === 'EM_ASSINATURA')")
    s=once(s,"  const criticalDelayCount = invoices.filter((inv) => {",
        "  const criticalDelayCount = visibleInvoices.filter((inv) => {")
    s=once(s,"  const demoCount = invoices.filter((i) => i.isDemo === true).length;",
        "  const demoCount = invoices.filter((i) => i.isDemo === true && !i.deletedAt).length;")
    s=s.replace("invoices={invoices}", "invoices={visibleInvoices}")
    anchor="      {/* Conteúdo Principal com Container Amplo */}"
    add="""      <div className="max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-4 flex flex-wrap items-center gap-3 text-xs">
        <label htmlFor="fiscal-year" className="font-bold text-[#253B53]">Ano dos documentos</label>
        <select id="fiscal-year" value={activeFiscalYear}
          onChange={event => void changeFiscalYear(Number(event.target.value))}
          className="px-3 py-2 border border-[#B8DBFA] rounded-lg bg-white font-bold text-[#287DBB]">
          {availableFiscalYears.map(year => <option value={year} key={year}>{year}</option>)}
        </select>
        <button type="button" onClick={addFiscalYear}
          className="px-3 py-2 border border-[#B8DBFA] rounded-lg bg-white font-bold text-[#287DBB]">
          + Criar novo ano
        </button>
        <span className="text-[#64788B]">{visibleInvoices.length} faturas neste ano</span>
      </div>

"""
    s=once(s,anchor,add+anchor)
    s=once(s,"        {isLoading ? (",
      """        {loadError ? (
          <div role="alert" className="bg-rose-50 border border-rose-300 rounded-xl p-5 text-rose-900">
            <strong>Falha no armazenamento local</strong><p className="my-2">{loadError}</p>
            <button className="rounded border bg-white px-3 py-2" onClick={() => { setIsLoading(true); void loadData(); }}>
              Tentar novamente
            </button>
          </div>
        ) : isLoading ? (""")
    anchor="            {currentTab === 'invoices' && (\n              <InvoicesListView"
    replace="""            {currentTab === 'invoices' && (
              <div className="mb-3 flex justify-end">
                <button type="button" onClick={() => setShowTrash(!showTrash)}
                  className="px-3 py-2 bg-white border border-[#B8DBFA] text-[#287DBB] rounded-lg text-xs font-bold">
                  {showTrash ? 'Voltar às faturas' : 'Lixo (' + trashedInvoices.length + ')'}
                </button>
              </div>
            )}
            {currentTab === 'invoices' && showTrash && (
              <div className="rounded-xl border border-[#B8DBFA] bg-white p-5 space-y-3">
                <h2 className="font-bold text-[#253B53]">Lixo — {activeFiscalYear}</h2>
                <p className="text-xs text-[#64788B]">Os registos permanecem guardados e podem ser recuperados.</p>
                {trashedInvoices.length === 0 && <p className="text-xs">Sem faturas no Lixo.</p>}
                {trashedInvoices.map(i => (
                  <div className="border-t pt-2 flex items-center justify-between gap-3 text-xs" key={i.id}>
                    <span>{i.documentNumber} — {i.supplier} ({i.amount.toFixed(2)} €)</span>
                    <button type="button" onClick={() => void handleRestoreInvoice(i)}
                      className="bg-[#DCEEFF] text-[#287DBB] font-bold rounded-lg px-3 py-2">Restaurar</button>
                  </div>
                ))}
              </div>
            )}
            {currentTab === 'invoices' && !showTrash && (
              <InvoicesListView"""
    s=once(s,anchor,replace)
    s=once(s,"        onUpdateInvoice={handleUpdateInvoice}",
        "        onUpdateInvoice={handleUpdateInvoice}\n        onTrashInvoice={handleTrashInvoice}")
    s=once(s,"                onSaveSigner={handleSaveSigner}",
        "                onSaveSigner={handleSaveSigner}\n                onDeleteSigner={handleDeleteSigner}")
    s=once(s,"    setCurrentTab('invoices');\n  };",
       """    const year = Number(newInv.documentDate?.slice(0,4));
    if (Number.isInteger(year) && year !== activeFiscalYear) void changeFiscalYear(year);
    setCurrentTab('invoices');
  };""")
    return s
edit('App.tsx',app)
print('Sem criação de faturas e responsáveis de demonstração; anos e Lixo preservam registos.')
