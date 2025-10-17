# test_multimedia.py
print("="*40)
print("Uji Instalasi Library Multimedia")
print("="*40)

libraries = {
    "librosa": "librosa",
    "soundfile": "soundfile",
    "scipy": "scipy",
    "opencv-python": "cv2",
    "pillow": "PIL",
    "scikit-image": "skimage",
    "matplotlib": "matplotlib",
    "moviepy": "moviepy",
    "numpy": "numpy",
    "pandas": "pandas",
    "jupyter": "jupyter"
}

for name, module in libraries.items():
    try:
        lib = __import__(module)
        version = getattr(lib, "__version__", "No version info")
        print(f"{name} terinstall (versi: {version})")
    except Exception as e:
        print(f"{name} error: {e}")

print("="*40)
print("Pengujian selesai")
print("="*40)
