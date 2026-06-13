# YouTube Clipper Tool

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://youtube-clipper.streamlit.app)

A Streamlit app for clipping YouTube videos you own or have permission to use. Paste a YouTube URL, choose start and end timestamps, then export the selected range as MP4 or MP3.

## Features

- MP4 video clipping and MP3 audio extraction.
- Timestamp input using `SS`, `MM:SS`, or `HH:MM:SS`.
- Video metadata preview before clipping.
- Source quality selector for smaller/faster or higher-quality clips.
- Bundled FFmpeg support through `imageio-ffmpeg`, so local users do not need a separate FFmpeg install.
- Optional `cookies.txt` upload for videos your browser account is allowed to view.
- Clearer error messages for common `yt-dlp`, network, and FFmpeg failures.

## Run Locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL Streamlit prints, usually:

```text
http://localhost:8501
```

`localhost` means the app is running on your own computer. Other people cannot use your local copy unless you deploy it somewhere.

## Deploy

This project is ready for Streamlit Community Cloud:

1. Push this repository to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io).
3. Choose this repository.
4. Set the main file path to `app.py`.
5. Deploy.

## Fixing HTTP 403 Errors

Most `HTTP Error 403: Forbidden` failures come from an outdated `yt-dlp`, a video that needs browser authentication, or a temporary YouTube client change.

Update first:

```powershell
python -m pip install --upgrade yt-dlp
```

If your browser account can view the video but the app cannot, export a Netscape-format `cookies.txt` file from that browser profile and upload it in the sidebar. Only use cookies for videos you are authorized to access.

## Legal Notice

Use this tool only with videos you own, videos you have permission to process, or content where your use is otherwise lawful. Respect YouTube's Terms of Service and all applicable copyright rules.

This project is not affiliated with YouTube or Google.
