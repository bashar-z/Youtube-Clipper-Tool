import streamlit as st
import tempfile, subprocess, os, glob
from yt_dlp import YoutubeDL

st.set_page_config(page_title="YouTube Clipper", page_icon="🎬", layout="centered")

# --- Title ---
st.title("🎬 YouTube Clipper")
st.caption("Paste a YouTube link, set start and end times, and download your MP4 clip.")

st.divider()

# --- Inputs ---
url = st.text_input("🔗 YouTube URL", placeholder="https://www.youtube.com/watch?v=...")

st.divider()
st.subheader("Start Time")
c1, c2, c3 = st.columns(3)
with c1:
    sh = st.number_input("Hours", min_value=0, max_value=23, value=0, step=1, key="sh")
with c2:
    sm = st.number_input("Minutes", min_value=0, max_value=59, value=0, step=1, key="sm")
with c3:
    ss = st.number_input("Seconds", min_value=0, max_value=59, value=0, step=1, key="ss")

st.subheader("End Time")
c4, c5, c6 = st.columns(3)
with c4:
    eh = st.number_input("Hours ", min_value=0, max_value=23, value=0, step=1, key="eh")
with c5:
    em = st.number_input("Minutes ", min_value=0, max_value=59, value=3, step=1, key="em")
with c6:
    es = st.number_input("Seconds ", min_value=0, max_value=59, value=0, step=1, key="es")

st.divider()

def fmt(h, m, s):
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"

start_ts = fmt(sh, sm, ss)
end_ts   = fmt(eh, em, es)
st.write(f"🎯 **Selected range:** {start_ts} → {end_ts}")

clip_button = st.button("🎬 Clip & Download", use_container_width=True)

# --- Helpers ---
def download_merged_mp4(yt_url: str, outtmpl: str):
    """Download best video+audio merged MP4."""
    ydl_opts = {
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
    """Trim clip precisely without re-encoding."""
    cmd = [
        "ffmpeg", "-y",
        "-ss", start, "-to", end,
        "-i", src_path,
        "-c", "copy",
        out_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

# --- Main logic ---
if clip_button:
    if not url.strip():
        st.error("Please paste a YouTube URL first.")
    else:
        with st.status("Processing...", expanded=True) as status:
            try:
                with tempfile.TemporaryDirectory() as tmp:
                    st.write("📥 Downloading source video...")
                    info = download_merged_mp4(url.strip(), os.path.join(tmp, "full_video.%(ext)s"))

                    files = sorted(glob.glob(os.path.join(tmp, "full_video.*")), key=len)
                    if not files:
                        st.error("Download failed — no video file found.")
                        status.update(label="Failed", state="error")
                        st.stop()
                    src = files[0]

                    # Ensure MP4 format
                    if not src.endswith(".mp4"):
                        st.write("🔄 Converting to MP4 format...")
                        mp4_path = os.path.join(tmp, "full_video.mp4")
                        subprocess.run(["ffmpeg","-y","-i",src,"-c","copy",mp4_path], check=True)
                        src = mp4_path

                    clip_name = f"clip_{start_ts.replace(':','-')}_{end_ts.replace(':','-')}.mp4"
                    clip_path = os.path.join(tmp, clip_name)

                    st.write(f"✂️ Trimming from {start_ts} to {end_ts}...")
                    run_ffmpeg_clip(src, start_ts, end_ts, clip_path)

                    st.success("✅ Clip ready.")
                    with open(clip_path, "rb") as f:
                        st.download_button(
                            label="⬇️ Download MP4",
                            data=f.read(),
                            file_name=clip_name,
                            mime="video/mp4",
                            use_container_width=True
                        )
                    status.update(label="Done", state="complete")
            except subprocess.CalledProcessError as e:
                st.error("FFmpeg failed during clipping.")
                st.code(e.stderr or str(e))
                status.update(label="Error", state="error")
            except Exception as e:
                st.error(f"Error: {e}")
                status.update(label="Error", state="error")

st.divider()
st.caption("⚠️ Use only with videos you own or have permission to process. Respect YouTube’s Terms of Service.")
