# Laporan Singkat Implementasi Real-time rPPG

### 1. Pustaka (Library) yang Digunakan

Berikut adalah beberapa library yang saya gunakan untuk membuat program ini:

- **OpenCV (`cv2`):** Berfungsi sebagai antarmuka utama untuk mengakses webcam, memanipulasi _frame_ gambar, dan menampilkan visualisasi (teks dan grafik) ke layar pengguna.
- **MediaPipe (`mediapipe`):** Digunakan untuk deteksi wajah dan penentuan titik koordinat wajah (_face landmarks_) secara presisi.
- **NumPy (`numpy`):** Digunakan untuk operasi matematika numerik, seperti perhitungan rata-rata kanal warna, manipulasi _array_, dan perhitungan FFT (Fast Fourier Transform).
- **SciPy (`scipy.signal`):** Berfungsi khusus untuk pemrosesan sinyal digital, yaitu menyediakan fitur _detrending_ (menghapus tren linear) dan penerapan _Bandpass Filter_ (Butterworth) untuk memisahkan sinyal detak jantung dari _noise_.

### 2. Penjelasan Metode dan Program

Program berjalan secara kontinu (real-time). Pertama, webcam menangkap video dan MediaPipe mendeteksi area wajah untuk menentukan _Region of Interest_ (ROI) pada bagian dahi. Program kemudian mengekstraksi rata-rata intensitas warna **Hijau (Green Channel)** dari area tersebut karena kanal ini memiliki respons terkuat terhadap perubahan aliran darah.
Data sinyal mentah tersebut dikumpulkan dalam sebuah _sliding window_ (buffer) agar pembaruan data terjadi terus-menerus tanpa memotong video. Sinyal dalam buffer kemudian diproses melalui tiga tahap: **Detrending** untuk menghilangkan perubahan pencahayaan lambat, **Bandpass Filter** (0.7–4.0 Hz) untuk mengambil rentang frekuensi detak jantung manusia yang wajar, dan terakhir **FFT** untuk mencari frekuensi dominan yang dikonversi menjadi nilai BPM (_Beats Per Minute_).

### 3. Aspek Pembeda dengan Demo di Kelas

Aspek pembeda dalam implementasi ini adalah **Visualisasi Grafik Sinyal Real-time**, kemudian juga menampilkan **Grafik Gelombang Sinyal** yang ditampilkan pada layar pojok kiri bawah. Selanjutnya memilih _area dahi tengah_ sebagai perhitungan **rata-rata ROI**. Selain itu, penggunaan **MediaPipe Face Mesh** memberikan stabilitas ROI yang jauh lebih baik dibandingkan metode deteksi wajah kotak biasa.
