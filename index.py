import os
import re
import sys
import glob
import subprocess
import uuid

"""
Create a timelapse video from JPG images in the current directory.

Usage:
    dk timelapse [--fps FPS] [output_file]
    dk timelapse [output_file] [--fps FPS]

Options:
    --fps FPS        Frames per second (default: 30)
    output_file      Output filename (default: output.mp4)

Requirements:
    - ffmpeg installed and available in PATH
    - JPG images in the current directory
"""

execution_context = sys.argv[1]
# args with the execution_context stripped out (so args[0] is the first argument)
args = sys.argv[2:]

# Move into the directory from which the dk command was executed by the user
# (Remove this if you need to start in the directory containing this command's code)
os.chdir(execution_context)

# Parse arguments
fps = 30  # default fps
output_file = 'output.mp4'  # default output file

i = 0
while i < len(args):
    if args[i] == '--fps':
        if i + 1 < len(args):
            try:
                fps = int(args[i + 1])
                i += 2
            except ValueError:
                print("Error: --fps must be followed by a number", file=sys.stderr)
                sys.exit(1)
        else:
            print("Error: --fps must be followed by a number", file=sys.stderr)
            sys.exit(1)
    elif args[i].endswith('.mp4'):
        # If it ends with .mp4, it's the output file
        output_file = args[i]
        i += 1
    else:
        print(f"Error: Unrecognized argument: {args[i]}", file=sys.stderr)
        sys.exit(1)

# Check for JPEG files
jpg_files = glob.glob('*.JPG') + glob.glob('*.jpg') + glob.glob('*.JPEG') + glob.glob('*.jpeg')
if not jpg_files:
    print("Error: No jpg files found in current directory", file=sys.stderr)
    sys.exit(1)

print(f"Creating timelapse: {output_file} ({fps} fps)")

# Create a temporary file list with a random name
temp_file = f'filelist_{uuid.uuid4().hex}.txt'
with open(temp_file, 'w') as f:
    for file in sorted(jpg_files):
        f.write(f"file '{file}'\n")
        f.write(f"duration {1/fps}\n")  # Set duration for each frame

# Construct ffmpeg command
ffmpeg_cmd = [
    'ffmpeg',
    '-f', 'concat',
    '-safe', '0',
    '-i', temp_file,
    '-vsync', 'vfr',  # Variable frame rate
    '-s:v', '1440x1080',
    '-c:v', 'libx264',
    '-crf', '17',
    '-pix_fmt', 'yuv420p',
    output_file
]

# Run ffmpeg
try:
    subprocess.run(ffmpeg_cmd, check=True)
    print(f"Created timelapse: {output_file} ({fps} fps)")
    # Clean up the temporary file
    os.remove(temp_file)
except subprocess.CalledProcessError as e:
    print(f"Error running ffmpeg: {e}", file=sys.stderr)
    # Clean up the temporary file even if there's an error
    if os.path.exists(temp_file):
        os.remove(temp_file)
    sys.exit(1)
except FileNotFoundError:
    print("Error: ffmpeg not found. Please install ffmpeg.", file=sys.stderr)
    # Clean up the temporary file even if there's an error
    if os.path.exists(temp_file):
        os.remove(temp_file)
    sys.exit(1)


