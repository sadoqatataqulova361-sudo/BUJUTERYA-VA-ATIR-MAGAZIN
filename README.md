# Zargarlik & Atir do'koni — Telegram bot + Admin panel

Bu loyiha ikki qismdan iborat:

1. **Telegram bot** (`bot/`) — mijozlar katalogni ko'radi, savatchaga mahsulot qo'shadi, buyurtma beradi, buyurtmasini kuzatadi yoki bekor qiladi.
2. **Admin panel** (`admin/`) — brauzerda ochiladigan veb-sayt: mahsulot/kategoriya qo'shish, narx va chegirma belgilash, rasm yuklash, buyurtmalar holatini boshqarish.

Ikkalasi ham bitta ma'lumotlar bazasidan (`shop.db`, SQLite) foydalanadi — admin panelda qo'shgan mahsulotingiz zudlik bilan botda ko'rinadi.

---

## 1. O'rnatish

```bash
cd shop_bot
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Sozlash

`.env.example` faylidan nusxa ko'chiring:

```bash
cp .env.example .env
```

`.env` faylini oching va to'ldiring:

- `BOT_TOKEN` — Telegram'da @BotFather ga yozib, `/newbot` orqali oling.
- `ADMIN_USERNAME` / `ADMIN_PASSWORD` — admin panelga kirish uchun login/parol (o'zingiz xohlagancha qo'ying).
- `SHOP_NAME` — botda ko'rinadigan do'kon nomi.

## 3. Ishga tushirish

Ikkita alohida terminal oynasida:

**Admin panel:**
```bash
cd shop_bot
python admin/app.py
```
Brauzerda oching: http://localhost:5000 — `.env`dagi login/parol bilan kiring.

**Bot:**
```bash
cd shop_bot
python bot/main.py
```
Telegram'da botingizga `/start` yozing.

## 4. Ishlatish tartibi

1. Admin panelga kiring → **Kategoriyalar** → bo'limlar qo'shing (masalan: Uzuklar, Sirg'alar, Atirlar).
2. **Mahsulotlar** → **+ Yangi mahsulot** → rasm yuklang, narx va (agar bo'lsa) chegirmadan oldingi narxni kiriting.
3. Botga o'ting, `/start` bosing — mahsulotlar shu yerda ko'rinadi.
4. Mijoz sifatida sinab ko'ring: savatchaga qo'shing, `/cart`, buyurtma bering.
5. Admin panelda **Buyurtmalar** bo'limida yangi buyurtmani ko'rasiz — holatini "tasdiqlandi" / "yetkazildi" ga o'zgartirishingiz mumkin.

## 5. Boshqa mijozga moslash (white-label)

Yangi do'kon uchun:
1. Loyihani nusxalang.
2. `.env` dagi `SHOP_NAME`, `ADMIN_USERNAME/PASSWORD`ni o'zgartiring.
3. Yangi `BOT_TOKEN` oling (@BotFather orqali yangi bot yarating — nomi, rasmi, username'ini xohlagancha qo'yasiz).
4. `admin/static/style.css` dagi `--gold`, `--rose` ranglarini mijozning brend ranglariga moslab o'zgartirsangiz bo'ldi.
5. Kerak bo'lsa `shop.db` faylini o'chirib, yangidan boshlang (bo'sh baza bilan).

## 6. Texnik eslatmalar

- **To'lov (Click/Payme)**: hozirgi versiyada buyurtma "naqd/yetkazib berilganda to'lov" tarzida ishlaydi. Click yoki Payme integratsiyasini keyingi bosqichda `bot/handlers/order_flow.py` ichidagi checkout jarayoniga qo'shish mumkin — ular uchun tasdiqlangan merchant hisobi kerak bo'ladi.
- **Ma'lumotlar bazasi**: demo uchun SQLite ishlatilgan. Foydalanuvchilar ko'payib, yuklama oshsa, PostgreSQL'ga o'tish tavsiya etiladi (bitta qatorni — `DB_PATH` ni — o'zgartirish yetarli, chunki SQLAlchemy ishlatilgan).
- **Savatcha**: hozir xotirada (RAM) saqlanadi — bot qayta ishga tushsa, foydalanuvchilarning savatchasi tozalanadi. Buyurtma berish tugagach, buyurtma bazaga yoziladi va yo'qolmaydi.
