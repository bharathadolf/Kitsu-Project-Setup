

import sys
import os
import shutil

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from project_ingester.utils.compat import QtWidgets, QtCore, QApplication
from project_ingester.ui.dialogs_builder import FolderBuilderDialog


def create_dummy_structure(base_path):
    # Scene 1: Direct Children (Sequences directly in root)
    # Actually, let's make a "ProjectA" with direct children
    proj_a = os.path.join(base_path, "ProjectA")
    os.makedirs(proj_a, exist_ok=True)
    os.makedirs(os.path.join(proj_a, "sq01"), exist_ok=True)
    os.makedirs(os.path.join(proj_a, "sq02"), exist_ok=True)
    
    # Subfolders for sq01 (Shots)
    # Let's say sq01 has "shots" folder
    os.makedirs(os.path.join(proj_a, "sq01", "shots", "sh010"), exist_ok=True)
    os.makedirs(os.path.join(proj_a, "sq01", "shots", "sh020"), exist_ok=True)
    
    # sq02 has NO shots folder, but maybe direct shots?
    os.makedirs(os.path.join(proj_a, "sq02", "sh010"), exist_ok=True)

    # Scene 2: Explicit Folder (Sequences in 'sequences' folder)
    proj_b = os.path.join(base_path, "ProjectB")
    os.makedirs(proj_b, exist_ok=True)
    os.makedirs(os.path.join(proj_b, "sequences", "sq01"), exist_ok=True)
    
    return proj_a, proj_b

def main():
    app = QtWidgets.QApplication(sys.argv)
    
    # Setup dummy data
    temp_dir = os.path.join(current_dir, "temp_test_data")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)
    
    proj_a, proj_b = create_dummy_structure(temp_dir)
    


    # Log to file
    log_file = os.path.join(current_dir, "test_ui_log.txt")
    
    def log(msg):
        with open(log_file, "a") as f:
            f.write(msg + "\n")
        print(msg)
        
    if os.path.exists(log_file):
        os.remove(log_file)
        

    log("Starting Test...")
    log(f"Sys Path: {sys.path}")
    

    try:
        dialog = FolderBuilderDialog()
        log("Dialog Created.")
        
        # Set Template to "Shots Only" (matches user case)
        index = dialog.template_combo.findText("Shots Only")
        if index >= 0:
            dialog.template_combo.setCurrentIndex(index)
            log("Template set to Shots Only.")
        
        log(f"--- TEST 1: Direct Children (ProjectA) ---")
        log(f"Path: {proj_a}")
        dialog.project_root = proj_a
        dialog.root_edit.setText(proj_a)
        dialog.refresh_tree()
        log("Tree Refreshed.")
        
        # Check Root
        root_item = dialog.tree.topLevelItem(0)
        log(f"Root Expanded: {root_item.isExpanded()}") 
        
        seq_category = None
        for i in range(root_item.childCount()):
            child = root_item.child(i)
            # Case-insensitive check
            if "sequence" in child.text(0).lower():
                seq_category = child
                break
                
        if seq_category:
            widget = dialog.tree.itemWidget(seq_category, 1)
            combo_text = widget.currentText()
            log(f"Sequence Category Selection: {combo_text}") 
            log(f"Sequence Category Child Count: {seq_category.childCount()}")
            log(f"Sequence Category Expanded: {seq_category.isExpanded()}")
            

            # Check sq01
            if seq_category.childCount() > 0:
                sq01 = seq_category.child(0)
                log(f"Instance 1: {sq01.text(0)}")
                log(f"Instance 1 Expanded: {sq01.isExpanded()}") # Should be False (Collapsed)
                
                shot_cat_sq01 = sq01.child(0)
                widget_sq01 = dialog.tree.itemWidget(shot_cat_sq01, 1)
                log(f"sq01 Shot Selection: {widget_sq01.currentText()}")
                # log(f"sq01 Shot Expanded: {shot_cat_sq01.isExpanded()}")

            # Check sq02
            if seq_category.childCount() > 1:
                sq02 = seq_category.child(1)
                log(f"Instance 2: {sq02.text(0)}")
                log(f"Instance 2 Expanded: {sq02.isExpanded()}") # Should be False
                
                shot_cat_sq02 = sq02.child(0)
                widget_sq02 = dialog.tree.itemWidget(shot_cat_sq02, 1)
                log(f"sq02 Shot Selection: {widget_sq02.currentText()}")
                # log(f"sq02 Shot Expanded: {shot_cat_sq02.isExpanded()}")
        else:
            log("ERROR: Sequence Category not found.")
            
        # Check Stats Log
        stats_text = dialog.log_edit.toPlainText()
        log(f"Stats Log Content:\n{stats_text}")
        
        # Verify stats?
        # Level 1 Entities: 2
        # Level 2 Entities: 3 (sq01->sh010, sh020; sq02->sh010). Total 3 shots.
        # Wait, sq01 has 2 shots. sq02 has 1 shot. Total 3.

        
        # Scene 2
        log(f"\n--- TEST 2: Empty Root ---")
        empty_dir = os.path.join(temp_dir, "EmptyProject")
        os.makedirs(empty_dir, exist_ok=True)
        dialog.project_root = empty_dir
        dialog.refresh_tree()
        
        root_item = dialog.tree.topLevelItem(0)
        log(f"Empty Root Expanded: {root_item.isExpanded()}")
        
        seq_category = root_item.child(0)
        widget = dialog.tree.itemWidget(seq_category, 1)
        log(f"Empty Sequence Selection: {widget.currentText()}")
        
        log("Test Complete.")

    except Exception as e:
        import traceback
        log(f"CRASH: {e}")
        log(traceback.format_exc())
    # sys.exit(app.exec_()) # Don't block


if __name__ == "__main__":
    main()
