from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from clipper import ClipError, create_clip, fetch_video_info, format_timestamp, parse_timestamp


st.set_page_config(
    page_title="YouTube Clip Tool",
    page_icon=":material/content_cut:",
    layout="centered",
)


def save_uploaded_cookies(uploaded_file) -> Path | None:
    if uploaded_file is None:
        return None
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".cookies.txt")
    tmp.write(uploaded_file.getvalue())
    tmp.close()
    return Path(tmp.name)


def main() -> None:
    st.title("YouTube Clip Tool")
    st.caption("Clip videos you own or have permission to use.")

    with st.sidebar:
        st.header("Export")
        output_kind = st.radio("Format", ["mp4", "mp3"], horizontal=True)
        quality = st.select_slider("Source quality", options=["Small", "Balanced", "Best"], value="Balanced")
        st.divider()
        cookies_file = st.file_uploader(
            "Optional cookies.txt",
            type=["txt"],
            help="Useful for videos your browser account can view but yt-dlp cannot access directly.",
        )

    url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
    col1, col2 = st.columns(2)
    with col1:
        start_raw = st.text_input("Start", value="00:00:00", help="Use SS, MM:SS, or HH:MM:SS")
    with col2:
        end_raw = st.text_input("End", value="00:00:30", help="Use SS, MM:SS, or HH:MM:SS")

    cookies_path = save_uploaded_cookies(cookies_file)

    if url:
        with st.expander("Video details", expanded=True):
            if st.button("Load details", use_container_width=True):
                try:
                    info = fetch_video_info(url, cookies_path)
                    if info.thumbnail:
                        st.image(info.thumbnail, use_container_width=True)
                    st.subheader(info.title)
                    if info.uploader:
                        st.write(info.uploader)
                    if info.duration is not None:
                        st.write(f"Duration: {format_timestamp(info.duration)}")
                except ClipError as exc:
                    st.error(str(exc))

    clip_clicked = st.button("Create clip", type="primary", use_container_width=True)
    status = st.empty()

    if clip_clicked:
        try:
            if not url.strip():
                raise ClipError("Paste a YouTube URL first.")
            start_seconds = parse_timestamp(start_raw)
            end_seconds = parse_timestamp(end_raw)
            if end_seconds - start_seconds > 60 * 60:
                raise ClipError("Please keep clips under 1 hour.")

            result = create_clip(
                url=url.strip(),
                start_seconds=start_seconds,
                end_seconds=end_seconds,
                output_kind=output_kind,
                quality=quality,
                cookies_path=cookies_path,
                progress=lambda message: status.info(message),
            )

            status.success("Clip ready.")
            with result.path.open("rb") as file:
                st.download_button(
                    "Download clip",
                    file,
                    file_name=result.filename,
                    mime=result.mime_type,
                    use_container_width=True,
                )
            st.caption(f"Saved locally to {result.path}")
        except ClipError as exc:
            status.error(str(exc))
        except Exception as exc:
            status.error(f"Unexpected error: {exc}")


if __name__ == "__main__":
    main()
