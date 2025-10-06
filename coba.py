import logging
import datetime
from collections import defaultdict

from telegram import Update, ChatPermissions
from telegram.ext import Application, MessageHandler, filters, ContextTypes, JobQueue
from telegram.constants import ParseMode

# --- ISI BAGIAN PENTING DI BAWAH INI ---
TOKEN = "8427394270:AAHLwxk9FzArbZ9nbNUPVl_h6IEGfcBufZI"
ID_GRUP_KAMU = -1002853838456
URL_FOTO_PROMOSI = "https://i.postimg.cc/7PcbWH3F/GAME-SLOT.png"
# --------------------------------------------------

# --- PENGATURAN KEAMANAN (BISA KAMU UBAH) ---
SPAM_MESSAGE_LIMIT = 5
SPAM_TIME_LIMIT_SECONDS = 3
# --- DAFTAR KATA TERLARANG BARU ---
KATA_TERLARANG = [
    "anjing", "babi", "pepek", "kontol", "penipu", "scam",
    "lonte", "jancok", "pelacur", "memek", "jembut"
]
# --------------------------------------------------

# Variabel untuk melacak spam (jangan diubah)
USER_SPAM_TRACKER = defaultdict(list)

# Mengatur logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# --- FUNGSI-FUNGSI PROMOSI ---
async def hapus_pesan_promo(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    try:
        await context.bot.delete_message(chat_id=job.chat_id, message_id=job.data['message_id'])
        print(f"Pesan promosi (ID: {job.data['message_id']}) berhasil dihapus.")
    except Exception as e:
        print(f"Gagal menghapus pesan promosi: {e}")

async def kirim_pesan_promosi(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        teks_promosi = (
            "📣 <b>PENGUMUMAN PENTING!</b> 📣\n\n"
            "📌 Kabar gembira buat kalian yang pengen menang! <a href='https://bit.ly/gps88slot'>GPS88</a> tempatnya! Rasakan sensasi kemenangan tanpa batas karena di sini, semua bisa menang❗️\n\n"
            "✅ WD berapapun, <b>PASTI DIBAYAR</b> ❗️\n"
            "✅ Proses Deposit & WD <b>SUPER CEPAT</b>❗️\n"
            "✅ CS Support <b>24 JAM NONSTOP</b>❗️\n\n"
            "👛🔤🔤🔤🔤🔤\n"
            "💙💚💜🧡❤️🤍🧡💙🧡💙\n\n"
            "🤩🤩 ❗️❗️❗️\n\n"
            "📌 Jangan sampai ketinggalan, klik link di bawah ini sekarang juga ❗️\n\n"
            "💰 <a href='https://linktr.ee/gps88_official'>LINK GACOR DISINI</a>\n"
            "✅ <a href='https://bit.ly/gps88slot'>LINK ALTERNATIF</a>\n\n"
            "🌟 <a href='https://wa.me/+6282160306696'>WA ADMIN 1</a>\n"
            "🌟 <a href='https://t.me/gps88adm'>TELE ADMIN 2</a>\n"
            "🌟 <a href='https://t.me/GPS88slot'>GRUP TELEGRAM</a>\n"
            "🌟 <a href='https://www.instagram.com/gps88_official/'>INSTAGRAM OFFICIAL</a>"
        )
        pesan_terkirim = await context.bot.send_photo(
            chat_id=ID_GRUP_KAMU, photo=URL_FOTO_PROMOSI, caption=teks_promosi, parse_mode=ParseMode.HTML
        )
        print("Pesan promosi berhasil terkirim.")
        # Jadwalkan penghapusan pesan ini 2 JAM dari sekarang (7200 detik)
        context.job_queue.run_once(
            hapus_pesan_promo, 7200, chat_id=ID_GRUP_KAMU, data={'message_id': pesan_terkirim.message_id}
        )
    except Exception as e:
        print(f"Gagal mengirim pesan promosi: {e}")

# --- FUNGSI-FUNGSI KEAMANAN BARU & LAMA ---
async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    message = update.message
    
    chat_admins = await context.bot.get_chat_administrators(chat_id)
    admin_ids = {admin.user.id for admin in chat_admins}
    if user_id in admin_ids:
        return

    # Hitung waktu untuk hukuman mute 24 jam
    mute_duration = datetime.timedelta(hours=24)
    mute_until_date = datetime.datetime.now() + mute_duration
    
    # Izin untuk pengguna yang di-mute (tidak bisa mengirim apapun)
    mute_permissions = ChatPermissions(can_send_messages=False, can_send_other_messages=False, can_add_web_page_previews=False)

    # 1. FITUR ANTI-LINK
    if message.entities and any(e.type in ["url", "text_link"] for e in message.entities):
        try:
            await message.delete()
            await context.bot.restrict_chat_member(
                chat_id=chat_id, user_id=user_id, permissions=mute_permissions, until_date=mute_until_date
            )
            print(f"Pengguna {update.effective_user.first_name} di-MUTE 24 JAM karena mengirim link.")
            return
        except Exception as e:
            print(f"Gagal menindak pengirim link: {e}")

    # 2. FITUR ANTI KATA KOTOR
    message_text = message.text or message.caption or ""
    if any(kata in message_text.lower() for kata in KATA_TERLARANG):
        try:
            await message.delete()
            await context.bot.restrict_chat_member(
                chat_id=chat_id, user_id=user_id, permissions=mute_permissions, until_date=mute_until_date
            )
            print(f"Pengguna {update.effective_user.first_name} di-MUTE 24 JAM karena berkata kotor.")
            return
        except Exception as e:
            print(f"Gagal menindak kata kotor: {e}")

    # 3. FITUR ANTI-SPAM (FLOODING)
    current_time = datetime.datetime.now()
    USER_SPAM_TRACKER[user_id].append(current_time)
    time_limit = datetime.timedelta(seconds=SPAM_TIME_LIMIT_SECONDS)
    USER_SPAM_TRACKER[user_id] = [t for t in USER_SPAM_TRACKER[user_id] if current_time - t < time_limit]
    
    if len(USER_SPAM_TRACKER[user_id]) > SPAM_MESSAGE_LIMIT:
        try:
            await message.delete() # Hapus pesan spam terakhir
            await context.bot.restrict_chat_member(
                chat_id=chat_id, user_id=user_id, permissions=mute_permissions, until_date=mute_until_date
            )
            print(f"Pengguna {update.effective_user.first_name} di-MUTE 24 JAM karena spam/flood.")
            del USER_SPAM_TRACKER[user_id]
        except Exception as e:
            print(f"Gagal mem-mute spammer: {e}")
            
def main() -> None:
    application = Application.builder().token(TOKEN).job_queue(JobQueue()).build()
    
    # Menjalankan fungsi promosi setiap 2 JAM (7200 detik)
    application.job_queue.run_repeating(kirim_pesan_promosi, interval=7200, first=10)
    
    # Menjalankan fungsi keamanan untuk SEMUA jenis pesan
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_all_messages))

    print("Bot berjalan dengan ATURAN BARU: Mute 24 Jam, Promosi 2 Jam Sekali...")
    application.run_polling()

if __name__ == "__main__":
    main()