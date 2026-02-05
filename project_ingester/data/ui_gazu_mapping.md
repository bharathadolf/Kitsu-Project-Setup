# UI to Gazu API Field Mapping

This document details how the fields visible in the "Properties Panel" are mapped to the Kitsu/Gazu API when generating entities.

## 1. Project

**UI Form:** `ProjectForm`
**API Function:** `gazu.project.new_project` & `gazu.raw.update`

| UI Label             | Internal Property  | Gazu API Parameter  | Status                     |
| :------------------- | :----------------- | :------------------ | :------------------------- |
| **Name**             | `name`             | `name`              | ✅ Mapped                  |
| **Type**             | `production_type`  | `production_type`   | ✅ Mapped                  |
| **Style**            | `production_style` | `production_style`  | ✅ Mapped                  |
| **Code**             | `code`             | `data.project_code` | ✅ Mapped (Custom Payload) |
| **Root Path**        | `data.root_path`   | `data.root_path`    | ✅ Mapped (Custom Payload) |
| **Description**      | `description`      | `description`       | ✅ Mapped                  |
| **FPS** (Opt)        | `fps`              | `fps`               | ✅ Mapped                  |
| **Ratio** (Opt)      | `ratio`            | `ratio`             | ✅ Mapped                  |
| **Resolution** (Opt) | `resolution`       | `resolution`        | ✅ Mapped                  |
| **Start Date** (Opt) | `start_date`       | -                   | ❌ **Unmapped / Ignored**  |
| **End Date** (Opt)   | `end_date`         | -                   | ❌ **Unmapped / Ignored**  |
| **Has Avatar** (Opt) | `has_avatar`       | -                   | ❌ **Unmapped / Ignored**  |

> [!NOTE]
> `Start Date`, `End Date`, and `Avatar` are selectable in the UI but are currently not sent to Kitsu during generation.

---

## 2. Episode

**UI Form:** `EpisodeForm`
**API Function:** `gazu.shot.new_episode`

| UI Label | Internal Property | Gazu API Parameter | Status    |
| :------- | :---------------- | :----------------- | :-------- |
| **Name** | `name`            | `name`             | ✅ Mapped |

---

## 3. Sequence

**UI Form:** `SequenceForm`
**API Function:** `gazu.shot.new_sequence`

| UI Label | Internal Property | Gazu API Parameter | Status    |
| :------- | :---------------- | :----------------- | :-------- |
| **Name** | `name`            | `name`             | ✅ Mapped |

---

## 4. Shot

**UI Form:** `ShotForm`
**API Function:** `gazu.shot.new_shot`

| UI Label              | Internal Property | Gazu API Parameter | Status    |
| :-------------------- | :---------------- | :----------------- | :-------- |
| **Name**              | `name`            | `name`             | ✅ Mapped |
| **Frame In** (Opt)    | `frame_in`        | `frame_in`         | ✅ Mapped |
| **Frame Out** (Opt)   | `frame_out`       | `frame_out`        | ✅ Mapped |
| **Nb Frames** (Opt)   | `nb_frames`       | `nb_frames`        | ✅ Mapped |
| **Description** (Opt) | `description`     | `description`      | ✅ Mapped |

---

## 5. Asset Type

**UI Form:** `AssetTypeForm`
**API Function:** `gazu.asset.new_asset_type` (Global)

| UI Label | Internal Property | Gazu API Parameter | Status    |
| :------- | :---------------- | :----------------- | :-------- |
| **Name** | `name`            | `name`             | ✅ Mapped |

---

## 6. Asset

**UI Form:** `AssetForm`
**API Function:** `gazu.asset.new_asset`

| UI Label | Internal Property | Gazu API Parameter | Status                                         |
| :------- | :---------------- | :----------------- | :--------------------------------------------- |
| **Name** | `name`            | `name`             | ✅ Mapped                                      |
| -        | `description`     | -                  | ⚠️ **Hidden Field** (Exists in API, not in UI) |
| -        | `asset_category`  | -                  | ❌ **Unmapped / Hidden**                       |
| -        | `primary_dcc`     | -                  | ❌ **Unmapped / Hidden**                       |
| -        | `render_engine`   | -                  | ❌ **Unmapped / Hidden**                       |
| -        | `asset_status`    | -                  | ❌ **Unmapped / Hidden**                       |

> [!WARNING]
> The Asset UI is very minimal (Name only). Several default properties exist in the code (`asset_category`, etc.) but are neither shown in the UI nor sent to the API.
