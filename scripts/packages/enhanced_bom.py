"""
Enhanced Bill of Materials (BOM) dialog for AlexCAD.

Features:
- Professional table styling with alternating row colors
- Supplier grouping and subtotals
- Clickable URLs with hover effects
- Copy to clipboard functionality
- Sortable columns
- Export options
- Supplier summary section
"""

import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from urllib.parse import urlparse
from collections import defaultdict
import csv
import os


class EnhancedBOMDialog:
    """Enhanced Bill of Materials dialog with supplier grouping and smart features."""
    
    def __init__(self, parent, bom_data, filename=None):
        """
        Initialize the Enhanced BOM dialog.
        
        Args:
            parent: Parent tkinter window
            bom_data: List of BOM line items (CSV format strings)
            filename: Optional filename for export default
        """
        self.parent = parent
        self.filename = filename
        self.original_bom_items = self._parse_bom_data(bom_data)
        self.bom_items = self.original_bom_items.copy()  # Working copy for filtering
        self.grouped_view = False  # Track if we're in grouped view
        self.expanded_suppliers = {}  # Track which suppliers are expanded
        self.sort_column = None  # Track current sort column
        self.sort_reverse = False  # Track sort direction
        self.search_var = None  # Search text variable
        
        # Create dialog window
        self.window = tk.Toplevel(parent)
        self.window.title(f"Bill of Materials - Total: ${self._calculate_total():.2f}")
        self.window.geometry("1000x600")
        
        # Build UI
        self._create_ui()
        
        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()
        
    def _parse_bom_data(self, bom_lines):
        """Parse BOM data from CSV format into structured items."""
        items = []
        
        print(f"DEBUG: Parsing {len(bom_lines)} BOM lines")
        
        for idx, line in enumerate(bom_lines):
            parts = line.split(',')
            print(f"DEBUG: Line {idx}: {len(parts)} parts - {line[:100]}")
            
            # Need at least 6 parts (qty, desc, x, y, z, unit_cost)
            if len(parts) >= 6:
                try:
                    # Get URL if available (index 7 or later)
                    url = ''
                    if len(parts) > 7:
                        url = parts[7].strip()
                    
                    item = {
                        'qty': int(parts[0]) if parts[0].strip() else 0,
                        'description': parts[1].strip(),
                        'dim_x': parts[2].strip(),
                        'dim_y': parts[3].strip(),
                        'dim_z': parts[4].strip(),
                        'unit_cost': float(parts[5].replace('$', '').strip()) if parts[5].strip() else 0.0,
                        'total_cost': float(parts[6].replace('$', '').strip()) if len(parts) > 6 and parts[6].strip() else 0.0,
                        'url': url,
                        'supplier': self._extract_supplier(url)
                    }
                    items.append(item)
                    print(f"DEBUG: Successfully parsed item: {item['description']}")
                except (ValueError, IndexError) as e:
                    print(f"Warning: Failed to parse BOM line {idx}: {line} - {e}")
                    continue
            else:
                print(f"DEBUG: Skipping line {idx} - only {len(parts)} parts")
        
        print(f"DEBUG: Parsed {len(items)} items total")
        
        if len(items) == 0:
            print("ERROR: No items were parsed from BOM data!")
            # Show error to user
            import tkinter.messagebox as messagebox
            messagebox.showerror(
                "BOM Parse Error",
                f"Failed to parse BOM data.\n\n"
                f"Received {len(bom_lines)} lines but could not parse any items.\n"
                f"Please check the console for details."
            )
        
        return items
    
    def _extract_supplier(self, url):
        """Extract supplier name from URL."""
        if not url or not url.startswith('http'):
            return 'Unknown'
        
        try:
            domain = urlparse(url).netloc
            # Remove 'www.' prefix
            domain = domain.replace('www.', '')
            # Get the main domain name
            parts = domain.split('.')
            if len(parts) >= 2:
                supplier_name = parts[-2]
                # Capitalize and handle special cases
                supplier_map = {
                    'misumi': 'Misumi',
                    'mcmaster': 'McMaster-Carr',
                    'amazon': 'Amazon',
                    'aliexpress': 'AliExpress',
                    'ebay': 'eBay',
                    'grainger': 'Grainger',
                    'fastenal': 'Fastenal',
                    'openbuilds': 'OpenBuilds',
                }
                return supplier_map.get(supplier_name.lower(), supplier_name.title())
        except Exception as e:
            print(f"Warning: Failed to extract supplier from {url}: {e}")
        
        return 'Unknown'
    
    def _calculate_total(self):
        """Calculate total cost of all items."""
        return sum(item['total_cost'] for item in self.bom_items)
    
    def _group_by_supplier(self):
        """Group items by supplier and calculate subtotals."""
        grouped = defaultdict(list)
        for item in self.bom_items:
            grouped[item['supplier']].append(item)
        return dict(grouped)
    
    def _create_ui(self):
        """Create the user interface."""
        # Import tooltip if available
        try:
            from packages import tooltip
            has_tooltip = True
        except ImportError:
            has_tooltip = False
        
        # Top button bar
        button_frame = tk.Frame(self.window, pady=5)
        button_frame.pack(fill='x', padx=10)
        
        copy_btn = tk.Button(
            button_frame,
            text="📋 Copy All",
            command=self._copy_all,
            padx=10
        )
        copy_btn.pack(side='left', padx=2)
        if has_tooltip:
            tooltip.add_tooltip(copy_btn, "Copy entire BOM to clipboard (Ctrl+C)")
        
        export_btn = tk.Button(
            button_frame,
            text="💾 Export CSV",
            command=self._export_csv,
            padx=10
        )
        export_btn.pack(side='left', padx=2)
        if has_tooltip:
            tooltip.add_tooltip(export_btn, "Export BOM to CSV file (Ctrl+E)")
        
        self.group_button = tk.Button(
            button_frame,
            text="📊 Group by Supplier",
            command=self._toggle_supplier_grouping,
            padx=10
        )
        self.group_button.pack(side='left', padx=2)
        if has_tooltip:
            tooltip.add_tooltip(self.group_button, "Toggle supplier grouping view (Ctrl+G)")
        
        # Expand/Collapse All button (only visible in grouped view)
        self.expand_all_button = tk.Button(
            button_frame,
            text="▼ Expand All",
            command=self._expand_collapse_all,
            padx=10
        )
        # Will be packed when grouped view is active
        if has_tooltip:
            tooltip.add_tooltip(self.expand_all_button, "Expand or collapse all supplier groups")
        
        # Search box
        tk.Label(button_frame, text="🔍", font=('Arial', 12)).pack(side='left', padx=(10, 2))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self._apply_filter())
        search_entry = tk.Entry(
            button_frame,
            textvariable=self.search_var,
            width=20,
            font=('Arial', 10)
        )
        search_entry.pack(side='left', padx=2)
        if has_tooltip:
            tooltip.add_tooltip(search_entry, "Search parts by description (Ctrl+F)")
        
        # Clear search button
        clear_btn = tk.Button(
            button_frame,
            text="✕",
            command=lambda: self.search_var.set(''),
            padx=5,
            font=('Arial', 9)
        )
        clear_btn.pack(side='left', padx=2)
        if has_tooltip:
            tooltip.add_tooltip(clear_btn, "Clear search")
        
        # Help button on the right
        help_btn = tk.Button(
            button_frame,
            text="❓",
            command=self._show_shortcuts_help,
            padx=8,
            font=('Arial', 10, 'bold')
        )
        help_btn.pack(side='right', padx=2)
        if has_tooltip:
            tooltip.add_tooltip(help_btn, "Show keyboard shortcuts (F1)")
        
        
        # Main content area with scrollbar
        content_frame = tk.Frame(self.window)
        content_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create canvas with scrollbar
        canvas = tk.Canvas(content_frame)
        scrollbar = tk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Build BOM table
        self._build_bom_table()
        
        # Bottom status bar
        self._create_status_bar()
    
    def _build_bom_table(self):
        """Build the BOM table with styling."""
        # Clear existing content
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Create table frame
        table_frame = tk.Frame(self.scrollable_frame)
        table_frame.pack(fill='both', expand=True)
        
        # Header row (clickable for sorting)
        headers = ['QTY', 'Description', 'Dimensions', 'Unit Cost', 'Total Cost', 'Supplier']
        header_keys = ['qty', 'description', 'dimensions', 'unit_cost', 'total_cost', 'supplier']
        header_bg = '#2c3e50'
        header_fg = 'white'
        
        for col, (header, key) in enumerate(zip(headers, header_keys)):
            # Add sort indicator if this is the sorted column
            header_text = header
            if self.sort_column == key:
                header_text += ' ▼' if self.sort_reverse else ' ▲'
            
            label = tk.Label(
                table_frame,
                text=header_text,
                bg=header_bg,
                fg=header_fg,
                font=('Arial', 10, 'bold'),
                padx=10,
                pady=8,
                relief='raised',
                borderwidth=1,
                cursor='hand2'
            )
            label.grid(row=0, column=col, sticky='ew')
            
            # Bind click to sort
            label.bind('<Button-1>', lambda e, k=key: self._sort_by_column(k))
        
        # Data rows with alternating colors
        row_colors = ['#ecf0f1', '#ffffff']
        
        for idx, item in enumerate(self.bom_items):
            row = idx + 1
            bg_color = row_colors[idx % 2]
            
            # Quantity
            tk.Label(
                table_frame,
                text=str(item['qty']),
                bg=bg_color,
                padx=10,
                pady=5,
                anchor='center'
            ).grid(row=row, column=0, sticky='ew')
            
            # Description
            desc_label = tk.Label(
                table_frame,
                text=item['description'],
                bg=bg_color,
                fg='#2c3e50',
                font=('Arial', 9, 'bold'),
                padx=10,
                pady=5,
                anchor='w'
            )
            desc_label.grid(row=row, column=1, sticky='ew')
            
            # Dimensions
            dims = f"{item['dim_x']}×{item['dim_y']}×{item['dim_z']}"
            tk.Label(
                table_frame,
                text=dims,
                bg=bg_color,
                padx=10,
                pady=5,
                anchor='center'
            ).grid(row=row, column=2, sticky='ew')
            
            # Unit Cost
            tk.Label(
                table_frame,
                text=f"${item['unit_cost']:.2f}",
                bg=bg_color,
                padx=10,
                pady=5,
                anchor='e'
            ).grid(row=row, column=3, sticky='ew')
            
            # Total Cost
            tk.Label(
                table_frame,
                text=f"${item['total_cost']:.2f}",
                bg=bg_color,
                font=('Arial', 9, 'bold'),
                padx=10,
                pady=5,
                anchor='e'
            ).grid(row=row, column=4, sticky='ew')
            
            # Supplier with clickable URL
            supplier_frame = tk.Frame(table_frame, bg=bg_color)
            supplier_frame.grid(row=row, column=5, sticky='ew')
            
            if item['url'] and item['url'].startswith('http'):
                supplier_label = tk.Label(
                    supplier_frame,
                    text=f"{item['supplier']} ↗",
                    bg=bg_color,
                    fg='#3498db',
                    cursor='hand2',
                    padx=10,
                    pady=5,
                    anchor='w'
                )
                supplier_label.pack(side='left')
                
                # Bind click to open URL
                supplier_label.bind('<Button-1>', lambda e, url=item['url']: webbrowser.open_new(url))
                
                # Hover effects
                def on_enter(e, label=supplier_label):
                    label.config(fg='#2980b9', font=('Arial', 9, 'bold underline'))
                
                def on_leave(e, label=supplier_label):
                    label.config(fg='#3498db', font=('Arial', 9))
                
                supplier_label.bind('<Enter>', on_enter)
                supplier_label.bind('<Leave>', on_leave)
            else:
                tk.Label(
                    supplier_frame,
                    text=item['supplier'],
                    bg=bg_color,
                    padx=10,
                    pady=5,
                    anchor='w'
                ).pack(side='left')
        
        # Configure column weights for resizing
        for col in range(len(headers)):
            table_frame.columnconfigure(col, weight=1)
    
    def _toggle_supplier_grouping(self):
        """Toggle between flat and supplier-grouped view."""
        self.grouped_view = not self.grouped_view
        
        if self.grouped_view:
            self.group_button.config(text="📋 Show All Items")
            # Show expand/collapse all button
            self.expand_all_button.pack(side='left', padx=2, after=self.group_button)
            self._build_grouped_view()
        else:
            self.group_button.config(text="📊 Group by Supplier")
            # Hide expand/collapse all button
            self.expand_all_button.pack_forget()
            self._build_bom_table()
    
    def _build_grouped_view(self):
        """Build supplier-grouped view with collapsible sections."""
        # Clear existing content
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Get supplier groups
        supplier_groups = self._group_by_supplier()
        
        # Sort suppliers alphabetically
        sorted_suppliers = sorted(supplier_groups.keys())
        
        # Create main container
        main_frame = tk.Frame(self.scrollable_frame)
        main_frame.pack(fill='both', expand=True)
        
        # For each supplier, create a collapsible section
        for supplier_name in sorted_suppliers:
            items = supplier_groups[supplier_name]
            supplier_total = sum(item['total_cost'] for item in items)
            supplier_qty = sum(item['qty'] for item in items)
            
            # Initialize expanded state if not set
            if supplier_name not in self.expanded_suppliers:
                self.expanded_suppliers[supplier_name] = True
            
            # Supplier header frame
            header_frame = tk.Frame(main_frame, bg='#3498db', relief='raised', borderwidth=2)
            header_frame.pack(fill='x', pady=2)
            
            # Expand/collapse button
            expand_symbol = '▼' if self.expanded_suppliers[supplier_name] else '▶'
            expand_btn = tk.Label(
                header_frame,
                text=expand_symbol,
                bg='#3498db',
                fg='white',
                font=('Arial', 12, 'bold'),
                cursor='hand2',
                padx=10
            )
            expand_btn.pack(side='left')
            
            # Bind click to toggle
            expand_btn.bind('<Button-1>', lambda e, s=supplier_name: self._toggle_supplier_section(s))
            
            # Supplier name and summary
            summary_text = f"{supplier_name} - {len(items)} items, {supplier_qty} parts - ${supplier_total:.2f}"
            summary_label = tk.Label(
                header_frame,
                text=summary_text,
                bg='#3498db',
                fg='white',
                font=('Arial', 11, 'bold'),
                cursor='hand2',
                padx=10,
                pady=8
            )
            summary_label.pack(side='left', fill='x', expand=True)
            summary_label.bind('<Button-1>', lambda e, s=supplier_name: self._toggle_supplier_section(s))
            
            # Copy supplier list button
            copy_btn = tk.Button(
                header_frame,
                text="📋 Copy",
                command=lambda s=supplier_name, itms=items: self._copy_supplier_list(s, itms),
                bg='#2980b9',
                fg='white',
                font=('Arial', 9, 'bold'),
                cursor='hand2',
                padx=10,
                pady=4,
                relief='flat'
            )
            copy_btn.pack(side='right', padx=5)
            
            # Items table (only if expanded)
            if self.expanded_suppliers[supplier_name]:
                items_frame = tk.Frame(main_frame, bg='#ecf0f1', relief='sunken', borderwidth=1)
                items_frame.pack(fill='x', padx=20, pady=(0, 5))
                
                # Table headers
                headers = ['QTY', 'Description', 'Dimensions', 'Unit Cost', 'Total Cost', 'Link']
                header_row = tk.Frame(items_frame, bg='#95a5a6')
                header_row.pack(fill='x')
                
                for col, header in enumerate(headers):
                    tk.Label(
                        header_row,
                        text=header,
                        bg='#95a5a6',
                        fg='white',
                        font=('Arial', 9, 'bold'),
                        padx=8,
                        pady=5
                    ).grid(row=0, column=col, sticky='ew')
                
                # Configure column weights
                for col in range(len(headers)):
                    header_row.columnconfigure(col, weight=1)
                
                # Data rows
                row_colors = ['#ffffff', '#f8f9fa']
                for idx, item in enumerate(items):
                    row_frame = tk.Frame(items_frame, bg=row_colors[idx % 2])
                    row_frame.pack(fill='x')
                    
                    bg = row_colors[idx % 2]
                    
                    # Quantity
                    tk.Label(
                        row_frame,
                        text=str(item['qty']),
                        bg=bg,
                        padx=8,
                        pady=4,
                        anchor='center'
                    ).grid(row=0, column=0, sticky='ew')
                    
                    # Description
                    tk.Label(
                        row_frame,
                        text=item['description'],
                        bg=bg,
                        font=('Arial', 9, 'bold'),
                        padx=8,
                        pady=4,
                        anchor='w'
                    ).grid(row=0, column=1, sticky='ew')
                    
                    # Dimensions
                    dims = f"{item['dim_x']}×{item['dim_y']}×{item['dim_z']}"
                    tk.Label(
                        row_frame,
                        text=dims,
                        bg=bg,
                        padx=8,
                        pady=4,
                        anchor='center'
                    ).grid(row=0, column=2, sticky='ew')
                    
                    # Unit Cost
                    tk.Label(
                        row_frame,
                        text=f"${item['unit_cost']:.2f}",
                        bg=bg,
                        padx=8,
                        pady=4,
                        anchor='e'
                    ).grid(row=0, column=3, sticky='ew')
                    
                    # Total Cost
                    tk.Label(
                        row_frame,
                        text=f"${item['total_cost']:.2f}",
                        bg=bg,
                        font=('Arial', 9, 'bold'),
                        padx=8,
                        pady=4,
                        anchor='e'
                    ).grid(row=0, column=4, sticky='ew')
                    
                    # Link
                    if item['url'] and item['url'].startswith('http'):
                        link_label = tk.Label(
                            row_frame,
                            text="↗ Open",
                            bg=bg,
                            fg='#3498db',
                            cursor='hand2',
                            padx=8,
                            pady=4,
                            anchor='center'
                        )
                        link_label.grid(row=0, column=5, sticky='ew')
                        link_label.bind('<Button-1>', lambda e, url=item['url']: webbrowser.open_new(url))
                        
                        def on_enter(e, label=link_label):
                            label.config(fg='#2980b9', font=('Arial', 9, 'underline'))
                        
                        def on_leave(e, label=link_label):
                            label.config(fg='#3498db', font=('Arial', 9))
                        
                        link_label.bind('<Enter>', on_enter)
                        link_label.bind('<Leave>', on_leave)
                    else:
                        tk.Label(
                            row_frame,
                            text="-",
                            bg=bg,
                            padx=8,
                            pady=4,
                            anchor='center'
                        ).grid(row=0, column=5, sticky='ew')
                    
                    # Configure column weights
                    for col in range(len(headers)):
                        row_frame.columnconfigure(col, weight=1)
    
    def _toggle_supplier_section(self, supplier_name):
        """Toggle expansion state of a supplier section."""
        self.expanded_suppliers[supplier_name] = not self.expanded_suppliers[supplier_name]
        self._build_grouped_view()
    
    def _expand_collapse_all(self):
        """Expand or collapse all supplier sections."""
        # Check if any are collapsed
        any_collapsed = any(not expanded for expanded in self.expanded_suppliers.values())
        
        # If any are collapsed, expand all; otherwise collapse all
        new_state = any_collapsed
        
        for supplier in self.expanded_suppliers:
            self.expanded_suppliers[supplier] = new_state
        
        # Update button text
        self.expand_all_button.config(text="▼ Expand All" if not new_state else "▲ Collapse All")
        
        self._build_grouped_view()
    
    def _sort_by_column(self, column_key):
        """Sort BOM items by the specified column."""
        # Toggle sort direction if clicking same column
        if self.sort_column == column_key:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column_key
            self.sort_reverse = False
        
        # Sort the items
        if column_key == 'dimensions':
            # Special handling for dimensions - sort by total volume
            def dim_key(item):
                try:
                    x = float(item['dim_x']) if item['dim_x'] else 0
                    y = float(item['dim_y']) if item['dim_y'] else 0
                    z = float(item['dim_z']) if item['dim_z'] else 0
                    return x * y * z
                except (ValueError, TypeError):
                    return 0
            self.bom_items.sort(key=dim_key, reverse=self.sort_reverse)
        else:
            self.bom_items.sort(key=lambda x: x[column_key], reverse=self.sort_reverse)
        
        # Rebuild the table
        if self.grouped_view:
            self._build_grouped_view()
        else:
            self._build_bom_table()
    
    def _apply_filter(self):
        """Apply search filter to BOM items."""
        search_text = self.search_var.get().lower().strip()
        
        if not search_text:
            # No filter - show all items
            self.bom_items = self.original_bom_items.copy()
        else:
            # Filter items by description
            self.bom_items = [
                item for item in self.original_bom_items
                if search_text in item['description'].lower() or
                   search_text in item['supplier'].lower() or
                   search_text in f"{item['dim_x']}×{item['dim_y']}×{item['dim_z']}".lower()
            ]
        
        # Reapply current sort if any
        if self.sort_column:
            self._sort_by_column(self.sort_column)
        else:
            # Rebuild the view
            if self.grouped_view:
                self._build_grouped_view()
            else:
                self._build_bom_table()
        
        # Update window title with filtered count
        total = self._calculate_total()
        if search_text:
            self.window.title(f"Bill of Materials - Showing {len(self.bom_items)}/{len(self.original_bom_items)} items - Total: ${total:.2f}")
        else:
            self.window.title(f"Bill of Materials - Total: ${total:.2f}")
    
    def _flash_feedback(self, color='#2ecc71', duration=150):
        """Flash the window background briefly to indicate success."""
        original_bg = self.window.cget('bg')
        self.window.config(bg=color)
        self.window.update()
        self.window.after(duration, lambda: self.window.config(bg=original_bg))
    
    def _copy_supplier_list(self, supplier_name, items):
        """Copy a specific supplier's items to clipboard."""
        csv_lines = [f"{supplier_name} - Parts List"]
        csv_lines.append('QTY,Description,Dimensions,Unit Cost,Total Cost,URL')
        
        supplier_total = 0
        for item in items:
            dims = f"{item['dim_x']}×{item['dim_y']}×{item['dim_z']}"
            line = f"{item['qty']},{item['description']},{dims},${item['unit_cost']:.2f},${item['total_cost']:.2f},{item['url']}"
            csv_lines.append(line)
            supplier_total += item['total_cost']
        
        csv_lines.append(f",,,,${supplier_total:.2f},")
        csv_text = '\n'.join(csv_lines)
        
        # Copy to clipboard
        self.window.clipboard_clear()
        self.window.clipboard_append(csv_text)
        self.window.update()
        
        self._flash_feedback()
    
    def _create_status_bar(self):
        """Create bottom status bar with summary."""
        status_frame = tk.Frame(self.window, bg='#34495e', pady=8)
        status_frame.pack(fill='x', side='bottom')
        
        total_parts = sum(item['qty'] for item in self.bom_items)
        total_cost = self._calculate_total()
        unique_parts = len(self.bom_items)
        
        # Supplier summary
        suppliers = self._group_by_supplier()
        supplier_count = len(suppliers)
        
        status_text = f"Total Parts: {total_parts} | Unique Items: {unique_parts} | Suppliers: {supplier_count} | Total Cost: ${total_cost:.2f}"
        
        tk.Label(
            status_frame,
            text=status_text,
            bg='#34495e',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=10
        ).pack(side='left')
    
    def _copy_all(self):
        """Copy entire BOM to clipboard in CSV format."""
        csv_lines = ['QTY,Description,Dimensions,Unit Cost,Total Cost,Supplier,URL']
        
        for item in self.bom_items:
            dims = f"{item['dim_x']}×{item['dim_y']}×{item['dim_z']}"
            line = f"{item['qty']},{item['description']},{dims},${item['unit_cost']:.2f},${item['total_cost']:.2f},{item['supplier']},{item['url']}"
            csv_lines.append(line)
        
        # Add total
        csv_lines.append(f",,,,${self._calculate_total():.2f},,")
        
        csv_text = '\n'.join(csv_lines)
        
        # Copy to clipboard
        self.window.clipboard_clear()
        self.window.clipboard_append(csv_text)
        self.window.update()
        
        self._flash_feedback()
    
    def _export_csv(self):
        """Export BOM to CSV file."""
        from tkinter import filedialog
        
        default_name = "bom.csv"
        if self.filename and self.filename.endswith('.xcad'):
            default_name = self.filename[:-5] + '_bom.csv'
        
        filename = filedialog.asksaveasfilename(
            title="Export BOM to CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=default_name
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['QTY', 'Description', 'Dimensions', 'Unit Cost', 'Total Cost', 'Supplier', 'URL'])
                    
                    for item in self.bom_items:
                        dims = f"{item['dim_x']}×{item['dim_y']}×{item['dim_z']}"
                        writer.writerow([
                            item['qty'],
                            item['description'],
                            dims,
                            f"${item['unit_cost']:.2f}",
                            f"${item['total_cost']:.2f}",
                            item['supplier'],
                            item['url']
                        ])
                    
                    # Add total row
                    writer.writerow(['', '', '', '', f"${self._calculate_total():.2f}", '', ''])
                
                messagebox.showinfo("Export Successful", f"BOM exported to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Export Failed", f"Failed to export BOM:\n{str(e)}")
    
    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for the BOM dialog."""
        # Ctrl+C - Copy all
        self.window.bind('<Control-c>', lambda e: self._copy_all())
        
        # Ctrl+E - Export CSV
        self.window.bind('<Control-e>', lambda e: self._export_csv())
        
        # Ctrl+G - Toggle grouping
        self.window.bind('<Control-g>', lambda e: self._toggle_supplier_grouping())
        
        # Ctrl+F - Focus search box
        self.window.bind('<Control-f>', lambda e: self.window.focus_set() or e.widget.focus_set() if isinstance(e.widget, tk.Entry) else None)
        
        # Escape - Close dialog
        self.window.bind('<Escape>', lambda e: self.window.destroy())
        
        # F1 - Show shortcuts help
        self.window.bind('<F1>', lambda e: self._show_shortcuts_help())
    
    def _show_shortcuts_help(self):
        """Show keyboard shortcuts help dialog."""
        help_text = """Keyboard Shortcuts:

Ctrl+C      Copy all items to clipboard
Ctrl+E      Export to CSV file
Ctrl+G      Toggle supplier grouping
Ctrl+F      Focus search box
Escape      Close this dialog
F1 or ?     Show this help

Features:
• Click column headers to sort
• Use search box to filter parts
• Click supplier groups to expand/collapse

Tip: Hover over buttons to see tooltips!"""
        
        messagebox.showinfo("Keyboard Shortcuts", help_text)


def show_enhanced_bom(parent, bom_data, filename=None):
    """
    Show the enhanced BOM dialog.
    
    Args:
        parent: Parent tkinter window
        bom_data: List of BOM line items (CSV format strings)
        filename: Optional filename for export default
    """
    EnhancedBOMDialog(parent, bom_data, filename)
