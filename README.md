# 🌌 CONCORD Telegram Boti (Kuchaytirilgan Referal Tizimi)

Ushbu Telegram bot faqat **referal havola** orqali ro'yxatdan o'tish imkoniyatiga ega bo'lib, to'liq o'zbek tilida yuqori tezlik va kengaytirilgan funksiyalar bilan ishlab chiqilgan.

---

## 📌 Asosiy Xususiyatlar va Kuchaytirilgan Funksiyalar

1. **Faqat referal havola orqali kirish:**
   - Yangi foydalanuvchi oddiy `/start` bosganda:
     `⚠️ Botda ro'yxatdan o'tish faqat taklif qiluvchining referal havolasi orqali mumkin.`
   - Taklif havolasi orqali kirganda (`t.me/bot_username?start=ref_ID`):
     - Taklif qiluvchi (Kurator) to'liq ma'lumotlari.
     - Yangi a'zoning o'z ma'lumotlari.
     - `✅ RO'YXATDAN O'TISH` tasdiqlash tugmasi.
     - Ro'yxatdan o'tgach, kuratorga real-vaqt rejimida bildirishnoma boradi.

2. **Asosiy Menyu:**
   - CONCORD kosmik banner rasmi.
   - O'zbek tilidagi tavsif matni:
     `CONCORD — ham faol, ham passiv daromad olish uchun yuqori salohiyatga ega qulay dastur. Ko'plab daromad manbalari va moliyaviy vositalar kapitalingizni ko'paytirishga yordam beradi.`
   - Tugmalar:
     - `♦️ Asosiy menyu ♦️`
     - `📊 Marketing` | `👤 Kabinet`

3. **📊 Kuchaytirilgan «Marketing» bo'limi:**
   - 💎 **Daromad turlari & Foizlar** (Direct 15%, Global pool, keshbek).
   - 🌳 **3-Darajali jamoaviy tizim** (1-daraja 15%, 2-daraja 7%, 3-daraja 3%).
   - 🏆 **Martabalar & Unvonlar** (Boshlang'ich, Bronza, Kumush, Oltin, VIP Diamond).
   - 🧮 **Interaktiv Daromad Kalkulyatori** — hamkorlar soni va depozit summasini tanlab, real-vaqtda kutilayotgan daromadni hisoblab ko'rish.

4. **👤 Kuchaytirilgan «Kabinet» bo'limi:**
   - 🎖 Foydalanuvchi maqomi va statistikasi.
   - 🏆 Kurator ma'lumotlari va to'g'ridan-to'g'ri bog'lanish tugmasi.
   - 🔗 **Referal havola** va 📤 **«Do'stlarga ulashish»** tezkor Telegram tugmasi.
   - 📲 **Dinamik QR Kod yaratish** — shaxsiy taklif havolasi uchun chiroyli QR kod rasm formatida jo'natiladi.
   - 👥 **Hamkorlar ro'yxati (Paginatsiya bilan)** — sahifalab hamkorlar holatini ko'rish.
   - 🌳 **3-Darajali jamoa strukturasi** (1-daraja, 2-daraja, 3-daraja soni).

4. **📱 Telegram Mini App (Web App):**
   - Skrinshotlarga mos zamonaviy zumrad (emerald dark) interfeys.
   - **Bosh sahifa:** Foydalanuvchi ma'lumotlari, umumiy daromad ($30), jamoa soni (7 ta), daraja (2-daraja), sana, referal havola va nusxalash.
   - **Yon menyu (Sidebar Drawer):** Bosh sahifa, Moliya, Hamkorlar, Tuzilma, Marketing, Asboblar, Taqdimotlar, Hujjatlar, Guruhlar, Chek generatori va Vizitka.
   - **Interaktiv xususiyatlar:** QR kod, Chek generatori, Vizitka kartochkasi, Telegram orqali bitta bosishda ulashish.

5. **👑 Admin Boshqaruv Paneli (`/admin`):**
   - Jami foydalanuvchilar va top-referallar reytingi.
   - Barcha a'zolarga ommaviy xabar yuborish (Broadcast).
   - Bosh admin (root) taklif havolasini olish.

---

## 🌐 Mini Appni Telegramda Ishlatish:

1. Agar Mini Appni to'g'ridan-to'g'ri Telegram ichida ochmoqchi bo'lsangiz, `ngrok` yoki serveringizning HTTPS domenini `.env` fayliga yozing:
   ```env
   WEBAPP_URL=https://sizning-domeningiz.com
   ```
2. Bot ishga tushganda avtomatik ravishda `http://localhost:8080` portida veb-serverni ham ishga tushiradi.

---

## ⚙️ O'rnatish va Ishga tushirish

### 1. Talablar:
- Python 3.10+
- Kutubxonalar: `aiogram`, `aiosqlite`, `python-dotenv`, `pillow`, `qrcode`

```bash
pip install -r requirements.txt
```

### 2. Sozlash (`.env` fayli):
`.env` faylini oching va bot tokeningiz hamda Telegram ID raqamingizni kiriting:

```env
BOT_TOKEN=1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ
ADMINS=SIZNING_TELEGRAM_ID
DB_NAME=concord_bot.db
```

### 3. Botni ishga tushirish:

```bash
python main.py
```
