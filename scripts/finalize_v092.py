
from pathlib import Path
import re, shutil

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
INDEX = DOCS / "index.html"
APPJS = DOCS / "assets" / "app.js"
SW = DOCS / "sw.js"

def fail(msg):
    print(f"\nERRO: {msg}")
    input("\nPressione ENTER para sair...")
    raise SystemExit(1)

if not INDEX.exists():
    fail(f"Não encontrei {INDEX}. Extraia este pacote na raiz de pulso-hidrico-ms.")
if not APPJS.exists():
    fail(f"Não encontrei {APPJS}.")

for p in (INDEX, APPJS, SW):
    if p.exists():
        bak = p.with_suffix(p.suffix + ".bak-v092")
        if not bak.exists():
            shutil.copy2(p, bak)

html = INDEX.read_text(encoding="utf-8")

css_link = '<link rel="stylesheet" href="./assets/final-v090.css?v=902" />'
if 'final-v090.css' not in html:
    m = re.search(r'(<link\s+rel=["\']stylesheet["\'][^>]*app\.css[^>]*>)', html, re.I)
    if m:
        html = html[:m.end()] + "\n  " + css_link + html[m.end():]
    else:
        html = html.replace("</head>", "  " + css_link + "\n</head>")
else:
    html = re.sub(r'final-v090\.css\?v=\d+', 'final-v090.css?v=902', html)

button = (
    '<a id="view3DBtn" class="view3d-button" href="./3d/" '
    'aria-label="Abrir modo 3D / Abrir modo 3D" '
    'title="Modo 3D · rios volumétricos">3D</a>'
)
if 'id="view3DBtn"' not in html:
    pat = re.compile(r'(<button\s+id=["\']langToggle["\'][\s\S]*?</button>)', re.I)
    m = pat.search(html)
    if not m:
        fail("Não consegui localizar o seletor PT/ES no docs/index.html.")
    html = html[:m.end()] + "\n        " + button + html[m.end():]

html = re.sub(
    r'(<span\s+class=["\']version["\']>)[\s\S]*?(</span>)',
    r'\1V0.9.2 · 2D + 3D\2',
    html,
    count=1,
    flags=re.I
)

pt_pattern = re.compile(
    r'<section><h3>Projeto relacionado</h3><div class="dialog-links">[\s\S]*?</div></section>',
    re.I
)
pt_replacement = (
    '<section><h3>Projetos relacionados</h3><div class="dialog-links">'
    '<a href="https://cbuson.github.io/atlas-geocientifico-ms/" target="_blank" rel="noopener">'
    '<strong>ITA ARANDU MS</strong><small>Atlas geocientífico educativo e científico de Mato Grosso do Sul · abrir projeto ↗</small></a>'
    '<a href="https://cbuson.github.io/pih-ms/" target="_blank" rel="noopener">'
    '<strong>PIH-MS</strong><small>Prioridade de Investigação Hidrogeológica de Mato Grosso do Sul · abrir projeto ↗</small></a>'
    '</div></section>'
)
html = pt_pattern.sub(pt_replacement, html, count=1)

es_pattern = re.compile(
    r'<section><h3>Proyecto relacionado</h3><div class="dialog-links">[\s\S]*?</div></section>',
    re.I
)
es_replacement = (
    '<section><h3>Proyectos relacionados</h3><div class="dialog-links">'
    '<a href="https://cbuson.github.io/atlas-geocientifico-ms/" target="_blank" rel="noopener">'
    '<strong>ITA ARANDU MS</strong><small>Atlas geocientífico educativo y científico de Mato Grosso do Sul · abrir proyecto ↗</small></a>'
    '<a href="https://cbuson.github.io/pih-ms/" target="_blank" rel="noopener">'
    '<strong>PIH-MS</strong><small>Prioridad de Investigación Hidrogeológica de Mato Grosso do Sul · abrir proyecto ↗</small></a>'
    '</div></section>'
)
html = es_pattern.sub(es_replacement, html, count=1)

html = re.sub(r'app\.css\?v=\d+', 'app.css?v=902', html)
html = re.sub(r'app\.js\?v=\d+', 'app.js?v=902', html)
INDEX.write_text(html, encoding="utf-8")

js = APPJS.read_text(encoding="utf-8")
js = re.sub(r'state\.timer=setTimeout\(playbackTick,\s*\d+\s*\)',
            'state.timer=setTimeout(playbackTick,1500)', js)
APPJS.write_text(js, encoding="utf-8")

if SW.exists():
    sw = SW.read_text(encoding="utf-8")
    sw = re.sub(r"const\s+CACHE\s*=\s*['\"][^'\"]+['\"]\s*;",
                "const CACHE='pulso-hidrico-ms-v0.9.2';", sw, count=1)
    sw = re.sub(r'app\.css\?v=\d+', 'app.css?v=902', sw)
    sw = re.sub(r'app\.js\?v=\d+', 'app.js?v=902', sw)
    sw = re.sub(r'final-v090\.css\?v=\d+', 'final-v090.css?v=902', sw)
    sw = re.sub(r'3d/assets/app\.css\?v=\d+', '3d/assets/app.css?v=902', sw)
    sw = re.sub(r'3d/assets/app\.js\?v=\d+', '3d/assets/app.js?v=902', sw)
    core = re.search(r"const\s+CORE\s*=\s*\[(.*?)\]\s*;", sw, re.S)
    if core:
        body = core.group(1).rstrip()
        if body and not body.endswith(","):
            body += ","
        for item in [
            "'./assets/final-v090.css?v=902'",
            "'./3d/'",
            "'./3d/index.html'",
            "'./3d/assets/app.css?v=902'",
            "'./3d/assets/app.js?v=902'"
        ]:
            if item not in body:
                body += item + ","
        body = body.rstrip(",")
        sw = sw[:core.start(1)] + body + sw[core.end(1):]
    SW.write_text(sw, encoding="utf-8")

print("="*72)
print("PULSO HIDRICO MS · V0.9.2")
print("="*72)
print("OK  botão 3D visível no 2D")
print("OK  botão 2D sempre visível no 3D, inclusive celular estreito")
print("OK  ITA ARANDU MS com link público")
print("OK  PIH-MS incorporado com link público")
print("OK  PT/ES atualizado")
print("OK  reprodução permanece em 1,5 s por mês")
print("OK  cache PWA atualizado")
print("\nTeste:")
print("  http://localhost:9564/")
print("  http://localhost:9564/3d/")
input("\nPressione ENTER para terminar...")
