# Module Integration & Pipeline Extension Skill

## Purpose

This skill handles adding new modular Python projects (modules) into the RDB data pipeline application. It covers the full lifecycle: placing module code in the correct subfolder, registering it in the pipeline, updating the UI, verifying logic, and safely committing with proper version control.

---

## Project Structure Reference

```
sevengen-internshipweek4.2/
├── app.py                 # Streamlit UI — sidebar, pipeline runner, file upload/download
├── config.py              # STEP_REGISTRY, GROUP_CONFIG, paths, colors
├── styles.py              # CSS styles (STYLES string) injected into Streamlit
├── main.py                # Entry point (launches Streamlit)
├── requirements.txt       # Python dependencies
├── data/
│   ├── raw/               # Input data
│   └── output/            # Output data
└── src/
    ├── __init__.py         # Package init — imports & re-exports all module functions
    ├── cleaning/           # Cleaning modules (normalize_headers, removing_duplicates)
    ├── transformation/     # Transformation modules (add_dates_metadata, translate_columns)
    └── utils/              # Utility modules (csv_handler)
```

**Existing module groups:** `cleaning`, `transformation`, `utils`
**Existing pipeline step groups:** `Cleaning`, `Enrichment`, `Transformation`

---

## Step-by-Step Procedure

### Phase 1: Prepare the Module Subfolder

1. **Determine the module group.** Decide whether the new module belongs in an existing subfolder (`cleaning/`, `transformation/`, `utils/`) or needs a new subfolder under `src/`.

2. **If creating a new subfolder:**
   - Create the directory: `src/<new_group>/`
   - Add an `__init__.py` with appropriate imports:
     ```python
     """
     <Group name> modules for the RDB pipeline.
     """
     from .<module_name> import <public_function>
     ```
   - If this group needs its own color in the UI, add entries to `GROUP_CONFIG`, `GROUP_DARK_BG`, and `GROUP_DARK_COLOR` in `config.py`.

3. **If using an existing subfolder:**
   - Place the new `.py` file directly in the appropriate `src/<group>/` directory.
   - Update that subfolder's `__init__.py` to import the new function.

4. **Module file conventions — every module file MUST follow this pattern:**
   ```python
   """
   Brief description of what this module does.
   """
   import config
   from utils.csv_handler import read_csv  # or read_csv_to_dict as needed

   def <function_name>(file_path=None, **other_params):
       """Docstring explaining parameters and return value."""
       file_path = file_path or config.RAW_DATA_FILE
       # ... processing logic ...
       return df  # Always return a pandas DataFrame
   ```
   Key conventions:
   - Accept `file_path=None` as first parameter, default to `config.RAW_DATA_FILE`
   - Use `read_csv()` or `read_csv_to_dict()` from `utils.csv_handler` to load data
   - Return a `pandas.DataFrame`
   - If the module supports progress tracking, accept an optional `progress_callback=None` parameter

---

### Phase 2: Register the Module in the Pipeline

1. **Update `src/__init__.py`:**
   - Add the import line for the new function:
     ```python
     from <group>.<module_file> import <function_name>
     ```
   - Add the function name to the `__all__` list.

2. **Update `config.py` — add a step to `STEP_REGISTRY`:**
   ```python
   {"id": "<short_id>",
    "group": "<Group Name>",  # Must match a key in GROUP_CONFIG
    "label": "<Human-readable label>",
    "min_files": 1},          # Optional, default 1. Set to 2+ for multi-file steps.
   ```
   - `id`: short snake_case identifier (used internally)
   - `group`: must match a key in `GROUP_CONFIG` (or add a new one)
   - `label`: displayed in sidebar and pipeline strip
   - `min_files` *(optional, default 1)*: minimum number of uploaded files required to enable this step. Steps with `min_files > 1` are automatically disabled in the sidebar when fewer files are uploaded. The main file uploader accepts multiple files; the sidebar enforces this constraint per-step.

3. **If a new group is needed in `config.py`:**
   ```python
   # In GROUP_CONFIG:
   "<NewGroup>": {"color": "#<hex>", "bg": "#<light_hex>"},

   # In GROUP_DARK_BG:
   "<NewGroup>": "#<deep_hex>",

   # In GROUP_DARK_COLOR:
   "<NewGroup>": "#<light_hex>",
   ```

---

### Phase 3: Update app.py

1. **Add the import** at the top of `app.py`:
   ```python
   from src.<group>.<module_file> import <function_name>
   ```

2. **Add sidebar controls** in `render_sidebar()`:
   - Find the section where steps are rendered (the `for step in STEP_REGISTRY:` loop or manual step blocks).
   - Add a checkbox and any step-specific options (column selectors, parameter inputs) using the same pattern as existing steps.
   - Use `st.expander` for steps that need configuration options.

3. **Add the step to `run_pipeline()`:**
   - Add an `elif` branch matching the new step's `id`:
     ```python
     elif step_id == "<short_id>":
         result_df = <function_name>(
             file_path=tmp_path,
             # ... pass any user-configured parameters from session_state ...
         )
     ```
   - Ensure the result DataFrame is saved back to the temp CSV between steps (follow existing pattern).

4. **UI considerations:**
   - The pipeline visualization strip auto-renders from `STEP_REGISTRY` — no changes needed there.
   - Step colors come from `GROUP_CONFIG` — ensure the group exists.
   - If adding new metric cards or display sections, follow the existing `.status-box` pattern.

