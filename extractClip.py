import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def parseTime(value):
    '''
    Parse a time given as plain seconds ("90", "90.5") or as H:MM:SS /
    MM:SS ("1:30", "01:02:03.5") into seconds.
    '''
    if ':' not in value:
        return float(value)
    parts = value.split(':')
    if len(parts) > 3:
        raise ValueError(f'invalid time: {value}')
    seconds = 0.0
    for part in parts:
        seconds = seconds * 60 + float(part)
    return seconds


def formatSeconds(seconds):
    '''Format seconds for use in a filename, dropping a trailing .0.'''
    if seconds == int(seconds):
        return str(int(seconds))
    return f'{seconds:.3f}'.rstrip('0').rstrip('.')


def main():
    parser = argparse.ArgumentParser(
        description='Extract a time range from a video as a new mp4, or (with --audio) '
                    'as an mp3. With no --start/--end/--duration, extracts the full '
                    'input (as a plain copy for video, or the full audio track for '
                    '--audio).')
    parser.add_argument('input', help='Input video file')
    parser.add_argument('--start', type=parseTime, default=None,
                        help='Start time, as seconds or H:MM:SS(.ms) (default: 0)')
    parser.add_argument('--end', type=parseTime, default=None,
                        help='End time, as seconds or H:MM:SS(.ms) (default: end of file)')
    parser.add_argument('--duration', type=parseTime, default=None,
                        help='Duration to extract, as seconds or H:MM:SS(.ms), '
                             'alternative to --end')
    parser.add_argument('--audio', action='store_true',
                        help='Extract audio only, as mp3, instead of a video clip')
    parser.add_argument('--fast', action='store_true',
                        help='Stream-copy the video instead of re-encoding it: instant, '
                             'but the start may snap to the nearest keyframe. Invalid '
                             'with --audio, which always re-encodes to mp3.')
    parser.add_argument('--output', default=None,
                        help='Output file path (default: derived from the input name '
                             'and time range)')
    args = parser.parse_args()

    if args.end is not None and args.duration is not None:
        parser.error('provide either --end or --duration, not both')
    if args.fast and args.audio:
        parser.error('--fast has no effect with --audio')
    if args.start is not None and args.start < 0:
        parser.error('--start must be >= 0')
    if args.duration is not None and args.duration <= 0:
        parser.error('--duration must be > 0')

    inputPath = Path(args.input)
    if not inputPath.is_file():
        print(f'Not found: {inputPath}', file=sys.stderr)
        return 1

    resolvedStart = args.start if args.start is not None else 0.0
    if args.end is not None and args.end <= resolvedStart:
        parser.error('--end must be after --start')

    hasEnd = args.end is not None or args.duration is not None
    fullRange = args.start is None and not hasEnd

    ext = 'mp3' if args.audio else 'mp4'
    if fullRange:
        suffix = 'full'
    else:
        startLabel = formatSeconds(resolvedStart)
        if args.end is not None:
            endLabel = formatSeconds(args.end)
        elif args.duration is not None:
            endLabel = formatSeconds(resolvedStart + args.duration)
        else:
            endLabel = 'end'
        suffix = f'{startLabel}-{endLabel}'

    outputPath = Path(args.output) if args.output else \
        inputPath.with_name(f'{inputPath.stem}_{suffix}.{ext}')

    if not args.audio and fullRange:
        # No trim requested at all: a plain copy is faster and lossless
        # compared to remuxing or re-encoding through ffmpeg.
        shutil.copy2(inputPath, outputPath)
        print(f'Wrote {outputPath} (no trim requested, copied as-is)')
        return 0

    if args.end is not None:
        ffmpegDuration = args.end - resolvedStart
    elif args.duration is not None:
        ffmpegDuration = args.duration
    else:
        ffmpegDuration = None

    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-y']
    if args.start is not None:
        cmd += ['-ss', str(resolvedStart)]
    cmd += ['-i', str(inputPath)]
    if ffmpegDuration is not None:
        cmd += ['-t', str(ffmpegDuration)]

    if args.audio:
        cmd += ['-vn', '-c:a', 'libmp3lame', '-q:a', '2']
    elif args.fast:
        cmd += ['-c', 'copy']
    else:
        cmd += ['-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', '-c:a', 'copy']
    cmd += [str(outputPath)]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr.strip(), file=sys.stderr)
        return 1

    print(f'Wrote {outputPath}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
