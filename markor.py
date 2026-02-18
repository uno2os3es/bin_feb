#!/data/data/com.termux/files/usr/bin/env python3
"""
Markor - A Markdown/Text Editor for Termux using termux-gui-python-bindings
Implements core features: file management, markdown editing, preview, and todo list management
"""

import sys
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

import markdown


class GUIFramework:
    """Wrapper for termux-gui-python-bindings."""

    def __init__(self):
        """Initialize GUI Framework."""
        self.session_id = None
        self.dialogs = {}

    def show_dialog(self, title: str, message: str, buttons: list[str] | None = None) -> int:
        """
        Show a dialog box.

        Args:
            title: Dialog title
            message: Message text
            buttons: List of button labels

        Returns:
            Button index selected (0-based)
        """
        if buttons is None:
            buttons = ["OK"]
        print(f"\n{'=' * 50}")
        print(f"[{title}]")
        print(f"{message}")
        print(f"{'=' * 50}")
        for i, btn in enumerate(buttons):
            print(f"{i}: {btn}")

        choice = input("Select option: ").strip()
        return int(choice) if choice.isdigit() else 0

    def show_text_input(self, title: str, hint: str = "", multi_line: bool = False) -> str | None:
        """
        Show text input dialog.

        Args:
            title: Dialog title
            hint: Input hint
            multi_line: Allow multiple lines

        Returns:
            User input text or None if cancelled
        """
        print(f"\n[{title}]")
        if hint:
            print(f"Hint: {hint}")

        if multi_line:
            print("Enter text (type 'END' on new line to finish):")
            lines = []
            while True:
                line = input()
                if line == "END":
                    break
                lines.append(line)
            return "\n".join(lines) if lines else None
        else:
            return input("Input: ").strip() or None

    def show_file_picker(self, initial_path: str | None = None) -> str | None:
        """
        Show file picker dialog.

        Args:
            initial_path: Starting directory

        Returns:
            Selected file path or None
        """
        if initial_path is None:
            initial_path = str(Path.home())

        return input(f"Enter file path (starting from {initial_path}): ").strip() or None

    def show_toast(self, message: str):
        """Show toast notification."""
        print(f"[Toast] {message}")

    def show_menu(self, title: str, items: list[str]) -> int:
        """
        Show menu.

        Args:
            title: Menu title
            items: Menu items

        Returns:
            Selected item index
        """
        print(f"\n[{title}]")
        for i, item in enumerate(items):
            print(f"{i}: {item}")

        choice = input("Select: ").strip()
        return int(choice) if choice.isdigit() else -1

    def show_snackbar(self, message: str, action: str | None = None):
        """Show snackbar notification."""
        msg = f"[Snackbar] {message}"
        if action:
            msg += f" [{action}]"
        print(msg)


class DocumentFormat(ABC):
    """Abstract base class for document formats."""

    @abstractmethod
    def get_syntax_highlight_rules(self) -> dict[str, str]:
        """Get syntax highlighting rules."""

    @abstractmethod
    def get_preview(self, content: str) -> str:
        """Get preview of content."""

    @abstractmethod
    def get_format_actions(self) -> list[str]:
        """Get format-specific quick actions."""


class MarkdownFormat(DocumentFormat):
    """Markdown format support."""

    def get_syntax_highlight_rules(self) -> dict[str, str]:
        """Get markdown syntax highlighting rules."""
        return {
            "heading1": r"^# .*$",
            "heading2": r"^## .*$",
            "heading3": r"^### .*$",
            "bold": r"\*\*.*?\*\*",
            "italic": r"\*.*?\*",
            "code": r"`.*?`",
            "codeblock": r"```.*?```",
            "link": r"\[.*?\]\(.*?\)",
            "image": r"!\[.*?\]\(.*?\)",
            "list": r"^[\*\-\+] .*$",
            "blockquote": r"^> .*$",
        }

    def get_preview(self, content: str) -> str:
        """Convert markdown to HTML preview."""
        try:
            return markdown.markdown(content)
        except Exception as e:
            return f"<p>Error rendering preview: {e!s}</p>"

    def get_format_actions(self) -> list[str]:
        """Get markdown quick actions."""
        return [
            "Insert Heading",
            "Insert Bold",
            "Insert Italic",
            "Insert Code Block",
            "Insert Link",
            "Insert Image",
            "Insert List",
            "Insert Table",
        ]


