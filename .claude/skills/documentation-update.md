# Documentation Update Skill

## Purpose

This skill handles adding, updating, or removing documentation when the RDB Media Analytics Pipeline changes — new modules added, existing modules modified, modules removed, or project-wide changes. It ensures consistency across all three documentation layers: markdown module docs, the interactive HTML, and workflow diagrams.

---

## Documentation Architecture

```
docs/
├── Project_Documentation.html       # Interactive 13-tab HTML (main deliverable)
├── modules/                          # Per-module markdown files
│   ├── normalize_headers.md
│   ├── removing_duplicates.md
│   ├── add_dates_metadata.md
│   ├── translate_columns.md
│   ├── csv_handler.md
│   ├── topic_clustering.md
│   └── merge_csv.md
└── workflows/                        # Reserved for exported diagram assets
```

**Three layers must stay in sync:**
1. **Markdown docs** (`docs/modules/<name>.md`) — detailed per-module reference
2. **HTML tabs** (`docs/Project_Documentation.html`) — interactive overview with workflow diagrams
3. **Full workflow SVG** (inside the HTML) — the pipeline flow diagram

---

## When a New Module Is Added

Perform ALL of the following steps in order:

### Step 1: Create the Markdown Documentation

Create `docs/modules/<module_name>.md` following this exact template:

```markdown
# <Module Display Name>

**Module:** `src/<category>/<filename>.py`
**Category:** <Cleaning | Transformation | Analysis | Merge | Utility>
**Version:** 1.0

---

## Purpose

<1-2 paragraphs explaining what this module does and why it matters for media analysts. Write in plain language — avoid developer jargon.>

---

## When to Use

Use this module when:

- <Scenario 1>
- <Scenario 2>
- <Scenario 3>

---

## What It Does

1. **<Step name>** — <Description of what happens>
2. **<Step name>** — <Description of what happens>
3. ...

---

## How to Use

### Via the Streamlit App (Recommended)

1. <Step-by-step instructions for non-technical users>

### Via Python (Programmatic)

\```python
from src.<category>.<module> import <function>

df = <function>(file_path="data/raw/example.csv")
\```

---

## Input & Output

| Aspect       | Details                                    |
|-------------|---------------------------------------------|
| **Input**   | <What the module receives>                  |
| **Output**  | <What the module returns>                   |
| **Changes** | <What changes in the data>                  |

### Example

<Before/after table showing concrete data transformation>

---

## Parameters

| Parameter   | Type   | Default   | Description                |
|------------|--------|-----------|----------------------------|
| `file_path` | `str`  | Config default | Path to CSV or Excel file |
| ...         | ...    | ...       | ...                        |

---

## Error Handling

- **<Error scenario>**: <What happens and how to fix it>

---

## Tips for Media Analysts

- **<Tip 1>** — <Practical advice>
- **<Tip 2>** — <Practical advice>
```

**Key conventions for markdown docs:**
- Write for media analysts, not developers
- Always include concrete before/after examples with tables
- Always include a "Tips for Media Analysts" section
- Always include "Via the Streamlit App" instructions first
- Parameters table must list every parameter with type, default, and description
- Error handling must list all known failure modes

---

### Step 2: Add a Tab to Project_Documentation.html

The HTML uses a tabbed interface. Module tabs go BEFORE the `quickstart` tab and AFTER the `mod-csvhandler` tab (or after the last module tab if more have been added).

#### 2a. Add the tab button

In the `.tabs` div, add a button. Use the `mod-` prefix for module tab IDs:

```html
<button class="tab-button" onclick="openTab(event, 'mod-<shortname>')"><Display Name></button>
```

Insert it before the `quickstart` button.

#### 2b. Add the tab content div

Insert a new `<div id="mod-<shortname>" class="tab-content">` section. Follow this structure:

