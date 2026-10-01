# GIF Loop Toggle

Figma plugin untuk mengontrol apakah sebuah GIF loop terus-menerus atau main
satu kali. Kerjanya dengan menambah/menghapus block `NETSCAPE2.0`
application extension di dalam file GIF — block itu yang menentukan apakah
decoder (browser, Figma, dll) mengulang animasinya atau berhenti di frame
terakhir.

## Struktur

- `manifest.json` — konfigurasi plugin.
- `code.js` — logic yang jalan di sandbox Figma (parsing/rewrite GIF, baca/tulis fill layer).
- `ui.html` — UI plugin: toggle arah (Stop loop / Loop forever) + dua tab ("From selection" dan "Upload GIF").
- `assets/` — icon 128×128 dan cover 1920×1080 untuk listing Figma Community, plus script generator-nya (`generate_assets.py`).

## Cara pakai

1. Pilih arah di toggle atas: **Stop loop (play once)** atau **Loop forever**.
2. **From selection** — pilih satu/lebih layer yang fill-nya GIF, klik tombol
   convert. Plugin cari semua fill bertipe GIF di dalam selection (termasuk
   di dalam frame/group) dan terapkan arah yang dipilih.
3. **Upload GIF** — upload file `.gif` langsung, lalu pilih mau di-download
   sebagai file baru atau di-apply sebagai fill ke layer yang sedang dipilih.

## Testing lokal (sebelum publish)

1. Buka Figma desktop app.
2. Menu **Plugins → Development → Import plugin from manifest…**
3. Pilih file `manifest.json` di folder ini.
4. Plugin muncul di **Plugins → Development → GIF Loop Toggle**, jalankan dan
   coba kedua arah di file test.

## Listing Figma Community

- **Name:** GIF Loop Toggle
- **Tagline:** Turn GIF looping on or off.
- **Category:** Design tools → (submenu sejenis Plugins/Productivity)
- **Sub-category (Editing & effects list):** Editing & effects
- **Tags:** gif, loop, animation, play once, gif editor
- **Icon:** `assets/icon-128.png`
- **Cover:** `assets/cover-1920x1080.png`
- **Plugin ID:** `1687042479450436538` (sudah di-set di `manifest.json`)

### Description (markdown)

```markdown
**GIF Loop Toggle** lets you control whether a GIF repeats forever or plays
exactly once. Switch either direction right inside Figma.

- **Stop loop** — remove the loop so a GIF plays once and stops on its last
  frame. Great for onboarding illustrations, success states, or any animated
  moment that should land once instead of repeating endlessly.
- **Loop forever** — add infinite looping back to a GIF that currently plays
  once.

### Two ways to use it

**From selection**
Select one or more layers whose fill is a GIF — even inside a frame or
group — pick a direction, and hit convert. The plugin finds every GIF fill
in your selection and rewrites it.

**Upload GIF**
Don't have it in Figma yet? Upload a `.gif` file directly. Choose to:
- Download the converted file, or
- Apply it straight to your selected layer(s) as a fill

### How it works

Looping is controlled by a small block inside the GIF file (the
`NETSCAPE2.0` extension). This plugin rewrites the GIF byte-for-byte to add
or remove that block — no re-encoding, no quality loss, no frame changes.

### Good to know

- Only works on real GIF files (`GIF87a`/`GIF89a`) — not APNG or video.
- If a GIF already matches the direction you picked, the plugin tells you
  and leaves it untouched.
- "Apply as fill" replaces the layer's existing fill(s) with the converted
  GIF.
```

## Sebelum publish ke Figma Community

1. Pastikan nama di Figma (**Plugins → Development → Manage plugin**) sudah
   diganti jadi **GIF Loop Toggle**, sesuai `manifest.json`.
2. Upload `assets/icon-128.png` dan `assets/cover-1920x1080.png` di form
   publish.
3. Pakai tagline, deskripsi, category, dan tags di atas (atau sesuaikan).
4. Jalankan **Plugins → Development → GIF Loop Toggle → Publish new
   release**, ikuti proses review Figma.

## Batasan yang perlu diketahui

- Hanya menyentuh file yang formatnya GIF asli (`GIF87a`/`GIF89a`). File PNG
  animasi (APNG) atau video tidak diproses.
- Kalau GIF sudah sesuai arah yang dipilih (misal sudah play-once lalu
  kamu pilih "Stop loop"), plugin akan bilang "already..." tanpa membuat
  image baru.
- Mode "Apply as fill" akan **menimpa seluruh fill** layer yang dipilih
  dengan GIF hasil convert (bukan menambah fill baru).
