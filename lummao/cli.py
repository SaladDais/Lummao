import sys

import lummao


def cli_main():
    if len(sys.argv) != 3:
        print("Usage:", sys.argv[0], "<input_file>", "<output_file>", file=sys.stderr)
        sys.exit(1)

    if sys.argv[1] == "-":
        in_bytes = sys.stdin.read()
    else:
        with open(sys.argv[1], "rb") as f:
            in_bytes = f.read()

    converted = lummao.convert_script(in_bytes)

    if sys.argv[2] == "-":
        sys.stdout.buffer.write(converted)
    else:
        with open(sys.argv[2], "wb") as f:
            f.write(converted)


if __name__ == "__main__":
    cli_main()
