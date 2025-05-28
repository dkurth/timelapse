#!/bin/bash

# This is just for reference.

# This would also work, but other dk commands are all in python.
# To install this as a local command, you could run:
#   sudo cp create-timelapse.sh /usr/local/bin/create-timelapse
#   sudo chmod +x /usr/local/bin/create-timelapse

# I prefer to use the `dk` system, so I can easily run `dk list` 
# and be reminded of all the commands I have available. It is
# also portable to Windows.

# Default values
fps=30
output="output.mp4"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fps)
            fps="$2"
            shift 2
            ;;
        --fps=*)
            fps="${1#*=}"
            shift
            ;;
        -*)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
        *)
            # Assume it's the output filename
            output="$1"
            shift
            ;;
    esac
done

# Check if there are any JPG files
if ! ls *.JPG >/dev/null 2>&1 && ! ls *.jpg >/dev/null 2>&1; then
    echo "Error: No JPG files found in current directory" >&2
    exit 1
fi

# Run ffmpeg with the specified parameters
echo "Creating timelapse: $output (${fps} fps)"

# Use case-insensitive pattern matching for JPG files
if ls *.JPG >/dev/null 2>&1; then
    pattern="*.JPG"
elif ls *.jpg >/dev/null 2>&1; then
    pattern="*.jpg"
fi

ffmpeg -framerate "$fps" -pattern_type glob -i "$pattern" -s:v 1440x1080 -c:v libx264 -crf 17 -pix_fmt yuv420p "$output"
