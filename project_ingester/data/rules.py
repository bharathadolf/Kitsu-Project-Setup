# ============================================================================
# RULE MAPS
# ============================================================================

FEATURE_FILM_RULES = {
    "project": {"children": ["sequence", "asset_type"], "deletable": False},
    "sequence": {"children": ["shot"], "deletable": True},
    "shot": {"children": [], "deletable": True},
    "asset_type": {"children": ["asset"], "deletable": True},
    "asset": {"children": [], "deletable": True}
}

TV_SHOW_RULES = {
    "project": {"children": ["episode", "asset_type"], "deletable": False},
    "episode": {"children": ["sequence"], "deletable": True},
    "sequence": {"children": ["shot"], "deletable": True},
    "shot": {"children": [], "deletable": True},
    "asset_type": {"children": ["asset"], "deletable": True},
    "asset": {"children": [], "deletable": True}
}

SHOTS_ONLY_RULES = {
    "project": {"children": ["sequence"], "deletable": False},
    "sequence": {"children": ["shot"], "deletable": True},
    "shot": {"children": [], "deletable": True}
}

ASSET_ONLY_RULES = {
    "project": {"children": ["asset_type"], "deletable": False},
    "asset_type": {"children": ["asset"], "deletable": True},
    "asset": {"children": [], "deletable": True}
}

CUSTOM_RULES = {
    "project": {"children": ["episode", "sequence", "asset_type"], "deletable": False},
    "episode": {"children": ["sequence"], "deletable": True},
    "sequence": {"children": ["shot"], "deletable": True},
    "shot": {"children": [], "deletable": True},
    "asset_type": {"children": ["asset"], "deletable": True},
    "asset": {"children": [], "deletable": True}
}

RULE_MAP = {
    "Feature Film": FEATURE_FILM_RULES,
    "TV Show": TV_SHOW_RULES,
    "Shots Only": SHOTS_ONLY_RULES,
    "Asset Only": ASSET_ONLY_RULES,
    "Custom": CUSTOM_RULES
}
