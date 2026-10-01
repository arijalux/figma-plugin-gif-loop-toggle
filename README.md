# GIF Loop Toggle

Figma plugin untuk mengontrol apakah sebuah GIF loop terus-menerus atau main
satu kali — langsung dari dalam Figma, tanpa software/convert eksternal.

![icon](assets/icon-128.png)

## Fitur

- **Stop loop** — GIF yang looping diubah supaya main sekali lalu berhenti
  di frame terakhir.
- **Loop forever** — GIF yang main sekali diubah supaya loop terus-menerus.
- Bisa diterapkan ke **layer yang sudah ada di Figma** (cari semua fill GIF
  di dalam selection, termasuk di dalam frame/group), atau ke **file GIF
  yang di-upload** langsung dari komputer.
- Hasil convert bisa langsung **diterapkan sebagai fill** ke layer terpilih,
  atau **di-download** sebagai file `.gif` baru.
- Tidak ada backend, tidak ada network request, tidak ada autentikasi, tidak
  ada data yang disimpan — semua proses murni lokal di sandbox Figma.

## Cara pakai

1. Install plugin dari Figma Community (atau import manual, lihat
   [Development](#development) di bawah).
2. Pilih arah di toggle atas: **Stop loop (play once)** atau **Loop
   forever**.
3. **Tab "From selection"** — pilih satu/lebih layer yang fill-nya GIF,
   klik tombol convert.
4. **Tab "Upload GIF"** — upload file `.gif`, lalu pilih mau di-download
   atau di-apply ke layer yang sedang dipilih.

## Cara kerja (teknis)

Perilaku loop pada GIF dikontrol oleh satu block kecil di dalam file-nya:
**`NETSCAPE2.0` application extension**. Kalau block ini ada (dengan loop
count 0), decoder (browser, Figma, image viewer, dll) akan mengulang
animasinya selamanya. Kalau block ini tidak ada, decoder akan memutar
animasinya sekali lalu berhenti — itu perilaku default semua decoder GIF.

Plugin ini membaca bytes GIF (lewat `figma.getImageByHash(...).getBytesAsync()`
untuk fill yang sudah ada di Figma, atau lewat file upload), lalu:

- **Stop loop** → parse struktur GIF block-per-block dan buang block
  `NETSCAPE2.0`-nya.
- **Loop forever** → cek dulu apakah block itu sudah ada; kalau belum,
  sisipkan block baru (loop count 0 = infinite) tepat setelah Logical
  Screen Descriptor (+ Global Color Table kalau ada), posisi konvensional
  tempat encoder biasa menaruhnya.

Tidak ada re-encode, tidak ada perubahan frame/kualitas gambar — murni
rewrite byte pada metadata loop-nya saja. Hasilnya dibuat jadi image baru
lewat `figma.createImage(...)` lalu dipasang sebagai fill lewat
`node.fills`.

## Privasi & data

- **Tidak ada backend** — semua logic jalan di sandbox plugin Figma
  (`code.js`) dan di UI iframe-nya (`ui.html`).
- **Tidak ada network request** — `manifest.json` di-set
  `networkAccess.allowedDomains: ["none"]`.
- **Tidak ada autentikasi** apa pun.
- **Tidak menyimpan data** — bytes GIF diproses in-memory saja, tidak
  pernah ditulis ke `figma.clientStorage`, `localStorage`, atau
  `setPluginData`.

## Development

Plugin ini plain JavaScript, tanpa build step/bundler.

```
figma-plugin-gif-play-once/
├── manifest.json          # konfigurasi plugin (id, main, ui, permissions)
├── code.js                 # logic di sandbox Figma: parsing GIF, baca/tulis fill
├── ui.html                  # UI plugin (toggle arah + dua tab mode)
├── assets/
│   ├── icon-128.png          # icon listing Figma Community
│   ├── cover-1920x1080.png    # cover/thumbnail listing
│   └── generate_assets.py      # script Python (Pillow) buat generate ulang icon/cover
└── README.md
```

### Jalankan secara lokal

1. Buka Figma desktop app.
2. **Plugins → Development → Import plugin from manifest…**
3. Pilih `manifest.json` di repo ini.
4. Plugin muncul di **Plugins → Development → GIF Loop Toggle**.

Setelah mengubah `code.js`/`ui.html`, klik kanan plugin di menu Development
lalu **Reload plugin** kalau perubahan tidak otomatis ter-refresh.

### Generate ulang icon/cover

```bash
cd assets
python3 generate_assets.py
```

Butuh `Pillow` dan `numpy` (`pip install pillow numpy`).

## Publishing checklist (Figma Community)

- **Name:** GIF Loop Toggle
- **Tagline:** Turn GIF looping on or off.
- **Category:** Design tools
- **Sub-category:** Editing & effects
- **Tags:** gif, loop, animation, play once, gif editor
- **Icon:** `assets/icon-128.png`
- **Cover:** `assets/cover-1920x1080.png`
- **Plugin ID:** `1687042479450436538` (sudah di-set di `manifest.json`)

<details>
<summary>Description (markdown, siap copy-paste)</summary>

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

</details>

Sebelum publish:

1. Pastikan nama plugin di **Plugins → Development → Manage plugin** sudah
   "GIF Loop Toggle", sesuai `manifest.json`.
2. Upload `assets/icon-128.png` dan `assets/cover-1920x1080.png`.
3. Isi tagline/deskripsi/category/tags sesuai di atas.
4. **Plugins → Development → GIF Loop Toggle → Publish new release**,
   ikuti proses review Figma.

## Batasan

- Hanya memproses file GIF asli (`GIF87a`/`GIF89a`) — APNG dan video tidak
  didukung.
- Kalau GIF sudah sesuai arah yang dipilih, plugin menampilkan status
  "already..." tanpa membuat image baru (menghindari duplikasi image yang
  tidak perlu).
- Mode "Apply as fill" **menimpa seluruh fill** layer yang dipilih dengan
  GIF hasil convert, bukan menambah fill baru.

## License

Belum ditentukan — tambahkan file `LICENSE` kalau repo ini mau dibuat
open-source (mis. MIT) sebelum dipublikasikan secara publik.
