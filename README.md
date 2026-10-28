# ویدئوها — Nimania Videos

آرشیو مستقل ویدئوهای چهره‌های پندار در **https://nimania.github.io/videos/**

## معماری
- مخزن و استقرار مستقل از `nimania/pendar`.
- صفحهٔ یکتای هر ویدئو: `/videos/video/{youtube-id}/`، همراه با پخش از یوتیوب، مشخصات و لینک به چهره‌ها و «جان کلام».
- گردآوری دوره‌ای، دادهٔ عمومی `https://pendar.io/data/figures.json` را در GitHub Actions می‌خواند و خروجی خودکفای `site/data/videos.json` می‌سازد. مرورگر از پندار درخواست زنده نمی‌فرستد.
- نبود دادهٔ سالم باعث شکست انتشار می‌شود تا آرشیو قبلی با خروجی خالی جایگزین نشود.
- پیوندهای محتوایی با پندار، جان کلام، بادبادک و پیشخوان فقط بر اساس شناسه و رابطهٔ تأییدشده هستند.
- ویدئوها بازنشر نمی‌شوند؛ مالکیت نزد ناشر اصلی است.

## استقرار
1. Settings → Pages → Build and deployment → **GitHub Actions**
2. اجرای **Publish Nimania Videos** یا push جدید به main
3. بررسی https://nimania.github.io/videos/ و صفحات ویدئو
4. ادغام شاخهٔ پیشنهادی پندار `extract-independent-videos-20261028` پس از تأیید انتشار.

## توسعه
`python3 scripts/build_catalog.py --out site`

`python3 -m unittest discover -s tests -v`

`data/relations.json` پیوندهای دستیِ تأییدشده به دیگر سایت‌ها را نگه می‌دارد.