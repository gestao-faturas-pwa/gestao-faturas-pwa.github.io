#!/usr/bin/env python3
"""Prepara a PWA para o domínio exclusivo gestao-faturas-pwa.github.io."""
import json
from pathlib import Path

root = Path("webapp")
manifest_path = root / "public" / "manifest.webmanifest"
index_path = root / "index.html"
sw_path = root / "public" / "sw.js"
finalizer_path = root / "scripts" / "finalize-pages.mjs"

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest.update({
    "id": "/gestao-faturas-assinaturas-app-v1",
    "start_url": "/",
    "scope": "/",
    "name": "Gestão de Faturas | Controlo de Assinaturas",
    "short_name": "Gestão de Faturas",
    "display": "standalone",
})
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

html = index_path.read_text(encoding="utf-8")
old_reg = "navigator.serviceWorker.register('./sw.js', { scope: './' })"
assert old_reg in html, "Registo do Service Worker inesperado: publicação interrompida"
html = html.replace(old_reg, "navigator.serviceWorker.register('/sw.js', { scope: '/' })")
assert '<link rel="manifest" href="./manifest.webmanifest" />' in html
html = html.replace('<link rel="manifest" href="./manifest.webmanifest" />',
                    '<link rel="manifest" href="/manifest.webmanifest" />')
index_path.write_text(html, encoding="utf-8")

sw = sw_path.read_text(encoding="utf-8")
finalizer = finalizer_path.read_text(encoding="utf-8")
old_cache = "gestao-faturas-v5"
new_cache = "gestao-faturas-exclusiva-v6"
assert old_cache in sw and old_cache in finalizer
sw = sw.replace(old_cache, new_cache)
sw = sw.replace('key.startsWith("gestao-faturas-")',
                'key.startsWith("gestao-faturas-exclusiva-")')
finalizer = finalizer.replace(old_cache, new_cache)
sw_path.write_text(sw, encoding="utf-8")
finalizer_path.write_text(finalizer, encoding="utf-8")
print("PWA isolada: origem, identidade e cache exclusivas no novo domínio.")
