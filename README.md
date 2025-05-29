# timelapse

This is a command meant to be used with [dk](https://github.com/dkurth/dk). It creates a timelapse video from a directory of jpg files.

## Usage

`cd` into a directory full of .jpg files.

Run `dk timelapse` to create a timelapse video.

You can optionally specify:
- The output file name
- The frames per second (default is 30)
- Whether to add timestamps to each frame

```
dk timelapse --fps 30 my_timelapse.mp4
dk timelapse --add-timestamps my_timelapse.mp4
dk timelapse --fps 30 --add-timestamps my_timelapse.mp4
```

## Features

### Timestamps
When using `--add-timestamps`, the script will:
1. Create a "timestamped" directory for keeping copies of your images with timestamps
2. Add the modification time of each image in the bottom right corner
3. Use these timestamped images to create the timelapse

If you run the command again with the same images, it will reuse the existing timestamped directory if available.
