"""Budget Ninja against the hosted job deadline, reserving checkpoint time."""
import argparse
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--elapsed-seconds', type=int, required=True)
    parser.add_argument('--requested-minutes', type=int, default=270)
    args = parser.parse_args()
    remaining = 350 * 60 - max(0, args.elapsed_seconds) - 45 * 60
    seconds = min(args.requested_minutes * 60, remaining)
    if seconds < 60:
        print('Insufficient job time; preserve the restored checkpoint without compiling.', file=sys.stderr)
        return 1
    print(seconds)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
