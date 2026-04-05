# The Design System: Operational Excellence through Editorial Depth

## 1. Overview & Creative North Star
The vision for this design system is **"The Fiscal Architect."** 

While most administrative dashboards feel like cold, utilitarian spreadsheets, this system treats financial data with the reverence of a premium editorial publication. We are moving beyond "standard" UI to create a workspace that feels intentional, layered, and sophisticated. 

The "Creative North Star" balances high-density data with **breathable, asymmetric layouts.** We avoid the "boxed-in" feeling of traditional dashboards by rejecting rigid borders in favor of tonal transitions and sophisticated layering. The result is a tracker that feels less like a chore and more like a high-end management suite.

---

## 2. Colors & Surface Narrative
Our palette uses the core brand DNA—the deep indigo and professional slate—but extends it into a hierarchy of functional surfaces.

### The "No-Line" Rule
**Explicit Instruction:** You are prohibited from using 1px solid borders to section off the UI. 
Instead of drawing a line to separate the sidebar from the main content or a card from the background, use **background color shifts.** 
- A `surface-container-low` section sitting on a `surface` background creates a natural boundary.
- For interactive containers, use the transition between `surface-container-lowest` (#ffffff) and `surface-container` (#e6eeff).

### Surface Hierarchy & Nesting
Treat the interface as physical layers of fine paper or frosted glass. 
1. **Base Layer:** `surface` (#f8f9ff) — The canvas.
2. **Structural Layer:** `surface-container-low` (#eff4ff) — Used for large sidebars or secondary content areas.
3. **Interactive Layer:** `surface-container-lowest` (#ffffff) — Used for primary data cards and input fields to make them "pop" against the structural layers.

### The "Glass & Gradient" Rule
To inject "soul" into the administrative experience:
- **Main CTAs:** Use a subtle linear gradient from `primary` (#3525cd) to `primary_container` (#4f46e5).
- **Floating Elements:** For tooltips or "Quick-Add" buttons, apply **Glassmorphism.** Use a semi-transparent `surface_container_lowest` with a 12px backdrop-blur.

---

## 3. Typography: The Editorial Scale
We use typography to establish an authoritative hierarchy. We pair **Plus Jakarta Sans** for high-impact display moments with **Inter** for precision data points.

- **Display & Headlines (Plus Jakarta Sans):** These are your "Editorial" voices. Use `display-md` for total balance overviews and `headline-sm` for section titles. The generous x-height feels modern and professional.
- **Body & Labels (Inter):** For the "nitty-gritty" of expense tracking—transaction IDs, dates, and descriptions—`body-md` and `label-md` provide the necessary legibility at small sizes.
- **Data Emphasis:** When displaying currency amounts, use `title-lg` in a medium or bold weight to ensure the most important information is the most visible.

---

## 4. Elevation & Depth
In this design system, depth is communicated through **Tonal Layering** rather than structural scaffolding.

### The Layering Principle
Hierarchy is achieved by "stacking." A `surface-container-lowest` card placed on a `surface-container-high` background creates an immediate sense of lift without a single pixel of shadow.

### Ambient Shadows
When a component must float (e.g., a dropdown or a modal), use **Ambient Shadows.**
- **Spec:** Blur: 24px-40px | Opacity: 4%-6% | Color: Tinted with `on_surface` (#0d1c2f).
- Shadows should never look "dirty" or grey; they should feel like a soft glow of light being blocked by a physical object.

### The "Ghost Border" Fallback
If accessibility requirements demand a border (e.g., in high-contrast modes), use a **Ghost Border.** 
- **Token:** `outline_variant` at 15% opacity. It should be barely perceptible, serving as a suggestion of a boundary rather than a hard wall.

---

## 5. Components

### Buttons
- **Primary:** Rounded `xl` (1.5rem) or `full`. Use the signature gradient (Primary to Primary Container).
- **Secondary:** Surface-only with a `ghost border`. 
- **States:** On hover, shift the gradient density or increase the ambient shadow slightly to suggest a "lift."

### Cards & Data Lists
- **Forbid Dividers:** Do not use lines between list items. Use a 12px `spacing-3` vertical gap or alternate background tones (Zebra striping using `surface` and `surface-container-low`).
- **Corner Radius:** All cards must use `rounded-lg` (1rem) to maintain the professional but approachable brand feel.

### Input Fields
- **Styling:** Use `surface-container-lowest` as the fill. 
- **Active State:** Instead of a thick border, use a 2px `primary` underline or a soft `primary_fixed` outer glow.
- **Labels:** Always use `label-md` in `on_surface_variant` positioned 8px above the field.

### Chips (Category Tags)
- **Income:** `tertiary_container` with `on_tertiary_container` text.
- **Expense:** `error_container` with `on_error_container` text.
- **Style:** Fully rounded (`full`) with no border.

---

## 6. Do's and Don'ts

### Do
- **Do** use white space as a structural element. If in doubt, add more padding from the Spacing Scale (`spacing-8` or `spacing-10`).
- **Do** use `tertiary` (#735c00) accents sparingly for "delight" moments, such as a successful savings goal.
- **Do** align data points (numbers) to the right in tables to ensure professional financial legibility.

### Don't
- **Don't** use pure black (#000000) for text. Always use `on_surface` (#0d1c2f) to maintain tonal depth.
- **Don't** use standard 4px "card shadows." They look "template-like." Stick to tonal shifts or high-blur ambient shadows.
- **Don't** cram information. If a dashboard view is crowded, use a nested "surface-container" to group related data and provide visual "breathing room."