import argparse
import itertools
import json
import subprocess
import sys
import tempfile
from pathlib import Path

OUTPUT_NAME = 'combined.mp4'


def probeDims(filepath):
    '''
    Return the display dimensions (width, height) of the file's video stream,
    or None if it has no video stream.
    '''
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
         '-show_entries', 'stream=width,height',
         '-of', 'json', str(filepath)],
        capture_output=True, text=True)
    if result.returncode != 0:
        return None
    try:
        stream = json.loads(result.stdout)['streams'][0]
        return int(stream['width']), int(stream['height'])
    except (KeyError, IndexError, ValueError, json.JSONDecodeError):
        return None


def findDefaultVideos():
    '''
    Return 1.mp4, 2.mp4, ... for as many consecutively-numbered files exist
    in the current directory.
    '''
    videos = []
    for i in itertools.count(1):
        candidate = Path(f'{i}.mp4')
        if not candidate.is_file():
            break
        videos.append(candidate)
    return videos


def main():
    parser = argparse.ArgumentParser(
        description='Concatenate videos (assumed to share the same encoding) into '
                    f'{OUTPUT_NAME}. With no arguments, uses 1.mp4, 2.mp4, ... for as '
                    'many such files exist in the current directory.')
    parser.add_argument('videos', nargs='*',
                        help='Video files to concatenate, in order (default: 1.mp4, 2.mp4, ...)')
    args = parser.parse_args()

    videos = [Path(v) for v in args.videos] if args.videos else findDefaultVideos()

    if len(videos) < 2:
        print(f'Need at least 2 videos to concatenate, found {len(videos)}', file=sys.stderr)
        return 1

    for video in videos:
        if not video.is_file():
            print(f'Not found: {video}', file=sys.stderr)
            return 1

    dims = {}
    for video in videos:
        d = probeDims(video)
        if d is None:
            print(f'Could not read video stream from: {video}', file=sys.stderr)
            return 1
        dims[video] = d

    firstDims = dims[videos[0]]
    mismatched = [v for v in videos if dims[v] != firstDims]
    if mismatched:
        print(f'All videos must share the same dimensions ({firstDims[0]}x{firstDims[1]}), '
              'but found:', file=sys.stderr)
        for v in videos:
            print(f'  {v}: {dims[v][0]}x{dims[v][1]}', file=sys.stderr)
        return 1

    print(f'Concatenating {len(videos)} video(s) ({firstDims[0]}x{firstDims[1]}) into {OUTPUT_NAME}')
    for v in videos:
        print(f'  {v}')

    with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as listFile:
        for video in videos:
            escaped = str(video.resolve()).replace("'", "'\\''")
            listFile.write(f"file '{escaped}'\n")
        listPath = listFile.name

    try:
        cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-y',
               '-f', 'concat', '-safe', '0', '-i', listPath, '-c', 'copy', OUTPUT_NAME]
        result = subprocess.run(cmd, capture_output=True, text=True)
    finally:
        Path(listPath).unlink(missing_ok=True)

    if result.returncode != 0:
        print(result.stderr.strip(), file=sys.stderr)
        return 1

    print(f'Wrote {OUTPUT_NAME}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
