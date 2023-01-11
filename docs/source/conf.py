import sys
import os

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

sys.path.insert(0, os.path.abspath(os.path.join('..', '..', 'src', 'lib')))
sys.path.insert(0, os.path.abspath(os.path.join('..', '..', 'src', 'Drivers')))
sys.path.insert(0, os.path.abspath(os.path.join('..', '..', 'src', 'Statistics')))
sys.path.insert(0, os.path.abspath(os.path.join('..', '..', 'src', 'RadioMessages')))
sys.path.insert(0, os.path.abspath(os.path.join('..', '..', 'src')))

# This is the expected signature of the handler for this event, cf doc
# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'glactracker_firmware'
copyright = '2023, aaaa'
author = 'aaaa'
release = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon']

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']

# Autodoc config
autodoc_mock_imports = ["adafruit_logging", "board", "busio", "digitalio", "adafruit_ds3231", "storage", "adafruit_datetime", "microcontroller", "glactracker_gps", "ulab", "watchdog", "adafruit_requests", "rtc", "adafruit_fona"]
