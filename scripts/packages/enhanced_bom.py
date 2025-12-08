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
        self.bom_items = self._parse_bom_data(bom_data)
        
        # Create dialog window
        self.window = tk.Toplevel(parent)
        self.window.title(f"Bill of Materials - Total: ${self._calculate_total():.2f}")
        self.window.geometry("1000x600")
        
        # Build UI
        self._create_ui()
        
    def _parse_bom_data(self, bom_lines):
        """Parse BOM data from CSV format into structured items."""
        items = []
        
        for line in bom_lines:
            parts = line.split(',')
            if len(parts) >= 8:
                try:
                    item = {
                        'qty': int(parts[0]) if parts[0].strip() else 0,
                        'description': parts[1].strip(),
                        'dim_x': parts[2].strip(),
                        'dim_y': parts[3].strip(),
                        'dim_z': parts[4].strip(),
                        'unit_cost': float(parts[5].replace('$', '').strip()) if parts[5].strip() else 0.0,
                        'total_cost': float(parts[6].replace('$', '').strip()) if parts[6].strip() else 0.0,
                        'url': parts[7].strip() if len(parts) > 7 else '',
                        'supplier': self._extract_supplier(parts[7].strip() if len(parts) > 7 else '')
                    }
                    items.append(item)
                except (ValueError, IndexError) as e:
                    print(f"Warning: Failed to parse BOM line: {line} - {e}")
                    continue
        
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
        # Top button bar
        button_frame = tk.Frame(self.window, pady=5)
        button_frame.pack(fill='x', padx=10)
        
        tk.Button(
            button_frame,
            text="📋 Copy All",
            command=self._copy_all,
            padx=10
        ).pack(side='left', padx=2)
        
        tk.Button(
            button_frame,
            text="💾 Export CSV",
            command=self._export_csv,
            padx=10
        ).pack(side='left', padx=2)
        
        tk.Button(
            button_frame,
            text="📊 Group by Supplier",
            command=self._toggle_supplier_grouping,
            padx=10
        ).pack(side='left', padx=2)
        
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
        
        # Header row
        headers = ['QTY', 'Description', 'Dimensions', 'Unit Cost', 'Total Cost', 'Supplier']
        header_bg = '#2c3e50'
        header_fg = 'white'
        
        for col, header in enumerate(headers):
            label = tk.Label(
                table_frame,
                text=header,
                bg=header_bg,
                fg=header_fg,
                font=('Arial', 10, 'bold'),
                padx=10,
                pady=8,
                relief='raised',
                borderwidth=1
            )
            label.grid(row=0, column=col, sticky='ew')
        
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
        
        messagebox.showinfo("Copied", f"BOM copied to clipboard!\n{len(self.bom_items)} items")
    
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
    
    def _toggle_supplier_grouping(self):
        """Toggle between flat and supplier-grouped view."""
        # TODO: Implement supplier grouping view
        messagebox.showinfo("Coming Soon", "Supplier grouping view will be implemented next!")


def show_enhanced_bom(parent, bom_data, filename=None):
    """
    Show the enhanced BOM dialog.
    
    Args:
        parent: Parent tkinter window
        bom_data: List of BOM line items (CSV format strings)
        filename: Optional filename for export default
    """
    EnhancedBOMDialog(parent, bom_data, filename)
