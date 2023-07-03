import argparse
import sys

sys.path.append("/mnt/cg/pipeline/capito")

import hlrs


HLRS = hlrs.HLRS("/mnt/cg/pipeline/hlrs/settings.json")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "inputs",
        nargs='+',
        help="The hlrs class method calls",
    )
    args = parser.parse_args()

    output = []
    for input in args.inputs:
        output.append(eval(f"HLRS.{input}"))
    print(output)

if __name__ == "__main__":
    main()