class TodoFormat(DocumentFormat):
    """todo.txt format support."""

    def get_syntax_highlight_rules(self) -> dict[str, str]:
        """Get todo.txt syntax highlighting rules."""
        return {
            "completed": r"^\(x\) .*$",
            "incomplete": r"^\(\) .*$",
            "priority_a": r"^\(A\) .*$",
            "priority_b": r"^\(B\) .*$",
            "priority_c": r"^\(C\) .*$",
            "project": r"\+\w+",
            "context": r"@\w+",
            "date": r"\d{4}-\d{2}-\d{2}",
        }

    def get_preview(self, content: str) -> str:
        """Generate todo.txt preview."""
        lines = content.split("\n")
        preview = []

        for line in lines:
            if line.startswith("(x)"):
                preview.append(f"✓ {line[4:]}")
            elif line.startswith("(A)"):
                preview.append(f"!!! {line[4:]} (Priority A)")
            elif line.startswith("(B)"):
                preview.append(f"!! {line[4:]} (Priority B)")
            elif line.startswith("(C)"):
                preview.append(f"! {line[4:]} (Priority C)")
            else:
                preview.append(line)

        return "\n".join(preview)

    def get_format_actions(self) -> list[str]:
        """Get todo.txt quick actions."""
        return [
            "Insert Task",
            "Toggle Completion",
            "Set Priority A",
            "Set Priority B",
            "Set Priority C",
            "Add Project Tag",
            "Add Context Tag",
        ]


class Document:
    """Represents a document file."""

    def __init__(self, file_path: str, format_type: str = "markdown"):
        """
        Initialize Document.

        Args:
            file_path: Path to document file
            format_type: Document format ('markdown', 'todo', 'text', 'json')
        """
        self.file_path = Path(file_path)
        self.format_type = format_type
        self.content = ""
        self.last_modified = None
        self.format_handler = self._get_format_handler()
        self._load()

    def _get_format_handler(self) -> DocumentFormat:
        """Get appropriate format handler."""
        if self.format_type == "markdown":
            return MarkdownFormat()
        elif self.format_type == "todo":
            return TodoFormat()
        else:
            return MarkdownFormat()  # Default to markdown

    def _load(self):
        """Load document from file."""
        if self.file_path.exists():
            self.content = self.file_path.read_text(encoding="utf-8")
            self.last_modified = datetime.fromtimestamp(self.file_path.stat().st_mtime)

    def save(self) -> bool:
        """Save document to file."""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self.file_path.write_text(self.content, encoding="utf-8")
            self.last_modified = datetime.now()
            return True
        except Exception as e:
            print(f"Error saving file: {e}")
            return False

    def get_preview(self) -> str:
        """Get document preview."""
        return self.format_handler.get_preview(self.content)

    def get_syntax_rules(self) -> dict[str, str]:
        """Get syntax highlighting rules."""
        return self.format_handler.get_syntax_highlight_rules()

    def get_quick_actions(self) -> list[str]:
        """Get format-specific quick actions."""
        return self.format_handler.get_format_actions()

    def insert_text(self, text: str, position: int | None = None):
        """Insert text at position."""
        if position is None:
            position = len(self.content)
        self.content = self.content[:position] + text + self.content[position:]

    def replace_text(self, old: str, new: str) -> int:
        """Replace all occurrences of text."""
        count = self.content.count(old)
        self.content = self.content.replace(old, new)
        return count

    def get_word_count(self) -> int:
        """Get word count."""
        return len(self.content.split())

    def get_char_count(self) -> int:
        """Get character count."""
        return len(self.content)

    def get_line_count(self) -> int:
        """Get line count."""
        return len(self.content.split("\n"))

    def get_info(self) -> dict[str, Any]:
        """Get document information."""
        return {
            "name": self.file_path.name,
            "path": str(self.file_path),
            "size_bytes": self.file_path.stat().st_size if self.file_path.exists() else 0,
            "format": self.format_type,
            "words": self.get_word_count(),
            "characters": self.get_char_count(),
            "lines": self.get_line_count(),
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
        }


