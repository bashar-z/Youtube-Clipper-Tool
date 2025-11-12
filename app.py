import streamlit as st
import tempfile, subprocess, os, re, glob, math
from yt_dlp import YoutubeDL

st.set_page_config(page_title="YouTube Clipper", page_icon="🎬", layout="centered")

# ---------- helpers ----------
def fmt_hms(total_seconds: int) -> str:
    if total_seconds is None:
        return "–"
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def fmt(h, m, s):
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"

def sanitize_filename(name: str, default="clip"):
    name = name.strip() or default
    # remove forbidden characters across OSes
    name = re.sub(r'[\\/:*?"<>|#%{}[\]^~`+=,;]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name[:120]

def download_merged_mp4(yt_url: str, outtmpl: str, progress_cb=None):
    """
    Download best video+audio as single MP4, with yt-dlp progress hook.
    """
    def hook(d):
        if progress_cb is None:
            return
        if d.get('status') == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            done = d.get('downloaded_bytes') or 0
            speed = d.get('speed') or 0
            eta   = d.get('eta')
            progress_cb(done, total, speed, eta, phase="Downloading")
        elif d.get('status') == 'finished':
            progress_cb(None, None, None, None, phase="Post-processing")

    ydl_opts = {
        "format": 'bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b',
        "outtmpl": outtmpl,
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [hook],
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(yt_url, download=True)
    return info

def run_ffmpeg_clip_video(src_path: str, start: str, end: str, out_path: str, progress=None):
    """
    Trim video (copy) between start and end to MP4.
    """
    cmd = [
        "ffmpeg", "-y",
        "-ss", start, "-to", end,
        "-i", src_path,
        "-c", "copy",
        out_path
    ]
    # We capture output for error display; progress is coarse via status text
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if progress:
        progress(1.0, "Trimming complete")

def run_ffmpeg_clip_audio_mp3(src_path: str, start: str, end: str, out_path: str):
    """
    Extract audio-only MP3 between start and end (libmp3lame).
    """
    cmd = [
        "ffmpeg", "-y",
        "-ss", start, "-to", end,
        "-i", src_path,
        "-vn",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        out_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

# ---------- UI ----------
st.title("🎬 YouTube Clipper")
st.caption("Paste a YouTube link, set times, and download your clip.")

st.divider()

# URL input
url = st.text_input("🔗 YouTube URL", placeholder="https://www.youtube.com/watch?v=...")

# Preview section
info_container = st.container()
with info_container:
    if url.strip():
        try:
            with st.spinner("Fetching video details…"):
                with YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
                    meta = ydl.extract_info(url.strip(), download=False)
            title = meta.get("title") or "Untitled"
            channel = meta.get("uploader") or meta.get("channel") or "Unknown"
            duration = fmt_hms(meta.get("duration"))
            thumb = meta.get("thumbnail")
            colA, colB = st.columns([1,2], vertical_alignment="center")
            with colA:
                if thumb:
                    st.image(thumb, use_column_width=True, caption=None)
            with colB:
                st.markdown(f"**Title:** {title}")
                st.markdown(f"**Channel:** {channel}")
                st.markdown(f"**Duration:** {duration}")
        except Exception as e:
            st.info("Could not load preview (link private/age-restricted/region-locked?). You can still try clipping.")

st.divider()

# Time pickers
st.subheader("⏱ Start Time")
c1, c2, c3 = st.columns(3)
with c1:
    sh = st.number_input("Hours", min_value=0, max_value=23, value=0, step=1, key="sh")
with c2:
    sm = st.number_input("Minutes", min_value=0, max_value=59, value=0, step=1, key="sm")
with c3:
    ss = st.number_input("Seconds", min_value=0, max_value=59, value=0, step=1, key="ss")

st.subheader("🏁 End Time")
c4, c5, c6 = st.columns(3)
with c4:
    eh = st.number_input("Hours ", min_value=0, max_value=23, value=0, step=1, key="eh")
with c5:
    em = st.number_input("Minutes ", min_value=0, max_value=59, value=3, step=1, key="em")
with c6:
    es = st.number_input("Seconds ", min_value=0, max_value=59, value=0, step=1, key="es")

start_ts = fmt(sh, sm, ss)
end_ts   = fmt(eh, em, es)
st.write(f"🎯 **Selected range:** {start_ts} → {end_ts}")

st.divider()

# Output options
out_mode = st.radio("Output type", ["MP4 (video + audio)", "MP3 (audio only)"], horizontal=True)
default_base = sanitize_filename((locals().get("title") or "clip") + f"_{start_ts.replace(':','-')}_{end_ts.replace(':','-')}")
custom_name = st.text_input("Output name (no extension)", value=default_base)
st.caption("Tip: You can rename the file here. Extension is added automatically.")

# Do it button
clip_button = st.button("🎬 Clip & Download", use_container_width=True)

# session history
if "recent" not in st.session_state:
    st.session_state.recent = []  # list of dicts: {"label":..., "bytes":..., "mime":..., "file_name":...}

def add_recent(label, blob, mime, file_name, max_items=3):
    st.session_state.recent.insert(0, {"label": label, "bytes": blob, "mime": mime, "file_name": file_name})
    st.session_state.recent = st.session_state.recent[:max_items]

# ---------- main action ----------
if clip_button:
    if not url.strip():
        st.error("Please paste a YouTube URL first.")
    else:
        with st.status("Processing…", expanded=True) as status:
            prog = st.progress(0.0, text="Starting…")

            def dl_progress(done, total, speed, eta, phase=""):
                if total and total > 0:
                    frac = min(0.99, done / total)
                else:
                    frac = 0.1  # unknown total
                txt = f"{phase} — {math.ceil((done or 0)/1_000_000)}MB"
                if total:
                    txt += f" / {math.ceil(total/1_000_000)}MB"
                if speed:
                    txt += f" • ~{math.ceil(speed/1024)} KB/s"
                if eta:
                    txt += f" • ETA {eta}s"
                prog.progress(frac, text=txt)

            try:
                with tempfile.TemporaryDirectory() as tmp:
                    # 1) Download
                    status.update(label="Downloading video", state="running")
                    info = download_merged_mp4(url.strip(), os.path.join(tmp, "full_video.%(ext)s"), progress_cb=dl_progress)

                    files = sorted(glob.glob(os.path.join(tmp, "full_video.*")), key=len)
                    if not files:
                        st.error("Download failed — no video file found.")
                        status.update(label="Failed", state="error")
                        st.stop()
                    src = files[0]
                    if not src.endswith(".mp4"):
                        st.write("Converting to MP4 container…")
                        mp4_path = os.path.join(tmp, "full_video.mp4")
                        subprocess.run(["ffmpeg","-y","-i",src,"-c","copy",mp4_path], check=True)
                        src = mp4_path

                    # 2) Clip
                    status.update(label="Trimming clip", state="running")
                    prog.progress(0.99, text="Trimming…")
                    base = sanitize_filename(custom_name or "clip")
                    if out_mode.startswith("MP4"):
                        file_name = base + ".mp4"
                        out_path = os.path.join(tmp, file_name)
                        run_ffmpeg_clip_video(src, start_ts, end_ts, out_path, progress=lambda f, t: prog.progress(1.0, text=t))
                        mime = "video/mp4"
                    else:
                        file_name = base + ".mp3"
                        out_path = os.path.join(tmp, file_name)
                        run_ffmpeg_clip_audio_mp3(src, start_ts, end_ts, out_path)
                        prog.progress(1.0, text="Audio extracted")
                        mime = "audio/mpeg"

                    # 3) Offer download + add to session history
                    with open(out_path, "rb") as f:
                        blob = f.read()
                    st.success("Clip ready.")
                    st.download_button(
                        label="⬇️ Download",
                        data=blob,
                        file_name=file_name,
                        mime=mime,
                        use_container_width=True
                    )
                    add_recent(file_name, blob, mime, file_name)

                    status.update(label="Complete", state="complete")
            except subprocess.CalledProcessError as e:
                st.error("FFmpeg failed.")
                st.code(e.stderr or str(e))
                status.update(label="Failed", state="error")
            except Exception as e:
                st.error(f"Error: {e}")
                status.update(label="Failed", state="error")

st.divider()

# ---------- recent clips ----------
if st.session_state.recent:
    st.subheader("Recent clips (this session)")
    for idx, item in enumerate(st.session_state.recent):
        cols = st.columns([3,1])
        with cols[0]:
            st.markdown(f"**{item['file_name']}**")
        with cols[1]:
            st.download_button("Download", data=item["bytes"], file_name=item["file_name"], mime=item["mime"], key=f"dl_{idx}")

st.caption("⚠️ Use only with videos you own or have permission to process. Respect YouTube’s Terms of Service.")
