from aiz.settings import TEMPLATES

TEMPLATES[0]["OPTIONS"]["context_processors"].append(
    "aiz_crumbs.context_processors.breadcrumbs",
)
