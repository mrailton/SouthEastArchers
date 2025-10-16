#!/bin/bash
# Test runner script for South East Archers

echo "🏹 South East Archers Test Suite"
echo "================================"
echo ""

# Check if pytest is installed
if ! python -m pytest --version > /dev/null 2>&1; then
    echo "❌ pytest not installed. Installing dependencies..."
    pip install -r requirements.txt
fi

# Parse command line arguments
case "$1" in
    "coverage")
        echo "📊 Running tests with coverage..."
        python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html -v
        echo ""
        echo "✅ Coverage report generated in htmlcov/index.html"
        ;;
    "fast")
        echo "⚡ Running tests (fast mode)..."
        python -m pytest tests/ -q
        ;;
    "verbose")
        echo "📝 Running tests (verbose mode)..."
        python -m pytest tests/ -vv --tb=short
        ;;
    "watch")
        echo "👀 Running tests in watch mode..."
        python -m pytest tests/ --looponfail
        ;;
    "specific")
        if [ -z "$2" ]; then
            echo "❌ Please specify test file or pattern"
            echo "Usage: ./run_tests.sh specific test_app.py"
            exit 1
        fi
        echo "🎯 Running specific tests: $2"
        python -m pytest tests/ -k "$2" -v
        ;;
    "help"|"-h"|"--help")
        echo "Usage: ./run_tests.sh [option]"
        echo ""
        echo "Options:"
        echo "  (none)      Run all tests with standard output"
        echo "  coverage    Run tests with coverage report"
        echo "  fast        Run tests in quiet mode"
        echo "  verbose     Run tests with detailed output"
        echo "  specific    Run specific test (requires pattern)"
        echo "  help        Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./run_tests.sh"
        echo "  ./run_tests.sh coverage"
        echo "  ./run_tests.sh specific test_admin"
        ;;
    *)
        echo "🧪 Running all tests..."
        python -m pytest tests/ -v
        ;;
esac

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✅ All tests passed!"
else
    echo ""
    echo "❌ Some tests failed. Check output above for details."
fi

exit $exit_code
