# Contributing to Imagen Apex

Thank you for your interest in contributing to Imagen Apex! This guide will help you get started.

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Docker (for server development)
- Google Cloud SDK
- Access to HuggingFace SAM 3D models

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/imagen-apex.git
   cd imagen-apex
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

## 📝 Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines
- Use type hints for function signatures
- Write docstrings for public functions and classes
- Keep lines under 100 characters

### Formatting

```bash
# Format code
black src/ server/ deploy/

# Check linting
flake8 src/ server/ deploy/

# Type checking
mypy src/
```

## 🔀 Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clear, descriptive commit messages
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   pytest tests/
   ```

4. **Submit a pull request**
   - Provide a clear description of the changes
   - Link any related issues
   - Request review from maintainers

## 🐛 Reporting Bugs

Please use GitHub Issues with the following template:

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior.

**Expected behavior**
What you expected to happen.

**Environment**
- OS: [e.g., macOS 14.0]
- Python version: [e.g., 3.11.5]
- Package versions: [output of `pip freeze`]

**Additional context**
Any other context about the problem.
```

## 💡 Feature Requests

We welcome feature requests! Please open an issue with:

- A clear description of the feature
- Use cases and benefits
- Any implementation ideas

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🙏
