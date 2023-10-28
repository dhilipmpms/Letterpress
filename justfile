default: black isort

format: black unimport isort
test: codespell

# Format with black formatter
black:
    black src/

# Sort imports using isort
isort:
    isort src/ --profile black

# Remove unused imports using unimport
unimport:
    unimport src/

# Check for typos with codespell
codespell:
    codespell --skip po
