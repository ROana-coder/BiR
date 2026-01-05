"""SPARQL template loader using Jinja2."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

# Template directory
TEMPLATE_DIR = Path(__file__).parent / "templates"

# Jinja2 environment with proper escaping disabled for SPARQL
_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape([]),  # No HTML escaping for SPARQL
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_sparql(template_name: str, **kwargs) -> str:
    """Render a SPARQL template with given parameters.
    
    Args:
        template_name: Name of template file (e.g., 'search_books.sparql')
        **kwargs: Template variables
        
    Returns:
        Rendered SPARQL query string
    
    Example:
        query = render_sparql(
            "search_books.sparql",
            country_qid="Q30",
            year_start=1920,
            year_end=1930,
            limit=50
        )
    """
    template = _env.get_template(template_name)
    return template.render(**kwargs)


def get_template_names() -> list[str]:
    """Get list of available template names."""
    return [p.name for p in TEMPLATE_DIR.glob("*.sparql")]
