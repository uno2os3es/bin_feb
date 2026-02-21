#!/data/data/com.termux/files/usr/bin/env python3
import argparse
import sys

import requests


def get_repos(username: str) -> None:
    url = f"https://api.github.com/users/{username}/repos"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 404:
            print(f"Error: User '{username}' not found.")
            sys.exit(1)
        response.raise_for_status()
        repos = response.json()
        if not repos:
            print(f"No public repositories found for user '{username}'.")
            return
        print(f"Repositories of '{username}':")
        for repo in repos:
            print(f"- {repo['name']}: {repo['html_url']}")
    except requests.RequestException as e:
        print(f"Error fetching repos: {e}")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Get GitHub repositories for a user")
    parser.add_argument(
        "username",
        type=str,
        help="GitHub username",
    )
    args = parser.parse_args()
    get_repos(args.username)


if __name__ == "__main__":
    main()
