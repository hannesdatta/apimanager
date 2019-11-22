install: in_virtual_env
	@echo "✨ Upgrading pip"
	@pip install --upgrade pip --quiet

	@echo "✨ Installing requirements"
	@pip install -e '.[test,dev]' --upgrade-strategy=eager --quiet

	@echo "✨ Gathering external sources in ./eggs folder"
	@rm -rf ./eggs
	@scrambler --target eggs 2>&1 | grep -v Skipping || true
	@rm -rf ./eggs/apimanager

update: in_virtual_env

	# update all dependencies
	pip list --outdated --format=freeze |  sed 's/==/>/g' | pip install --upgrade -r /dev/stdin

	# apply install step to avoid deviations
	make install

test: in_virtual_env
	@echo "✨ Running flake8"
	@flake8

	@echo "✨ Running py.test"
	@py.test

in_virtual_env:
	@if python -c 'import sys; (hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)) and sys.exit(1) or sys.exit(0)'; then \
		echo "An active virtual environment is required"; exit 1; \
		else true; fi
