---
name: ae8-wsl-bootstrap
description: |
  WSL2 + Tailscale + SSH Bootstrap für AE8 (Windows Desktop) im Hermes Mesh.
  Deckt: WSL2-Start, Tailscale-Verbindung, SSH-Fallback, Hermes-Deps,
  Auto-Start und WSL2-Keepalive gegen Standby.
version: "1.0.0"
category: devops
requires:
  - tailscale-hermes-mesh
author: KlausDIG
---

# 🖥️ AE8 WSL2 Bootstrap

Vollständige Einrichtung von **AE8** (Windows Desktop) als Hermes-Mesh-Node.
AE8 ist ein Windows-Rechner mit Ubuntu 24.04 in **WSL2** — keine dedizierte Linux-Installation.

## Architektur

```
[AE8 Windows Host]
   └─ [WSL2 Ubuntu 24.04]
         ├─ tailscaled (Tailscale Daemon)
         ├─ sshd (OpenSSH Fallback)
         ├─ systemd (init)
         └─ Hermes Agent (optional)
```

**Mesh-IP:** `100.64.108.109`  
**Tailscale Name:** `ae8`  
**OS:** Windows 11 / WSL2 Ubuntu 24.04 LTS

---

## Voraussetzungen

| Voraussetzung | Status | Prüfung |
|---------------|--------|---------|
| Windows 10/11 mit WSL2 | ✅ Muss vorhanden sein | `wsl --version` in PowerShell |
| Ubuntu in WSL2 installiert | ✅ Standarddistro | Tab `klausi@AE8` zeigt Ubuntu 24.04 |
| Tailscale Windows-Client | ⚠️ Optional | WSL2 bringt eigenen `tailscaled` |
| Internet-Zugang | ✅ Notwendig | curl auf tailscale.com/install.sh |

---

## Schritt 1: WSL2 Starten (falls geschlossen)

**In Windows Terminal oder PowerShell:**
```powershell
wsl
```
→ Öffnet die **Standarddistribution** (Ubuntu 24.04).

> ⚠️ **Wichtig:** Der Prompt zeigt `klausi@AE8:/mnt/c/Users/klaus$` — das ist **WSL2**, nicht Windows! Befehle wie `wsl` funktionieren hier **nicht** (nur in `cmd.exe` oder PowerShell).

---

## Schritt 2: Tailscale in WSL2 installieren & starten

### 2.1 Prüfen ob Tailscale bereits läuft
```bash
tailscale status
```
→ Sollte den aktuellen Status zeigen.  
→ Falls `tailscaled: inactive` oder `Logged out` → Weiter mit 2.2.

### 2.2 Tailscale installieren (falls nicht vorhanden)
```bash
curl -fsSL https://tailscale.com/install.sh | sh
```
→ Insta1liert `tailscale` + `tailscaled` in WSL2.

### 2.3 Tailscale Daemon starten
```bash
sudo systemctl enable tailscaled --now
```
→ Startet `tailscaled` als systemd-Service bei jedem WSL2-Start.

### 2.4 Tailscale verbinden (mit SSH-Feature)
```bash
sudo tailscale up --ssh --accept-routes
```
→ Verbindet AE8 mit dem Mesh, aktiviert **Tailscale SSH**.

**Falls "Access denied" Fehler:**
```bash
sudo tailscale up --ssh --accept-routes --force-reauth
```

**Wichtig:** Bei WSL2 entsteht oft ein iptables-Fehler (`nf_tables: unknown option`), der aber **kosmetisch** ist — Tailscale funktioniert trotzdem.

### 2.5 Verifizieren
```bash
tailscale status
```
→ Sollte `100.95.25.46 ae8` als **online** (mit `-` am Ende) zeigen.

> **Hinweis:** Die Tailscale-IP kann sich bei Re-Authentifizierung ändern (vorher `100.64.108.109`, jetzt `100.95.25.46`). Die IP ist **nicht statisch** — verwende immer den Tailscale-Namen `ae8` statt der IP.

---

## Schritt 3: SSH-Zugang sicherstellen

### Variante A: Tailscale SSH (empfohlen, kein Passwort nötig)

Tailscale bringt einen eigenen SSH-Server — **kein openssh-server nötig**.

**Voraussetzung:** `--ssh` Flag bei `tailscale up` (siehe Schritt 2.4).

**Verbindung von einem anderen Node:**
```bash
# Von Hostinger (oder Mac Mini, lokaler Host)
tailscale ssh klausi@ae8
```
→ Öffnet direkt eine SSH-Session über Tailscale.

**Falls Tailscale SSH nicht funktioniert:**
- Prüfe mit `tailscale status` ob AE8 als **online** gilt
- Prüfe mit `sudo systemctl status tailscaled` ob der Daemon läuft
- Führe Schritt 2.4 erneut aus

### Variante B: OpenSSH-Server (Fallback)

Wenn Tailscale SSH blockiert ist oder für Nicht-Tailscale-User gebraucht wird:

```bash
sudo apt-get update -qq
sudo apt-get install -y -qq openssh-server
sudo systemctl enable ssh --now
```
→ Lauscht dann auf Port 22 im WSL2.

