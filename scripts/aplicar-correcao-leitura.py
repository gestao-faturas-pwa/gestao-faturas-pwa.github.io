#!/usr/bin/env python3
from pathlib import Path
from shutil import copyfile
root=Path("webapp")
service=root/"src/services"
# Recusar diferenças inesperadas para evitar corromper a aplicação.
path=service/"extractor.ts"
s=path.read_text(encoding="utf-8")
old="      reconstructedLines.sort((a, b) => b.y - a.y);"
assert s.count(old)==1, "Estrutura do PDF mudou: verificação necessária"
new="""      // A camada interna do PDF não segue necessariamente a leitura visual.
      for (const line of reconstructedLines) {
        line.tokens.sort((a, b) => a.x - b.x);
        line.text = line.tokens.map(token => token.str).join(' ').replace(/\\s+/g, ' ').trim();
      }
      reconstructedLines.sort((a, b) => b.y - a.y);
      const visualText = reconstructedLines.map(line => line.text).join('\\n');"""
s=s.replace(old,new)
before="""          totalExtractedText,
          reconstructedLines,
          clientCompanyName,
          qrFiscalData,
          confirmedSuppliers
        );"""
after="""          visualText,
          reconstructedLines,
          clientCompanyName,
          qrFiscalData,
          confirmedSuppliers
        );"""
assert s.count(before)==1
s=s.replace(before,after)
old="""  if (!chosenNumber) {
    const numPatterns = ["""
new="""  if (!chosenNumber && /\\bfatura\\s*[-–]?\\s*recibo\\b/i.test(fullText)) {
    // A série pode estar distante de "Fatura-recibo" na ordem interna do PDF.
    const pattern = /\\b(F[A-Z0-9]{2,12}\\s*\\/\\s*\\d[\\d ]{0,15})\\b/gi;
    const matches = [...fullText.matchAll(pattern)].map(m => m[1].replace(/\\s+/g, ''));
    const unique = [...new Set(matches)];
    if (unique.length === 1) {
      chosenNumber = 'FR ' + unique[0];
      numberConfidence = false;
      numberReason = 'Número de fatura-recibo reconstruído da série; confirmar visualmente.';
    }
  }
  if (!chosenNumber) {
    const numPatterns = ["""
assert s.count(old)==1
s=s.replace(old,new)
path.write_text(s,encoding="utf-8")
for filename in ("invoiceTotal.ts","issuerHeader.ts"):
    copyfile(Path("correcoes/leitura")/filename,service/filename)
print("Leitura reconstruída por posição, total e OCR corrigidos sem alterar o armazenamento.")
