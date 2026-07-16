# Bot Ticket Discord

Bot tạo ticket nhắn riêng với **Support** và **Admin**. Các vai trò khác không xem được kênh ticket.

## Tính năng

- **Tạo ticket** — Người dùng nhấn nút để mở kênh riêng
- **Ẩn vai trò** — Chỉ Support và Admin được xem/nhắn trong ticket
- **Đóng / Xóa ticket** — Đóng ticket hoặc xóa kênh (staff)
- **Xóa TẤT CẢ Ticket** — Nút cho Admin khi số ticket ≥ ngưỡng (mặc định 20)
- **Thống kê** — Lệnh `/ticket-stats` cho Admin

## Cài đặt

### 1. Tạo Bot trên Discord Developer Portal

1. Vào https://discord.com/developers/applications
2. Tạo Application mới → **Bot** → Copy **Token**
3. Bật **Privileged Gateway Intents**: `SERVER MEMBERS INTENT`, `MESSAGE CONTENT INTENT`
4. Mời bot vào server với quyền: Manage Channels, Manage Roles, Send Messages, Embed Links

### 2. Cấu hình Server Discord

Tạo trên server:

| Thành phần | Mô tả |
|-----------|--------|
| Category `Tickets` | Chứa các kênh ticket |
| Role `Support` | Nhân viên hỗ trợ |
| Role `Admin` | Quản trị viên |
| Kênh `#tao-ticket` | Kênh gửi panel |
| Kênh `#ticket-log` | (Tùy chọn) Ghi log |

**Lấy ID:** Bật Developer Mode → Chuột phải → Copy ID

### 3. Cài đặt Bot

```bash
cd Botticket
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Sửa file `.env`:

```env
DISCORD_TOKEN=token_bot_cua_ban
TICKET_PANEL_CHANNEL_ID=id_kenh_panel
TICKET_CATEGORY_ID=id_category_tickets
SUPPORT_ROLE_ID=id_role_support
ADMIN_ROLE_ID=id_role_admin
MAX_TICKETS_BEFORE_DELETE_ALL=20
LOG_CHANNEL_ID=id_kenh_log
```

### 4. Chạy Bot

```bash
python bot.py
```

Trong Discord, dùng lệnh:

```
/setup-ticket
```

Gửi panel tạo ticket vào kênh hiện tại.

## Lệnh Slash

| Lệnh | Quyền | Mô tả |
|------|-------|--------|
| `/setup-ticket` | Admin | Gửi panel tạo ticket |
| `/ticket-stats` | Admin | Xem thống kê ticket |
| `/refresh-panel` | Admin | Cập nhật panel (hiện nút xóa all nếu đủ ticket) |

## Cách hoạt động

1. Người dùng nhấn **Tạo Ticket** → Bot tạo kênh riêng
2. Quyền kênh:
   - ✅ Người tạo ticket
   - ✅ Role Support
   - ✅ Role Admin
   - ❌ Mọi vai trò khác (kể cả Moderator nếu không phải Support/Admin)
3. Khi ticket ≥ `MAX_TICKETS_BEFORE_DELETE_ALL`, Admin thấy nút **Xóa TẤT CẢ Ticket**
4. Dùng `/refresh-panel` để cập nhật panel sau khi xóa ticket

## Cấu trúc thư mục

```
Botticket/
├── bot.py              # Bot chính
├── config.py           # Đọc cấu hình từ .env
├── tickets.json        # Lưu trạng thái ticket
├── requirements.txt
├── .env.example
└── README.md
```
