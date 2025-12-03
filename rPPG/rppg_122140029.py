import cv2
import numpy as np
import mediapipe as mp
import time
from scipy import signal
from collections import deque

class RPPG_Realtime:
    def __init__(self, buffer_size=300, fs=30):
        """
        Inisialisasi parameter rPPG.
        
        Args:
            buffer_size (int): Panjang sliding window (jumlah frame). 
            fs (int): Estimasi frame rate kamera (default 30 fps).
        """
        # --- Konfigurasi Pipeline ---
        self.buffer_size = buffer_size
        self.fs = fs
        
        # Buffer untuk menyimpan rata-rata intensitas kanal hijau
        self.signal_buffer = deque(maxlen=buffer_size)
        self.times = deque(maxlen=buffer_size)
        
        # Buffer untuk grafik visualisasi
        self.filtered_buffer = deque(maxlen=buffer_size)
        
        # --- Deteksi Wajah (MediaPipe) ---
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Variabel BPM
        self.bpm = 0.0
        self.last_bpm_update = 0
        self.bpm_update_interval = 0.5 # Update BPM setiap 0.5 detik agar stabil

    def get_roi_average(self, frame, landmarks):
        """
        Ekstraksi Sinyal: Mengambil rata-rata kanal Hijau dari ROI wajah.
        Menggunakan area dahi/pipi yang stabil.
        """
        h, w, _ = frame.shape
        
        # Indeks landmark untuk pipi (kanan dan kiri) dan dahi
        # Dipilih area kulit yang minim ekspresi
        roi_indices = [33, 133, 362, 263, 4, 152] 
        
        # Ambil koordinat bounding box sederhana dari landmarks
        roi_points = []
        for idx in roi_indices:
            pt = landmarks.landmark[idx]
            roi_points.append([int(pt.x * w), int(pt.y * h)])
            
        roi_points = np.array(roi_points)
        
        # Masking area wajah (ambil bounding box dahi)
        # ambil rata-rata area dahi tengah:
        # Landmark 10 adalah tengah dahi atas.
        forehead_x = int(landmarks.landmark[10].x * w)
        forehead_y = int(landmarks.landmark[10].y * h)
        
        # Buat ROI kotak kecil di dahi (20x20 pixel)
        y1, y2 = max(0, forehead_y + 10), min(h, forehead_y + 40)
        x1, x2 = max(0, forehead_x - 15), min(w, forehead_x + 15)
        
        roi = frame[y1:y2, x1:x2]
        
        if roi.size == 0:
            return 0
            
        # Fokus pada kanal Hijau (Green) karena penyerapan hemoglobin kuat
        g_channel = roi[:, :, 1]
        return np.mean(g_channel)

    def process_signal(self):
        """
        Pemrosesan Sinyal: Detrending, Filtering, dan FFT. 
        """
        if len(self.signal_buffer) < self.buffer_size:
            return 0.0, []

        # Konversi buffer ke numpy array
        raw_signal = np.array(self.signal_buffer)
        
        # 1. Detrending (Mengurangi pergeseran baseline)
        detrended = signal.detrend(raw_signal)
        
        # 2. Bandpass Filter (0.7 Hz - 4.0 Hz)
        # Rentang: 42 BPM sampai 240 BPM
        b, a = signal.butter(3, [0.7 / (0.5 * self.fs), 4.0 / (0.5 * self.fs)], btype='bandpass')
        filtered = signal.filtfilt(b, a, detrended)
        
        # Simpan untuk visualisasi
        self.filtered_buffer.clear()
        self.filtered_buffer.extend(filtered)

        # 3. Estimasi BPM dengan FFT
        # Hanning window untuk mengurangi kebocoran spektral
        window = np.hanning(len(filtered))
        fft_spec = np.fft.rfft(filtered * window)
        fft_mag = np.abs(fft_spec)
        freqs = np.fft.rfftfreq(len(filtered), d=1.0/self.fs)
        
        # Cari frekuensi dominan dalam rentang valid (0.7 - 4.0 Hz)
        valid_idx = np.where((freqs >= 0.7) & (freqs <= 4.0))[0]
        if len(valid_idx) > 0:
            peak_idx = valid_idx[np.argmax(fft_mag[valid_idx])]
            bpm = freqs[peak_idx] * 60.0
            return bpm, filtered
        
        return 0.0, filtered

    def draw_graph(self, frame, signal_data):
        """
        Improvement: Visualisasi grafik sinyal real-time overlay pada frame.
        """
        if len(signal_data) < 2:
            return frame
            
        h, w, _ = frame.shape
        
        # Parameter area grafik (di pojok kiri bawah)
        graph_w = 250
        graph_h = 150
        margin = 20
        start_x = margin
        start_y = h - margin
        
        # Gambar background semi-transparan
        overlay = frame.copy()
        cv2.rectangle(overlay, (start_x, start_y - graph_h), (start_x + graph_w, start_y), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
        
        # Normalisasi sinyal agar pas di kotak grafik
        sig = np.array(signal_data)
        if np.max(sig) == np.min(sig):
            return frame
            
        # Ambil 100 data terakhir agar grafik bergerak cepat
        plot_data = sig[-100:] 
        
        # Normalize ke range 0-1
        norm_sig = (plot_data - np.min(plot_data)) / (np.max(plot_data) - np.min(plot_data) + 1e-6)
        
        # Gambar garis
        points = []
        step_x = graph_w / len(norm_sig)
        
        for i, val in enumerate(norm_sig):
            px = int(start_x + i * step_x)
            py = int(start_y - (val * graph_h))
            points.append((px, py))
            
        # Gambar polylines
        if len(points) > 1:
            cv2.polylines(frame, [np.array(points)], False, (0, 255, 0), 2)
            
        # Label
        cv2.putText(frame, "Filtered Signal", (start_x, start_y - graph_h - 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        return frame

    def run(self):
        """Loop utama untuk menangkap video dan memproses secara real-time."""
        # Initialize webcam
        cap = cv2.VideoCapture(0) # Ambil webcam default laptop
        cap.set(3, 1280) # Lebar
        cap.set(4, 720) # Tinggi
        
        if not cap.isOpened():
            print("Error: Tidak dapat membuka webcam.")
            return

        print("Mulai rPPG Real-time... Tekan 'q' untuk keluar.")
        
        prev_time = time.time()
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1) # Mirror 
                
            curr_time = time.time()
            dt = curr_time - prev_time
            prev_time = curr_time
            
            # Update estimasi FPS secara dinamis (simple moving average)
            current_fps = 1.0 / dt if dt > 0 else 30.0
            # Smoothing FPS sedikit agar stabil
            self.fs = 0.9 * self.fs + 0.1 * current_fps 

            # Deteksi Wajah
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_frame)
            
            avg_green = 0
            
            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    # 1. Ekstraksi Sinyal
                    avg_green = self.get_roi_average(frame, face_landmarks)
                    
                    # Gambar kotak di dahi (indikator ROI)
                    h, w, _ = frame.shape
                    fx = int(face_landmarks.landmark[10].x * w)
                    fy = int(face_landmarks.landmark[10].y * h)
                    cv2.rectangle(frame, (fx-15, fy+10), (fx+15, fy+40), (255, 0, 0), 2)
            
            # Masukkan data ke buffer (Sliding Window)
            self.signal_buffer.append(avg_green)
            self.times.append(curr_time)
            
            # Proses BPM jika buffer cukup penuh
            if len(self.signal_buffer) > self.buffer_size // 2:
                # Update BPM setiap interval tertentu
                if (curr_time - self.last_bpm_update) > self.bpm_update_interval:
                    new_bpm, filtered_sig = self.process_signal()
                    if new_bpm > 40 and new_bpm < 200: # Filter nilai tidak masuk akal
                        self.bpm = new_bpm
                    self.last_bpm_update = curr_time
            
            # --- Visualisasi & Overlay ---
            # Tampilkan BPM
            text_bpm = f"BPM: {self.bpm:.1f}"
            
            # Warna teks (Hijau jika stabil, Merah jika 0/awal)
            color = (0, 255, 0) if self.bpm > 0 else (0, 0, 255)
            
            # Background untuk teks BPM
            cv2.rectangle(frame, (10, 10), (200, 60), (0,0,0), -1)
            cv2.putText(frame, text_bpm, (20, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            
            # Visualisasi Grafik Sinyal (Improvement)
            if len(self.filtered_buffer) > 0:
                frame = self.draw_graph(frame, self.filtered_buffer)
            else:
                cv2.putText(frame, "Mengumpulkan data...", (20, 150), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            cv2.imshow('Tugas rPPG Real-time', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    # Buffer 150 frame (sekitar 5 detik di 30 fps) untuk responsif
    app = RPPG_Realtime(buffer_size=150)
    app.run()