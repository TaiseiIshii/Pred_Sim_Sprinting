"""Make compact looping GIFs from the 3D musculoskeletal MP4s so they can be
embedded inline in Markdown (GIFs render as images in every viewer, incl. GitHub
and VS Code preview). Uses the ffmpeg bundled with imageio-ffmpeg + palettegen
for good quality/size."""
import os
import subprocess

import imageio_ffmpeg

STUDY = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "Results", "PelvicTD_Study")
FF = imageio_ffmpeg.get_ffmpeg_exe()


def mk_gif(src, dst, width, fps):
    src, dst = os.path.join(STUDY, src), os.path.join(STUDY, dst)
    vf = (f"fps={fps},scale={width}:-1:flags=lanczos,"
          "split[s0][s1];[s0]palettegen=max_colors=128[p];"
          "[s1][p]paletteuse=dither=bayer:bayer_scale=3")
    subprocess.run([FF, "-y", "-i", src, "-vf", vf, "-loop", "0", dst],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    mb = os.path.getsize(dst) / 1e6
    print(f"  {os.path.basename(dst)}  {mb:.1f} MB")


print("ffmpeg:", FF)
mk_gif("pelvic_td_musculoskeletal_sidebyside.mp4",
       "pelvic_td_musculoskeletal_sidebyside.gif", 1100, 12)
mk_gif("pelvic_td_musculoskeletal_overlay.mp4",
       "pelvic_td_musculoskeletal_overlay.gif", 680, 12)
print("done")