class FileManager:
    """Manages documents and folders."""

    def __init__(self, root_path: str | None = None):
        """
        Initialize FileManager.

        Args:
            root_path: Root directory for documents
        """
        if root_path is None:
            root_path = str(Path.home() / "Documents" / "Markor")

        self.root_path = Path(root_path)
        self.root_path.mkdir(parents=True, exist_ok=True)

    def create_document(self, name: str, format_type: str = "markdown", parent_dir: str | None = None) -> Document:
        """Create a new document."""
        file_path = self.root_path / f"{name}.md" if parent_dir is None else self.root_path / parent_dir / f"{name}.md"

        doc = Document(str(file_path), format_type=format_type)
        doc.save()
        return doc

    def open_document(self, relative_path: str) -> Document | None:
        """Open an existing document."""
        file_path = self.root_path / relative_path

        if not file_path.exists():
            return None

        # Detect format from extension
        ext = file_path.suffix.lower()
        if ext == ".md":
            format_type = "markdown"
        elif ext == ".txt" and "todo" in file_path.name.lower():
            format_type = "todo"
        elif ext == ".json":
            format_type = "json"
        else:
            format_type = "text"

        return Document(str(file_path), format_type=format_type)

    def delete_document(self, relative_path: str) -> bool:
        """Delete a document."""
        file_path = self.root_path / relative_path
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def list_documents(self, folder: str | None = None, recursive: bool = False) -> list[dict[str, Any]]:
        """List documents."""
        search_path = self.root_path / folder if folder else self.root_path

        if not search_path.exists():
            return []

        documents = []
        pattern = "**/*" if recursive else "*"

        for file_path in search_path.glob(pattern):
            if file_path.is_file() and file_path.suffix in [".md", ".txt", ".json"]:
                documents.append(
                    {
                        "name": file_path.name,
                        "path": str(file_path.relative_to(self.root_path)),
                        "size": file_path.stat().st_size,
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    }
                )

        return sorted(documents, key=lambda x: x["name"])

    def create_folder(self, name: str, parent_dir: str | None = None) -> bool:
        """Create a new folder."""
        folder_path = self.root_path / parent_dir / name if parent_dir else self.root_path / name

        folder_path.mkdir(parents=True, exist_ok=True)
        return True

    def list_folders(self, parent_dir: str | None = None) -> list[str]:
        """List folders."""
        search_path = self.root_path / parent_dir if parent_dir else self.root_path

        if not search_path.exists():
            return []

        folders = [d.name for d in search_path.iterdir() if d.is_dir()]
        return sorted(folders)

    def search_documents(self, query: str, search_content: bool = False) -> list[dict[str, Any]]:
        """Search documents by name or content."""
        results = []

        for doc_info in self.list_documents(recursive=True):
            # Search by filename
            if query.lower() in doc_info["name"].lower():
                results.append(doc_info)

            # Search by content
            elif search_content:
                doc = self.open_document(doc_info["path"])
                if doc and query.lower() in doc.content.lower():
                    results.append(doc_info)

        return results

    def get_recent_documents(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recently modified documents."""
        docs = self.list_documents(recursive=True)
        docs.sort(key=lambda x: x["modified"], reverse=True)
        return docs[:limit]


class TextEditor:
    """Main text editor UI."""

    def __init__(self):
        """Initialize text editor."""
        self.gui = GUIFramework()
        self.file_manager = FileManager()
        self.current_document: Document | None = None
        self.undo_stack = []
        self.redo_stack = []
        self.is_modified = False

    def run(self):
        """Run the editor main loop."""
        while True:
            if self.current_document is None:
                self.show_home_screen()
            else:
                self.show_editor_screen()

    def show_home_screen(self):
        """Show home/file browser screen."""
        menu_items = [
            "New Document",
            "Open Document",
            "Recent Documents",
            "Search",
            "Manage Folders",
            "Settings",
            "Exit",
        ]

        choice = self.gui.show_menu("Markor - Text Editor", menu_items)

        if choice == 0:
            self.create_new_document()
        elif choice == 1:
            self.open_document()
        elif choice == 2:
            self.show_recent_documents()
        elif choice == 3:
            self.search_documents()
        elif choice == 4:
            self.manage_folders()
        elif choice == 5:
            self.show_settings()
        elif choice == 6:
            sys.exit(0)

    def create_new_document(self):
        """Create a new document."""
        name = self.gui.show_text_input("New Document", "Enter document name")
        if not name:
            return

        format_choice = self.gui.show_menu(
            "Select Format", ["Markdown (.md)", "Todo List (.txt)", "Plain Text (.txt)", "JSON (.json)"]
        )

        formats = ["markdown", "todo", "text", "json"]
        format_type = formats[format_choice] if 0 <= format_choice < len(formats) else "markdown"

        self.current_document = self.file_manager.create_document(name, format_type=format_type)
        self.gui.show_toast(f"Created: {name}")

    def open_document(self):
        """Open an existing document."""
        docs = self.file_manager.list_documents(recursive=True)

        if not docs:
            self.gui.show_dialog("No Documents", "No documents found")
            return

        doc_names = [doc["name"] for doc in docs]
        choice = self.gui.show_menu("Open Document", doc_names)

        if 0 <= choice < len(docs):
            self.current_document = self.file_manager.open_document(docs[choice]["path"])
            if self.current_document:
                self.gui.show_toast(f"Opened: {docs[choice]['name']}")

    def show_recent_documents(self):
        """Show recently modified documents."""
        recent = self.file_manager.get_recent_documents()

        if not recent:
            self.gui.show_dialog("No Recent Documents", "No recent documents found")
            return

        doc_names = [doc["name"] for doc in recent]
        choice = self.gui.show_menu("Recent Documents", doc_names)

        if 0 <= choice < len(recent):
            self.current_document = self.file_manager.open_document(recent[choice]["path"])
            if self.current_document:
                self.gui.show_toast(f"Opened: {recent[choice]['name']}")

    def search_documents(self):
        """Search documents."""
        query = self.gui.show_text_input("Search", "Enter search query")
        if not query:
            return

        search_content = (
            self.gui.show_dialog(
                "Search Scope", "Search in filenames only or file content?", ["Filenames Only", "Content Too"]
            )
            == 1
        )

        results = self.file_manager.search_documents(query, search_content=search_content)

        if not results:
            self.gui.show_dialog("No Results", f"No documents found matching '{query}'")
            return

        result_names = [r["name"] for r in results]
        choice = self.gui.show_menu("Search Results", result_names)

        if 0 <= choice < len(results):
            self.current_document = self.file_manager.open_document(results[choice]["path"])

    def manage_folders(self):
        """Manage folders."""
        menu_items = ["Create Folder", "List Folders", "Back to Home"]

        choice = self.gui.show_menu("Manage Folders", menu_items)

        if choice == 0:
            folder_name = self.gui.show_text_input("New Folder", "Enter folder name")
            if folder_name:
                self.file_manager.create_folder(folder_name)
                self.gui.show_toast(f"Created folder: {folder_name}")
        elif choice == 1:
            folders = self.file_manager.list_folders()
            if folders:
                self.gui.show_dialog("Folders", "Folders:\n" + "\n".join(folders))
            else:
                self.gui.show_dialog("No Folders", "No folders found")

    def show_editor_screen(self):
        """Show editor screen."""
        doc_name = self.current_document.file_path.name
        menu_items = [
            "Edit",
            "View Preview",
            "Insert Template",
            "Format Actions",
            "Find & Replace",
            "Document Info",
            "Save",
            "Close Document",
        ]

        choice = self.gui.show_menu(f"Editor - {doc_name}", menu_items)

        if choice == 0:
            self.edit_document()
        elif choice == 1:
            self.show_preview()
        elif choice == 2:
            self.insert_template()
        elif choice == 3:
            self.show_format_actions()
        elif choice == 4:
            self.find_and_replace()
        elif choice == 5:
            self.show_document_info()
        elif choice == 6:
            self.save_document()
        elif choice == 7:
            self.close_document()

    def edit_document(self):
        """Edit document content."""
        print(f"\n{'=' * 50}")
        print(f"Editing: {self.current_document.file_path.name}")
        print(f"Current content ({self.current_document.get_line_count()} lines):")
        print(f"{'=' * 50}")
        print(self.current_document.content[:500] + ("..." if len(self.current_document.content) > 500 else ""))
        print(f"{'=' * 50}")

        edit_choice = self.gui.show_menu("Edit Options", ["View Full", "Edit Full", "Append", "Back"])

        if edit_choice == 0:
            print("\n" + self.current_document.content)
        elif edit_choice == 1:
            new_content = self.gui.show_text_input("Edit Content", "", multi_line=True)
            if new_content is not None:
                self.current_document.content = new_content
                self.is_modified = True
        elif edit_choice == 2:
            append_text = self.gui.show_text_input("Append Text", "", multi_line=True)
            if append_text:
                self.current_document.content += "\n" + append_text
                self.is_modified = True

    def show_preview(self):
        """Show document preview."""
        preview = self.current_document.get_preview()

        print(f"\n{'=' * 50}")
        print(f"Preview: {self.current_document.file_path.name}")
        print(f"{'=' * 50}")
        print(preview)
        print(f"{'=' * 50}")

        input("Press Enter to continue...")

    def insert_template(self):
        """Insert format templates."""
        templates = {
            "markdown": {
                "H1": "# Heading 1",
                "H2": "## Heading 2",
                "Bold": "**bold text**",
                "Italic": "*italic text*",
                "Code": "`code`",
                "Link": "[Link](url)",
                "List": "- Item 1\n- Item 2\n- Item 3",
                "Table": "| Col1 | Col2 |\n|------|------|\n| A    | B    |",
            },
            "todo": {
                "Task": "() New task",
                "Completed": "(x) Completed task",
                "Priority A": "(A) High priority task",
                "Priority B": "(B) Medium priority task",
                "With Project": "() Task +ProjectName",
                "With Context": "() Task @ContextTag",
            },
        }

        format_type = self.current_document.format_type
        if format_type not in templates:
            self.gui.show_toast("No templates available for this format")
            return

        template_names = list(templates[format_type].keys())
        choice = self.gui.show_menu("Insert Template", template_names)

        if 0 <= choice < len(template_names):
            template_name = template_names[choice]
            template_text = templates[format_type][template_name]
            self.current_document.insert_text("\n" + template_text)
            self.is_modified = True
            self.gui.show_toast(f"Inserted: {template_name}")

    def show_format_actions(self):
        """Show format-specific quick actions."""
        actions = self.current_document.get_quick_actions()
        choice = self.gui.show_menu("Format Actions", actions)

        if 0 <= choice < len(actions):
            action = actions[choice]
            self.gui.show_toast(f"Action: {action}")
            # Add specific action logic here

    def find_and_replace(self):
        """Find and replace text."""
        find_text = self.gui.show_text_input("Find", "Enter text to find")
        if not find_text:
            return

        # Show occurrences
        count = self.current_document.content.count(find_text)

        if count == 0:
            self.gui.show_dialog("Not Found", f"'{find_text}' not found")
            return

        replace_choice = self.gui.show_dialog("Replace", f"Found {count} occurrence(s).\nReplace all?", ["Yes", "No"])

        if replace_choice == 0:
            replace_text = self.gui.show_text_input("Replace With", "")
            if replace_text is not None:
                replaced = self.current_document.replace_text(find_text, replace_text)
                self.is_modified = True
                self.gui.show_snackbar(f"Replaced {replaced} occurrence(s)")

    def show_document_info(self):
        """Show document information."""
        info = self.current_document.get_info()

        info_text = f"""
Document Information
{"=" * 40}
Name: {info["name"]}
Path: {info["path"]}
Format: {info["format"]}
Size: {info["size_bytes"]} bytes
Words: {info["words"]}
Characters: {info["characters"]}
Lines: {info["lines"]}
Last Modified: {info["last_modified"]}
"""

        self.gui.show_dialog("Document Info", info_text)

    def save_document(self):
        """Save document."""
        if self.current_document.save():
            self.is_modified = False
            self.gui.show_snackbar("Document saved successfully")
        else:
            self.gui.show_dialog("Error", "Failed to save document")

    def close_document(self):
        """Close current document."""
        if self.is_modified:
            save_choice = self.gui.show_dialog(
                "Save Changes?", "Document has unsaved changes", ["Save", "Don't Save", "Cancel"]
            )

            if save_choice == 0:
                self.save_document()
            elif save_choice == 2:
                return

        self.current_document = None

    def show_settings(self):
        """Show settings screen."""
        settings_menu = ["Theme (Dark/Light)", "Auto-save", "Font Size", "Word Wrap", "Show Line Numbers", "Back"]

        choice = self.gui.show_menu("Settings", settings_menu)

        if choice >= 0 and choice < 5:
            self.gui.show_toast(f"Setting {choice}: Not yet implemented")


# Main entry point
if __name__ == "__main__":
    editor = TextEditor()
    editor.run()
