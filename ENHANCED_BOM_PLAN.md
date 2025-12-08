# Enhanced BOM Implementation Plan

## Current State Analysis
The existing BOM (`alex_bom()`) already has:
- ✅ Part aggregation by description
- ✅ Quantity counting
- ✅ Cost totaling (unit + total)
- ✅ CSV export
- ✅ Basic clickable URLs (blue text)
- ✅ Part highlighting on click

## Enhancement Goals

### 1. Visual Polish (30 min)
- **Better table styling**
  - Header row with bold text and background color
  - Alternating row colors for readability
  - Better column alignment (right-align numbers)
  - Padding and borders
  
- **URL improvements**
  - Underline on hover
  - Hand cursor on hover
  - "Open" icon/button next to URL
  - Tooltip showing full URL

### 2. Supplier Grouping (45 min)
- **Group by supplier**
  - Extract supplier from URL domain
  - Subtotals per supplier
  - Collapsible sections per supplier
  - Supplier logos/icons (optional)

- **Supplier summary**
  - Total cost per supplier
  - Part count per supplier
  - Highlight cheapest supplier option

### 3. Enhanced Actions (30 min)
- **Copy to clipboard**
  - "Copy All" button → CSV format
  - "Copy Selected Supplier" → Just one supplier's parts
  - "Copy Shopping List" → Formatted for ordering

- **Export options**
  - Export to CSV (already exists, enhance)
  - Export to Excel-friendly format
  - Export with supplier grouping

### 4. Smart Features (30 min)
- **Sorting options**
  - Sort by: Description, Quantity, Unit Cost, Total Cost, Supplier
  - Click column headers to sort
  
- **Filtering**
  - Show/hide by supplier
  - Filter by price range
  - Search parts

### 5. Window Improvements (15 min)
- **Better window**
  - Resizable with scrollbars
  - Remember window size (use config!)
  - Title shows total cost
  - Status bar with summary stats

## Implementation Order (Highest Impact First)

### Phase 1: Visual Polish + Actions (1 hour)
1. Styled table with headers
2. Better URL styling with hover effects
3. Copy to clipboard buttons
4. Improved window layout

### Phase 2: Supplier Intelligence (1 hour)
1. Extract supplier from URLs
2. Group by supplier with subtotals
3. Supplier summary section
4. Visual supplier indicators

### Phase 3: Interactive Features (30 min)
1. Sortable columns
2. Search/filter
3. Show/hide suppliers

## Technical Approach

### Libraries Needed
- `tkinter.ttk.Treeview` - Better table widget
- `urllib.parse` - Extract supplier from URL
- `pyperclip` or `tkinter.clipboard` - Copy to clipboard
- Existing: `webbrowser`, `csv`

### Data Structure
```python
BOMItem = {
    'qty': int,
    'description': str,
    'dimensions': (x, y, z),
    'unit_cost': float,
    'total_cost': float,
    'url': str,
    'supplier': str,  # NEW: extracted from URL
    'part_refs': []   # NEW: references to actual parts for highlighting
}
```

### Supplier Extraction
```python
def extract_supplier(url):
    \"\"\"Extract supplier name from URL\"\"\"
    if not url or not url.startswith('http'):
        return 'Unknown'
    
    domain = urllib.parse.urlparse(url).netloc
    # misumi.com → Misumi
    # amazon.com → Amazon
    # mcmaster.com → McMaster-Carr
    return domain.split('.')[-2].title()
```

## UI Mockup

```
┌─────────────────────────────────────────────────────────────────┐
│ Bill of Materials - Total: $1,234.56                      [X]   │
├─────────────────────────────────────────────────────────────────┤
│ [Copy All] [Export CSV] [Export Excel] [Group by Supplier ▼]   │
├─────────────────────────────────────────────────────────────────┤
│ QTY │ Description    │ Dimensions  │ Unit │ Total  │ Supplier  │
├─────┼────────────────┼─────────────┼──────┼────────┼───────────┤
│  4  │ 2020 Extrusion │ 500×20×20   │ $5.00│ $20.00 │ Misumi ↗  │
│  8  │ M5 T-Nut       │ 10×8×4      │ $0.25│  $2.00 │ Amazon ↗  │
│  2  │ Corner Bracket │ 40×40×40    │ $3.50│  $7.00 │ Misumi ↗  │
├─────┴────────────────┴─────────────┴──────┴────────┴───────────┤
│ Supplier Summary:                                               │
│   Misumi:       $27.00 (6 items)  [Copy List]                  │
│   Amazon:        $2.00 (8 items)  [Copy List]                  │
├─────────────────────────────────────────────────────────────────┤
│ Total Parts: 14 │ Total Cost: $29.00                           │
└─────────────────────────────────────────────────────────────────┘
```

## Success Metrics
- ✅ Professional, polished appearance
- ✅ One-click copy to clipboard
- ✅ Supplier grouping and totals
- ✅ Clickable URLs with visual feedback
- ✅ Sortable/filterable
- ✅ Export options
- ✅ User can order parts in < 30 seconds

## Future Enhancements (Not in this session)
- Price comparison across suppliers
- Affiliate links
- Inventory tracking
- Order history
- Supplier ratings/reviews
- Auto-fill shopping carts via API
