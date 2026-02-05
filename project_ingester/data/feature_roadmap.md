# Feature Planner & Roadmap: Gazu API Integration

This document outlines the strategic roadmap for deepening the integration between the **Project Ingester** and **Kitsu (Gazu API)**.

## 🎯 Objective

Achieve 1:1 parity between the **Ingester UI** and **Kitsu's Data Model**, ensuring no data is lost during project generation.

---

## 📅 Phase 1: Project Foundation (Immediate)

**Goal:** Ensure accurate project setup and scheduling data.

- [ ] **Project Dates:** Sync `Start Date` and `End Date` to Kitsu.
- [ ] **Technical Specs:** Verify `FPS`, `Ratio`, and `Resolution` are correctly stored.
- [ ] **Description:** Ensure project descriptions are populated from the auto-generated templates.
- [ ] **Dry Run:** Validate these fields in the Console before creation.

## 🎨 Phase 2: Asset Pipeline (Next)

**Goal:** enrich Asset creation with pipeline-specific metadata.

- [ ] **Categorization:** Map `Asset Category` (Prop, Character, Environment) to Kitsu.
- [ ] **Workflow Data:** Store `Primary DCC` (Maya, Blender) and `Render Engine` (Arnold, Cycles) as custom metadata.
- [ ] **Status:** Set initial Asset Status (e.g., "Concept" or "Ready to Start").

## 🎬 Phase 3: Production Tracking

**Goal:** Precision in Shot and Episode management.

- [ ] **Frame Ranges:** Ensure `Frame In`, `Frame Out`, and `Nb Frames` are accurately set on Shots.
- [ ] **Hierarchy:** Verify relationships between Episodes, Sequences, and Shots are robust.
- [ ] **Tasks:** Auto-create default tasks (e.g., "Compositing") if requested by the Shot template.

## 🔮 Phase 4: Future Polish

**Goal:** Enhanced UX and complete coverage.

- [ ] **Project Avatar:** Implement file picker and upload logic for project thumbnails.
- [ ] **Two-Way Sync:** (Future) Fetch existing Kitsu data back into the UI for editing.
- [ ] **Validation:** Add UI validators (e.g., End Date > Start Date).

---

_Reference Documents:_

- [Technical Implementation Plan](implementation_plan.md)
- [UI <-> API Mapping Table](ui_gazu_mapping.md)
