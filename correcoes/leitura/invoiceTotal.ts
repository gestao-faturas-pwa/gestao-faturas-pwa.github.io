export interface InvoiceLineForTotal { text: string }
export interface TotalResult { amount?: number; confidence: boolean; reason: string }

// Valores monetários devem conter centésimos. Nunca converter NIF, referências
// de pagamento ou totais de IVA em montantes de fatura.
function parseMoney(input: string): number | undefined {
  const normal = input.replace(/[\s.](?=\d{3}(?:\D|$))/g, '').replace(',', '.');
  const value = Number(normal);
  return Number.isFinite(value) && Math.abs(value) <= 1_000_000_000
    ? Math.round(value * 100) / 100 : undefined;
}
const monetary = /(?<!\d)(-?(?:\d{1,3}(?:[. ]\d{3})+|\d+)[,.]\d{2})(?!\d)/g;
const primaryLabels = [
  /\bTOTAL\s*\(\s*EUR\s*\)/i,
  /\bTOTAL\s+(?:DO\s+DOCUMENTO|DA\s+FATURA|A\s+PAGAR|GERAL)(?!\s+IVA)/i,
  /\b(?:VALOR|MONTANTE)\s+TOTAL(?:\s+A\s+PAGAR)?\b/i,
  /\bTOTAL\s+EUR\b/i,
];
const disallowed = /\b(?:TOTAL\s+(?:VALOR\s+)?IVA|TOTAL\s+(?:DESCONTOS|IL[IÍ]QUIDO|INCID[EÊ]NCIA|IMPOSTOS)|VAL\.\s*TOT\.\s*M\.\s*L[IÍ]QUID\.)\b/i;

export function selectInvoiceTotal(lines: InvoiceLineForTotal[]): TotalResult {
  const primary: number[] = [];
  const secondary: number[] = [];
  for (const { text: raw } of lines) {
    const line = raw.replace(/\s+/g, ' ').trim();
    if (!line) continue;
    for (const marker of primaryLabels) {
      const match = marker.exec(line);
      if (!match) continue;
      const tail = line.slice(match.index + match[0].length, match.index + match[0].length + 100);
      const first = [...tail.matchAll(monetary)][0]?.[1];
      if (first !== undefined) {
        const value = parseMoney(first);
        if (value !== undefined) primary.push(value);
      }
    }
    if (!disallowed.test(line)) {
      const plain = /^\s*TOTAL\s*[:–-]?\s*(?:€\s*)?(-?(?:\d{1,3}(?:[. ]\d{3})+|\d+)[,.]\d{2})\s*€?\s*$/i.exec(line);
      if (plain) {
        const value = parseMoney(plain[1]);
        if (value !== undefined) secondary.push(value);
      }
    }
  }
  const values = [...new Set(primary.length ? primary : secondary)];
  if (values.length === 1) return { amount: values[0], confidence: true, reason: 'Total confirmado por rótulo monetário explícito no documento.' };
  if (values.length > 1) return { confidence: false, reason: 'Há vários totais contraditórios; confirmar manualmente.' };
  return { confidence: false, reason: 'Total não confirmado; não serão usados números sem contexto monetário.' };
}