**Von außen verbinden (nur über Tailscale-IP):**
```bash
ssh klausi@100.64.108.109
```

---

## Schritt 4: Hermes-Agent vorbereiten (optional)

### 4.1 Dependencies installieren
```bash
sudo apt-get install -y -qq \
    git curl wget jq python3 python3-pip python3-venv \
    nodejs npm htop ncdu
```

### 4.2 Verzeichnisstruktur
```bash
mkdir -p ~/.hermes/{skills,memory,logs,scripts,cron/output}
```

### 4.3 SSH-Key erstellen (für Mesh-Sync)
```bash
if [ ! -f ~/.ssh/id_ed25519 ]; then
    ssh-keygen -t ed25519 -C "ae8-hermesh-$(date +%Y%m%d)" -f ~/.ssh/id_ed25519 -N ""
    cat ~/.ssh/id_ed25519.pub
fi
```
→ Den Public Key zu Hostinger/Mac Mini `~/.ssh/authorized_keys` hinzufügen.

---

## Schritt 5: WSL2 Standby verhindern (kritisch!)

**Problem:** WSL2 geht nach ~5 Minuten Inaktivität in Standby → Tailscale wird "idle".

### Lösung 1: `vmIdleTimeout` auf `-1` setzen

**In Windows PowerShell als Admin:**
```powershell
notepad $env:USERPROFILE\.wslconfig
```

Inhalt:
```ini
[wsl2]
vmIdleTimeout=-1
localhostForwarding=true
autoProxy=false
```

**WSL2 neu starten:**
```powershell
wsl --shutdown
```
→ Danach WSL2-Terminal neu öffnen.

### Lösung 2: Windows Scheduled Task (Keepalive)

```powershell
# PowerShell als Admin
schtasks /create /tn "Tailscale-WSL-Keepalive" `
    /tr "wsl -d Ubuntu -e bash -c 'tailscale status'" `
    /sc minute /mo 5 `
    /ru SYSTEM
```
→ Führt alle 5 Minuten `tailscale status` in WSL2 aus und hält es wach.

### Lösung 3: Systemd-Timer in WSL2 (innerhalb von Ubuntu)

```bash
sudo tee /etc/systemd/system/wsl-keepalive.service > /dev/null << 'EOF'
[Unit]
Description=WSL2 Keepalive
After=tailscaled.service

[Service]
Type=simple
ExecStart=/bin/bash -c 'while true; do tailscale status > /dev/null; sleep 60; done'
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable wsl-keepalive --now
```

> ⚠️ **Wichtig:** Lösung 1 (`vmIdleTimeout=-1`) ist die zuverlässigste. Lösungen 2+3 sind Workarounds falls 1 nicht greift.

---

## Schritt 6: Verifizierung vom Mesh aus

### Von Hostinger (Jumphost):
```bash
# 1. Ping testen
ping -c 2 100.64.108.109

# 2. Tailscale SSH testen
tailscale ssh klausi@ae8 'whoami; hostname; tailscale status | head -1'
```

### Von lokalem Linux-Host:
```bash
# Nachdem lokaler Tailscale läuft:
tailscale up --ssh --accept-routes
ping -c 2 100.64.108.109
tailscale ssh klausi@ae8 'echo AE8_ONLINE'
```

---

## Troubleshooting

### "Command 'wsl' not found, but can be installed with: sudo apt install wsl"

**Ursache:** Du bist **bereits in WSL2** (`klausi@AE8:...`) und versuchst `wsl` aufzurufen — ein Windows-Befehl.

**Fix:** WSL2-Commands **nicht in WSL2** ausführen, sondern in **PowerShell** oder **cmd.exe**.

### "tailscale: Logged out" oder "tailscaled: inactive"

```bash
# Prüfen
sudo systemctl status tailscaled

# Fix
sudo systemctl start tailscaled
sudo tailscale up --ssh --accept-routes --force-reauth
```

### "Cannot connect to the tailscale daemon"

```bash
# tailscaled läuft nicht als Daemon — manuell starten
sudo tailscaled &
sleep 2
sudo tailscale up --ssh --accept-routes
```

### "Access denied: prefs write access denied" bei `tailscale up`

**Ursache:** Tailscale wurde ohne `sudo` aufgerufen.

**Fix:**
```bash
sudo tailscale up --ssh --accept-routes
```

### AE8 zeigt "idle; offline, last seen Xm ago"

**Ursache:** WSL2 ging in Standby.

**Fix:** Siehe **Schritt 5** (vmIdleTimeout=-1).

### SSH-Zugriff funktioniert nicht

| Test | Befehl |
|------|--------|
| Tailscale SSH direkt | `tailscale ssh klausi@ae8` |
| IP-basiert | `ssh klausi@100.64.108.109` |
| OpenSSH-Status in WSL2 | `sudo systemctl status ssh` |

---

## Referenzen

- Skill: `tailscale-hermes-mesh` — Mesh-Topologie und andere Nodes
- Skill: `mac-mini-remote-access` — Mac Mini via Hostinger Jumphost
- Skill: `ssh-hostinger-vps` — Hostinger VPS Zugang

---

## Tags

- `wsl2` `windows` `tailscale` `ssh` `mesh` `ae8` `bootstrap` `desktop`
