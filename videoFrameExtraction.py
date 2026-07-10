import argparse
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


def hasVideoStream(filepath):
    '''Return True if ffprobe finds a video stream in the file.'''
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
         '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', str(filepath)],
        capture_output=True, text=True)
    return result.returncode == 0 and 'video' in result.stdout


def buildFfmpegCommand(videoPath, name, origDir, resizedDir, args):
    '''
    Build a single-pass ffmpeg command that decodes the video once and writes
    full-size frames (origDir) and/or resized frames (resizedDir).
    Either dir may be None if that output isn't wanted.
    '''
    blur = f'smartblur=luma_strength={args.blur}' if args.blur > 0 else None
    scale = f'scale={args.width}:-2'

    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin',
           '-i', str(videoPath)]

    def outputOpts(fmt):
        opts = ['-fps_mode', 'passthrough']
        if fmt in QUALITY_FORMATS:
            opts += ['-q:v', str(qualityToQscale(args.quality))]
        return opts

    origPattern = str(origDir / f'{name}.%04d.{args.extractionFormat}') if origDir else None
    resizedPattern = str(resizedDir / f'{name}.%04d.{args.finalFormat}') if resizedDir else None

    if origDir and resizedDir:
        # Decode and blur once, then split into a full-size and a resized stream
        chain = (blur + ',' if blur else '')
        cmd += ['-filter_complex',
                f'[0:v]{chain}split=2[full][pre];[pre]{scale}[small]',
                '-map', '[full]', *outputOpts(args.extractionFormat), origPattern,
                '-map', '[small]', *outputOpts(args.finalFormat), resizedPattern]
    elif origDir:
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

    Frames are written to <dir>.partial folders which are renamed into place
    only on success, so an interrupted run redoes incomplete videos instead
    of silently skipping them.
    '''
    name = videoPath.stem
    heightLabel = args.width * 3 // 4
    origDir = fullSetsDir / name
    resizedDir = fullSetsDir / f'{name}_RESIZED_{args.width}x{heightLabel}'

    # With single-pass extraction, "delete originals" means never writing them
    wantOrig = not (args.resize and args.deleteOriginals)
    wantResized = args.resize

    origTarget = origDir if wantOrig and not origDir.is_dir() else None
    resizedTarget = resizedDir if wantResized and not resizedDir.is_dir() else None
    if origTarget is None and resizedTarget is None:
        # Clean up any stale partial folders from an interrupted earlier run
        for stale in (d.with_name(d.name + '.partial') for d in (origDir, resizedDir)):
            if stale.exists():
                shutil.rmtree(stale)
        return (name, 'skipped', 'output folder(s) already exist')

    if not hasVideoStream(videoPath):
        return (name, 'skipped', 'no video stream (not a video file?)')

    partials = {}  # finalDir -> partialDir
    for finalDir in filter(None, [origTarget, resizedTarget]):
        partial = finalDir.with_name(finalDir.name + '.partial')
        if partial.exists():
            shutil.rmtree(partial)
        partial.mkdir(parents=True)
        partials[finalDir] = partial

    cmd = buildFfmpegCommand(
        videoPath, name,
        partials.get(origTarget), partials.get(resizedTarget), args)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        for partial in partials.values():
            shutil.rmtree(partial, ignore_errors=True)
        detail = result.stderr.strip().splitlines()
        return (name, 'failed', detail[-1] if detail else f'ffmpeg exit code {result.returncode}')

    for finalDir, partial in partials.items():
        partial.rename(finalDir)
    return (name, 'done', f'{len(partials)} output folder(s)')


def main():
    parser = argparse.ArgumentParser(
        description='Extract frames from all videos in a directory into '
                    f'./{FULL_SETS}/<vid>/ and resized copies into '
                    f'./{FULL_SETS}/<vid>_RESIZED_<w>x<h>/, in a single '
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
    parser.add_argument('--width', type=int, default=2400,
                        help='Width of the resized frames; height keeps aspect ratio (default: 2400)')
    parser.add_argument('--blur', type=float, default=0.25,
                        help='smartblur luma strength applied to all frames; 0 disables (default: 0.25)')
    parser.add_argument('--jobs', type=int, default=max(1, (os.cpu_count() or 2) // 2),
                        help='Number of videos to process in parallel '
                             '(default: half the logical cores)')
    args = parser.parse_args()

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
