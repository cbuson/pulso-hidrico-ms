from pathlib import Path
import re, shutil

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
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

# Backups only once.
for p in (INDEX, APPJS, SW):
    if p.exists():
        bak = p.with_suffix(p.suffix + ".bak-v091")
        if not bak.exists():
            shutil.copy2(p, bak)

html = INDEX.read_text(encoding="utf-8")

# Final CSS.
css_link = '<link rel="stylesheet" href="./assets/final-v090.css?v=901" />'
if 'final-v090.css' not in html:
    m = re.search(r'(<link\s+rel=["\']stylesheet["\'][^>]*app\.css[^>]*>)', html, re.I)
    if m:
        html = html[:m.end()] + "\n  " + css_link + html[m.end():]
    else:
        html = html.replace("</head>", f"  {css_link}\n</head>")
else:
    html = re.sub(r'final-v090\.css\?v=\d+', 'final-v090.css?v=901', html)

# Visible 3D button after language selector.
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

# Public release label.
html = re.sub(
    r'(<span\s+class=["\']version["\']>)[\s\S]*?(</span>)',
    r'\1V0.9.1 · 2D + 3D\2',
    html,
    count=1,
    flags=re.I
)

# Cache-bust stable 2D assets.
html = re.sub(r'app\.css\?v=\d+', 'app.css?v=901', html)
html = re.sub(r'app\.js\?v=\d+', 'app.js?v=901', html)
INDEX.write_text(html, encoding="utf-8")

# Match mapped.earth-like pace while preserving monthly stepping:
# reference video ≈20 days/s -> ≈1.5 s per month.
js = APPJS.read_text(encoding="utf-8")
old = "state.timer=setTimeout(playbackTick,1100)"
if old in js:
    js = js.replace(old, "state.timer=setTimeout(playbackTick,1500)")
else:
    # tolerate any previous timeout value in the exact playback expression
    js, n = re.subn(r'state\.timer=setTimeout\(playbackTick,\s*\d+\s*\)',
                    'state.timer=setTimeout(playbackTick,1500)', js, count=1)
    if n == 0:
        fail("Não consegui localizar a temporização da reprodução mensal em docs/assets/app.js.")
APPJS.write_text(js, encoding="utf-8")

# PWA cache bump and 2D/3D shell cache keys.
if SW.exists():
    sw = SW.read_text(encoding="utf-8")
    sw = re.sub(r"const\s+CACHE\s*=\s*['\"][^'\"]+['\"]\s*;",
                "const CACHE='pulso-hidrico-ms-v0.9.1';", sw, count=1)

    # update previous cache-busted entries
    sw = re.sub(r'app\.css\?v=\d+', 'app.css?v=901', sw)
    sw = re.sub(r'app\.js\?v=\d+', 'app.js?v=901', sw)
    sw = re.sub(r'final-v090\.css\?v=\d+', 'final-v090.css?v=901', sw)
    sw = re.sub(r'3d/assets/app\.css\?v=\d+', '3d/assets/app.css?v=901', sw)
    sw = re.sub(r'3d/assets/app\.js\?v=\d+', '3d/assets/app.js?v=901', sw)

    core_match = re.search(r"const\s+CORE\s*=\s*\[(.*?)\]\s*;", sw, re.S)
    if core_match:
        body = core_match.group(1)
        extras = [
            "'./assets/final-v090.css?v=901'",
            "'./3d/'",
            "'./3d/index.html'",
            "'./3d/assets/app.css?v=901'",
            "'./3d/assets/app.js?v=901'",
        ]
        current = body.rstrip()
        if current and not current.rstrip().endswith(","):
            current += ","
        for x in extras:
            # avoid duplicate exact entries
            if x not in current:
                current += x + ","
        current = current.rstrip(",")
        sw = sw[:core_match.start(1)] + current + sw[core_match.end(1):]
    SW.write_text(sw, encoding="utf-8")

print("="*70)
print("PULSO HIDRICO MS · V0.9.1 · 2D + 3D · VELOCIDADE AJUSTADA")
print("="*70)
print("OK  botão 3D incorporado")
print("OK  2D continua como vista principal")
print("OK  3D permanece opcional")
print("OK  reprodução 2D ajustada para 1,5 s por mês")
print("OK  reprodução 3D já usa 1,5 s por mês")
print("OK  cache PWA atualizado para V0.9.1")
print("\nEquivalência visual aproximada:")
print("  1 mês / 1,5 s  ≈ 20 dias por segundo")
print("  1 ano           ≈ 18 segundos")
print("\nConsulta manual continua diária.")
print("Nenhum dado científico foi alterado.")
print("\nTeste:")
print("  http://localhost:9564/")
print("  http://localhost:9564/3d/")
input("\nPressione ENTER para terminar...")
