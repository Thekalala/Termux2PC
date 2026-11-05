
import argparse
import json
import sys

import requests

from client.android import deploy_and_run, request_run


def main():

    parser = argparse.ArgumentParser(
        description="Termux2PC - Android to Windows"
    )

    commands = parser.add_subparsers(
        dest="command",
        required=True
    )

    deploy = commands.add_parser("deploy")
    deploy.add_argument("path")

    run = commands.add_parser("run")
    run.add_argument("project")

    args = parser.parse_args()

    try:

        if args.command == "deploy":
            result = deploy_and_run(args.path)

        elif args.command == "run":
            result = request_run(args.project)

        print(json.dumps(
            result,
            indent=4,
            ensure_ascii=False
        ))

        return 0

    except requests.HTTPError as error:

        response = error.response

        print(
            f"HTTP error: {response.status_code}",
            file=sys.stderr
        )

        try:
            details = response.json()
        except ValueError:
            details = response.text

        print(
            json.dumps(details, indent=4, ensure_ascii=False)
            if isinstance(details, (dict, list))
            else details,
            file=sys.stderr
        )

        return 1

    except requests.Timeout:

        print(
            "Error: Windows server timed out.",
            file=sys.stderr
        )
        return 1

    except requests.ConnectionError:

        print(
            "Error: Could not connect to Windows server.",
            file=sys.stderr
        )
        return 1

    except KeyboardInterrupt:

        print("\nOperation cancelled.")
        return 130

    except (ValueError, PermissionError, FileNotFoundError) as error:

        print(f"Error: {error}", file=sys.stderr)
        return 1

    except Exception as error:

        print(
            f"Unexpected error: {type(error).__name__}: {error}",
            file=sys.stderr
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
