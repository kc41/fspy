from os import path
from fspy.agent import runner
from fspy.common import defaults
import argparse


def main():
    parser = argparse.ArgumentParser("FSPY client")
    parser.add_argument("--target", type=str, help="Directory to scan", required=True)
    parser.add_argument("--server_host", type=str, help="FSPY server hostname/IP", default="127.0.0.1")
    parser.add_argument("--server_port", type=int, help="FSPY server port", default=defaults.DEFAULT_PORT)

    args = parser.parse_args()

    ws_url = f"ws://{args.server_host}:{args.server_port}/ws"
    target = path.abspath(args.target)

    if not path.isdir(target):
        print(f"{target} is not a directory")

    runner.main(ws_url=ws_url, scan_target=target)


if __name__ == '__main__':
    main()
