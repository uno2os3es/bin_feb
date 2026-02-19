#!/data/data/com.termux/files/usr/bin/env python3
import argparse
import sys

import requests


def normalize_repo_address(repo_arg: str) -> str:
    """Convert input to 'user/repo' format."""
    if repo_arg.startswith("http://") or repo_arg.startswith("https://"):
        parts = repo_arg.rstrip("/").split("/")
        if len(parts) >= 5:
            return f"{parts[3]}/{parts[4]}"
        else:
            raise ValueError("Invalid GitHub URL format.")
    elif "/" in repo_arg:
        return repo_arg
    else:
        raise ValueError("Repo address must be URL or user/repo format.")


def get_repo_size(repo: str) -> int:
    """Fetch repo size in KB using GitHub API."""
    url = f"https://api.github.com/repos/{repo}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get("size", 0)
    elif response.status_code == 404:
        raise ValueError("Repository not found.")
    else:
        raise RuntimeError(f"GitHub API error: {response.status_code}")


def get_branches(repo: str) -> list:
    """Return list of branch names."""
    url = f"https://api.github.com/repos/{repo}/branches"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return [branch["name"] for branch in data]
    else:
        raise RuntimeError(f"Failed to fetch branches: {response.status_code}")


def get_branch_size(repo: str, branch: str) -> int:
    """Estimate branch size by summing sizes of all files in default tree."""
    url = f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        size_bytes = sum(item.get("size", 0) for item in data.get("tree", []) if item["type"] == "blob")
        return size_bytes // 1024
    else:
        raise RuntimeError(f"Failed to fetch branch tree: {branch}, status {response.status_code}")


def format_size(kb: int) -> str:
    """Return human-readable size."""
    mb = kb / 1024
    return f"{kb} KB ({mb:.2f} MB)"


def main() -> None:
    parser = argparse.ArgumentParser(description="Check GitHub repo size")
    parser.add_argument("repo", help="Repo URL or user/repo")
    parser.add_argument(
        "--all-branches",
        action="store_true",
        help="Show size of all branches",
    )
    args = parser.parse_args()

    try:
        repo = normalize_repo_address(args.repo)
        if args.all_branches:
            branches = get_branches(repo)
            for branch in branches:
                size_kb = get_branch_size(repo, branch)
                print(f"Branch '{branch}': {format_size(size_kb)}")
        else:
            size_kb = get_repo_size(repo)
            print(f"Repository '{repo}' size: {format_size(size_kb)}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
