from ...utils.compat import *
from ...utils.kitsu_fetcher import KitsuFetcher
import gazu

class ProjectHierarchyWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.fetcher = KitsuFetcher()
        self.layout = QVBoxLayout(self)
        
        # Controls
        self.btn_refresh = QPushButton("Refresh Projects")
        self.btn_refresh.clicked.connect(self.refresh_projects)
        self.layout.addWidget(self.btn_refresh)
        
        # Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.layout.addWidget(self.tree)
        
        self.tree.itemExpanded.connect(self.on_item_expanded)
        
    def refresh_projects(self):
        self.tree.clear()
        projects = self.fetcher.get_all_projects()
        
        for proj in projects:
            p_item = QTreeWidgetItem(self.tree)
            p_item.setText(0, proj['name'])
            # Store ID or full object. Converting to dict if it's a gazu object might be safer.
            p_item.setData(0, Qt.UserRole, proj) 
            
            # Add dummy child to make it expandable
            p_item.addChild(QTreeWidgetItem(["Loading..."]))

    def on_item_expanded(self, item):
        # If it has a dummy child, remove it and load real data
        if item.childCount() == 1 and item.child(0).text(0) == "Loading...":
            item.removeChild(item.child(0))
            
            data = item.data(0, Qt.UserRole)
            if not data: return
            
            # Determine type based on hierarchy level or data content
            # Top level items are projects
            if 'production_type' in data or 'type' in data and data['type'] == 'project': # Project
                 self._load_project_hierarchy(item, data)
            elif 'type' in data and data['type'] == 'episode':
                 # If we had lazy loading for episodes -> sequences
                 pass
            
    def _load_project_hierarchy(self, item, project_data):
        hierarchy = self.fetcher.get_project_hierarchy(project_data)
        
        # Episodes
        if 'episodes' in hierarchy:
             for ep_data in hierarchy['episodes']:
                 ep_name = ep_data['entity']['name']
                 ep_item = QTreeWidgetItem(item)
                 ep_item.setText(0, ep_name)
                 # Store entity data if needed
                 
                 for seq_data in ep_data['sequences']:
                     seq_name = seq_data['entity']['name']
                     seq_item = QTreeWidgetItem(ep_item)
                     seq_item.setText(0, seq_name)
                     
                     for shot in seq_data['shots']:
                         shot_name = shot['name']
                         s_item = QTreeWidgetItem(seq_item)
                         s_item.setText(0, shot_name)

        # Sequences (Direct children of project)
        elif 'sequences' in hierarchy:
             for seq_data in hierarchy['sequences']:
                 seq_name = seq_data['entity']['name']
                 seq_item = QTreeWidgetItem(item)
                 seq_item.setText(0, seq_name)
                 
                 for shot in seq_data['shots']:
                     shot_name = shot['name']
                     s_item = QTreeWidgetItem(seq_item)
                     s_item.setText(0, shot_name)
                     
        # Assets
        if 'raw_assets' in hierarchy and hierarchy['raw_assets']:
             assets_root = QTreeWidgetItem(item)
             assets_root.setText(0, "Assets")
             
             # Maybe group by type?
             # Simple list for now as per previous logic
             for asset in hierarchy['raw_assets']:
                 a_item = QTreeWidgetItem(assets_root)
                 a_item.setText(0, asset['name'])
