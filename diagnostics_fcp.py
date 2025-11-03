"""
Football Club Platform - Pre-Flight Check Diagnostics
=====================================================
Comprehensive diagnostic script to verify the backend is ready for PyTorch integration.

Checks:
- Environment variables
- Python packages (FastAPI, PyTorch, OpenCV, etc.)
- Docker and docker-compose availability
- Port availability
- File structure
- HTTP endpoints (health, OpenAPI, predict)
- Git status
"""

import json
import os
import socket
import subprocess
import sys
import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from shutil import which

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def check_command(cmd: str) -> str:
    """Check if a command is available in PATH."""
    result = which(cmd)
    return result if result else f"NOT_FOUND"


def check_import(pkg: str) -> bool:
    """Check if a Python package can be imported."""
    spec = importlib.util.find_spec(pkg)
    return spec is not None


def run_command(cmd: str, timeout: int = 20) -> str:
    """Run a shell command and return output."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            timeout=timeout,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )
        return result.stdout.strip() if result.returncode == 0 else f"ERROR: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "ERROR: Command timed out"
    except Exception as e:
        return f"ERROR: {e}"


def check_port(host: str, port: int, timeout: float = 1.0) -> bool:
    """Check if a port is open."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        sock.close()
        return True
    except (socket.timeout, socket.error):
        return False


def get_env_vars(keys: list) -> dict:
    """Get environment variable status (set or missing)."""
    return {k: ("<set>" if os.getenv(k) else "<missing>") for k in keys}


