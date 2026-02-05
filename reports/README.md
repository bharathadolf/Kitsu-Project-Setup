# Project Creation Refactoring Report

## Overview

As per the development roadmap, the **Project Creation Phase** has been refactored from a monolithic helper script into a modular, entity-based architecture. This ensures better maintainability, scalability, and strict adherence to the "Generate" workflow required by the user.

## Changes Architecture

### 1. Entity Modules (`project_ingester/entities/`)

Each Kitsu entity now has its own dedicated python file handling its specific creation and retrieval logic.

- **`project.py`**: Handles Project creation, updates (FPS, Resolution), and metadata injection.
- **`episode.py`**: Handles Episode creation.
- **`sequence.py`**: Handles Sequence creation (Project-bound or Episode-bound).
- **`shot.py`**: Handles Shot creation and triggers default Task creation (e.g., "Compositing").
- **`asset.py`**: Handles Asset and AssetType creation.
- **`task.py`**: Handles TaskType creation and assigning Tasks to entities.
- **`people.py`**: Wrappers for User/Person retrieval.

### 2. Core Orchestrator (`project_ingester/core/setup.py`)

A new `ProjectManager` class replaces the old `KitsuGenerator`.

- **Context Awareness**: It intelligently resolves the context (Project -> Episode -> Sequence) by walking up the UI tree before creating the target node.
- **Strict Workflow**: Supports "Selected Entity Only" and "Hierarchy" generation modes.
- **Logging**: all operations are logged back to the UI Console.

### 3. UI Integration

- The `ui/tree.py` file has been updated to use `ProjectManager`.
- The right-click "Generate" context menu now routes to this new logic.

## Usage

The creation workflow remains same for the user but is now powered by the new engine:

1.  **Right-click** a node in the Project Structure tree.
2.  Select **Generate**.
3.  Choose **Selected Entity Only** or **Includes Hierarchy**.

## Next Steps

- Verify the "Project Querying" phase (Step 2 in TODO).
- Expand `people.py` for assigning users to tasks if needed.
