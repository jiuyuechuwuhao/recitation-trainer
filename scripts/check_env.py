#!/usr/bin/env python3
"""
Check and auto-install all dependencies for the Recitation Trainer pipeline.

Usage:
    python3 check_env.py

This script:
1. Detects the operating system (macOS / Linux / Windows)
2. Checks for required Python packages (edge-tts, Pillow, python-pptx)
3. Checks for system tools (pdftoppm, Keynote/LibreOffice, gh CLI)
4. Auto-installs missing Python packages via pip
5. Reports system tools that need manual installation
6. Returns exit code 0 if all essential deps are ready, 1 otherwise

The AI agent should run this FIRST before any other step.
"""

import sys
import os
import platform
import subprocess
import shutil
import json


def get_os_info():
    """Detect OS and return structured info."""
    system = platform.system()
    if system == "Darwin":
        return {
            "os": "macOS",
            "has_keynote": os.path.exists("/Applications/Keynote.app"),
            "pkg_manager": "brew",
            "pkg_install_cmd": "brew install",
        }
    elif system == "Linux":
        # Detect distro
        has_apt = shutil.which("apt-get")
        has_dnf = shutil.which("dnf")
        return {
            "os": "Linux",
            "has_libreoffice": shutil.which("libreoffice") is not None,
            "pkg_manager": "apt-get" if has_apt else "dnf" if has_dnf else "unknown",
            "pkg_install_cmd": "sudo apt-get install -y" if has_apt else "sudo dnf install -y" if has_dnf else "unknown",
        }
    elif system == "Windows":
        return {
            "os": "Windows",
            "has_powerpoint": True,  # Assume PowerPoint is available
            "pkg_manager": "choco",
            "pkg_install_cmd": "choco install",
        }
    else:
        return {"os": system, "pkg_manager": "unknown", "pkg_install_cmd": "unknown"}


def check_python_package(pkg_name, import_name=None):
    """Check if a Python package is installed."""
    if import_name is None:
        import_name = pkg_name.replace("-", "_")
    try:
        __import__(import_name)
        return True
    except ImportError:
        return False


def check_system_tool(tool_name):
    """Check if a system command is available."""
    return shutil.which(tool_name) is not None


def auto_install_python(packages):
    """Auto-install Python packages via pip."""
    installed = []
    failed = []
    for pkg in packages:
        print(f"  Installing {pkg}...", end=" ", flush=True)
        try:
            # Always use the system pip3 to install packages.
            # This ensures they're available to ALL Python interpreters,
            # including venvs, IDEs, and AI agent subprocesses.
            pip_cmd = shutil.which("pip3") or shutil.which("pip")
            if pip_cmd:
                cmd = [pip_cmd, "install", pkg, "--break-system-packages", "-q"]
            else:
                cmd = [sys.executable, "-m", "pip", "install", pkg, "-q"]
            subprocess.run(cmd, check=True, capture_output=True, timeout=120)
            print("✅")
            installed.append(pkg)
        except Exception as e:
            print(f"❌ ({e})")
            failed.append(pkg)
    return installed, failed