```html
<!-- ============================================================ -->
<!-- TAB: MODULE - <UPPERCASE NAME> -->
<!-- ============================================================ -->
<div id="mod-<shortname>" class="tab-content">
    <h2><Module Display Name></h2>
    <span class="module-badge badge-<category>"><Category> Module</span>
    <p><code>src/<category>/<filename>.py</code></p>

    <hr class="divider">

    <h3>Purpose</h3>
    <p>...</p>

    <h3>When to Use</h3>
    <ul>...</ul>

    <h3>Workflow Diagram</h3>
    <div class="workflow-chart">
        <svg>... (see SVG conventions below) ...</svg>
    </div>

    <h3>Parameters</h3>
    <table class="param-table">...</table>

    <h3>Example</h3>
    <div class="example-box">...</div>

    <div class="callout tip">
        <div class="callout-label">Tip for Media Analysts</div>
        <p>...</p>
    </div>

    <div class="navigation">
        <button class="nav-button" onclick="prevTab()">Previous: <Previous Tab Name></button>
        <button class="nav-button" onclick="nextTab()">Next: <Next Tab Name></button>
    </div>
</div>
```

#### 2c. Update the JavaScript tabs array

Find the `const tabs = [...]` array and add the new tab ID in the correct position (matching the tab button order):

```javascript
const tabs = ['overview', 'structure', 'ipo', 'workflow-full', 'mod-normalize', 'mod-duplicates', 'mod-dates', 'mod-translate', 'mod-csvhandler', 'mod-clustering', 'mod-merge', /* new tab here */ 'quickstart', 'adding-modules'];
```

#### 2d. Update navigation buttons on adjacent tabs

- The **previous tab** must update its "Next" button text to point to the new tab
- The **next tab** must update its "Previous" button text to point to the new tab

---

### Step 3: Update the Overview Tab

Add a module card to the `module-grid` in the `overview` tab:

```html
<div class="module-card">
    <span class="module-badge badge-<category>"><Category></span>
    <h4><Module Name></h4>
    <p><One-sentence description></p>
</div>
```

---

### Step 4: Update the Project Structure Tab

Update the `<pre>` block showing the directory tree to include the new file. Also update the directory description `<div class="process-section">` for the relevant category.

---

### Step 5: Update the I-P-O Table

Add a row to the per-module I-P-O table in the `ipo` tab:

```html
<tr>
    <td><strong><Module Name></strong></td>
    <td><Input description></td>
    <td><Process description></td>
    <td><Output description></td>
</tr>
```

---

### Step 6: Update the Full Workflow SVG

The full workflow diagram is an inline SVG in the `workflow-full` tab. To add a new step:

1. **Insert a new step block** between the last real step and the "Future Modules..." placeholder
2. **Shift all elements below it down by 80px** (each step block is 48px tall + ~27px spacing = ~80px per step)
3. **Update the SVG height** attribute to accommodate the new step
4. **Update the side bracket** (the "Optional" label line) to extend to the new bottom

**Step block template** (adjust Y coordinates):

```svg
<!-- Step N: <Name> -->
<rect x="220" y="<Y>" width="260" height="48" rx="4" fill="<bg_color>" stroke="<border_color>" stroke-width="1.5"/>
<text x="350" y="<Y+20>" text-anchor="middle" fill="<label_color>" font-size="11" font-weight="600"><CATEGORY> &middot; STEP <N></text>
<text x="350" y="<Y+37>" text-anchor="middle" fill="#37352f" font-size="14" font-weight="500"><Step Name></text>

<line x1="350" y1="<Y+48>" x2="350" y2="<Y+73>" stroke="#37352f" stroke-width="1.5"/>
<polygon points="350,<Y+78> 347,<Y+71> 353,<Y+71>" fill="#37352f"/>
```

**Category color scheme for SVG steps:**

| Category       | Fill (bg)   | Stroke (border) | Label text color |
|---------------|-------------|-----------------|------------------|
| Cleaning       | `#f3eef7`   | `#6940a5`       | `#6940a5`        |
| Enrichment     | `#e6f0f6`   | `#2e6b8a`       | `#2e6b8a`        |
| Analysis       | `#d6eaf8`   | `#0e6ba8`       | `#0e6ba8`        |
| Merge          | `#ede9fe`   | `#7c3aed`       | `#7c3aed`        |
| Utility        | `#dbeddb`   | `#2e7d32`       | `#2e7d32`        |
| Future (dashed)| `white`     | `rgba(55,53,47,0.2)` | `rgba(55,53,47,0.4)` |

