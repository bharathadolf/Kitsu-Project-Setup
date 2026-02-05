import unittest
import sys
# Only allow importing gazu, no other project files
try:
    import gazu
except ImportError:
    print("Error: 'gazu' module not found. Please pip install gazu.")
    sys.exit(1)

# ============================================================================
# CONFIGURATION (Embedded for independent testing)
# ============================================================================
KITSU_HOST = "http://192.100.0.112/api"
KITSU_EMAIL = "adolfbharath@gmail.com"
KITSU_PASSWORD = "Bharath@2026"


# ============================================================================
# LOGIC UNDER TEST (Mirroring project_ingester.entities.project)
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

def generate_project_payload(name, preset_name="short", root_path="/mnt/nas/projects"):
    """
    Generates the 'data' and 'file_tree' for a project based on the schema.
    """
    if preset_name not in ENTITIES_PRESETS:
        preset_name = "custom"
        
    entities_config = ENTITIES_PRESETS[preset_name]
    
    # Construct "data"
    data = {
        "schema_version": 4,
        "preset": {"name": preset_name},
        "storage": {"root_path": root_path},
        "paths": {"project_root": f"{root_path}/{name}"},
        "entities": {k: {"enabled": v} for k, v in entities_config.items()}
    }

    file_tree = get_file_tree_template()
    return data, file_tree

def get_or_create_project(name, production_type="short", production_style="2d3d", preset="film", root_path="/mnt/nas/projects", fps=24, ratio="1.78", resolution="1920x1080", description=""):
    """
    Get or create a project in Kitsu with validated schema data.
    """
    project = gazu.project.get_project_by_name(name)
    if not project:
        project = gazu.project.new_project(name, production_type=production_type, production_style=production_style)
        print(f"Created Project: {name}")
    else:
        print(f"Found Project: {name}")

    # Generate Schema Data
    data, file_tree = generate_project_payload(name, preset_name=preset, root_path=root_path)

    # Update optional fields + Schema Data
    update_data = {
        "data": data,
        "file_tree": file_tree,
        "description": description
    }
    
    if fps: update_data["fps"] = int(fps)
    if ratio: update_data["ratio"] = str(ratio)
    if resolution: update_data["resolution"] = str(resolution)
    
    # In standalone test, gazu might not be mocked, but we are connecting to real gazu
    gazu.raw.update("projects", project["id"], update_data)
    
    # Refresh to get latest
    project = gazu.project.get_project(project["id"])
    return project

# ============================================================================
# TEST EXECUTION
# ============================================================================
class TestProjectEntity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print(f"Connecting to Kitsu at {KITSU_HOST}...")
        gazu.client.set_host(KITSU_HOST)
        try:
            gazu.log_in(KITSU_EMAIL, KITSU_PASSWORD)
            print("Successfully connected to Kitsu.")
        except Exception as e:
            raise Exception(f"Failed to connect to Kitsu: {e}")

    def test_get_or_create_project(self):
        project_name = "Test_Project_Entity_Standalone"
        print(f"\n[TEST] Testing get_or_create_project for '{project_name}'...")
        
        try:

            project = get_or_create_project(
                name=project_name,
                production_type="short",
                production_style="2d3d",
                preset="film",
                root_path="T:/Production 2026",
                description="Schema Test Project"
            )
            


            self.assertIsNotNone(project, "Project should not be None")
            self.assertEqual(project["name"], project_name, "Project name should match")
            
            print(f"[SUCCESS] Project retrieved successfully.")
            
            # Categorize parameters
            categories = {
                "Mandatory Parameters": ["name", "production_type"],
                "Custom Parameters": ["data", "file_tree", "code", "homepage"],
                "Optional Parameters": [
                    "description", "fps", "ratio", "resolution", "production_style", 
                    "start_date", "end_date", "man_days", "nb_episodes", "episode_span", 
                    "max_retakes", "is_clients_isolated", "is_preview_download_allowed", 
                    "is_set_preview_automated", "is_publish_default_for_artists", 
                    "hd_bitrate_compression", "ld_bitrate_compression"
                ],
                "Not Useful / System Parameters": [
                    "id", "created_at", "updated_at", "type", "project_status_id", 
                    "default_preview_background_file_id", "has_avatar", "shotgun_id"
                ]
            }

            all_keys = set(project.keys())
            categorized_keys = set()

            for category, keys in categories.items():
                print(f"\n{'='*60}")
                print(f"{category.upper()}:")
                print(f"{'='*60}")
                for key in keys:
                    if key in project:
                        print(f"{key}: {project[key]}")
                        categorized_keys.add(key)
            
            # Print any remaining keys
            uncategorized = all_keys - categorized_keys
            if uncategorized:
                print(f"\n{'='*60}")
                print("UNCATEGORIZED PARAMETERS:")
                print(f"{'='*60}")
                for key in uncategorized:
                    print(f"{key}: {project[key]}")
            print(f"{'='*60}\n")
            
        except Exception as e:
            self.fail(f"get_or_create_project failed with error: {e}")

if __name__ == "__main__":
    unittest.main()
