py.test --cov argh --cov-report term --cov-report html "$@" \
    && uzbl-browser htmlcov/index.html