---

### Step 7: Update the Quick Start Tab

Update the pipeline steps table and the "Recommended Pipeline Order" list in the `quickstart` tab to include the new step in the correct position.

---

### Step 8: Update the Adding Modules Tab (if structural changes)

If new categories or conventions were introduced, update the "Adding Modules" tab to reflect them. This tab serves as the developer-facing guide.

---

## Per-Module Workflow Diagram SVG Conventions

Each module tab has its own workflow diagram. Follow these conventions:

- **Canvas**: `max-width: 520-580px`, centered with `margin: 0 auto; display: block`
- **Start block**: filled `#37352f` (dark), white text, labeled "Input: ..."
- **End block**: filled `#37352f` (dark), white text, labeled "Output: ..."
- **Process blocks**: white fill, colored stroke matching the module's category
- **Decision diamonds**: white fill, `#37352f` stroke, centered text
- **Arrows**: `#37352f` stroke, 1.5px width, with filled polygon arrowheads
- **Sub-labels**: `rgba(55,53,47,0.5)` fill, font-size 11
- **Block size**: 260px wide, 44px tall, 4px border-radius
- **Spacing**: 25-30px between blocks (line + arrowhead)
- **X centering**: blocks at x=130 or x=140 (depending on width), text at midpoint

---

## CSS Badge Classes

When adding a new module category, add the badge class to the `<style>` section:

```css
.badge-<category> { background: <light_bg>; color: <text_color>; }
```

Existing badges:
- `.badge-cleaning` — purple (`#e8deee` / `#6940a5`)
- `.badge-transformation` — blue (`#d3e5ef` / `#2e6b8a`)
- `.badge-analysis` — light blue (`#d6eaf8` / `#0e6ba8`)
- `.badge-merge` — violet (`#ede9fe` / `#7c3aed`)
- `.badge-utility` — green (`#dbeddb` / `#2e7d32`)

---

## When an Existing Module Is Modified

If a module's behavior, parameters, or I/O changes:

1. Update the markdown doc in `docs/modules/<name>.md`
2. Update the corresponding HTML tab (parameters table, workflow diagram if flow changed, examples)
3. Update the I-P-O table if inputs/outputs changed
4. Update the Quick Start table if the step's description changed

---

## When a Module Is Removed

1. Delete `docs/modules/<name>.md`
2. Remove the tab button from the `.tabs` div
3. Remove the tab content `<div>` entirely
4. Remove from the JavaScript `tabs` array
5. Fix navigation buttons on the now-adjacent tabs
6. Remove the module card from the Overview tab
7. Remove the row from the I-P-O table
8. Remove the step from the Full Workflow SVG (shift subsequent elements up by 80px)
9. Update the Quick Start pipeline table

---

## Callout Types

Use these callout styles consistently:

```html
<!-- General info (dark left border) -->
<div class="callout">
    <p>...</p>
</div>

<!-- Tip (green left border) -->
<div class="callout tip">
    <div class="callout-label">Tip for Media Analysts</div>
    <p>...</p>
</div>

<!-- Warning (orange left border) -->
<div class="callout warning">
    <div class="callout-label">Important</div>
    <p>...</p>
</div>
```

---

## Checklist Summary

Before marking a documentation update as complete, verify:

- [ ] Markdown doc created/updated in `docs/modules/<name>.md`
- [ ] Markdown follows the template (Purpose, When to Use, What It Does, How to Use, I/O, Parameters, Errors, Tips)
- [ ] HTML tab button added in correct position
- [ ] HTML tab content div added with workflow diagram, params, examples, callouts
- [ ] JavaScript `tabs` array updated with new tab ID
- [ ] Navigation buttons on adjacent tabs updated (Previous/Next text)
- [ ] Overview tab module-grid updated
- [ ] Project Structure tab tree and descriptions updated
- [ ] I-P-O table row added/updated
- [ ] Full Workflow SVG updated (new step block, heights shifted, bracket extended)
- [ ] Quick Start pipeline table and recommended order updated
- [ ] All cross-references between tabs are consistent
- [ ] HTML renders correctly in browser (open file, click through all tabs)
