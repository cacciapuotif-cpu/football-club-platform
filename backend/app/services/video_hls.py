"""
HLS Video Processing Service with chunked transcoding.
Production-ready video pipeline: transcode → segment HLS → upload to S3.
"""

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from uuid import UUID

import m3u8
from rq import get_current_job

from app.services.storage import storage_service

logger = logging.getLogger(__name__)


class HLSVideoProcessor:
    """
    HLS video processor with chunked transcoding and S3 upload.
    """

    def __init__(self):
        self.segment_duration = 6  # seconds per segment
        self.target_resolution = "1280x720"
        self.target_bitrate = "2M"
        self.ffmpeg_threads = 4

    def process_video(
        self,
        input_path: Path,
        video_id: UUID,
        tenant_id: UUID,
    ) -> dict:
        """
        Process video: transcode, segment, upload HLS files.
        Returns: {
            "playlist_url": str,
            "segments_count": int,
            "duration_sec": float,
            "resolution": str
        }
        """
        job = get_current_job()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            output_playlist = tmpdir_path / "playlist.m3u8"
            segment_pattern = tmpdir_path / "segment_%03d.ts"

            # Step 1: Transcode and segment
            logger.info(f"Transcoding video {video_id}...")
            if job:
                job.meta["step"] = "transcoding"
                job.save_meta()

            self._transcode_to_hls(
                input_path=input_path,
                output_playlist=output_playlist,
                segment_pattern=segment_pattern,
            )

            # Step 2: Parse playlist
            logger.info(f"Parsing HLS playlist for video {video_id}...")
            playlist = m3u8.load(str(output_playlist))
            segments = playlist.segments
            total_duration = sum(s.duration for s in segments)

            if job:
                job.meta["step"] = "uploading"
                job.meta["segments_total"] = len(segments)
                job.save_meta()

            # Step 3: Upload segments to S3
            logger.info(f"Uploading {len(segments)} segments for video {video_id}...")
            base_key = f"videos/{tenant_id}/{video_id}"

            for idx, segment in enumerate(segments):
                segment_path = tmpdir_path / segment.uri
                s3_key = f"{base_key}/segment_{idx:03d}.ts"

                with open(segment_path, "rb") as f:
                    storage_service.upload_file(
                        file=f,
                        key=s3_key,
                        content_type="video/MP2T",
                    )

                # Update playlist with S3 URLs
                segments[idx].uri = storage_service.get_url(s3_key, expires_in=86400)

                if job:
                    job.meta["segments_uploaded"] = idx + 1
                    job.save_meta()

            # Step 4: Upload modified playlist
            playlist_content = playlist.dumps()
            playlist_key = f"{base_key}/playlist.m3u8"

            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".m3u8") as tmp_playlist:
                tmp_playlist.write(playlist_content)
                tmp_playlist.flush()

                with open(tmp_playlist.name, "rb") as f:
                    playlist_url = storage_service.upload_file(
                        file=f,
                        key=playlist_key,
                        content_type="application/vnd.apple.mpegurl",
                    )

            logger.info(f"Video {video_id} processed successfully. Playlist: {playlist_url}")

            return {
                "playlist_url": playlist_url,
                "segments_count": len(segments),
                "duration_sec": total_duration,
                "resolution": self.target_resolution,
            }

    def _transcode_to_hls(
        self,
        input_path: Path,
        output_playlist: Path,
        segment_pattern: Path,
    ):
        """
        Transcode video to HLS format using ffmpeg.
        """
        cmd = [
            "ffmpeg",
            "-i", str(input_path),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-s", self.target_resolution,
            "-b:v", self.target_bitrate,
            "-c:a", "aac",
            "-b:a", "128k",
            "-threads", str(self.ffmpeg_threads),
            "-f", "hls",
            "-hls_time", str(self.segment_duration),
            "-hls_list_size", "0",
            "-hls_segment_filename", str(segment_pattern),
            str(output_playlist),
        ]

        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 min timeout
            )
            logger.debug(f"ffmpeg stdout: {result.stdout}")
        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg failed: {e.stderr}")
            raise RuntimeError(f"Video transcoding failed: {e.stderr}")
        except subprocess.TimeoutExpired:
            logger.error("ffmpeg timeout exceeded")
            raise RuntimeError("Video transcoding timeout")

    def get_video_info(self, video_path: Path) -> dict:
        """
        Extract video metadata using ffprobe.
        """
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration,size:stream=width,height,codec_name",
            "-of", "json",
            str(video_path),
        ]

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=30)
            import json
            return json.loads(result.stdout)
        except Exception as e:
            logger.error(f"ffprobe failed: {e}")
            return {}


# Global singleton
hls_processor = HLSVideoProcessor()
