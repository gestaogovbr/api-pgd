#!/usr/bin/env python3

"""
Generate fief initial credentials and create a `../.env` file based on
.env.template file content.
"""

import os
import subprocess
import secrets
import re
import argparse
from getpass import getpass


def generate_fief_env_vars(email: str, password: str) -> str:
    """Run docker fief image to auto generete initial credentials.

    Args:
        email (str): string like `default@foo.com`
        password (str): string like `abcde*12345`

    Returns:
        str: shell output with fief credentials created
    """

    cmd = [
        "docker",
        "run",
        "--name",
        "fief-init",
        "ghcr.io/fief-dev/fief:0.27",
        "fief",
        "quickstart",
        "--docker",
        "--user-email",
        email,
        "--user-password",
        password,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    subprocess.run(["docker", "rm", "fief-init"])

    return result.stdout


def parse_cmd_stdout(cmd_stdout: str) -> dict:
    """Filter fief quickstart shell output and parse to a dictionay only
    the content about env variables.

    Args:
        cmd_stdout (str): fief quickstart shell output

    Returns:
        dict: shell output filtered only with env values
    """

    env_lines = re.findall(r'-e "(.*?)"', cmd_stdout)
    env_dict = {}

    for line in env_lines:
        key, value = line.split("=", 1)
        env_dict[key] = value

    return env_dict


def create_dot_env(env_dict: dict) -> str:
    """Get the file `.env.template`, update with `env_dict` and save at
    `../.env`.

    Args:
        env_dict (dict): updated env credentials to be stored

    Returns:
        str: .env file created content
    """

    def _update_environment_variables(input_list: list, new_values: dict) -> list:
        """Update origin `.env.template` list with env variables at
        `new_values`.

        Args:
            input_list (list): `.env.template` file content parsed as list
            new_values (dict): generated env variables

        Returns:
            list: of a updated `.env.template` envs values
        """

        # XXX can improve?
        output_list = input_list
        for i, line in enumerate(input_list):
            for key, value in new_values.items():
                if line.startswith(f"{key}="):
                    output_list[i] = f"{key}={value}\n"
                    break

        return output_list

    # read, update content string
    init_dir = os.path.dirname(__file__)
    with open(os.path.join(init_dir, ".env.template"), "r") as f:
        env_list_updated = _update_environment_variables(f.readlines(), env_dict)

    # save
    with open(os.path.join(init_dir, "..", ".env"), "w") as f:
        for line in env_list_updated:
            f.write(line + "\n")

    return "".join(env_list_updated)


def main(
    email: str = "default@foo.com",
    password: str = "abcde*12345",
    fief_main_admin_api_key: str = None,
):
    parser = argparse.ArgumentParser(
        description="Script with optional email and password parameter"
    )
    parser.add_argument(
        "-it",
        "--input_prompt",
        action="store_true",
        help="Enable input email and password prompt",
    )
    args = parser.parse_args()

    if args.input_prompt:
        email = input("email: ")
        password = getpass()
        fief_main_admin_api_key = input(
            "FIEF_MAIN_API_KEY [leave blank if want auto-generated]: "
        )

    cmd_stdout = generate_fief_env_vars(email, password)
    env_dict = parse_cmd_stdout(cmd_stdout)
    env_dict["FIEF_MAIN_ADMIN_API_KEY"] = (
        fief_main_admin_api_key if fief_main_admin_api_key else secrets.token_urlsafe()
    )

    r = create_dot_env(env_dict)
    print("\n[INFO] .env file created at ../.env\n")
    print(r)


if __name__ == "__main__":
    main()
