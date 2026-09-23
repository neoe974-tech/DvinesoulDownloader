import os
import platform
from pathlib import Path

p4a_dir = Path(os.environ.get(
    "P4A_DIR",
    ".buildozer/android/platform/python-for-android"
))

root = p4a_dir / "pythonforandroid/pythonpackage.py"

if not root.exists():
    raise SystemExit(f"p4a file not found: {root}")

s = root.read_text()

imports = "from urllib.parse import urlparse\n"
needed = "from urllib.parse import urlparse\nfrom packaging.requirements import Requirement\nimport platform\n"

if "from packaging.requirements import Requirement" not in s:
    if imports not in s:
        raise SystemExit("Expected urllib.parse import was not found.")
    s = s.replace(imports, needed, 1)
elif "import platform" not in s:
    s = s.replace(
        "from packaging.requirements import Requirement\n",
        "from packaging.requirements import Requirement\nimport platform\n",
        1,
    )

if "req_name = parsed_req.name" in s and '"extra": "default"' in s:
    print(f"p4a marker patch already applied: {root}")
else:
    old = '''                    req_name = get_package_name(new_req)
'''

    new = '''                    parsed_req = Requirement(new_req)
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

    if old not in s:
        raise SystemExit("Expected p4a dependency code was not found.")

    s = s.replace(old, new, 1)
    root.write_text(s)
    print(f"p4a marker patch applied successfully: {root}")
