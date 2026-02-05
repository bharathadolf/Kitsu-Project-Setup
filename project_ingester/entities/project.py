import gazu


# ============================================================================
# PRESETS & SCHEMA
# ============================================================================
ENTITIES_PRESETS = {
    "film": {"asset": True, "episode": False, "sequence": True, "shot": True, "task": True},
    "tv": {"asset": True, "episode": True, "sequence": True, "shot": True, "task": True},
    "short": {"asset": True, "episode": False, "sequence": True, "shot": True, "task": True},
    "shots_only": {"asset": False, "episode": False, "sequence": True, "shot": True, "task": True},
    "assets_only": {"asset": True, "episode": False, "sequence": False, "shot": False, "task": True},
    "custom": {"asset": True, "episode": True, "sequence": True, "shot": True, "task": True},
}

def get_file_tree_template():
    return {
        "assets": {
            "{asset_type}": {
                "{asset_name}": {
                    "{task_type}": {"work": {}, "publish": {}}
                }
            }
        },
        "episodes": {
            "{episode}": {
                "{sequence}": {
                    "{shot}": {
                        "{task_type}": {"work": {}, "publish": {}}
                    }
                }
            }
        },
        "film": {
            "{sequence}": {
                "{shot}": {
                    "{task_type}": {"work": {}, "publish": {}}
                }
            }
        },
        "shared": {
            "reference": {},
            "docs": {},
            "lut": {}
        }
    }

def generate_project_payload(name, production_type="film", root_path="E:/Data", project_code=None):
    """
    Generates the 'data' for a project based on the user's specified schema.
    """
    if not project_code:
        project_code = name.lower()[:3] # Fallback, though usually provided
        
    project_path = f"{root_path}/{project_code}"
    
    # Base Data
    data = {
        "root_path": root_path,
        "project_code": project_code,
        "project_path": project_path,
        "production_type": production_type,
        "project_tree": {}
    }

    # Tree Structure Logic
    if production_type == "film":
        data["project_tree"] = {
            "film": {
                "{sequence}": {
                    "{shot}": {
                        "{task_type}": {"work": {}, "publish": {}}
                    }
                }
            },
            "assets": {
                "{asset_type}": {
                    "{asset_name}": {
                        "{task_type}": {"work": {}, "publish": {}}
                    }
                }
            },
            "shared": {"lut": {}, "docs": {}, "reference": {}}
        }
    elif production_type == "tv":
        data["project_tree"] = {
            "{episode}": {
                "{sequence}": {
                    "{shot}": {
                        "{task_type}": {"work": {}, "publish": {}}
                    }
                }
            },
            "assets": {
                "{asset_type}": {
                    "{asset_name}": {
                        "{task_type}": {"work": {}, "publish": {}}
                    }
                }
            },
            "shared": {"lut": {}, "docs": {}, "reference": {}}
        }
    elif production_type == "shots_only":
        data["project_tree"] = {
            "shots": {
                "{shot}": {
                    "{task_type}": {"work": {}, "publish": {}}
                }
            },
            "shared": {"lut": {}, "docs": {}, "reference": {}}
        }
    elif production_type == "assets_only":
        data["project_tree"] = {
            "assets": {
                "{asset_type}": {
                    "{asset_name}": {
                        "{task_type}": {"work": {}, "publish": {}}
                    }
                }
            },
            "shared": {"lut": {}, "docs": {}, "reference": {}}
        }
    elif production_type == "custom":
        data["project_tree"] = {
            "{episode}": {
                "{sequence}": {
                    "{shot}": {
                        "{task_type}": {"work": {}, "publish": {}}
                    }
                }
            },
            "film": {
                "{sequence}": {
                    "{shot}": {
                        "{task_type}": {"work": {}, "publish": {}}
                    }
                }
            },
            "assets": {
                "{asset_type}": {
                    "{asset_name}": {
                        "{task_type}": {"work": {}, "publish": {}}
                    }
                }
            },
            "shared": {"lut": {}, "docs": {}, "reference": {}}
        }
    
    # Return data and project_tree separately if needed, 
    # but the requirement treats project_tree as PART of data.
    # The original function returned (data, file_tree). 
    # To maintain compatibility with the calling function's unpacking, we return (data, data['project_tree'])
    return data, data["project_tree"]

def get_or_create_project(name, production_type="short", production_style="2d3d", preset="film", root_path="/mnt/nas/projects", fps=24, ratio="1.78", resolution="1920x1080", description="", start_date=None, end_date=None, code=None, custom_data=None, data=None, file_tree=None):
    """
    Get or create a project in Kitsu with validated schema data.
    """
    project = gazu.project.get_project_by_name(name)
    if not project:
        # Create minimal project first
        project = gazu.project.new_project(name, production_type=production_type, production_style=production_style)
        print(f"Created Project: {name}")
    else:
        print(f"Found Project: {name}")

    # Generate Schema Data
    # Mapping 'preset' arg to 'production_type' logic
    gen_data, gen_file_tree = generate_project_payload(name, production_type=preset, root_path=root_path, project_code=code)
    
    # 1. Base is generated data
    final_data = gen_data
    final_file_tree = gen_file_tree
    
    # 2. Update with provided 'data' argument if any (e.g. from UI)
    if data:
        final_data.update(data)
        
    # 3. Merge custom_data if provided
    if custom_data:
        final_data.update(custom_data)
        
    # 4. Override file_tree if provided
    if file_tree:
        final_file_tree = file_tree

    # Update optional fields + Schema Data
    update_data = {
        "data": final_data,
        "file_tree": final_file_tree,
        "description": description
    }
    
    if code: update_data["code"] = code
    if fps: update_data["fps"] = int(fps)
    if ratio: update_data["ratio"] = str(ratio)
    if resolution: update_data["resolution"] = str(resolution)
    if start_date: update_data["start_date"] = start_date
    if end_date: update_data["end_date"] = end_date
    
    gazu.raw.update("projects", project["id"], update_data)
    
    # Refresh to get latest
    project = gazu.project.get_project(project["id"])
    return project
