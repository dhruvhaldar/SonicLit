#!/bin/bash
export PYTHONPATH=/app/src:$PYTHONPATH
pytest tests/ --ignore=tests/test_gui_e2e.py
