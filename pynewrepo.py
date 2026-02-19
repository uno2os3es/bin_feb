#!/data/data/com.termux/files/usr/bin/env python3
"""
GitHub Repository Manager with gh CLI
Creates a new GitHub repo using gh CLI, auto-commits changes, and pushes to GitHub.
Handles existing repos by offering merge or new repo creation options.
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class GitHubRepoManager:
    def __init__(self, repo_name: str | None = None):
        """Initialize the GitHub Repository Manager."""
        self.current_dir = Path.cwd()
        self.repo_name = repo_name or self.current_dir.name
        self.github_username = "uno2os3es"
        self.git_email = "mkalafsaz@gmail.com"
        self.git_user = "uno2os3es"
        self.repo_url = f"https://github.com/{self.github_username}/{self.repo_name}. git"

    def _run_command(
        self,
        command: list,
        cwd: Path | None = None,
        capture_output: bool = False,
    ) -> tuple[int, str, str]:
        """Execute shell command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                command,
                check=False,
                cwd=cwd or self.current_dir,
                capture_output=capture_output,
                text=True,
            )
            stdout = result.stdout.strip() if result.stdout else ""
            stderr = result.stderr.strip() if result.stderr else ""
            return (
                result.returncode,
                stdout,
                stderr,
            )
        except Exception as e:
            print(f"Error executing command: {' '.join(command)}")
            print(f"Exception: {e}")
            return 1, "", str(e)

    def _check_gh_cli_installed(self) -> bool:
        """Check if GitHub CLI (gh) is installed."""
        returncode, _, _ = self._run_command(
            ["gh", "--version"],
            capture_output=True,
        )
        return returncode == 0

    def _check_gh_authenticated(self) -> bool:
        """Check if GitHub CLI is authenticated."""
        returncode, _, _ = self._run_command(
            ["gh", "auth", "status"],
            capture_output=True,
        )
        return returncode == 0

    def _repo_exists_locally(self) -> bool:
        """Check if git repo already exists in current directory."""
        git_dir = self.current_dir / ". git"
        return git_dir.exists()

    def _repo_exists_on_github(self) -> bool:
        """Check if repository exists on GitHub using gh CLI."""
        returncode, _, _ = self._run_command(
            [
                "gh",
                "repo",
                "view",
                f"{self.github_username}/{self.repo_name}",
            ],
            capture_output=True,
        )
        return returncode == 0

    def _get_remote_url(self) -> str | None:
        """Get the current remote URL."""
        returncode, stdout, _ = self._run_command(
            [
                "git",
                "config",
                "--get",
                "remote.origin.url",
            ],
            capture_output=True,
        )
        return stdout if returncode == 0 and stdout else None

    def _init_local_repo(self):
        """Initialize local git repository."""
        print(f"\n📦 Initializing local git repository in {self.current_dir}...")
        returncode, _stdout, stderr = self._run_command(
            ["git", "init"],
            capture_output=True,
        )
        if returncode != 0 and "Reinitialized" not in stderr and "Initialized" not in stderr:
            print(f"Error initializing git repo:    {stderr}")
            sys.exit(1)

        self._run_command(
            [
                "git",
                "config",
                "user. name",
                self.git_user,
            ],
            capture_output=True,
        )
        self._run_command(
            [
                "git",
                "config",
                "user.email",
                self.git_email,
            ],
            capture_output=True,
        )
        print("✓ Local repository initialized")

    def _create_github_repo(self):
        """Create repository on GitHub using gh CLI."""
        print(f"\n🌐 Creating repository on GitHub:  {self.repo_name}...")

        if self._repo_exists_on_github():
            print(f"✓ Repository {self.repo_name} already exists on GitHub")
            return True

        returncode, stdout, stderr = self._run_command(
            [
                "gh",
                "repo",
                "create",
                self.repo_name,
                "--source=.",
                "--remote=origin",
                "--public",
            ],
            capture_output=True,
        )

        if returncode != 0:
            print("Error creating repository on GitHub")
            print(f"stdout:  {stdout}")
            print(f"stderr: {stderr}")
            return False

        print("✓ Repository created on GitHub")
        return True

    def _stage_all_changes(self):
        """Stage all changes."""
        print("\n📝 Staging all changes...")
        returncode, _, stderr = self._run_command(
            ["git", "add", "."],
            capture_output=True,
        )
        if returncode != 0:
            print(f"Error staging changes:  {stderr}")
            sys.exit(1)
        print("✓ Changes staged")

    def _ensure_content(self):
        """Ensure there's at least one file to commit."""
        files = list(self.current_dir.glob("*"))
        hidden_files = list(self.current_dir.glob(".*"))

        files = [f for f in files if f.name != ".git"]
        hidden_files = [f for f in hidden_files if f.name not in [".git", ".", ".."]]

        has_content = len(files) > 0 or len(hidden_files) > 0

        if not has_content:
            print("📄 No files found, creating initial README. md...")
            readme = self.current_dir / "README.md"
            if not readme.exists():
                readme.write_text(
                    f"# {self.repo_name}\n\nRepository initialized on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                print("✓ Created README.md")
                return True

        return has_content

    def _commit_changes(self, message: str | None = None):
        """Commit staged changes."""
        if not message:
            message = self._generate_commit_message()

        print(f"\n💾 Committing changes with message: '{message}'")
        returncode, stdout, stderr = self._run_command(
            ["git", "commit", "-m", message],
            capture_output=True,
        )
        if returncode != 0:
            if "nothing to commit" in stderr or "nothing to commit" in stdout:
                print("⚠️  Nothing to commit")
                return False
            print(f"Error committing changes: {stderr}")
            return False
        print("✓ Changes committed")
        return True

    def _generate_commit_message(self) -> str:
        """Generate commit message with current date and time."""
        now = datetime.now()
        return now.strftime("Auto-commit: %Y-%m-%d %H:%M:%S")

    def _add_remote(self):
        """Add GitHub remote."""
        print(f"\n🔗 Adding remote:  {self.repo_url}")

        returncode, current_url, _ = self._run_command(
            [
                "git",
                "remote",
                "get-url",
                "origin",
            ],
            capture_output=True,
        )

        if returncode == 0 and current_url:
            if current_url == self.repo_url:
                print("✓ Remote 'origin' already configured correctly")
                return
            else:
                print(f"Updating remote URL from {current_url} to {self.repo_url}")
                self._run_command(
                    [
                        "git",
                        "remote",
                        "set-url",
                        "origin",
                        self.repo_url,
                    ],
                    capture_output=True,
                )
                return

        returncode, _, stderr = self._run_command(
            [
                "git",
                "remote",
                "add",
                "origin",
                self.repo_url,
            ],
            capture_output=True,
        )
        if returncode != 0:
            print(f"Error adding remote: {stderr}")
            sys.exit(1)
        print("✓ Remote added")

    def _push_to_github(self, branch: str = "main"):
        """Push commits to GitHub."""
        print(f"\n🚀 Pushing to GitHub ({branch} branch)...")

        returncode, stdout, stderr = self._run_command(
            [
                "git",
                "push",
                "-u",
                "origin",
                branch,
            ],
            capture_output=True,
        )

        if returncode != 0:
            print(f"stdout: {stdout}")
            print(f"stderr: {stderr}")
            if "permission denied" in stderr.lower():
                print("Error:  Permission denied.  Check your GitHub credentials.")
                sys.exit(1)
            elif "not found" in stderr.lower() or "does not appear" in stderr.lower():
                print(f"Note: Remote branch '{branch}' doesn't exist yet (creating on push)")
            else:
                print(f"Warning: Push encountered an issue: {stderr}")

        print("✓ Successfully pushed to GitHub")

    def _rename_branch_to_main(self):
        """Rename current branch to 'main' if it's not already."""
        returncode, current_branch, _ = self._run_command(
            [
                "git",
                "rev-parse",
                "--abbrev-ref",
                "HEAD",
            ],
            capture_output=True,
        )

        if returncode == 0 and current_branch and current_branch != "main":
            print(f"\n🔄 Renaming branch from '{current_branch}' to 'main'...")
            returncode, _, stderr = self._run_command(
                [
                    "git",
                    "branch",
                    "-M",
                    "main",
                ],
                capture_output=True,
            )
            if returncode != 0:
                print(f"Warning: Could not rename branch: {stderr}")

    def handle_existing_repo(self) -> bool:
        """Handle existing local repository."""
        print(f"\n⚠️  Git repository already exists in {self.current_dir}")

        current_remote = self._get_remote_url()
        print(f"Current remote: {current_remote or 'None'}")

        while True:
            print("\nOptions:")
            print("1. Merge changes (stage and commit to current repo)")
            print("2. Create new repository (enter new name)")
            print("3. Exit")

            choice = input("\nSelect option (1-3): ").strip()

            if choice == "1":
                print("✓ Using existing repository")
                return True
            elif choice == "2":
                self.repo_name = input("Enter new repository name: ").strip()
                if not self.repo_name:
                    print("Error: Repository name cannot be empty.")
                    continue
                self.repo_url = f"https://github.com/{self.github_username}/{self.repo_name}.git"
                print(f"✓ New repository name set:  {self.repo_name}")
                return False
            elif choice == "3":
                print("Exiting...")
                sys.exit(0)
            else:
                print("Invalid choice. Please select 1, 2, or 3.")

    def run(self):
        """Main execution method."""
        print("=" * 60)
        print("GitHub Repository Manager (with gh CLI)")
        print("=" * 60)
        print(f"Directory: {self.current_dir}")
        print(f"Repository:  {self.repo_name}")
        print(f"GitHub User: {self.github_username}")
        print(f"Email: {self.git_email}")
        print("=" * 60)

        if not self._check_gh_cli_installed():
            print("\n❌ Error: GitHub CLI (gh) is not installed.")
            print("Please install it from:  https://cli.github.com")
            sys.exit(1)

        if not self._check_gh_authenticated():
            print("\n❌ Error: GitHub CLI is not authenticated.")
            print("Please run:  gh auth login")
            sys.exit(1)

        print("\n✓ GitHub CLI is installed and authenticated\n")

        if self._repo_exists_locally():
            use_existing = self.handle_existing_repo()
            if not use_existing:
                self._run_command(
                    [
                        "git",
                        "remote",
                        "remove",
                        "origin",
                    ],
                    capture_output=True,
                )
        else:
            self._init_local_repo()

        self._ensure_content()

        self._stage_all_changes()

        if self._commit_changes():
            self._rename_branch_to_main()

            if self._create_github_repo():
                self._add_remote()

                self._push_to_github()

                print("\n" + "=" * 60)
                print("✅ Success! Repository created and pushed to GitHub")
                print(f"Repository URL: https://github.com/{self.github_username}/{self.repo_name}")
                print("=" * 60)
            else:
                print("\n❌ Failed to create repository on GitHub")
                sys.exit(1)
        else:
            print("\n⚠️  Could not commit changes.")
            sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create a GitHub repository using gh CLI and auto-commit with current date/time"
    )
    parser.add_argument(
        "-n",
        "--name",
        help="Repository name (default: current directory name)",
        type=str,
    )
    parser.add_argument(
        "-m",
        "--message",
        help="Custom commit message (default: auto-generated with timestamp)",
        type=str,
    )

    args = parser.parse_args()

    try:
        manager = GitHubRepoManager(repo_name=args.name)
        manager.run()
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
