default: black isort unimport

# Format with black formatter
black:
    black src/

# Sort imports using isort
isort:
    isort src/ --profile black

# Remove unused imports using unimport
unimport:
    unimport src/