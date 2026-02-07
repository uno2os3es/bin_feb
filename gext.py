#!/data/data/com.termux/files/usr/bin/env python3
import ast
from multiprocessing import Pool, cpu_count
import os
from pathlib import Path
import shutil
import tarfile
from typing import Any
import zipfile

import regex as re

# --- Configuration ---
OUTPUT_DIR = Path("output")
ARCHIVE_EXTENSIONS = (
    ".whl",
    ".zip",
    ".tar.gz",
    ".tgz",
    ".tar.zst",
    ".tar.xz",
    ".tar",
    ".zst",
)
ALLOWED_PYTHON_EXTENSIONS = (
    ".py",
    "",
)  # .py or no extension

# --- Core AST Visitor for Entity Extraction ---


class EntityExtractor(ast.NodeVisitor):
    """
    Traverses the Python Abstract Syntax Tree (AST) to identify and store
    functions, classes, and module-level constants, handling nested structures.
    """

    def __init__(
        self,
        source_content: str,
        original_path: Path,
    ):
        self.entities = []
        self.source_lines = source_content.splitlines(keepends=True)
        self.original_path = original_path
        self.scope_stack = []

    def _get_source_slice(self, node: ast.AST) -> str:
        """Extracts the source code corresponding to the AST node."""
        start_line = node.lineno - 1
        end_line = node.end_lineno or node.lineno
        # Get the lines, excluding the end line if end_col_offset is 0
        code_slice = self.source_lines[start_line:end_line]
        # Handle slicing start and end columns for accurate extraction
        if node.col_offset is not None:
            code_slice[0] = code_slice[0][node.col_offset :]
        if node.end_col_offset is not None and node.end_col_offset > 0:
            last_line = code_slice[-1]
            # Adjust the last line content to stop at end_col_offset
            code_slice[-1] = last_line[: node.end_col_offset]
        return "".join(code_slice)

    def _extract_and_save(
        self,
        node: ast.AST,
        entity_type: str,
        name: str,
    ):
        """Prepares and saves the entity data."""
        entity_code = self._get_source_slice(node)
        scope_prefix = "_".join(self.scope_stack)
        full_name = f"{scope_prefix}_{name}" if scope_prefix else name
        self.entities.append(
            {
                "name": name,
                "full_name": full_name,
                "type": entity_type,
                "code": entity_code,
                "path": str(self.original_path),
                "is_constant": entity_type in ("constant"),
                "is_class": entity_type in ("class"),
                "is_function": entity_type in ("function"),
            }
        )

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Handle function or method definition
        entity_type = "method" if self.scope_stack and self.scope_stack[-1].startswith("class_") else "function"
        if entity_type == "function":
            self._extract_and_save(node, entity_type, node.name)
            self.scope_stack.append(f"func_{node.name}")
            self.generic_visit(node)
            self.scope_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        # Handle async function or method definition
        entity_type = "method" if self.scope_stack and self.scope_stack[-1].startswith("class_") else "function"
        if entity_type == "function":
            self._extract_and_save(node, entity_type, node.name)
            self.scope_stack.append(f"async_func_{node.name}")
            self.generic_visit(node)
            self.scope_stack.pop()

    def visit_ClassDef(self, node: ast.ClassDef):
        # Handle class definition
        self._extract_and_save(node, "class", node.name)
        self.scope_stack.append(f"class_{node.name}")
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_Assign(self, node: ast.Assign):
        # Check for module-level or class-level simple assignments (potential constants)
        if not self.scope_stack:  # Module level assignment
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                target_name = node.targets[0].id
                # Check for common constant naming conventions (all caps)
                if re.match(
                    r"^[A-Z_][A-Z0-9_]*$",
                    target_name,
                ):
                    self._extract_and_save(
                        node,
                        "constant",
                        target_name,
                    )
        # Do not recurse into children for Assign nodes to avoid processing assignments inside lists/tuples etc.
        # We rely on generic_visit in FunctionDef/ClassDef to handle nested statements.

    # Ensure constants are only extracted at the top level or inside classes

    def generic_visit(self, node: ast.AST):
        # Stop traversing deeper if we hit an inner function/class definition,
        # but the visit methods handle the internal recursion correctly.
        super().generic_visit(node)


