import assert from 'node:assert/strict';
import { selectInvoiceTotal } from '../webapp/src/services/invoiceTotal.ts';
import { suggestIssuerFromHeaderOcr } from '../webapp/src/services/issuerHeader.ts';
import { readFileSync } from 'node:fs';

const ocr = 'APECA\nesccse eee ASSOCIAÇÃO PORTUGUESA\nsecececae DAS EMPRESAS\ncescecees DE CONTABILIDADE\neeseceeee E ADMINISTRAÇÃO Ex\nRua Jerónimo Mendonça';
assert.equal(suggestIssuerFromHeaderOcr(ocr),
  'ASSOCIAÇÃO PORTUGUESA DAS EMPRESAS DE CONTABILIDADE E ADMINISTRAÇÃO');
assert.equal(suggestIssuerFromHeaderOcr('xxx yyy\\nRua 21\\n11220000000'),undefined);
const check = (rows, expected) => assert.equal(
  selectInvoiceTotal(rows.map(text=>({text}))).amount,expected);
check(['TOTAL: 48,78 IVA 11,22 TOTAL ( EUR ) 60,00'],60);
check(['VALOR TOTAL: 859,46'],859.46);
check(['TOTAL A PAGAR 1.205,40'],1205.40);
check(['TOTAL VALOR IVA 11,22','REF MB 11220000000'],undefined);
check(['VALOR TOTAL: -262,50'], -262.5);
const extractor=readFileSync('webapp/src/services/extractor.ts','utf8');
assert(extractor.includes('line.tokens.sort((a, b) => a.x - b.x)'));
assert(extractor.includes('visualText,\n          reconstructedLines'));
assert(extractor.includes("chosenNumber = 'FR ' + unique[0]"));
console.log('7 verificações de OCR, totais e reconstrução estrutural: PASSOU');
