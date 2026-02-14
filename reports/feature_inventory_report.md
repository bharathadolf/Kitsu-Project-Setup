# Kitsu Project Ingester — Feature Inventory Report

## Scope
This report documents the currently implemented capabilities of the **Kitsu Project Ingester** tool based on the repository codebase and documentation.

---

## 1) Platform and Runtime Features

- **Cross-platform launcher support** for Windows (`launcher.bat`) and macOS/Linux (`launcher.sh`).
- **Auto-update workflow** via launcher scripts (documented in README) to keep teams synced to latest code.
- **Dual execution context support**:
  - Standalone desktop Qt application.
  - Embedded launch path for Houdini (single-window session behavior and Houdini parenting).

---

## 2) UI Architecture and UX Features

### Main window and layout
- Three-panel split layout:
  - **Project Structure** tree panel.
  - **Properties** panel.
  - **Console Log** panel.
- Status bar features:
  - Runtime status text.
  - Kitsu connection status light indicator.
  - Active theme toggle button.
  - Dynamic window-size and panel-size readouts.

### Theming
- Theme system with runtime **theme switching**.
- Theme propagation across major UI panels (tree, properties, console, headers).

### Logging UX
- Structured in-app console with log levels.
- Manual **Clear Console** action.
- Verbose load/generation feedback, including field-level details in several flows.

---

## 3) Project Structure Authoring Features

### Rule/template-driven hierarchy
- Structure generation is driven by `RULE_MAP` templates.
- Template menu supports multiple production presets.
- Applying a template:
  - Clears/rebuilds the tree.
  - Sets default project production type mapping.
  - Populates child entity graph based on template rules.

### Node editing model
- Supported node/entity types:
  - Project
  - Episode
  - Sequence
  - Shot
  - Asset Type
  - Asset
- Each node has:
  - Typed defaults (name/code/data and type-specific metadata).
  - Add child / add sibling controls (rule-dependent).
  - Conditional delete control with sibling constraints.

### Naming and ID behavior
- Auto-initialized human-readable names by type and local index.
- Hierarchical local node IDs (e.g., `1::2`) for contextual identity.
- Auto-generated short codes for non-root entities with type-based prefixes.

### Selection workflows
- Single-click selection.
- Ctrl multi-select toggling.
- Rubber-band rectangle selection.
- Selection drives tabbed form rendering in the properties panel.

### Tree visualization
- Custom connector drawing between nodes.
- Expand/collapse behavior with custom expander states.
- Watermark text in tree viewport (template/production context signal).

### Export
- Context menu action to **export current structure as JSON**.

---

## 4) Properties Panel and Form Features

- Dynamic form system (`FORM_MAP`) resolving form class by node type.
- Multi-selection support with tabbed property pages.
- Entity-specific forms with structured inputs.
- Optional-field toggles and grouped/collapsible sections for certain entities.
- Change tracking/logging for property edits.
- Auto-updated dependent fields in certain rename/edit scenarios.
- Data payload (`data`) support for custom/extended metadata.

---

## 5) Generation, Dry-run, and Validation Features

### Context menus on nodes
- For non-loaded nodes:
  - **Dry-run**
    - Selected entity only
    - Includes hierarchy
  - **Generate**
    - Selected entity only
    - Includes hierarchy
- For loaded nodes:
  - **Viewer** action to inspect entity data.

### Planning/generation pipeline
Implemented orchestration in `ProjectManager` includes:
1. Kitsu connection attempt.
2. Build linear execution plan from tree context.
3. Resolve parameters/codes/data with parent-child context.
4. Present confirmation dialog with editable entity names.
5. Execute plan against Kitsu entity APIs.
6. Optional post-generate fetch/query refresh.

### Generation Summary dialog features
- Hierarchical plan preview with entity/action columns.
- Parameter/details inspection panel.
- Editable names before generation.
- Recursive downstream dependency recalculation after renames.
- Actions:
  - Generate
  - Generate & Query
  - Cancel/Close

### Sanity checks
- Pre-generation project uniqueness check flow (manager-backed).

---

## 6) Kitsu Integration Features

### Connection/authentication
- Uses configured Kitsu host and credentials via `kitsu_config`.
- Connection feedback surfaced in UI and logs.

### Entity creation/retrieval wrappers
Dedicated modules per entity encapsulate creation/get-or-create logic:
- Project
- Episode
- Sequence
- Shot
- Asset Type
- Asset
- Task Type / Task
- People/user helper wrapper module

### Loader (read/sync from Kitsu)
- Fetch all projects for menu population.
- Load full project hierarchy into local tree:
  - Project → Episodes/Sequences → Shots
  - Asset Types → Assets
- Extract and normalize key entity fields into local properties.
- Includes support for preserving custom `data` payload when available.

---

## 7) Data Model and Utility Features

- Code-generation utilities for entity/project codes.
- Compatibility layer for PySide2/PySide6.
- Rule-based config and constants for node geometry/UI behavior.
- Mapping and planning docs for UI-to-Gazu alignment and roadmap.

---

## 8) QA and Validation Footprint

Repository includes test coverage across several areas:
- UI logic and dialog behavior tests.
- Data generation and metadata logic tests.
- Fetch/backend interaction tests.
- Resize/panel/layout behavior tests.
- Project/entity behavior tests.

---

## 9) Current Tool Positioning

The tool currently acts as an end-to-end **project structure authoring + Kitsu ingest workstation** with:
- Visual hierarchy authoring,
- Form-driven metadata editing,
- Simulated dry-runs,
- Confirmed generation execution,
- Optional fetch-back verification,
- and project reload capabilities.

This makes it suitable for production coordination and technical setup workflows where both planning and system-of-record synchronization are required.