# --- Output and Saving Logic ---


def get_unique_filepath(base_path: Path) -> Path:
    """Finds a unique filename by appending a counter if the file already exists."""
    if not base_path.exists():
        return base_path
    name = base_path.stem
    suffix = base_path.suffix
    i = 1
    while True:
        new_path = base_path.with_name(f"{name}_{i}{suffix}")
        if not new_path.exists():
            return new_path
        i += 1


def save_entity(entity: dict[str, Any]):
    """Saves a single extracted entity to the output folder."""
    filename_base = f"{entity['full_name']}.py"
    output_path_base = OUTPUT_DIR / entity["type"] / filename_base
    # Ensure the target directory exists
    output_path_base.parent.mkdir(parents=True, exist_ok=True)
    # 1. Prepare Content
    #    comment = f'# Original path: {entity["path"]}\n'
    content = entity["code"]
    # 2. Save .py file (and handle naming conflict)
    final_py_path = get_unique_filepath(output_path_base)
    try:
        with open(final_py_path, "w", encoding="utf-8") as f:
            f.write(content)
        # print(f"Saved: {final_py_path}") # Optional logging
    except Exception as e:
        print(f"Error saving {final_py_path}: {e}")
        return


# --- Processing Functions ---


def extract_entities_from_content(content: str, path: Path) -> list[dict[str, Any]]:
    """Parses content using AST and extracts entities."""
    try:
        tree = ast.parse(content)
        extractor = EntityExtractor(content, path)
        extractor.visit(tree)
        return extractor.entities
    except SyntaxError:
        # File is likely not valid Python or only partially Python (e.g. an extensionless file)
        # print(f"Skipping {path}: Not valid Python syntax.")
        return []
    except Exception as e:
        print(f"Error parsing AST for {path}: {e}")
        return []


def is_python_file_no_extension(
    path: Path,
) -> bool:
    """Heuristically checks if a file with no extension might be a Python file."""
    if path.suffix:
        return False
    # Check if the file starts with a Python shebang or contains common Python keywords
    try:
        with open(
            path,
            encoding="utf-8",
            errors="ignore",
        ) as f:
            first_lines = "".join(f.readlines(1024))
            if re.match(r"#!\s*/.*python", first_lines):
                return True
            if "def " in first_lines or "class " in first_lines or "import " in first_lines:
                return True
    except:
        pass
    return False


def process_single_file(
    path: Path,
) -> list[dict[str, Any]]:
    """Reads a file and extracts entities."""
    try:
        if path.suffix == ".py" or is_python_file_no_extension(path):
            content = path.read_text(encoding="utf-8", errors="ignore")
            return extract_entities_from_content(content, path)
        return []
    except Exception as e:
        print(f"Error reading file {path}: {e}")
        return []