def main():
    print("=" * 55)
    print("Recitation Trainer — Environment Check")
    print("=" * 55)
    
    os_info = get_os_info()
    print(f"\nOS: {os_info['os']}")
    print(f"Package manager: {os_info['pkg_manager']}")
    
    results = {"os": os_info, "python_packages": {}, "system_tools": {}, "ready": True}
    
    # ---- Python packages ----
    print("\n── Python Packages ──")
    py_packages = [
        ("edge-tts", "edge_tts"),
        ("Pillow", "PIL"),
        ("python-pptx", "pptx"),
    ]
    
    missing_py = []
    for pkg_name, import_name in py_packages:
        ok = check_python_package(pkg_name, import_name)
        results["python_packages"][pkg_name] = ok
        print(f"  {pkg_name:20s} {'✅' if ok else '❌ MISSING'}")
        if not ok:
            missing_py.append(pkg_name)
    
    if missing_py:
        print(f"\n⚠️  {len(missing_py)} Python package(s) missing. Auto-installing...")
        installed, failed = auto_install_python(missing_py)
        if failed:
            print(f"\n❌ Failed to install: {', '.join(failed)}")
            print(f"   Manual install: pip3 install {' '.join(failed)} --break-system-packages")
            results["ready"] = False
        else:
            print(f"   All {len(installed)} package(s) installed successfully.")
            for pkg in installed:
                results["python_packages"][pkg] = True
    
    # ---- System tools ----
    print("\n── System Tools ──")
    
    # pdftoppm
    has_pdftoppm = check_system_tool("pdftoppm")
    results["system_tools"]["pdftoppm"] = has_pdftoppm
    print(f"  {'pdftoppm':20s} {'✅' if has_pdftoppm else '❌ MISSING'}")
    if not has_pdftoppm:
        if os_info["os"] == "macOS":
            print(f"    Install: brew install poppler")
        elif os_info["os"] == "Linux":
            print(f"    Install: {os_info['pkg_install_cmd']} poppler-utils")
    
    # Slide export tool (Keynote / LibreOffice / PowerPoint)
    if os_info["os"] == "macOS":
        has_slide_tool = os_info.get("has_keynote", False)
        tool_name = "Keynote"
        install_hint = "Keynote is pre-installed on macOS"
    elif os_info["os"] == "Linux":
        has_slide_tool = os_info.get("has_libreoffice", False)
        tool_name = "LibreOffice"
        install_hint = f"{os_info['pkg_install_cmd']} libreoffice"
    else:
        has_slide_tool = os_info.get("has_powerpoint", False)
        tool_name = "PowerPoint"
        install_hint = "Use PowerPoint's Export feature manually"
    
    results["system_tools"]["slide_exporter"] = {"name": tool_name, "available": has_slide_tool}
    
    if has_slide_tool:
        print(f"  {tool_name:20s} ✅ (slide export)")
    else:
        print(f"  {tool_name:20s} ❌ NOT FOUND")
        if os_info["os"] == "Linux":
            print(f"    Install: {install_hint}")
            print(f"    Or use the manual PNG export fallback (python-pptx + Pillow)")
        elif os_info["os"] == "macOS":
            print(f"    {install_hint}")
    
    # LibreOffice (for best-quality slide export)
    has_lo = shutil.which('soffice') is not None
    results["system_tools"]["libreoffice"] = has_lo
    if has_lo:
        print(f"  {'LibreOffice':20s} ✅ (best-quality slide export)")
    else:
        print(f"  {'LibreOffice':20s} ⚠️  Optional — for pixel-perfect slides")
        if os_info["os"] == "macOS":
            print(f"    Install: brew install --cask libreoffice")
        elif os_info["os"] == "Linux":
            print(f"    Install: {os_info['pkg_install_cmd']} libreoffice-impress")

# gh CLI (for GitHub Pages deployment)
    has_gh = check_system_tool("gh")
    results["system_tools"]["gh"] = has_gh
    print(f"  {'gh (GitHub CLI)':20s} {'✅' if has_gh else '⚠️  Optional (for deployment)'}")
    if not has_gh:
        if os_info["os"] == "macOS":
            print(f"    Install: brew install gh")
        elif os_info["os"] == "Linux":
            print(f"    Install: {os_info['pkg_install_cmd']} gh")
    
    # ---- Summary ----
    print("\n" + "=" * 55)
    
    all_py_ok = all(results["python_packages"].values())
    # pdftoppm is optional — export_slides.py handles everything via python-pptx
    # slide exporter is optional — export_slides.py is the primary method
    
    if all_py_ok:
        print("✅ All essential dependencies ready!")
        if False:  # slide exporter optional
            print(f"⚠️  Slide export tool ({tool_name}) not found — will use fallback method.")
        if not has_gh:
            print("ℹ️  gh CLI not installed — GitHub Pages deployment unavailable (local use still OK).")
        print("\nReady to build recitation trainer.")
        results["ready"] = True
    else:
        print("❌ Some dependencies could not be resolved:")
        if not all_py_ok:
            missing = [pkg for pkg, ok in results["python_packages"].items() if not ok]
            print(f"   Python packages: {', '.join(missing)}")
        if False:  # pdftoppm is optional
            print(f"   System tool: pdftoppm")
        print("\nPlease install the missing items and run this check again.")
        results["ready"] = False
    
    # Output JSON for AI agent consumption
    print("\n" + json.dumps(results, indent=2, ensure_ascii=False))
    
    return 0 if results["ready"] else 1


if __name__ == "__main__":
    sys.exit(main())
