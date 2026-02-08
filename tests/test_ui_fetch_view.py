import sys
import os
import gazu
import gazu

# Add project root path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from project_ingester.utils.compat import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem, QTextEdit, QSplitter, QAction, QMenu, Qt
from project_ingester.kitsu_config import KITSU_HOST, KITSU_EMAIL, KITSU_PASSWORD

class KitsuInspector(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kitsu Project Inspector")
        self.resize(1000, 700)
        
        # Central Widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        # Splitter (Tree | Details)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 1. Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Entity", "Type"])
        self.tree.setColumnWidth(0, 300)
        self.tree.itemClicked.connect(self.on_item_clicked)
        splitter.addWidget(self.tree)
        
        # 2. Details (HTML)
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setStyleSheet("background-color: #f5f5f5; color: #333; font-family: Consolas, monospace;")
        splitter.addWidget(self.details)
        
        splitter.setSizes([400, 600])

        # Menu Bar
        self.create_menus()
        
        self.projects = []

    def create_menus(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        
        # 1. Connect
        action_connect = QAction("Connect", self)
        action_connect.triggered.connect(self.connect_kitsu)
        file_menu.addAction(action_connect)
        
        # 2. Fetch (Submenu holder)
        self.fetch_menu = file_menu.addMenu("Fetch Projects")

        # QMenu doesn't signal click easily. Better: Action "Fetch Projects" that populates a list or a separate dialog?
        # User said: "fetch - once clicked this , will fetch all ... as its sub menu"
        # So "Fetch" is a submenu? 
        # Standard: Click "Fetch Projects" parent menu -> it opens -> populates. 
        # But fetching takes time. 
        # Let's add a "Refresh Projects List" action inside.
        
        refresh_action = QAction("Refresh List...", self)
        refresh_action.triggered.connect(self.fetch_projects)
        self.fetch_menu.addAction(refresh_action)
        self.fetch_menu.addSeparator()

    def connect_kitsu(self):
        try:
            print(f"Connecting to {KITSU_HOST}...")
            gazu.set_host(KITSU_HOST)
            gazu.log_in(KITSU_EMAIL, KITSU_PASSWORD)
            print("Connected!")
            self.setWindowTitle("Kitsu Project Inspector - [Connected]")
        except Exception as e:
            print(f"Connection Failed: {e}")
            self.details.setText(f"Connection Error:\n{e}")

    def fetch_projects(self):
        try:
            print("Fetching Projects...")
            self.fetch_menu.clear()
            
            # Re-add Refresh
            refresh_action = QAction("Refresh List...", self)
            refresh_action.triggered.connect(self.fetch_projects)
            self.fetch_menu.addAction(refresh_action)
            self.fetch_menu.addSeparator()
            
            projects = gazu.project.all_open_projects()
            for p in projects:
                action = QAction(p['name'], self)
                # Capture closure
                action.triggered.connect(lambda checked=False, proj=p: self.load_project(proj))
                self.fetch_menu.addAction(action)
                
            print(f"Index {len(projects)} projects.")
            
        except Exception as e:
            print(f"Fetch Failed: {e}")

    def load_project(self, project):
        print(f"Loading Project: {project['name']}")
        self.tree.clear()
        self.setWindowTitle(f"Kitsu Inspector - Loading {project['name']}...")
        QApplication.processEvents() # Force update
        
        # Add Project Root
        root = QTreeWidgetItem(self.tree)
        root.setText(0, project['name'])
        root.setText(1, "Project")
        root.setData(0, Qt.UserRole, {"type": "project", "data": project})
        
        try:
            # 1. Assets
            print("Fetching Assets...")
            assets = gazu.asset.all_assets_for_project(project)
            if assets:
                assets_root = QTreeWidgetItem(root)
                assets_root.setText(0, "Assets")
                
                # Group by Type
                grouped = {}
                for asset in assets:
                    # Kitsu assets usually have 'asset_type_name' or similar
                    # Or we fetch asset types mapping.
                    # 'asset_type_name' might be in the dict if expanded? 
                    # If not, we might check 'entity_type_id' or similar.
                    # Standard gazu usually returns 'asset_type_name' or we must fetch types.
                    # Let's check 'asset_type_name'.
                    at_name = asset.get('asset_type_name', 'Unknown')
                    if at_name not in grouped: grouped[at_name] = []
                    grouped[at_name].append(asset)
                
                for at_name, asset_list in grouped.items():
                    at_node = QTreeWidgetItem(assets_root)
                    at_node.setText(0, at_name)
                    at_node.setText(1, "Asset Type")
                    # Asset Type Data? We don't have the specific AT object here, just name.
                    # Mock it or leave empty.
                    
                    for asset in asset_list:
                        a_node = QTreeWidgetItem(at_node)
                        a_node.setText(0, asset['name'])
                        a_node.setText(1, "Asset")
                        a_node.setData(0, Qt.UserRole, {"type": "asset", "data": asset})

            # 2. Shots Hierarchy
            print("Fetching Hierarchy...")
            
            # Check Production Type
            prod_type = project.get('production_type', 'short')
            
            if prod_type == 'tv_show':
                # TV Logic: Episodes -> Sequences -> Shots
                episodes = gazu.shot.all_episodes_for_project(project)
                if episodes:
                    ep_folder = QTreeWidgetItem(root)
                    ep_folder.setText(0, "Episodes")
                    for ep in episodes:
                        ep_node = QTreeWidgetItem(ep_folder)
                        ep_node.setText(0, ep['name'])
                        ep_node.setText(1, "Episode")
                        ep_node.setData(0, Qt.UserRole, {"type": "episode", "data": ep})
                        
                        # Sequences
                        seqs = gazu.shot.all_sequences_for_episode(ep)
                        for seq in seqs:
                            seq_node = QTreeWidgetItem(ep_node)
                            seq_node.setText(0, seq['name'])
                            seq_node.setText(1, "Sequence")
                            seq_node.setData(0, Qt.UserRole, {"type": "sequence", "data": seq})
                            
                            # Shots
                            shots = gazu.shot.all_shots_for_sequence(seq)
                            for shot in shots:
                                shot_node = QTreeWidgetItem(seq_node)
                                shot_node.setText(0, shot['name'])
                                shot_node.setText(1, "Shot")
                                shot_node.setData(0, Qt.UserRole, {"type": "shot", "data": shot})
            else:
                # Film/Short Logic: Sequences -> Shots
                # Some workflows might skip sequences, but usually Sequences -> Shots
                # Fetch Sequences for Project
                seqs = gazu.shot.all_sequences_for_project(project)
                if seqs:
                    for seq in seqs:
                        seq_node = QTreeWidgetItem(root)
                        seq_node.setText(0, seq['name'])
                        seq_node.setText(1, "Sequence")
                        seq_node.setData(0, Qt.UserRole, {"type": "sequence", "data": seq})
                        
                        shots = gazu.shot.all_shots_for_sequence(seq)
                        for shot in shots:
                            shot_node = QTreeWidgetItem(seq_node)
                            shot_node.setText(0, shot['name'])
                            shot_node.setText(1, "Shot")
                            shot_node.setData(0, Qt.UserRole, {"type": "shot", "data": shot})
            
            root.setExpanded(True)
            self.on_item_clicked(root, 0)
            self.setWindowTitle(f"Kitsu Inspector - {project['name']}")
            
        except Exception as e:
            print(f"Error loading children: {e}")
            self.setWindowTitle("Kitsu Inspector - Error")

    def on_item_clicked(self, item, col):
        payload = item.data(0, Qt.UserRole)
        if not payload: return
        
        entity_type = payload.get('type')
        data = payload.get('data', {})
        
        self.display_entity(entity_type, data)

    def display_entity(self, entity_type, data):
        # Classify Parameters
        core = ["name", "code"]
        update = ["description", "data"]
        system = ["id", "created_at", "updated_at", "type", "project_id", "entity_type_id"]
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Consolas, monospace; padding: 10px; }}
                h2 {{ color: #333; border-bottom: 2px solid #ccc; padding-bottom: 5px; }}
                .section {{ margin-bottom: 15px; border-left: 5px solid #ccc; padding-left: 10px; }}
                .core {{ border-color: #4CAF50; }}
                .update {{ border-color: #2196F3; }}
                .system {{ border-color: #9E9E9E; }}
                .label {{ font-weight: bold; color: #555; }}
                .value {{ color: #000; }}
                h3 {{ margin: 5px 0; font-size: 14px; color: #666; }}
            </style>
        </head>
        <body>
            <h2>{str(entity_type).upper()} DETAILS</h2>
        """
        
        # Helper to render dict
        def render_section(title, css_class, keys, source):
            section_html = f'<div class="section {css_class}">'
            section_html += f"<h3>{title}</h3>"
            has_content = False
            
            for k in keys:
                if k in source:
                    val = source[k]
                    # Format dicts neatly
                    if isinstance(val, dict):
                        import json
                        val = f"<pre>{json.dumps(val, indent=2)}</pre>"
                    elif isinstance(val, list):
                        val = f"{val}"
                    
                    section_html += f"<div><span class='label'>{k}:</span> <span class='value'>{val}</span></div>"
                    has_content = True
            
            # Special case for 'data' dictionary which might have remaining keys
            # In Core/Update split, 'data' is usually in Update.
            
            section_html += "</div>"
            return section_html if has_content else ""

        html += render_section("MANDATORY (Core)", "core", core, data)
        html += render_section("OPTIONAL (Update)", "update", update, data)
        html += render_section("SYSTEM (Generated)", "system", system, data)
        
        html += "</body></html>"
        self.details.setHtml(html)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = KitsuInspector()
    window.show()
    sys.exit(app.exec_())