def process_archive(
    path: Path,
) -> list[dict[str, Any]]:
    """Handles compressed files (.zip, .tar.*, .whl) and extracts entities from Python files within."""
    entities = []
    # 1. Handle ZST-only files (often used for single compressed files)
    if path.suffix == ".zst":
        try:
            dctx = zstd.ZstdDecompressor()
            content = dctx.decompress(path.read_bytes()).decode("utf-8", errors="ignore")
            return extract_entities_from_content(content, path)
        except Exception as e:
            print(f"Error decompressing ZST file {path}: {e}")
            return []
    # 2. Handle standard archive types
    if path.suffix in (".zip", ".whl"):
        try:
            with zipfile.ZipFile(path, "r") as zf:
                for member in zf.namelist():
                    member_path = Path(member)
                    if member_path.suffix == ".py":
                        with zf.open(member) as member_file:
                            content = member_file.read().decode(
                                "utf-8",
                                errors="ignore",
                            )
                            virtual_path = Path(f"{path}/{member}")
                            entities.extend(
                                extract_entities_from_content(
                                    content,
                                    virtual_path,
                                )
                            )
        except Exception as e:
            print(f"Error processing ZIP/WHL archive {path}: {e}")
    elif any(
        path.name.endswith(ext)
        for ext in [
            ".tar",
            ".tar.gz",
            ".tgz",
            ".tar.zst",
            ".tar.xz",
        ]
    ):
        mode_map = {
            ".tar.gz": "r:gz",
            ".tgz": "r:gz",
            ".tar.zst": "r:zst",
            ".tar.xz": "r:xz",
            ".tar": "r",
        }
        mode = next(
            (mode_map[ext] for ext in mode_map if path.name.endswith(ext)),
            "r",
        )
        try:
            with tarfile.open(path, mode) as tf:
                for member in tf.getmembers():
                    member_path = Path(member.name)
                    if member.isfile() and member_path.suffix == ".py":
                        member_file = tf.extractfile(member)
                        if member_file:
                            content = member_file.read().decode(
                                "utf-8",
                                errors="ignore",
                            )
                            virtual_path = Path(f"{path}/{member.name}")
                            entities.extend(
                                extract_entities_from_content(
                                    content,
                                    virtual_path,
                                )
                            )
        except tarfile.ReadError:
            # Not a valid archive, or wrong compression mode
            pass
        except Exception as e:
            print(f"Error processing TAR archive {path}: {e}")
    return entities


def worker_process(
    path_str: str,
) -> list[dict[str, Any]]:
    """Worker function for the multiprocessing pool."""
    path = Path(path_str)
    if path.name.endswith(ARCHIVE_EXTENSIONS):
        return process_archive(path)
    return process_single_file(path)


# --- Main Execution ---


def main():
    print(f"Starting analysis in {Path.cwd()}...")
    # Remove existing output folder for a clean run
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
        print(f"Cleaned previous output directory: {OUTPUT_DIR}")
    OUTPUT_DIR.mkdir(exist_ok=True)
    # 1. Collect all files to process
    files_to_process = []
    current_dir = Path(".")
    for root, _, filenames in os.walk(current_dir):
        for name in filenames:
            path = Path(root) / name
            # Skip files in the output directory
            if path.is_relative_to(OUTPUT_DIR):
                continue
            # Check if it's a python file or an archive
            is_archive = path.suffix in ARCHIVE_EXTENSIONS or any(path.name.endswith(ext) for ext in ARCHIVE_EXTENSIONS)
            is_py = path.suffix in ALLOWED_PYTHON_EXTENSIONS or is_python_file_no_extension(path)
            if is_archive or is_py:
                files_to_process.append(str(path))
    if not files_to_process:
        print("No Python files or archives found to process.")
        return
    print(f"Found {len(files_to_process)} relevant files/archives. Starting multiprocessing pool...")
    # 2. Process files in parallel
    num_cpus = cpu_count()
    all_entities = []
    # Use a pool for parallel processing (CPU bound AST parsing)
    with Pool(processes=num_cpus) as pool:
        # map returns results in order, which is fine here
        results_list = pool.map(worker_process, files_to_process)
        # Flatten the list of lists of entities
        for result in results_list:
            all_entities.extend(result)
    print(f"Processing complete. Extracted {len(all_entities)} entities.")
    # 3. Save all extracted entities
    print(f"Saving entities to {OUTPUT_DIR}...")
    for entity in all_entities:
        save_entity(entity)
    print("\n\nAll tasks finished successfully!")
    print(f"Results are saved in the '{OUTPUT_DIR}' folder, organized by entity type (class, function, constant).")


if __name__ == "__main__":
    main()
