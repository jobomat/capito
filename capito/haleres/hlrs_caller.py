import argparse

import hlrs


HLRS = hlrs.HLRS()

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