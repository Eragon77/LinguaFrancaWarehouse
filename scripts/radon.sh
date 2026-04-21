#!/bin/bash
if [ ! -d "randon/" ]; then
  mkdir randon/
fi

poetry run radon cc "$1" --total-average -s -o SCORE --min C -j | python3 -m json.tool > randon/radon_cc_result.json
poetry run radon mi "$1" --min B -j | python3 -m json.tool > randon/radon_mi_result.json
poetry run radon hal "$1" -j | python3 -m json.tool > randon/radon_hal_result.json
poetry run radon raw "$1" -j | python3 -m json.tool > randon/radon_raw_result.json