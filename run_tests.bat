@echo off
REM Test runner script for Windows

echo Running Django tests...
python manage.py test

echo.
echo Running tests with coverage...
coverage run --source=. manage.py test
coverage report
coverage html

echo.
echo Coverage report generated in htmlcov\index.html
pause

