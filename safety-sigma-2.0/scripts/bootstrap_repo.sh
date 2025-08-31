#!/bin/bash
set -euo pipefail

echo "🚀 Bootstrapping Safety Sigma 2.0 Repository..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    log_error "pyproject.toml not found. Run this script from the safety-sigma-2.0 root directory."
    exit 1
fi

log_info "Checking Python version..."
if ! python3 --version | grep -q "Python 3\.[9-9]"; then
    if ! python3 --version | grep -q "Python 3\.1[0-9]"; then
        log_warning "Python 3.9+ recommended. Current version: $(python3 --version)"
    fi
fi

# Create virtual environment
log_info "Creating Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    log_success "Virtual environment created at .venv/"
else
    log_info "Virtual environment already exists"
fi

# Activate virtual environment
log_info "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
log_info "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
log_info "Installing project dependencies..."
pip install -e ".[dev]"

# Create __init__.py files for all packages
log_info "Creating package __init__.py files..."
for dir in analysis agents drivers orchestration tools workflow metrics adaptive; do
    touch "$dir/__init__.py"
done

# Create safety_sigma package
log_info "Creating safety_sigma package structure..."
mkdir -p safety_sigma
touch safety_sigma/__init__.py

# Set up Safety Sigma 1.0 reference (read-only)
SS1_PATH="../Desktop/safety_sigma/phase_1"
if [ -d "$SS1_PATH" ]; then
    log_success "Found Safety Sigma 1.0 at $SS1_PATH"
    # Create symbolic link for easy access
    if [ ! -L "safety_sigma_1.0" ]; then
        ln -s "$SS1_PATH" safety_sigma_1.0
        log_success "Created symbolic link: safety_sigma_1.0 -> $SS1_PATH"
    fi
else
    log_warning "Safety Sigma 1.0 not found at expected path: $SS1_PATH"
    log_warning "Update SS1_PATH in .env if needed for parity testing"
fi

# Set up environment file
log_info "Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    log_success "Created .env from .env.example"
    log_warning "Please configure API keys in .env file"
else
    log_info ".env file already exists"
fi

# Create audit directories
log_info "Creating audit and log directories..."
mkdir -p audit_logs logs outputs

# Create Makefile
log_info "Creating Makefile..."
cat > Makefile << 'EOF'
.PHONY: bootstrap test lint demo clean test-parity help

# Default target
help:
	@echo "Safety Sigma 2.0 - Available targets:"
	@echo "  bootstrap     - Initialize repository and dependencies"
	@echo "  test         - Run all tests including parity checks"
	@echo "  test-parity  - Run parity tests against Safety Sigma 1.0"
	@echo "  lint         - Run code formatting and linting"
	@echo "  demo         - Run demo with sample data"
	@echo "  clean        - Clean build artifacts and caches"

bootstrap:
	@./scripts/bootstrap_repo.sh

test:
	@echo "Running all tests..."
	@source .venv/bin/activate && python -m pytest tests/ -v

test-parity:
	@echo "Running parity tests..."
	@source .venv/bin/activate && python -m pytest tests/test_parity_baseline.py -v

test-stage1:
	@echo "Running Stage 1 tests with tools enabled..."
	@source .venv/bin/activate && SS2_ENABLE_TOOLS=true python -m pytest tests/ -v -k "stage1"

test-stage2:
	@echo "Running Stage 2 tests with agent enabled..."
	@source .venv/bin/activate && SS2_USE_AGENT=true python -m pytest tests/ -v -k "stage2"

lint:
	@echo "Running code formatting and linting..."
	@source .venv/bin/activate && black safety_sigma/ tests/ --check
	@source .venv/bin/activate && isort safety_sigma/ tests/ --check-only
	@source .venv/bin/activate && flake8 safety_sigma/ tests/

format:
	@echo "Formatting code..."
	@source .venv/bin/activate && black safety_sigma/ tests/
	@source .venv/bin/activate && isort safety_sigma/ tests/

demo:
	@echo "Running demo..."
	@source .venv/bin/activate && python -m safety_sigma.demo

clean:
	@echo "Cleaning build artifacts..."
	@rm -rf build/ dist/ *.egg-info/
	@find . -type d -name __pycache__ -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
EOF

log_success "Created Makefile with common targets"

# Run initial tests to verify setup
log_info "Running initial verification..."
if python -c "import safety_sigma" 2>/dev/null; then
    log_success "Package import successful"
else
    log_warning "Package import failed - this is expected until Stage 1 implementation"
fi

log_success "🎉 Bootstrap complete!"
log_info "Next steps:"
log_info "  1. Configure API keys in .env file"
log_info "  2. Run 'make test' to verify setup"
log_info "  3. Run 'make demo' to test basic functionality"
log_info "  4. Begin Stage 1 implementation"

echo ""
log_info "Repository structure:"
find . -type d -maxdepth 2 | head -20 | sed 's|^\./||' | sort