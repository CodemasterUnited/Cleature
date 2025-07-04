"""
Core rendering engine for Cleature.

Processes CHTML files with support for file includes, variable substitution,
and configurable output rendering.

© CodemasterUnited 2025
"""

import json
import re
import shutil
import random
import string

from pathlib import Path
from typing import Union, List, Tuple

from cleature.config_merge_handler import merge_configs

SRC_DIR = None
DIST_DIR = None
DEBUG_MODE = False
CONFIG = {}


def debug_print(*args, level="DEBUG", start='', **kwargs):
    """ Print only in debug mode, with optional levels like DEBUG, INFO, WARN, ERROR. """
    if DEBUG_MODE:
        print(f"{start}[{level}]", *args, **kwargs)


def parse(file_path, local_vars):
    """ Parse the given CHTML file. """
    debug_print(f"Parsing file: {file_path.relative_to(SRC_DIR) }", level="INFO")
    parsed_code = file_path.read_text()
    parsed_code, constants = extract_constants(parsed_code, file_path)

    local_vars = local_vars.copy()
    local_vars.update(constants)
    debug_print(f"Local variables after merging constants: {local_vars}", level="DEBUG")

    parsed_code = process_variables(parsed_code, local_vars)
    parsed_code = process_includes(parsed_code, file_path, local_vars)
    parsed_code = parsed_code.lstrip("\n")
    return parsed_code


def load_config():
    """ Load the configurations from cleature.config.json in the source directory. """
    config_file = SRC_DIR / 'cleature.config.json'
    try:
        config = json.loads(config_file.read_text(encoding='utf-8'))
        debug_print(f"Loaded config from {config_file}", level="INFO")
        debug_print(f"Config content: {config}", level="DEBUG")
        return config
    except FileNotFoundError:
        debug_print("No cleature.config.json found, using default config.", level="WARN")
        return {}
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in cleature.config.json: {e}")
        return {}


def extract_constants(content, file_path="<string>"):
    """Extract and parse <constants(...) /> to override/add variables."""
    constants = {}
    open_tag = "<constants("
    close_suffix = ") />"

    rel_file_path = file_path.relative_to(SRC_DIR)

    def parse_constants_arg(arg_str, tag_start):
        """Parse the key-value pairs inside <constants(...) />."""
        try:
            # Wrap as a JSON object if not already
            json_like = "{" + arg_str + "}"
            return json.loads(json_like)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"[{rel_file_path}] Invalid constants block at index {tag_start}: {e}"
            ) from e

    def find_constants_blocks(text):
        """Find all <constants(...) /> blocks, even if multiline."""
        blocks = []
        idx = 0
        while True:
            start = text.find(open_tag, idx)
            if start == -1:
                break

            i = start + len(open_tag)
            in_str = False
            escape = False

            while i < len(text):
                c = text[i]

                if c == '\\' and not escape:
                    escape = True
                    i += 1
                    continue

                if c == '"' and not escape:
                    in_str = not in_str
                elif not in_str and c == ')':
                    suffix_match = re.match(r'\s*/>', text[i+1:])
                    if suffix_match:
                        end = i + 1 + suffix_match.end()
                        blocks.append((start, end))
                        break

                escape = False
                i += 1

            else:
                raise ValueError(f"[{rel_file_path}] Unclosed <constants( block at index {start}")

            idx = start + 1
        return blocks

    matches = find_constants_blocks(content)
    debug_print(
        f"[extract_constants] Found {len(matches)} constants block(s) in {rel_file_path}",
        level="DEBUG"
    )

    new_content = content
    for start, end in reversed(matches):  # reverse to avoid messing up indices
        full_tag = content[start:end]
        inner = full_tag[len(open_tag):-len(close_suffix)]
        parsed = parse_constants_arg(inner, start)
        constants.update(parsed)
        debug_print(f"[extract_constants] Parsed constants: {parsed}", level="DEBUG")
        new_content = new_content[:start] + new_content[end:]

    return new_content, constants


def process_variables(file_src, variables):
    """ Process the variables in an CHTML file source code. """
    pattern = re.compile(r'\{\{\s*(\w+)\s*\}\}')

    def replacer(match):
        var_name = match.group(1)
        if var_name not in variables:
            print(f"[WARNING] Variable '{var_name}' not found")
            return match.group(0)

        debug_print(
            f"[process_variables] Replacing: {var_name} -> {variables[var_name]}",
            level="DEBUG"
        )

        return str(variables[var_name])

    return pattern.sub(replacer, file_src)


def process_includes(file_src, file_path, variables):
    """ Process the includes in an CHTML file source code. """
    pattern = re.compile(r'<include\(["\']?(.*?)["\']?\)\/>')

    def replacer(match):
        inc_filename = match.group(1).strip()
        inc_filepath = file_path.parent / inc_filename
        debug_print(
            f"[process_includes] Including file: {inc_filepath.relative_to(SRC_DIR)}",
            level="INFO"
        )
        return parse(inc_filepath, variables)

    return pattern.sub(replacer, file_src)