---

### Phase 4: Update styles.py (If Needed)

Only modify `styles.py` if:
- A new UI component type is introduced (not just a new step)
- New group colors need CSS custom properties
- New layout sections are added to the page

When modifying:
- Add styles to the `STYLES` multi-line string
- Include both light mode and dark mode variants (dark mode uses `@media (prefers-color-scheme: dark)`)
- Follow existing naming conventions (BEM-like: `.component-name`, `.component-part`)
- Test both light and dark modes

---

### Phase 5: Verify Logic & Functionality

1. **Import check:** Run the app and verify no import errors:
   ```bash
   cd "<project_root>" && python -c "from src import *; print('All imports OK')"
   ```

2. **Module standalone test:** Test the new function directly:
   ```python
   python -c "from src.<group>.<module> import <func>; print(<func>('<test_csv_path>'))"
   ```

3. **Pipeline integration test:**
   - Launch the app: `streamlit run app.py`
   - Upload a test CSV
   - Enable ONLY the new step → run pipeline → verify output
   - Enable the new step WITH all other steps → run pipeline → verify no conflicts
   - Check that existing steps still produce correct results

4. **Edge cases to verify:**
   - Empty DataFrame input
   - Missing expected columns
   - The new step as first step vs last step in pipeline
   - File encoding handling (UTF-8, Latin-1, etc.)

---

### Phase 6: Git & Version Control

**CRITICAL: Follow this exact workflow for safe backtracking.**

1. **Before any changes — create a feature branch:**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/add-<module_name>
   ```

2. **Commit in logical, atomic units (not one big commit):**

   - **Commit 1 — Module code only:**
     ```
     feat(src): add <module_name> module to <group>

     - Add src/<group>/<module_file>.py with <function_name>
     - Update src/<group>/__init__.py imports
     ```

   - **Commit 2 — Pipeline registration:**
     ```
     feat(config): register <module_name> in STEP_REGISTRY

     - Add step entry in config.py STEP_REGISTRY
     - Update src/__init__.py exports
     ```

   - **Commit 3 — UI integration:**
     ```
     feat(app): integrate <module_name> into pipeline UI

     - Add sidebar controls for <module_name>
     - Add run_pipeline handler for <step_id>
     - Update imports in app.py
     ```

   - **Commit 4 — Style changes (if any):**
     ```
     style(ui): add styles for <new_component>
     ```

   - **Commit 5 — Dependency updates (if any):**
     ```
     chore(deps): add <package> to requirements.txt
     ```

3. **After all commits — push and create PR:**
   ```bash
   git push -u origin feature/add-<module_name>
   ```
   Create a PR against `main` with a summary of what the module does and what steps were added.

4. **Tagging (for version tracking):**
   After merge to main, tag the release:
   ```bash
   git tag -a v<X.Y.Z> -m "Add <module_name> module"
   git push origin v<X.Y.Z>
   ```
   Use semantic versioning:
   - Patch (0.0.X): bug fixes to existing modules
   - Minor (0.X.0): new module added
   - Major (X.0.0): breaking changes to pipeline interface

---

### Phase 7: Modularity Adjustments (When Needed)

Review and apply these improvements when the project grows:

1. **Step handler registry pattern** — If `run_pipeline()` has too many `elif` branches, refactor to a dispatch dictionary:
   ```python
   STEP_HANDLERS = {
       "normalize": lambda opts: normalize_headers(file_path=opts["path"]),
       "duplicates": lambda opts: remove_duplicates(columns=opts.get("cols"), file_path=opts["path"]),
       # ... new steps added here
   }
   ```

2. **Auto-discovery** — If many modules are added, consider scanning `src/` subfolders for modules that expose a standard interface (e.g., a `register()` function or a `STEP_INFO` dict).

3. **Sidebar rendering from registry** — Move step-specific sidebar UI into each module file as a `render_options(st)` function, so adding a module doesn't require editing `app.py` sidebar code.

4. **Shared base class** — If modules share patterns (read CSV → process → return DataFrame), consider a base class or decorator:
   ```python
   @pipeline_step(id="normalize", group="Cleaning", label="Normalize headers")
   def normalize_headers(df, **kwargs):
       ...
   ```

---

## Checklist Summary

Before marking a module integration as complete, verify:

- [ ] Module `.py` file exists in correct `src/<group>/` subfolder
- [ ] Module follows conventions: `file_path=None` param, returns DataFrame, uses `csv_handler`
- [ ] Subfolder `__init__.py` updated with import
- [ ] `src/__init__.py` updated with import and `__all__` entry
- [ ] `config.py` `STEP_REGISTRY` has new step entry
- [ ] `config.py` `GROUP_CONFIG` has color entry (if new group)
- [ ] `app.py` imports the new function
- [ ] `app.py` `render_sidebar()` has controls for the step
- [ ] `app.py` `run_pipeline()` handles the step's `id`
- [ ] `styles.py` updated (only if new UI components needed)
- [ ] `requirements.txt` updated (only if new dependencies needed)
- [ ] Import check passes (`python -c "from src import *"`)
- [ ] Pipeline runs with new step alone
- [ ] Pipeline runs with new step + all other steps
- [ ] Existing functionality unchanged
- [ ] Feature branch created, commits are atomic and descriptive
- [ ] PR created against `main`
