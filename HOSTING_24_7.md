# Bot online 24/7 (ke ca khi ban tat may)

## Quan trong

| Cach chay | PC bat | PC tat |
|-----------|--------|--------|
| `python bot.py` thu cong | Bot online | Bot OFF |
| `run_bot_forever.bat` + Startup | Bot tu chay, tu khoi dong lai | Bot OFF |
| **Cloud hosting (mien phi)** | Bot online | **Bot van online** |

**Tat may = khong co gi chay tren may ban duoc.** Muon 24/7 that su can host bot tren cloud.

---

## Cach 1: Tu chay khi bat may (mien phi, can PC bat)

### Buoc 1 - Cai tu khoi dong

Mo PowerShell trong thu muc `Botticket`, chay:

```powershell
powershell -ExecutionPolicy Bypass -File install_autostart.ps1
```

### Buoc 2 - Hoac chay thu cong

Double-click file `run_bot_forever.bat`

- Bot tu khoi dong lai neu bi loi/crash
- Khong can mo `python bot.py` moi lan

---

## Cach 2: Online 24/7 tren Railway (mien phi, PC tat van chay)

### Buoc 1 - Tai code len GitHub

1. Tao repo GitHub moi
2. Push thu muc `Botticket` len (KHONG push file `.env` - co token!)

### Buoc 2 - Dang ky Railway

1. Vao https://railway.app
2. Dang nhap bang GitHub
3. **New Project** -> **Deploy from GitHub repo**
4. Chon repo bot cua ban

### Buoc 3 - Them bien moi truong (Environment Variables)

Trong Railway -> project -> **Variables**, them:

```
DISCORD_TOKEN=token_bot_cua_ban
GUILD_ID=1514496260206235679
TICKET_PANEL_CHANNEL_ID=1527382894673264943
TICKET_CATEGORY_ID=0
SUPPORT_ROLE_ID=0
ADMIN_ROLE_ID=0
MAX_TICKETS_BEFORE_DELETE_ALL=20
LOG_CHANNEL_ID=0
```

(Lay gia tri tu file `.env` tren may ban)

### Buoc 4 - Deploy

Railway tu dong chay `Procfile` -> bot online 24/7.

---

## Cach 3: Render.com (mien phi)

1. Vao https://render.com
2. **New** -> **Background Worker**
3. Ket noi GitHub repo
4. Build command: `pip install -r requirements.txt`
5. Start command: `python bot.py`
6. Them Environment Variables giong Railway

**Luu y:** Goi mien phi Render co the sleep sau mot thoi gian khong hoat dong.

---

## Cach 4: VPS (Oracle Cloud mien phi)

- Tao VM Linux mien phi
- Cai Python, clone repo
- Dung `systemd` de chay bot nen 24/7

---

## Khuyen nghi

| Nhu cau | Chon |
|---------|------|
| Chi can chay khi bat may | `install_autostart.ps1` |
| **Online 24/7 that su** | **Railway** hoac VPS |

Sau khi deploy cloud, bot chay doc lap - ban tat may van online.
