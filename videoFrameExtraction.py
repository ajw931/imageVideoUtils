import argparse
import json
import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

FULL_SETS = 'FULL_SETS'

# Formats where ffmpeg's -q:v quality scale applies
QUALITY_FORMATS = ('jpg', 'jpeg')


def qualityToQscale(quality):
    '''
    Map ImageMagick-style quality (1=worst, 100=best) to ffmpeg's mjpeg
    -q:v scale (31=worst, 2=best).
    '''
    return max(2, min(31, round(31 - (quality / 100) * 29)))


def probeVideo(filepath):
    '''
    Return the display dimensions (width, height) of the file's video stream,
    accounting for rotation metadata, or None if it has no video stream.
    '''
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
         '-show_entries', 'stream=width,height:stream_side_data=rotation',
         '-of', 'json', str(filepath)],
        capture_output=True, text=True)
    if result.returncode != 0:
        return None
    try:
        stream = json.loads(result.stdout)['streams'][0]
        width, height = int(stream['width']), int(stream['height'])
    except (KeyError, IndexError, ValueError, json.JSONDecodeError):
        return None
    # Phone videos are often stored sideways with a rotation flag;
    # ffmpeg auto-rotates on decode, so report the rotated dimensions
    rotation = 0
    for sideData in stream.get('side_data_list', []):
        if 'rotation' in sideData:
            rotation = int(sideData['rotation'])
    if abs(rotation) % 180 == 90:
        width, height = height, width
    return width, height


def computeResizedDims(inWidth, inHeight, width, height):
    '''
    Compute output dimensions from the requested width OR height, keeping
    aspect ratio. The derived dimension is rounded to the nearest even number.
    '''
    if width is not None:
        derived = round(inHeight * width / inWidth / 2) * 2
        return width, max(2, derived)
    derived = round(inWidth * height / inHeight / 2) * 2
    return max(2, derived), height


def buildFfmpegCommand(videoPath, name, origOut, resizedOut, outWidth, outHeight, args):
    '''
    Build a single-pass ffmpeg command that decodes the video once and writes
    full-size frames (origOut) and/or resized frames (resizedOut).
    Either output dir may be None if that output isn't wanted.
    '''
    blur = f'smartblur=luma_strength={args.blur}' if args.blur > 0 else None
    scale = f'scale={outWidth}:{outHeight}'

    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin',
           '-i', str(videoPath)]

    def outputOpts(fmt):
        opts = ['-fps_mode', 'passthrough']
        if fmt in QUALITY_FORMATS:
            opts += ['-q:v', str(qualityToQscale(args.quality))]
        return opts

    origPattern = str(origOut / f'{name}.%04d.{args.extractionFormat}') if origOut else None
    resizedPattern = str(resizedOut / f'{name}.%04d.{args.finalFormat}') if resizedOut else None

    if origOut and resizedOut:
        # Decode and blur once, then split into a full-size and a resized stream
        chain = (blur + ',' if blur else '')
        cmd += ['-filter_complex',
                f'[0:v]{chain}split=2[full][pre];[pre]{scale}[small]',
                '-map', '[full]', *outputOpts(args.extractionFormat), origPattern,
                '-map', '[small]', *outputOpts(args.finalFormat), resizedPattern]
    elif origOut:
        if blur:
            cmd += ['-vf', blur]
        cmd += [*outputOpts(args.extractionFormat), origPattern]
    else:
        vf = (blur + ',' if blur else '') + scale
        cmd += ['-vf', vf, *outputOpts(args.finalFormat), resizedPattern]
    return cmd


