# Expected media

This composition credits a third-party creator, so their images are **not**
committed to this repo. Supply your own before rendering, or the card renders
with two gaps where the images should be.

| File | What it is | Displayed at |
|---|---|---|
| `images/jason_avatar.png` | square avatar, cropped to a circle in CSS | 300 × 300 |
| `images/jason_thumb.png`  | 16:9 video thumbnail | 744 × 408 |

Source images smaller than the display size will look soft at 4K. Upscale with a
good filter first rather than letting the browser interpolate:

```bash
ffmpeg -i avatar_raw.png -vf "scale=756:756:flags=lanczos" images/jason_avatar.png
ffmpeg -i thumb_raw.png  -vf "scale=1488:816:flags=lanczos" images/jason_thumb.png
```
