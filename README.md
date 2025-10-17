### Matakuliah Sistem Teknologi Multimedia (IF25-40305)

---

### Repositori ini berisi kumpulan file dan Notebook Jupyter dari latihan ataupun tugas matakuliah Sistem Teknologi Multimedia.

#### Struktur Repositori

```
Tugas-Multimedia/
├─ audio/
├─ Worksheet-1/
├─ Worksheet-2/
├─ 122140029_Exercise_Audio.ipynb
├─ 122140029_Exercise_Audio.pdf
└─ README.md
```

Keterangan:

- Folder `audio/` berisi dataset audio untuk kebutuhan tugas **Exercise_Audio**.
- **Worksheet-x** berisi file hasil pengerjaan tugas

---

### Cara Menjalankan Kode

1. Lakukan cloning repositori terlebih dahulu

```bash
git clone https://github.com/TawakkalM/Tugas-Multimedia.git
```

2. Buka Jupyter Notebook dengan menjalankan perintah di terminal

```bash
jupyter notebook
```

3. Pilih file .ipynb yang diinginkan, kemudian aktifkan environment uv

```bash
*Untuk Windows
.venv\Scripts\activate

*Untuk Mac/Linux
source .venv/bin/activate
```

3. Install library yang diperlukan, sebagai contoh:

```bash
pip install numpy matplotlib scipy librosa jupyterlab
```
