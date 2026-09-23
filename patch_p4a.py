import os
from pathlib import Path

p4a_dir = Path(os.environ.get(
    "P4A_DIR",
    ".buildozer/android/platform/python-for-android"
))

root = p4a_dir / "pythonforandroid/pythonpackage.py"

if not root.exists():
    raise SystemExit(f"p4a file not found: {root}")

s = root.read_text()

# p4a evaluates PEP 508 markers while resolving dependencies.
if "from packaging.requirements import Requirement" not in s:
    marker_import = (
        "from urllib.parse import urlparse\n"
        "from packaging.requirements import Requirement\n"
        "import platform\n"
    )
    if "from urllib.parse import urlparse\n" not in s:
        raise SystemExit("Expected urllib.parse import was not found.")
    s = s.replace("from urllib.parse import urlparse\n", marker_import, 1)
elif "import platform" not in s:
    s = s.replace(
        "from packaging.requirements import Requirement\n",
        "from packaging.requirements import Requirement\nimport platform\n",
        1,
    )

marker_block = '''                    parsed_req = Requirement(new_req)
                    if parsed_req.marker is not None:
                        marker_env = {
                            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
                            "python_full_version": ".".join(map(str, sys.version_info[:3])),
                            "os_name": os.name,
                            "sys_platform": sys.platform,
                            "platform_system": platform.system(),
                            "platform_machine": platform.machine(),
                            "platform_python_implementation": "CPython",
                            "implementation_name": "cpython",
                            "extra": "default",
                        }
                        if not parsed_req.marker.evaluate(marker_env):
                            continue
                    req_name = parsed_req.name
'''

old_simple = '''                    req_name = get_package_name(new_req)
'''
if "req_name = parsed_req.name" not in s:
    if old_simple not in s:
        raise SystemExit("Expected p4a dependency code was not found.")
    s = s.replace(old_simple, marker_block, 1)

# charset-normalizer publishes a CPython wheel that p4a can attempt to carry
# into Android, but that wheel is not Android-compatible. Requests treats this
# package as an optional charset detector, so omit it from the Android bundle.
exclude_block = '''                    if req_name.lower() == "charset-normalizer":
                        continue
'''
anchor = "                    req_name = parsed_req.name\n"
if exclude_block not in s:
    if anchor not in s:
        raise SystemExit("Expected patched dependency name assignment was not found.")
    s = s.replace(anchor, anchor + exclude_block, 1)

root.write_text(s)

# p4a's pip report resolver can reintroduce charset-normalizer after the
# dependency graph has been resolved. Filter it at the final module list
# before requirements.txt is generated.
build_root = p4a_dir / "pythonforandroid/build.py"
if not build_root.exists():
    raise SystemExit(f"p4a build file not found: {build_root}")

b = build_root.read_text()
filter_anchor = """        mname = module["metadata"]["name"]
        mver = module["metadata"]["version"]
"""
filter_block = """        mname = module["metadata"]["name"]
        if mname.lower().replace("-", "_") == "charset_normalizer":
            continue
        mver = module["metadata"]["version"]
"""
if 'charset_normalizer' not in b:
    if filter_anchor not in b:
        raise SystemExit("Expected p4a module report loop was not found.")
    b = b.replace(filter_anchor, filter_block, 1)

build_root.write_text(b)
print(f"p4a dependency patch applied successfully: {root}")
print(f"p4a module filtering patch applied successfully: {build_root}")
