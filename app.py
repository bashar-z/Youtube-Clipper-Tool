import streamlit as st
import tempfile, subprocess, os, glob, io
from yt_dlp import YoutubeDL

st.set_page_config(page_title="YouTube Clipper", page_icon="🎬", layout="centered")

st.title("🎬 YouTube Clipper")
st.caption("Paste a YouTube link, set timestamps, get an MP4 clip. (Use only with content you have rights to.)")

# --- Inputs ---
url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Start")
    sh = st.number_input("H", min_value=0, max_value=23, value=0, step=1, key="sh")
    sm = st.number_input("M", min_value=0, max_value=59, value=0, step=1, key="sm")
    ss = st.number_input("S", min_value=0, max_value=59, value=0, step=1, key="ss")

with col2:
    st.subheader("End")
    eh = st.number_input("H ", min_value=0, max_value=23, value=0, step=1, key="eh")
    em = st.number_input("M ", min_value=0, max_value=59, value=3, step=1, key="em")
    es = st.number_input("S ", min_value=0, max_value=59, value=0, step=1, key="es")

def fmt(h, m, s):
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"

start_ts = fmt(sh, sm, ss)
end_ts   = fmt(eh, em, es)

st.write(f"**Selected range:** `{start_ts}` → `{end_ts}`")

go = st.button("🎯 Clip it")

# --- Helpers ---
def download_merged_mp4(yt_url: str, outtmpl: str):
    """
    Download best video+audio as a single MP4 using yt-dlp.
    """
    ydl_opts = {
        # prefer mp4 video+audio; fall back to best and merge to mp4
        "format": 'bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b',
        "outtmpl": outtmpl,
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(yt_url, download=True)
    return info

def run_ffmpeg_clip(src_path: str, start: str, end: str, out_path: str):
    """
    Fast, stream-copy trim (no re-encode). Requires ffmpeg.
    """
    cmd = [
        "ffmpeg", "-y",
        "-ss", start, "-to", end,
        "-i", src_path,
        "-c", "copy",
        out_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

# --- Main action ---
if go:
    if not url.strip():
        st.error("Paste a YouTube URL first.")
    else:
        with st.status("Working…", expanded=True) as status:
            try:
                with tempfile.TemporaryDirectory() as tmp:
                    st.write("⬇️ Downloading source video (merged A/V)…")
                    info = download_merged_mp4(url.strip(), os.path.join(tmp, "full_video.%(ext)s"))

                    # Locate the downloaded file (should be full_video.mp4)
                    files = sorted(glob.glob(os.path.join(tmp, "full_video.*")), key=len)
                    if not files:
                        st.error("Download failed — no video file found.")
                        status.update(label="Failed", state="error")
                        st.stop()
                    src = files[0]

                    # Ensure mp4 container
                    if not src.endswith(".mp4"):
                        st.write("🔁 Remuxing to MP4…")
                        mp4_path = os.path.join(tmp, "full_video.mp4")
                        subprocess.run(["ffmpeg","-y","-i",src,"-c","copy",mp4_path], check=True)
                        src = mp4_path

                    clip_name = f"clip_{start_ts.replace(':','-')}_{end_ts.replace(':','-')}.mp4"
                    clip_path = os.path.join(tmp, clip_name)

                    st.write(f"✂️ Trimming from **{start_ts}** to **{end_ts}** …")
                    run_ffmpeg_clip(src, start_ts, end_ts, clip_path)

                    st.success("Done! Your clip is ready.")
                    with open(clip_path, "rb") as f:
                        data = f.read()
                    st.download_button(
                        "⬇️ Download MP4",
                        data=data,
                        file_name=clip_name,
                        mime="video/mp4",
                        use_container_width=True
                    )
                    status.update(label="Complete", state="complete")
            except subprocess.CalledProcessError as e:
                st.error("FFmpeg failed while clipping.")
                st.code(e.stderr or str(e))
                status.update(label="Failed", state="error")
            except Exception as e:
                st.error(f"Error: {e}")
                status.update(label="Failed", state="error")

st.divider()
st.caption("⚠️ Use only with videos you own or have permission to process. Respect YouTube’s Terms of Service.")
