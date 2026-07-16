import os
from dotenv import load_dotenv

load_dotenv()

# ID server Discord
GUILD_ID = int(os.getenv("GUILD_ID", "0"))

# Token bot Discord
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")

# ID kênh gửi panel tạo ticket (kênh công khai)
TICKET_PANEL_CHANNEL_ID = int(os.getenv("TICKET_PANEL_CHANNEL_ID", "0"))

# ID category chứa các kênh ticket
TICKET_CATEGORY_ID = int(os.getenv("TICKET_CATEGORY_ID", "0"))

# ID vai trò Support - người dùng chỉ thấy vai trò này
SUPPORT_ROLE_ID = int(os.getenv("SUPPORT_ROLE_ID", "0"))

# ID vai trò Admin - người dùng chỉ thấy vai trò này
ADMIN_ROLE_ID = int(os.getenv("ADMIN_ROLE_ID", "0"))

# Số ticket tối đa trước khi hiện nút xóa tất cả
MAX_TICKETS_BEFORE_DELETE_ALL = int(os.getenv("MAX_TICKETS_BEFORE_DELETE_ALL", "20"))

# ID log channel (tùy chọn)
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))
