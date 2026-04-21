echo "Storing the current python path"
PYTHON_PATH="$(poetry run which python3)"

poetry run tox run "$@"