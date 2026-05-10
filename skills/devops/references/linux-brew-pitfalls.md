# Linuxbrew Pitfalls – Session-Protokoll

## 1. cyrus-sasl Compile-Fehler blockiert Batch-Installationen

**Ursache:** GCC-Inkompatibilität im `cyrus-sasl`-Formel-Build (ab Mai 2026).
Das betrifft ALLE Pakete, die `curl` oder `openldap` als Dependency haben.

**Blockierte Pakete:**
- `tldr` (hängt von `curl` ab)
- `gh` (hängt von `curl` ab)  
- `pandoc` (hängt von `curl` ab)
- `starship` (in Batch-Kontext blockiert, einzeln geht)
- `thefuck` (Python-Compile bricht)
- `gdu` (wird als `gdu-go` installiert)
- `rustup` → existiert nicht als Formel, nur `rust`

**Workaround:**
```bash
# NIE alle auf einmal!
# ❌ brew install tldr gh pandoc starship thefuck gdu rustup
# Die obigen werden failen und die Batch abbrechen

# ✅ Stattdessen: Einzeln oder mit || true
brew install eza bat fd fzf htop tree jq tmux zoxide duf lazygit neovim || true
brew install fnm pnpm volta yarn || true
brew install go pyenv rbenv jenv pipx poetry || true
brew install kubectl helm ansible lazydocker || true

# Fehlende separat:
# starship → ~/.local/bin (Binary-Download)
# tldr → npm install -g tldr
# gh → GitHub-Release-Binary
# pandoc → apt (wenn sudo verfügbar) oder Release-Binary
# rustup → curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
```

## 2. Batch-Abbruch bei erstem Fehler

Brew bricht die **gesamte** Batch-Installation ab, wenn ein einzelnes Paket fehlschlägt:
```bash
# ❌ NIE so:
brew install pkg-a pkg-b pkg-c pkg-fail pkg-d
# → pkg-d wird NIE installiert

# ✅ Immer so:
brew install pkg-a pkg-b || true
brew install pkg-c || true
brew install pkg-d || true
# Oder einzeln in Loop
for pkg in a b c d; do
  brew install "$pkg" 2>&1 | grep -E "installed|Error"
done
```

## 3. PEP 668 blockiert pip3 install --user

Moderne Debian/Ubuntu blockiert `pip install --user` via PEP 668.
Das System-Python hat kein `pip` Modul (`/usr/bin/python3 -m pip` failt).

**Alternativen:**
- `--break-system-packages` Flag (nur wenn sicher)
- `pipx` statt pip
- `npm install -g` für JS-Tools (tldr, bun, deno)
- Release-Binary direkt downloaden (starship, gh, kubectl)

## 4. Nicht in Linuxbrew verfügbare Tools

| Tool | Richtiger Weg |
|------|---------------|
| terraform | `tfenv` oder HashiCorp APT Repo |
| rustup | Direkt von rustup.rs |
| bun | `npm install -g bun` |
| deno | `npm install -g deno` |
| thefuck | pipx install oder brew einzeln |
| pandoc | apt (sudo erforderlich) oder Release-Binary |

## 5. Background-Prozesse Zeit-Limit

Homebrew-Source-Builds können 10-30 Minuten dauern.
Hermes-Terminal-Tool hat ein Timeout – nutze `background=true`:
```python
# ✅ Richtig: Background-Job
terminal(command="brew install ...", background=true, timeout=600)

# ❌ FALSCH:
terminal(command="brew install ...", timeout=60)
# → Timeout nach 60s, halb-installierter State
```
