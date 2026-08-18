# 👑 BUYUK HAYOTGA YO'L Telegram Boti (Kuchaytirilgan Referal Tizimi)

Ushbu Telegram boti **aiogram 3** asosida ishlab chiqilgan bo'lib, **faqat taklif (referal) havolasi orqali ro'yxatdan o'tish**, 6 bosqichli marketing rejasi, shaxsiy kabinet, ko'p tarmoqli jamoa statistikasi, kassa/hamyonlar integratsiyasi, **Telegram Mini App (Web App)** hamda **Render.com** veb-boshqaruv panelini taqdim etadi.

---

## 🌟 Asosiy Xususiyatlar:

1. 🔒 **Qat'iy Referal Ro'yxatdan O'tish Tizimi:**
   - Yangi a'zo botga shunchaki `/start` bossa, bot ro'yxatdan o'tkazmaydi va referal havola talab qiladi.
   - Referal havola orqali kirilganda (`/start ref_USERID`), Taklif qiluvchi (Kurator) va foydalanuvchining ma'lumotlari kartochka shaklida ko'rsatiladi va `✅ RO'YXATDAN O'TISH` tugmasi chiqadi.

2. 👑 **Asosiy Menyu va Dizayn:**
   - Rasmiy oltin shior va banner rasmi.
   - Sarlavha:
     `«BUYUK HAYOTGA YO'L» — ham faol, ham passiv daromad olish uchun yuqori salohiyatga ega qulay dastur. Ko'plab daromad manbalari va moliyaviy vositalar kapitalingizni ko'paytirishga yordam beradi.`
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
   - **Bosh sahifa:** Foydalanuvchi real ma'lumotlari, umumiy daromad (0 so'm), jamoa a'zolari, joriy daraja (1-5), sana, shaxsiy referal havola va QR kod.
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
DB_NAME=buyukhayot.db
```

### 3. Botni ishga tushirish:

```bash
python main.py
```
