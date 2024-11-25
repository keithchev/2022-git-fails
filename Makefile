setup-dev:
	pip install -e .'[dev]'
	
lint:
	flake8 ./ --count --statistics --exit-zero
	python -m pylint gitfails

format:
	black .

pre-commit:
	pre-commit run --all-files

test:
	pytest -v
