# ffmpeg 合成说明

## 逐页片段

每页：静图 loop + 音轨，时长以音频为准（`-shortest`）。

```bash
ffmpeg -y -loop 1 -i slide.png -i audio.mp3 \
  -c:v libx264 -tune stillimage -pix_fmt yuv420p \
  -c:a aac -b:a 192k -r 30 -shortest segment.mp4
```

若音频短于 `min_slide_seconds`，用 `-t` 延长静图时长。

## 拼接

concat demuxer：

```
file 'segments/001.mp4'
file 'segments/002.mp4'
...
```

```bash
ffmpeg -y -f concat -safe 0 -i concat.txt -c copy narrated.mp4
```

## 依赖

- `ffmpeg` 须在 PATH 中
- Windows：`winget install Gyan.FFmpeg` 或 `winget install ffmpeg`

## 分辨率

默认 1920x1080；Marp PNG 若尺寸不同，ffmpeg 会 scale 到 `-s` 指定分辨率。
