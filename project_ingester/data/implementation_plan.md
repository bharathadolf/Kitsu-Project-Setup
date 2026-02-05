# Implementation Plan - Gazu API Parameter Mapping for All Entities

## Goal

Systematically map all UI parameters to the Gazu API for every entity type (`Project`, `Episode`, `Sequence`, `Shot`, `Asset`, `AssetType`). We will implement this entity by entity, starting with **Project**.

## Execution Order

1.  **Project** (Immediate Focus)
2.  **Asset**
3.  **Shot**
4.  **Sequence & Episode**

---

## Phase 1: Project Entity (Immediate)

**Objective**: Map `start_date`, `end_date`, `fps`, `ratio`, `resolution` and ensure `description` is consistently updated.

### Changes

**File:** `project_ingester/entities/project.py`

- Update `get_or_create_project` to accept `start_date`, `end_date`.
- In `update_data` dictionary:
  - Add `start_date` (Format: `YYYY-MM-DD`).
  - Add `end_date` (Format: `YYYY-MM-DD`).
- **Avatar**: `has_avatar` boolean in UI requires a file upload. Since we don't have the file path in the UI property (just a boolean?), we will **skip** avatar implementation for now unless we add a specific file picker for it. _Note: UI currently has `has_avatar` but no path input._

**File:** `project_ingester/core/setup.py`

- In `_resolve_entity` for `project`:
  - Retrieve `start_date` and `end_date` from properties.
  - Pass them to `get_or_create_project`.

---

## Phase 2: Asset Entity

**Objective**: Map `asset_category`, `primary_dcc`, `render_engine`, `asset_status`.

### Changes

**File:** `project_ingester/entities/asset.py`

- Update `get_or_create_asset` to accept `extra_data` (dict containing the fields above).
- If `gazu.asset.new_asset` supports `data` arg, use it. Else use `gazu.raw.update`.
- **Fields to Map**:
  - `asset_category` -> `data.category` (or Gazu specific field if exists)
  - `primary_dcc` -> `data.primary_dcc`
  - `render_engine` -> `data.render_engine`
  - `asset_status` -> `data.status` (or trigger status change if possible)

---

## Phase 3: Shot Entity

**Objective**: Verify and refine `frame_in`, `frame_out`, `nb_frames`.

### Changes

**File:** `project_ingester/entities/shot.py`

- Validate `frame_in`, `frame_out`, `nb_frames` are integers before passing.
- Ensure `description` is passed.
- Ensure `tasks` creation remains robust.

---

## Phase 4: Sequence & Episode

**Objective**: Basic Name mapping.

### Changes

- **Sequence**: No additional fields in UI currently.
- **Episode**: No additional fields in UI currently.
- Verify robust creation logic in `setup.py`.

---

## Validation

- **Manual Verification**:
  - Create entities with full populated fields.
  - Trigger "Generate".
  - Login to Kitsu (or check logs) to verify values.
