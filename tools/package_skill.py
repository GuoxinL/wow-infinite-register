#!/usr/bin/env python3
"""把当前仓库打包成可安装的 Skill zip。

默认只打包发布所需的白名单内容（SKILL.md、README.md、LICENSE、
scripts/、references/），并排除运行期产物和含个人信息的配置；
evidence/ 体积较大，默认不打包，可用 --include-evidence 显式加入。

用法：
    python tools/package_skill.py                 # 生成 dist/<name>-<version>.zip
    python tools/package_skill.py --list          # 只预览会打包哪些文件
    python tools/package_skill.py --verify        # 校验已有 zip
    python tools/package_skill.py --include-evidence
    python tools/package_skill.py --no-prefix     # zip 根目录不套 skill 名文件夹
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 始终打包的根级文件
ROOT_FILES = ("SKILL.md", "README.md")
# 始终打包的目录
INCLUDE_DIRS = ("scripts", "references")
# 可选打包的目录（体积大 / 含实测凭证）
OPTIONAL_DIRS = ("evidence",)

# 目录名黑名单（任意层级命中即跳过）
EXCLUDE_DIR_NAMES = {
    ".git",
    ".github",
    ".idea",
    ".vscode",
    "dist",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
}
# 文件名黑名单
EXCLUDE_FILE_NAMES = {".DS_Store", "Thumbs.db"}
# 相对路径（POSIX 风格）黑名单：仅匹配「会进入打包范围」的目录
EXCLUDE_PATH_PATTERNS = (
    re.compile(r"^scripts/config_run.*\.json$"),
    re.compile(r".*\.py[co]$"),
)


def read_front_matter(key: str, default: str) -> str:
    """从 SKILL.md 的 YAML front matter 中读取简单标量字段。"""
    skill_md = ROOT / "SKILL.md"
    if not skill_md.is_file():
        return default
    text = skill_md.read_text(encoding="utf-8")
    match = re.search(rf"^{re.escape(key)}:\s*(.+?)\s*$", text, re.MULTILINE)
    if not match:
        return default
    return match.group(1).strip().strip("\"'")


def is_excluded(rel: Path) -> bool:
    if rel.name in EXCLUDE_FILE_NAMES:
        return True
    if any(part in EXCLUDE_DIR_NAMES for part in rel.parts[:-1]):
        return True
    posix = rel.as_posix()
    return any(pattern.match(posix) for pattern in EXCLUDE_PATH_PATTERNS)


def collect_files(include_evidence: bool) -> list[Path]:
    """按白名单收集待打包文件，返回相对 ROOT 的路径列表。"""
    files: list[Path] = []

    for name in ROOT_FILES:
        path = ROOT / name
        if path.is_file():
            files.append(Path(name))

    dirs = list(INCLUDE_DIRS) + (list(OPTIONAL_DIRS) if include_evidence else [])
    for dir_name in dirs:
        base = ROOT / dir_name
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(ROOT)
            if is_excluded(rel):
                continue
            files.append(rel)

    # 去重并保持根级文件在前的稳定顺序
    seen: set[Path] = set()
    ordered: list[Path] = []
    for rel in files:
        if rel not in seen:
            seen.add(rel)
            ordered.append(rel)
    return ordered


def human_size(num: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num < 1024 or unit == "GB":
            return f"{num:.1f} {unit}" if unit != "B" else f"{num} B"
        num /= 1024
    return f"{num:.1f} GB"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_zip(
    output: Path,
    files: list[Path],
    prefix: str | None,
) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(output.suffix + ".tmp")
    if tmp.exists():
        tmp.unlink()

    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for rel in files:
            arcname = f"{prefix}/{rel.as_posix()}" if prefix else rel.as_posix()
            zf.write(ROOT / rel, arcname)

    tmp.replace(output)
    return output


def forbidden_entries(names: list[str]) -> list[str]:
    bad: list[str] = []
    for name in names:
        parts = name.split("/")
        if any(part in EXCLUDE_DIR_NAMES for part in parts):
            bad.append(name)
        elif any(part in EXCLUDE_FILE_NAMES for part in parts):
            bad.append(name)
        elif re.search(r"(^|/)config_run.*\.json$", name):
            bad.append(name)
        elif name.endswith((".pyc", ".pyo")):
            bad.append(name)
    return bad


def verify_zip(zip_path: Path, prefix: str | None) -> int:
    if not zip_path.is_file():
        print(f"[x] 找不到压缩包：{zip_path}", file=sys.stderr)
        print("    请先运行 `make package`。", file=sys.stderr)
        return 1

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        broken = zf.testzip()
        bad = forbidden_entries(names)

    root = f"{prefix}/" if prefix else ""
    required = [root + "SKILL.md", root + "scripts/register.py"]
    missing = [item for item in required if item not in names]

    print(f"压缩包：{zip_path}")
    print(f"文件数：{len(names)}    大小：{human_size(zip_path.stat().st_size)}")
    ok = True
    if broken:
        print(f"[x] 压缩包内部损坏：{broken}", file=sys.stderr)
        ok = False
    if missing:
        print(f"[x] 缺少必需文件：{', '.join(missing)}", file=sys.stderr)
        ok = False
    if bad:
        print(f"[x] 含有不应发布的文件：{', '.join(bad)}", file=sys.stderr)
        ok = False
    if ok:
        print("[✓] 校验通过：SKILL.md 位于根目录，未包含敏感配置与缓存文件。")
        return 0
    return 1


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="打包 Skill 为 zip")
    parser.add_argument("--output-dir", default="dist", help="输出目录（默认 dist）")
    parser.add_argument("--output", help="显式指定 zip 输出路径（优先于 --output-dir）")
    parser.add_argument(
        "--include-evidence",
        action="store_true",
        help="把 evidence/ 实测凭证一并打包（体积较大）",
    )
    parser.add_argument(
        "--no-prefix",
        action="store_true",
        help="zip 内不套 skill 名文件夹，SKILL.md 直接位于根目录",
    )
    parser.add_argument("--list", action="store_true", help="只列出将打包的文件，不生成 zip")
    parser.add_argument("--verify", action="store_true", help="校验已有的 zip")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    name = read_front_matter("name", ROOT.name)
    version = read_front_matter("version", "0.0.0")
    prefix = None if args.no_prefix else name

    if args.output:
        output = Path(args.output)
    else:
        output = Path(args.output_dir) / f"{name}-{version}.zip"
    if not output.is_absolute():
        output = ROOT / output

    if args.verify:
        return verify_zip(output, prefix)

    files = collect_files(args.include_evidence)

    if args.list:
        print(f"Skill：{name} v{version}")
        print(f"打包前缀：{prefix + '/' if prefix else '(无)'}")
        print(f"共 {len(files)} 个文件：")
        total = 0
        for rel in files:
            size = (ROOT / rel).stat().st_size
            total += size
            print(f"  {rel.as_posix():<48} {human_size(size):>10}")
        print(f"  {'合计':<48} {human_size(total):>10}")
        return 0

    if not files or not any(rel.as_posix() == "SKILL.md" for rel in files):
        print("[x] 未找到 SKILL.md，确认在仓库根目录运行。", file=sys.stderr)
        return 1

    build_zip(output, files, prefix)
    digest = sha256_of(output)

    print(f"[✓] 已生成：{output.relative_to(ROOT)}")
    print(f"    文件数：{len(files)}")
    print(f"    大小：  {human_size(output.stat().st_size)}")
    print(f"    SHA256：{digest}")

    return verify_zip(output, prefix)


if __name__ == "__main__":
    raise SystemExit(main())
