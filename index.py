import os
import re
import sys
import glob
import subprocess
import uuid
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import shutil

"""
Create a timelapse video from JPG images in the current directory.

Usage:
    dk timelapse [--fps FPS] [--add-timestamps] [output_file]
    dk timelapse [output_file] [--fps FPS] [--add-timestamps]

Options:
    --fps FPS        Frames per second (default: 30)
    --add-timestamps Add timestamps to each image
    output_file      Output filename (default: output.mp4)

Requirements:
    - ffmpeg installed and available in PATH
    - JPG images in the current directory
    - PIL (Python Imaging Library) for timestamp functionality
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
add_timestamps = False
clean_up_timestamped_dir = False # set this to True to delete the "timestamped" directory after the video is created

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
    elif args[i] == '--add-timestamps':
        add_timestamps = True
        i += 1
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

# Sort files by creation time
jpg_files.sort(key=lambda x: os.path.getmtime(x))

if add_timestamps:
    # Create timestamped directory
    timestamped_dir = 'timestamped'
    if os.path.exists(timestamped_dir):
        print("Using existing timestamped directory...")
        # Verify all required files exist in timestamped directory
        missing_files = []
        for jpg_file in jpg_files:
            timestamped_path = os.path.join(timestamped_dir, os.path.basename(jpg_file))
            if not os.path.exists(timestamped_path):
                missing_files.append(jpg_file)
        
        if missing_files:
            print(f"Warning: {len(missing_files)} files missing from timestamped directory. Recreating...")
            shutil.rmtree(timestamped_dir)
            os.makedirs(timestamped_dir)
        else:
            # All files exist, use the timestamped directory
            jpg_files = [os.path.join(timestamped_dir, os.path.basename(f)) for f in jpg_files]
            add_timestamps = False  # Skip timestamping since we're using existing files
    
    if add_timestamps:
        # Ensure timestamped directory exists
        if not os.path.exists(timestamped_dir):
            os.makedirs(timestamped_dir)
            
        print("Adding timestamps to images...")
        total_files = len(jpg_files)
        for i, jpg_file in enumerate(jpg_files, 1):
            try:
                # Get modification time
                mod_time = datetime.fromtimestamp(os.path.getmtime(jpg_file))
                timestamp_str = mod_time.strftime('%Y-%m-%d %H:%M:%S')
                
                # Open image and add timestamp
                with Image.open(jpg_file) as img:
                    # Create a copy of the image
                    img_copy = img.copy()
                    draw = ImageDraw.Draw(img_copy)
                    
                    # Try to load a font, fall back to default if not available
                    try:
                        font = ImageFont.truetype("Arial", 36)
                    except IOError:
                        font = ImageFont.load_default()
                    
                    # Add timestamp to bottom right
                    text_bbox = draw.textbbox((0, 0), timestamp_str, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]
                    
                    # Position text in bottom right with padding
                    x = img_copy.width - text_width - 20
                    y = img_copy.height - text_height - 20
                    
                    # Add black outline for better visibility
                    for offset_x, offset_y in [(-1,-1), (-1,1), (1,-1), (1,1)]:
                        draw.text((x + offset_x, y + offset_y), timestamp_str, font=font, fill='black')
                    
                    # Add white text
                    draw.text((x, y), timestamp_str, font=font, fill='white')
                    
                    # Save to timestamped directory
                    output_path = os.path.join(timestamped_dir, os.path.basename(jpg_file))
                    img_copy.save(output_path, quality=95)
                
                # Show progress
                progress = (i / total_files) * 100
                print(f"\rProgress: {progress:.1f}% ({i}/{total_files})", end="", flush=True)
            except Exception as e:
                print(f"\nError processing {jpg_file}: {str(e)}")
                raise
        
        print()  # New line after progress
        # Update jpg_files to use the timestamped versions
        jpg_files = [os.path.join(timestamped_dir, os.path.basename(f)) for f in jpg_files]

print(f"Creating timelapse: {output_file} ({fps} fps)")

# Create a temporary file list with a random name
temp_file = f'filelist_{uuid.uuid4().hex}.txt'
with open(temp_file, 'w') as f:
    for file in jpg_files:
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

should_clean_up_timestamped_dir = add_timestamps and clean_up_timestamped_dir and os.path.exists(timestamped_dir)

# Run ffmpeg
try:
    subprocess.run(ffmpeg_cmd, check=True)
    print(f"Created timelapse: {output_file} ({fps} fps)")
    # Clean up the temporary file
    os.remove(temp_file)
    # Clean up timestamped directory if it was created
    if should_clean_up_timestamped_dir:
        shutil.rmtree(timestamped_dir)
except subprocess.CalledProcessError as e:
    print(f"Error running ffmpeg: {e}", file=sys.stderr)
    # Clean up the temporary file even if there's an error
    if os.path.exists(temp_file):
        os.remove(temp_file)
    if should_clean_up_timestamped_dir:
        shutil.rmtree(timestamped_dir)
    sys.exit(1)
except FileNotFoundError:
    print("Error: ffmpeg not found. Please install ffmpeg.", file=sys.stderr)
    # Clean up the temporary file even if there's an error
    if os.path.exists(temp_file):
        os.remove(temp_file)
    if should_clean_up_timestamped_dir:
        shutil.rmtree(timestamped_dir)
    sys.exit(1)


