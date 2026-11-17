# 📲 Fireport Telegram Listener (Raspberry Pi)

Python listener postavený na knihovně **Telethon**, který na Raspberry Pi v reálném čase sleduje příchozí zprávy od Telegram bota `FIREPORTcz_bot`, parsuje z nich strukturované údaje o výjezdu včetně GPS souřadnic a rozesílá je do lokálního dashboardu ([FIREPORT_Dashboard](https://github.com/maximmat/FIREPORT_Dashboard)), do **Node-RED** a na další lokální HTTP cíle.

---

## ✨ Klíčové vlastnosti

* **Napojení na `FIREPORTcz_bot` (Telethon):**
  * Naslouchá příchozím zprávám v reálném čase s identifikací desktopového klienta (`Desktop`, `Windows 11`, `4.8.1`).
  * Konfigurace Telegram API údajů bezpečně přes `.env` (`TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `SESSION_NAME`).
* **Inteligentní parser zpráv podle emoji:**
  * `🔥` → kategorie události (`kategorie`)
  * `🏙️` / `🏙` → místo události (`lokace`)
  * `🏠` → dopřesnění místa (spojeno s `ℹ️` oddělovačem ` | ` do pole `dopres`)
  * `ℹ️` / `ℹ` → doplňující popis události
  * `🚒` → výjezdová technika (`tech`)
  * Řádek s odkazem `http` a parametrem `q=lat,lon` → extrakce GPS souřadnic (`gps_lat`, `gps_lon`)
* **Odeslání poplachu na více cílů:**
  1. `POST http://127.0.0.1:5000/novy-vyjezd` – JSON data pro **FIREPORT Dashboard**
  2. `POST http://127.0.0.1:1880/poplach` – JSON data pro **Node-RED**
  3. `GET http://192.168.0.69:6879` – lokální HTTP trigger pro navazující automatizaci
* **Watchdog & hlášení stavu do dashboardu:**
  * Při startu produkčního režimu odešle `POST http://127.0.0.1:5000/set-status` (`{"offline": false}`).
  * Asynchronní smyčka `watchdog_ping()` každých **60 sekund** posílá heartbeat `POST http://127.0.0.1:5000/ping`.
  * Při kritické chybě klienta odešle `{"offline": true}` na `/set-status` a ukončí se s kódem `1`, aby jej `systemd` automaticky restartoval.
* **Bezpečný produkční režim (`setup = 0`):**
  * V produkci používá `client.start(phone=auth_failed)`, takže při neplatné `.session` nespadne do interaktivního čekání na telefonní číslo, ale zaloguje chybu a ukončí se.

---

## 🛠 Požadavky

* Raspberry Pi (nebo jiný Linux server) s Pythonem 3
* Telegram účet přihlášený k odběru zpráv od `@FIREPORTcz_bot`
* API údaje (`api_id`, `api_hash`) z [my.telegram.org](https://my.telegram.org/)
* Python knihovny: `telethon`, `requests`, `python-dotenv`

---

## 📁 Struktura projektu

```text
/home/pi/FIREPORT_TELEGRAM/
├── main_rpi.py         # Hlavní Telegram listener a watchdog
├── .env                # Citlivé API údaje (v repozitáři .env.example)
├── Fireport.session    # Vygenerovaná Telethon session databáze (negitovat!)
└── nodered_flow.txt    # Export ukázkového flow pro Node-RED
```

---

## 🚀 Instalace a první spuštění

### 1. Stažení a instalace závislostí

```bash
mkdir -p /home/pi/FIREPORT_TELEGRAM
cd /home/pi/FIREPORT_TELEGRAM
pip3 install telethon requests python-dotenv
```

### 2. Konfigurace `.env`

Zkopírujte `.env.example` do `.env` a doplňte své údaje z `my.telegram.org`:

```bash
cp .env.example .env
nano .env
```

Proměnné v `.env`:
* `TELEGRAM_API_ID` – číselné API ID aplikace.
* `TELEGRAM_API_HASH` – tajný API hash aplikace.
* `SESSION_NAME` – název souboru session (výchozí `Fireport` → vytvoří `Fireport.session`).

### 3. Prvotní vygenerování Telegram session

Před prvním spuštěním jako služby je nutné se jednou přihlásit interaktivně:

1. V `main_rpi.py` dočasně nastavte `setup = 1`.
2. Spusťte skript ručně: `python3 main_rpi.py`.
3. Zadejte telefonní číslo a ověřovací kód z Telegramu.
4. Po výpisu `Úspěšně přihlášeno!` a vytvoření `Fireport.session` nastavte v `main_rpi.py` zpět `setup = 0`.

---

## ⚙️ Automatické spouštění (Systemd)

Vytvořte soubor `/etc/systemd/system/fireport-telegram.service`:

```ini
[Unit]
Description=Fireport telegram

[Service]
User=pi
WorkingDirectory=/home/pi/FIREPORT_TELEGRAM/
ExecStart=python main_rpi.py
TimeoutStartSec=15
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Povolte a spusťte službu:

```bash
sudo systemctl daemon-reload
sudo systemctl enable fireport-telegram.service
sudo systemctl start fireport-telegram.service
```

---

## 📡 Formát odesílaných dat a Node-RED

Při každé příchozí zprávě skript sestaví a odešle JSON payload na dashboard (`/novy-vyjezd`) i do Node-RED (`/poplach`):

```json
{
  "fireport": "poplach",
  "kategorie": "POŽÁR, LESNÍ POROST",
  "lokace": "Hrádek nad Nisou, U Koupaliště",
  "dopres": "Hoří tráva 50x50m | Oznamovatel na místě",
  "tech": "CAS 20, CAS 30",
  "gps_lat": "50.853561",
  "gps_lon": "14.826439"
}
```

### Node-RED (`nodered_flow.txt`)
Soubor `nodered_flow.txt` obsahuje export flow pro Node-RED:
* Přijímá `POST /poplach` a okamžitě odpovídá HTTP kódem `200`, aby Python skript nečekal na timeout.
* Kontroluje hodnotu `fireport == "poplach"` a stav dashboardového přepínače `fireport on/off` (pomocí uzlu `join`).
* Pokud je automatizace zapnutá, odešle zprávu `"command:poplach"` na navazující akce (např. siréna, světla, hlášení).
