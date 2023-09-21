.PHONY: pip_install
pip_install:
	pipenv install --dev
	pip install --upgrade build


.PHONY: test
test:
	pytest -v --cov --cov-report=term --cov-report=html


.PHONY: build
build: clean docs
	python -m build
	twine check dist/*


.PHONY: clean
clean:
	rm -rf ./dist/*
	rm -rf ./htmlcov


.PHONY: docs
docs:
	rm -rf ./docs/*
	pdoc --html --output-dir ./docs ./src/dotchain
	mv ./docs/dotchain/* ./docs/
	rmdir ./docs/dotchain


.PHONY: install_local
install_local:
	pip install -e .


.PHONY: publish
publish: build
	python -m twine upload dist/*


.PHONY: uninstall
uninstall:
	pip uninstall -y dotchain
