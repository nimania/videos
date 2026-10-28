# ویدئوها — Nimania Videos

**https://nimania.github.io/videos/** · [فهرست رسانه‌ها](https://nimania.github.io/videos/media/)

این مخزن مالک مستقل کشف و آرشیو کردن ویدئوهاست. پندار مصرف‌کنندهٔ خروجیِ آماده است و دیگر گردآورندهٔ یوتیوب برای آرشیو ویدئو اجرا نمی‌کند.

## معماری بعد از جداسازی کامل

- **منابع:** `data/sources.json`، فهرست مستقل ۴۹ منبع و ۸ رسانهٔ میزبان مشترک؛ قابل گسترش بدون تغییر مخزن پندار.
- **گردآوری:** `scripts/collect_videos.py`، خواندن خوراک RSS/Atom یوتیوب در GitHub Actions با استفاده از `urllib` و `ElementTree`، بدون نیاز به سرویس پندار یا کلید API.
- **حافظهٔ پایدار:** آخرین `https://nimania.github.io/videos/data/videos.json` مبنای افزایشی آرشیو است. قطع یک کانال به حذف ویدئوهای قبلی منجر نمی‌شود؛ اگر مبنا ناقص/خالی باشد انتشار متوقف می‌شود.
- **انتشار:** `scripts/build_catalog.py --archive ... --out site` برای ساخت صفحات HTML، JSON، رسانه‌ها، نقشهٔ سایت و دادهٔ سازگار با پندار.
- **خروجی برای پندار:** `https://nimania.github.io/videos/data/pendar-youtube-videos.json`؛ هر ردیف دارای `id`، `handle`، عنوان، تاریخ، URL منبع و شناسهٔ رسانه/شخص است. پندار این خروجی را **مصرف** می‌کند و آخرین نسخهٔ سالم را در cache نگه می‌دارد.
- **اتصال محتوایی:** چهره‌ها و جان کلام در پندار، ناشرها و ویدئوها در این سایت؛ لینک‌ها بر مبنای شناسه و نقش ثبت‌شده.
- **مالکیت:** ویدئوها از منبع رسمی یوتیوب پخش می‌شوند؛ نسخهٔ محلی از فایل ویدئویی نگهداری نمی‌شود.

## شروع کار و آزمون

```bash
python3 -m unittest discover -s tests -v
python3 scripts/collect_videos.py --previous https://nimania.github.io/videos/data/videos.json --out /tmp/nimania-videos-owned.json
python3 scripts/build_catalog.py --archive /tmp/nimania-videos-owned.json --out site
```

GitHub Actions با push به main و نیز به صورت زمان‌بندی‌شده اجرا می‌شود؛ GitHub Pages باید روی **GitHub Actions** باشد. تاریخچهٔ موجود قبل از مهاجرت حفظ شده است.

نکته: `build_catalog.build()` فقط برای آزمون‌های قدیمی با fixture محلی در کد باقی مانده؛ **مسیر تولید** صرفاً `build_owned()` و آرشیو مستقل است. برنامهٔ اصلی هیچ داده‌ای از `pendar.io/data/figures.json` دریافت نمی‌کند.

## اعتبارسنجی

- رسانه‌های `source-...` از اشخاص جدا هستند.
- فقط نقشِ سردبیری تأییدشده در `data/credits.json` به‌عنوان «میزبان» یا «مهمان» ثبت می‌شود.
- `data/relations.json` برای لینک‌های دستیِ تأییدشده است؛ از عنوان ویدئو برای ادعای محتوایی یا ایجاد نقش استفاده نمی‌شود.

[قرارداد اتصال به پندار](docs/pendar-integration.md)
