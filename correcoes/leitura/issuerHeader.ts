// OCR local pode confundir símbolos de um logótipo com palavras. Apenas
// reconstruir frases societárias ou institucionais legíveis. Exigir confirmação.
const institutional = /\b(?:ASSOCIA[CÇ][AÃ]O|FUNDA[CÇ][AÃ]O|INSTITUTO|UNIVERSIDADE|COOPERATIVA|FEDERA[CÇ][AÃ]O|MUNIC[IÍ]PIO|ORDEM|SINDICATO|CENTRO|SOCIEDADE|COMPANHIA)\b/i;
const legal = /\b(?:LDA\.?|S\.?A\.?|UNIPESSOAL|E\.?P\.?E\.?)\b/i;
const bad = /\b(?:FATURA|RECIBO|NIF|CLIENTE|EXM[OA]|RUA|AVENIDA|IBAN|REF\.?|TOTAL|CONTRIBUINTE|ORIGINAL|PAGAMENTO|DATA|DOCUMENTO)\b/i;
const upper = /\b(?:[A-ZÁÀÂÃÉÊÍÓÔÕÚÜÇ]{2,}|E|A|O)\b(?:\s+\b(?:[A-ZÁÀÂÃÉÊÍÓÔÕÚÜÇ]{2,}|E|A|O|DE|DA|DO|DAS|DOS)\b){0,9}/g;
const clean = (s: string) => s.replace(/\s+/g, ' ').replace(/^[^A-ZÁÀÂÃÉÊÍÓÔÕÚÇ]+|[^A-ZÁÀÂÃÉÊÍÓÔÕÚÇ.]+$/g, '').trim();

export function suggestIssuerFromHeaderOcr(text: string): string | undefined {
  const entries = text.split(/\r?\n/).map(line =>
    ([...line.matchAll(upper)].map(m => clean(m[0]))
      .filter(p => p.length >= 3 && !bad.test(p))
      .sort((a, b) => b.length - a.length)[0] || '')
  ).filter(Boolean);
  const anchor = entries.findIndex(s => institutional.test(s) || legal.test(s));
  if (anchor < 0) return undefined;
  const parts = [entries[anchor]];
  for (let i = anchor + 1; i < Math.min(entries.length, anchor + 5); i++) {
    const s = entries[i];
    if (bad.test(s) || /\d/.test(s) || s.length > 65) break;
    if (!/^(?:A|O|E|DE|DA|DO|DAS|DOS)\b/i.test(s) && !institutional.test(s) && !legal.test(s)) break;
    parts.push(s);
    if (parts.join(' ').length > 125) break;
  }
  const result = clean(parts.join(' '));
  if (result.length < 28 || result.length > 140 || result.split(/\s+/).length < 4) return undefined;
  return result;
}
