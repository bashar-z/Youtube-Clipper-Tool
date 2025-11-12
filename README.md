# 🎬 YouTube Clipper

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://youtube-clipper.streamlit.app)
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/bashar-z/Youtube-Clipper-Tool/blob/main/Clipper_Project.ipynb)

Simple, browser-based tool for clipping and downloading specific segments from YouTube videos.  
Clean interface with timestamp controls — ideal for editors, streamers, and creators working with YouTube VODs.

Choose how you want to run it:
- **Streamlit App (Recommended):** No setup, works directly in your browser.
- **Google Colab:** For users who prefer a notebook environment.

---

## 📦 What It Can Do
- Download and clip any YouTube video segment.
- Keep full video + audio quality.
- Interactive UI with arrow controls for hours, minutes, and seconds.
- Automatic MP4 download directly in Colab.
- 100 % browser-based — no setup or installation needed.

---

## 🖥 Interface
**Platform:** Streamlit (and optional Colab)  
**UI:** Interactive time controls  
**Backend:** `yt-dlp` + `ffmpeg`  
**Output Format:** MP4  
**Environment:** Fully browser-based, no local install needed

---

## 🚀 Quick Start
1. Click **Open in Streamlit** above to launch the web app.  
2. Paste a YouTube video link.  
3. Adjust the start and end times.  
4. Click **🎬 Clip & Download**.  
5. Wait a few seconds — your MP4 will be ready to download.

---

## ⚙️ Requirements
If you prefer running locally instead of Streamlit:

```bash
pip install streamlit yt-dlp ffmpeg-python
sudo apt install ffmpeg
```
Then run:
```
streamlit run app.py
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
- Extracting reference sections from videos.  
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
| **Streamlit** | Provides the interactive browser interface |
| **yt-dlp** | Handles video and audio extraction |
| **ffmpeg** | Performs precise trimming without re-encoding |
| **Python 3** | Core runtime environment |

---

## 🧾 License
MIT License © 2025 Bashar Zaher  
This project is not affiliated with or endorsed by YouTube or Google LLC.