def processVideo(videoPath, fullSetsDir, args):
    '''
    Extract (and resize) one video. Returns (name, status, detail) where
    status is 'done', 'skipped', or 'failed'.

    Full-size frames go to FULL_SETS/<name>/ and resized frames to
    FULL_SETS/<name>/RESIZED_<w>x<h>/, where <w>x<h> are the actual output
    dimensions. Frames are written to .partial folders which are renamed
    into place only on success, so an interrupted run redoes incomplete
    videos instead of silently skipping them.
    '''
    name = videoPath.stem
    origDir = fullSetsDir / name

    dims = probeVideo(videoPath)
    if dims is None:
        return (name, 'skipped', 'no video stream (not a video file?)')
    outWidth, outHeight = computeResizedDims(*dims, args.width, args.height)
    resizedName = f'RESIZED_{outWidth}x{outHeight}'
    resizedDir = origDir / resizedName

    # With single-pass extraction, "delete originals" means never writing them
    wantOrig = not (args.resize and args.deleteOriginals)
    wantResized = args.resize

    # The video folder also holds the RESIZED subfolder, so "originals exist"
    # means it contains frame files, not merely that the folder exists
    originalsExist = origDir.is_dir() and any(p.is_file() for p in origDir.iterdir())
    needOrig = wantOrig and not originalsExist
    needResized = wantResized and not resizedDir.is_dir()

    rootPartial = fullSetsDir / f'{name}.partial'
    resizedPartial = origDir / f'{resizedName}.partial'

    if not needOrig and not needResized:
        # Clean up any stale partial folders from an interrupted earlier run
        for stale in (rootPartial, resizedPartial):
            if stale.exists():
                shutil.rmtree(stale)
        return (name, 'skipped', 'output folder(s) already exist')

    if needOrig:
        # (Re)build the whole video folder atomically
        if rootPartial.exists():
            shutil.rmtree(rootPartial)
        rootPartial.mkdir(parents=True)
        origOut = rootPartial
        resizedOut = rootPartial / resizedName if wantResized else None
        if resizedOut:
            resizedOut.mkdir()
        partialDirs = [rootPartial]
    else:
        # Originals are in place (or not wanted); only add the resized set
        if resizedPartial.exists():
            shutil.rmtree(resizedPartial)
        resizedPartial.mkdir(parents=True)
        origOut = None
        resizedOut = resizedPartial
        partialDirs = [resizedPartial]

    cmd = buildFfmpegCommand(videoPath, name, origOut, resizedOut,
                             outWidth, outHeight, args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        for partial in partialDirs:
            shutil.rmtree(partial, ignore_errors=True)
        detail = result.stderr.strip().splitlines()
        return (name, 'failed', detail[-1] if detail else f'ffmpeg exit code {result.returncode}')

    if needOrig:
        if origDir.exists():
            shutil.rmtree(origDir)
        rootPartial.rename(origDir)
    else:
        resizedPartial.rename(resizedDir)

    outputs = (1 if origOut else 0) + (1 if resizedOut else 0)
    return (name, 'done', f'{outputs} output set(s), resized to {outWidth}x{outHeight}'
            if wantResized else f'{outputs} output set(s)')


def main():
    parser = argparse.ArgumentParser(
        description='Extract frames from all videos in a directory into '
                    f'./{FULL_SETS}/<vid>/ and resized copies into '
                    f'./{FULL_SETS}/<vid>/RESIZED_<w>x<h>/, in a single '
                    'ffmpeg pass per video, with videos processed in parallel.')
    parser.add_argument('directory', nargs='?', default='.',
                        help='Directory containing the videos (default: current directory)')
    parser.add_argument('--extractionFormat', default='bmp',
                        help='Image format for the full-size frames (default: bmp)')
    parser.add_argument('--finalFormat', default='jpg',
                        help='Image format for the resized frames (default: jpg)')
    parser.add_argument('--quality', type=int, default=80,
                        help='Image quality 1 (worst) to 100 (best), for jpg output (default: 80)')
    parser.add_argument('--resize', action=argparse.BooleanOptionalAction, default=True,
                        help='Produce resized frames (default: yes; use --no-resize to disable)')
    parser.add_argument('--deleteOriginals', action=argparse.BooleanOptionalAction, default=False,
                        help='Skip writing the full-size frames entirely, keeping only the '
                             'resized ones (default: keep both)')
    parser.add_argument('--width', type=int, default=None,
                        help='Width of the resized frames; height derived from aspect ratio')
    parser.add_argument('--height', type=int, default=None,
                        help='Height of the resized frames; width derived from aspect ratio '
                             '(default: 2400 if neither --width nor --height is given)')
    parser.add_argument('--blur', type=float, default=0.25,
                        help='smartblur luma strength applied to all frames; 0 disables (default: 0.25)')
    parser.add_argument('--jobs', type=int, default=max(1, (os.cpu_count() or 2) // 2),
                        help='Number of videos to process in parallel '
                             '(default: half the logical cores)')
    args = parser.parse_args()

    if args.width is not None and args.height is not None:
        parser.error('provide either --width or --height, not both')
    if args.width is None and args.height is None:
        args.height = 2400

    srcDir = Path(args.directory)
    fullSetsDir = srcDir / FULL_SETS
    fullSetsDir.mkdir(exist_ok=True)

    videos = sorted(p for p in srcDir.iterdir()
                    if p.is_file() and not p.name.startswith('.'))
    if not videos:
        print(f'No files found in {srcDir}')
        return 0

    print(f'Processing {len(videos)} file(s) with {args.jobs} parallel job(s)')
    counts = {'done': 0, 'skipped': 0, 'failed': 0}
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {pool.submit(processVideo, v, fullSetsDir, args): v for v in videos}
        for future in as_completed(futures):
            name, status, detail = future.result()
            counts[status] += 1
            print(f'[{status.upper():7s}] {name}: {detail}')

    print(f"\nDone: {counts['done']} extracted, {counts['skipped']} skipped, "
          f"{counts['failed']} failed")
    return 1 if counts['failed'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