def empty_directory(dir_path):
    """ Empty a directory completely. """
    debug_print(f"[empty_directory] Emptying: {dir_path}", level="INFO")
    for item in dir_path.iterdir():
        try:
            if item.is_file() or item.is_symlink():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        except Exception as e:  # pylint:disable=broad-exception-caught
            print(f"Failed to delete {item}: {e}")


def is_inside(
    file_path: Union[str, Path],
    folder_path: Union[str, Path, List[Union[str, Path]]],
) -> Tuple[bool, Union[Path, None]]:
    """
    Check if a file_path is inside or equal to any of the given folder_path(s),
    which may be files or directories.

    Returns (True, matched_path) if matched, else (False, None).
    """
    if not folder_path:
        return (False, None)

    file_path = Path(file_path).expanduser()  # Expanding the ~ to the home directory
    try:
        file_resolved = file_path.resolve(strict=True)
    except FileNotFoundError:
        return (False, None)

    if not isinstance(folder_path, list):
        folder_path = [folder_path]

    for fp in folder_path:
        if not fp or str(fp).strip() in ("", ".", "./"):
            continue  # skip empty or trivial paths

        try:
            base_path = SRC_DIR / Path(fp)  # Make the fp path relative to the SRC_DIR

            if base_path.is_file():
                if file_resolved == base_path:
                    return (True, base_path)
            else:
                file_resolved.relative_to(base_path)
                return (True, base_path)
        except FileNotFoundError:
            continue
        except Exception: #pylint:disable=broad-exception-caught
            continue

    return (False, None)


def render(src_directory, dist_directory, provided_options):
    """ Main function to start processing files. """
    global SRC_DIR, DIST_DIR, DEBUG_MODE, CONFIG  # pylint:disable=global-statement

    SRC_DIR = src_directory
    DIST_DIR = dist_directory
    CONFIG = load_config()

    DEBUG_MODE = provided_options.get('debug', CONFIG.get('debug_mode', False))
    debug_print("\n⚙ Ran in Debug Mode\n\n", level="INFO")

    debug_print(f"\n SRC directory is set as: {SRC_DIR}", level="INFO")
    debug_print(f"\n DIST directory is set as: {DIST_DIR}\n\n", level="INFO")

    # Merge config options via (defaults, config file, command arguments)
    options = merge_configs({
        'variables': {},
        'refresh_dist': False,
        'excluded_dirs': []
    }, CONFIG, provided_options)

    debug_print("\nThese render options are being applied:", level="DEBUG")
    debug_print(options, level="DEBUG")

    if options["refresh_dist"]:
        debug_print("\nEmptying DIST directory, if it's not empty...", level="INFO")
        empty_directory(DIST_DIR)

    # Store the variables
    variables = options.get('variables')
    variables["unique_id"] = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    debug_print(f"Injected variable 'unique_id': {variables['unique_id']}", level="DEBUG")

    # Make dist directory if it doesn't exist
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize a dictionary for storing the processed files, for further uses.
    processed_files = {}

    for src_file in SRC_DIR.rglob('*'):
        filename, rel_path = src_file.name, src_file.relative_to(SRC_DIR)

        # Ignore directories
        if src_file.is_dir():
            continue

        # Ignore excluded files
        if (is_inside(src_file, options.get("excluded_dirs", [])))[0]:
            debug_print(f"📁 {rel_path} has been excluded", level="INFO", start="\n")
            continue

        # Variables have been already extracted, so ignore vars.json
        if filename == 'cleature.config.json':
            continue

        # Process Cleature HTML files
        if filename.endswith('.chtml'):
            dist_rel_path = rel_path.with_suffix('.html')
            dist_file = DIST_DIR / dist_rel_path
            try:
                debug_print(f"🔄 Rendering {rel_path}", level="INFO", start="\n\n")
                parsed = parse(src_file, variables)

                dist_file.parent.mkdir(parents=True, exist_ok=True)
                dist_file.write_text(parsed, encoding='utf-8')

                processed_files[str(dist_rel_path)] = parsed
                debug_print(f"✅ Rendered {rel_path} -> {dist_rel_path}\n", level="INFO")

            except Exception as e:  # pylint:disable=broad-exception-caught
                print(f"[ERROR] Failed to process {rel_path}: {e}")
        else:
            dist_file = DIST_DIR / rel_path
            try:
                content = src_file.read_bytes()
                dist_file.parent.mkdir(parents=True, exist_ok=True)
                dist_file.write_bytes(content)
                processed_files[str(rel_path)] = "Need not to be processed"
                debug_print(f"📦 Copied {rel_path} (static)", level="DEBUG")
            except Exception as e:  # pylint:disable=broad-exception-caught
                print(f"[ERROR] Failed to copy {rel_path}: {e}")

    return processed_files
