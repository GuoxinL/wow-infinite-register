# Skill 打包
#
#   make              打包（等同 make package）
#   make list         预览将打包的文件
#   make verify       校验已生成的 zip
#   make clean        删除 dist/
#
# 可选变量：
#   make INCLUDE_EVIDENCE=1   把 evidence/ 实测凭证一并打包
#   make NO_PREFIX=1          zip 内不套 skill 名文件夹（SKILL.md 直接在根）
#   make PYTHON=python        Windows 上 python3 不可用时改用 python
#
# 产物：dist/<skill-name>-<version>.zip

PYTHON        ?= python3
DIST_DIR      ?= dist
INCLUDE_EVIDENCE ?= 0
NO_PREFIX     ?= 0

PACKAGE_ARGS :=
ifeq ($(INCLUDE_EVIDENCE),1)
PACKAGE_ARGS += --include-evidence
endif
ifeq ($(NO_PREFIX),1)
PACKAGE_ARGS += --no-prefix
endif

.PHONY: all package list verify clean help

all: package

package:
	@$(PYTHON) tools/package_skill.py --output-dir "$(DIST_DIR)" $(PACKAGE_ARGS)

list:
	@$(PYTHON) tools/package_skill.py --list $(PACKAGE_ARGS)

verify:
	@$(PYTHON) tools/package_skill.py --verify --output-dir "$(DIST_DIR)" $(PACKAGE_ARGS)

clean:
	@$(PYTHON) -c "import shutil, pathlib; shutil.rmtree(pathlib.Path('$(DIST_DIR)'), ignore_errors=True); print('[✓] 已清理 $(DIST_DIR)/')"

help:
	@echo "可用目标："
	@echo "  make                    打包 Skill 为 zip"
	@echo "  make list               预览将打包的文件"
	@echo "  make verify             校验已生成的 zip"
	@echo "  make clean              删除 $(DIST_DIR)/"
	@echo ""
	@echo "可选变量："
	@echo "  INCLUDE_EVIDENCE=1      打包 evidence/ 实测凭证"
	@echo "  NO_PREFIX=1             zip 内不套 skill 名文件夹"
	@echo "  PYTHON=python           指定 Python 命令"
