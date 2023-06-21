import argparse
from pathlib import Path
import time
from subprocess import TimeoutExpired

from plumbum import local


def call_rsync(source: str, target: str, communication_folder: str):
    communication_folder = Path(communication_folder)
    from_file = communication_folder / "filelist.txt"
    abort_file = communication_folder / "abort"
    log_file = communication_folder / "log.txt"
    
    rsync = local["rsync"]

    process = rsync.popen([
        "-avr",
        "--ignore-missing-args",
        f"--files-from={from_file}",
        f"--log-file={log_file}",
        source,
        target
    ])
    try:
        process.communicate(timeout=1)
    except TimeoutExpired:
        pass

    while process.poll() is None:
        if abort_file.exists():
            process.terminate()
            break
        time.sleep(2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "source",
        help="The source directory. [eg. zmcjbomm@hawk.bla.bla:/lustre/bla/bla]",
        type=str
    )
    parser.add_argument(
        "target",
        help="The target directory. [eg. /mnt]",
        type=str
    )
    parser.add_argument(
        "communication_folder",
        help="The folder for process communication.",
        type=str
    )

    args = parser.parse_args()

    call_rsync(args.source, args.target, args.communication_folder)


if __name__ == "__main__":
    main()