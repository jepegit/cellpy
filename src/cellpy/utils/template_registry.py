"""Registered cookiecutter batch templates (GitHub-hosted)."""

_GITHUB_REPO_PARENT = "jepegit"
_GITHUB_TEMPLATES_REPO = "cellpy_cookies.git"

STANDARD_TEMPLATE_URI = f"https://github.com/{_GITHUB_REPO_PARENT}/{_GITHUB_TEMPLATES_REPO}"

REGISTERED_TEMPLATES = {
    "standard": (STANDARD_TEMPLATE_URI, "standard"),
    "ife": (STANDARD_TEMPLATE_URI, "ife"),
    "single": (STANDARD_TEMPLATE_URI, "single"),
}