def check_http_endpoint(url: str, timeout: int = 5) -> dict:
    """Check HTTP endpoint and return status."""
    try:
        import urllib.request
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read(512).decode(errors="ignore")
            return {
                "status": "ok",
                "code": response.status,
                "body_snippet": body[:200]
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def main():
    """Run comprehensive diagnostics."""
    print("=" * 80)
    print("Football Club Platform - Pre-Flight Check Diagnostics")
    print("=" * 80)
    now = datetime.now(timezone.utc).isoformat()
    print(f"Started at: {now}\n")

    report = {
        "timestamp": now,
        "project": "football-club-platform",
        "python_version": sys.version,
        "cwd": str(Path.cwd()),
    }

    # ================================
    # 1. EXECUTABLES CHECK
    # ================================
    print("[1/10] Checking executables...")
    report["executables"] = {
        "python": check_command("python"),
        "pip": check_command("pip"),
        "poetry": check_command("poetry"),
        "docker": check_command("docker"),
        "docker-compose": check_command("docker-compose") or check_command("docker compose"),
        "git": check_command("git"),
        "curl": check_command("curl"),
    }
    print(f"  [+] Found {sum(1 for v in report['executables'].values() if 'NOT_FOUND' not in v)}/{len(report['executables'])} executables")

    # ================================
    # 2. ENVIRONMENT VARIABLES
    # ================================
    print("[2/10] Checking environment variables...")
    env_keys = [
        "APP_ENV", "DEBUG", "API_VERSION",
        "POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD",
        "DATABASE_URL", "REDIS_URL",
        "STORAGE_BACKEND", "S3_ENDPOINT_URL", "S3_BUCKET", "S3_ACCESS_KEY", "S3_SECRET_KEY",
        "ALLOWED_ORIGINS", "JWT_SECRET",
        "ENABLE_GPU", "POSE_BACKEND",
        "ML_MODEL_VERSION", "MLFLOW_TRACKING_URI"
    ]
    report["env_vars"] = get_env_vars(env_keys)
    set_count = sum(1 for v in report["env_vars"].values() if v == "<set>")
    print(f"  [+] Found {set_count}/{len(env_keys)} environment variables")

    # ================================
    # 3. PYTHON PACKAGES
    # ================================
    print("[3/10] Checking Python packages...")
    packages = [
        "fastapi", "uvicorn", "pydantic", "pydantic_settings",
        "sqlalchemy", "alembic", "psycopg2", "redis",
        "boto3", "loguru", "prometheus_client",
        "pandas", "numpy", "scikit_learn", "xgboost",
        "torch", "torchvision", "cv2", "PIL", "onnxruntime",
        "pytest", "httpx", "requests"
    ]
    report["python_packages"] = {pkg: check_import(pkg) for pkg in packages}
    installed_count = sum(1 for v in report["python_packages"].values() if v)
    print(f"  [+] Found {installed_count}/{len(packages)} Python packages")

    # ================================
    # 4. PYTORCH DETAILS
    # ================================
    print("[4/10] Checking PyTorch details...")
    torch_info = {}
    if check_import("torch"):
        try:
            import torch
            torch_info["version"] = torch.__version__
            torch_info["cuda_available"] = torch.cuda.is_available()
            torch_info["cuda_device_count"] = torch.cuda.device_count() if torch.cuda.is_available() else 0
            if torch.cuda.is_available():
                torch_info["cuda_device_name"] = torch.cuda.get_device_name(0)
                torch_info["cuda_version"] = torch.version.cuda
            torch_info["backends"] = {
                "cudnn": torch.backends.cudnn.is_available(),
                "mps": torch.backends.mps.is_available() if hasattr(torch.backends, "mps") else False,
            }
            print(f"  [+] PyTorch {torch_info['version']} installed")
            print(f"  [+] CUDA available: {torch_info['cuda_available']}")
        except Exception as e:
            torch_info["error"] = str(e)
            print(f"  [-] PyTorch check failed: {e}")
    else:
        torch_info["available"] = False
        print("  [-] PyTorch not installed")
    report["torch"] = torch_info

    # ================================
    # 5. OPENCV DETAILS
    # ================================
    print("[5/10] Checking OpenCV details...")
    opencv_info = {}
    if check_import("cv2"):
        try:
            import cv2
            opencv_info["version"] = cv2.__version__
            opencv_info["build_info_snippet"] = cv2.getBuildInformation()[:500]
            print(f"  [+] OpenCV {opencv_info['version']} installed")
        except Exception as e:
            opencv_info["error"] = str(e)
            print(f"  [-] OpenCV check failed: {e}")
    else:
        opencv_info["available"] = False
        print("  [-] OpenCV not installed")
    report["opencv"] = opencv_info

    # ================================
    # 6. DOCKER & GIT
    # ================================
    print("[6/10] Checking Docker and Git...")
    report["docker_version"] = run_command("docker --version")
    report["docker_compose_version"] = run_command("docker compose version")
    report["git_sha"] = run_command("git rev-parse --short HEAD")
    report["git_branch"] = run_command("git rev-parse --abbrev-ref HEAD")
    report["git_status"] = run_command("git status --porcelain")
    print(f"  [+] Git SHA: {report['git_sha']}")
    print(f"  [+] Docker: {report['docker_version']}")

    # ================================
    # 7. FILE STRUCTURE
    # ================================
    print("[7/10] Checking file structure...")
    files_to_check = [
        "Dockerfile",
        "docker-compose.yml",
        "docker-compose.prod.yml",
        ".env",
        ".env.example",
        "pyproject.toml",
        "README.md",
        "backend/app/main.py",
        "backend/app/config.py",
        "backend/app/routers/ml_predict.py",
        "backend/tests/conftest.py",
        "backend/alembic/env.py",
    ]
    report["files"] = {f: Path(f).exists() for f in files_to_check}
    existing_count = sum(1 for v in report["files"].values() if v)
    print(f"  [+] Found {existing_count}/{len(files_to_check)} required files")

    # ================================
    # 8. PORT AVAILABILITY
    # ================================
    print("[8/10] Checking port availability...")
    ports_to_check = {
        "backend_dev": ("127.0.0.1", 8101),
        "backend_prod": ("127.0.0.1", 8000),
        "postgres_dev": ("127.0.0.1", 5433),
        "postgres_prod": ("127.0.0.1", 5432),
        "redis_dev": ("127.0.0.1", 6380),
        "redis_prod": ("127.0.0.1", 6379),
        "minio_dev": ("127.0.0.1", 9001),
        "minio_prod": ("127.0.0.1", 9000),
        "mlflow": ("127.0.0.1", 5000),
    }
    report["ports"] = {
        f"{name}_{host}:{port}": check_port(host, port)
        for name, (host, port) in ports_to_check.items()
    }
    open_ports = sum(1 for v in report["ports"].values() if v)
    print(f"  [+] Found {open_ports}/{len(ports_to_check)} open ports")

    # ================================
    # 9. HTTP ENDPOINTS
    # ================================
    print("[9/10] Checking HTTP endpoints...")
    # Try both dev and prod ports
    api_ports = [8101, 8000]
    endpoints_checked = False

    for api_port in api_ports:
        if check_port("127.0.0.1", api_port):
            print(f"  [+] API running on port {api_port}")
            base_url = f"http://127.0.0.1:{api_port}"

            endpoints = [
                "/healthz",
                "/readyz",
                "/api/v1/openapi.json",
                "/api/v1/ml/predict/health",
            ]

            for endpoint in endpoints:
                url = f"{base_url}{endpoint}"
                report[f"http_{endpoint}"] = check_http_endpoint(url)
                status = report[f"http_{endpoint}"]["status"]
                print(f"    [{'+'if status == 'ok' else '-'}] {endpoint}: {status}")

            endpoints_checked = True
            break

    if not endpoints_checked:
        print("  [-] API not running on any port")
        report["http_endpoints"] = "API not running"

    # ================================
    # 10. DOCKER CONTAINERS
    # ================================
    print("[10/10] Checking Docker containers...")
    report["docker_ps"] = run_command("docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'")
    print(f"  [+] Docker containers listed")

    # ================================
    # SAVE REPORT
    # ================================
    output_file = "fcp_diagnostics.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print(f"[+] Diagnostics complete! Report saved to: {output_file}")
    print("=" * 80)

    # ================================
    # SUMMARY
    # ================================
    print("\nSUMMARY:")
    print(f"  Python packages: {installed_count}/{len(packages)} installed")
    print(f"  PyTorch: {'[+] Installed' if torch_info.get('version') else '[-] Missing'}")
    print(f"  OpenCV: {'[+] Installed' if opencv_info.get('version') else '[-] Missing'}")
    print(f"  Docker: {'[+] Available' if 'NOT_FOUND' not in report['docker_version'] else '[-] Missing'}")
    print(f"  API running: {'[+] Yes' if endpoints_checked else '[-] No'}")
    print(f"  Required files: {existing_count}/{len(files_to_check)} present")

    # Return exit code based on critical checks
    critical_checks = [
        check_import("fastapi"),
        check_import("torch"),
        check_import("cv2"),
        Path("backend/app/main.py").exists(),
    ]

    if all(critical_checks):
        print("\n[SUCCESS] All critical checks passed!")
        return 0
    else:
        print("\n[WARNING] Some critical checks failed. Review the report for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
