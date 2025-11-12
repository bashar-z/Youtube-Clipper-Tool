# 🎬 YouTube Clipper

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/bashar-z/Youtube-Clipper-Tool/blob/main/Clipper_Project.ipynb)

Google Colab-based tool for quickly clipping and downloading specific segments from YouTube videos.  
Simple interactive interface with start/end time pickers, ideal for stream editors and creators working with YouTube VODs.

---

## 📦 What It Can Do
- Download and clip any YouTube video segment (for videos you have rights to).
- Keep full video + audio quality.
- Interactive UI with arrow controls for hours, minutes, and seconds.
- Automatic MP4 download directly in Colab.
- 100 % browser-based — no setup or installation needed.

---

## 🖥 Interface
**Platform:** Google Colab  
**UI:** Interactive widgets (`ipywidgets`)  
**Backend:** `yt-dlp` + `ffmpeg`  
**Output Format:** MP4  
**Environment:** Runs entirely in the browser

---

## 🚀 Quick Start
1. Click the Colab badge above to launch the notebook.  
2. Paste the YouTube video link.  
3. Adjust the start and end times using the arrow pickers.  
4. Press **🎬 Clip & Download**.  
5. Wait until the clip finishes — it will automatically download when ready.

---

## ⚙️ Requirements
If you prefer running locally instead of Colab:

```
pip install yt-dlp ipywidgets
sudo apt install ffmpeg
```

---

## 🧩 How It Works
1. `yt-dlp` fetches the best available video + audio streams.  
2. The tool merges them into a single MP4 file.  
3. `ffmpeg` trims only the selected section without re-encoding.  
4. The final clip downloads automatically.

---

## 📚 Example Use Cases
- Clipping highlights from long YouTube VODs.  
- Creating short viral segments for social media.  
- Extracting reference sections from educational videos.  
- Quick review and sharing of specific time-frames.

---

## ⚠️ Legal Notice
This tool is intended for **personal and educational use only.**  
Do **not** use it to download or redistribute copyrighted content.  
Always respect [YouTube’s Terms of Service](https://www.youtube.com/static?template=terms).

---

## 🛠 Technical Details
| Component | Purpose |
|------------|----------|
| **yt-dlp** | Handles video and audio stream extraction |
| **ffmpeg** | Performs precise, lossless trimming |
| **ipywidgets** | Provides time selection and UI controls |
| **Colab Python 3 Runtime** | Browser-based execution environment |

---

## 🧾 License
MIT License © 2025 Bashar Zaher  
This project is not affiliated with or endorsed by YouTube or Google LLC.
