"""StockFlow: sistema de inventario con interfaz gráfica. Python 3, sin dependencias."""
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

DATA_FILE = Path(__file__).with_name('stockflow_datos.json')


def load_products():
    if not DATA_FILE.exists():
        return [
            {'codigo': 'P001', 'nombre': 'Cuaderno', 'precio': 8500.0, 'cantidad': 24},
            {'codigo': 'P002', 'nombre': 'Bolígrafo', 'precio': 2500.0, 'cantidad': 7},
            {'codigo': 'P003', 'nombre': 'Carpeta', 'precio': 4200.0, 'cantidad': 15},
        ]
    try:
        data = json.loads(DATA_FILE.read_text(encoding='utf-8'))
        if not isinstance(data, list):
            raise ValueError('Formato inválido')
        return data
    except (OSError, ValueError, json.JSONDecodeError) as error:
        messagebox.showerror('Error', f'No se pudieron leer los datos: {error}')
        return []


class StockFlow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('StockFlow | Gestión de inventario')
        self.geometry('1000x650')
        self.minsize(800, 550)
        self.configure(bg='#f4f6fb')
        self.products = load_products()
        self.search_var = tk.StringVar()
        self.create_ui()
        self.refresh()

    def create_ui(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('Treeview', font=('Segoe UI', 10), rowheight=33, background='white', fieldbackground='white')
        style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'), background='#e9eef8', foreground='#253858')
        style.map('Treeview', background=[('selected', '#dbeafe')], foreground=[('selected', '#102a43')])

        header = tk.Frame(self, bg='#152b4a', height=110)
        header.pack(fill='x')
        header.pack_propagate(False)
        tk.Label(header, text='STOCKFLOW', font=('Segoe UI', 23, 'bold'), fg='white', bg='#152b4a').pack(anchor='w', padx=32, pady=(19, 0))
        tk.Label(header, text='Sistema de gestión de inventario y ventas', font=('Segoe UI', 11), fg='#c6d8ef', bg='#152b4a').pack(anchor='w', padx=33)

        body = tk.Frame(self, bg='#f4f6fb')
        body.pack(fill='both', expand=True, padx=30, pady=22)
        self.summary = tk.Label(body, text='', font=('Segoe UI', 12, 'bold'), fg='#243b53', bg='#f4f6fb')
        self.summary.pack(anchor='w', pady=(0, 16))

        toolbar = tk.Frame(body, bg='#f4f6fb')
        toolbar.pack(fill='x', pady=(0, 12))
        tk.Label(toolbar, text='Buscar:', font=('Segoe UI', 10), bg='#f4f6fb').pack(side='left')
        entry = ttk.Entry(toolbar, textvariable=self.search_var, width=28)
        entry.pack(side='left', padx=10)
        self.search_var.trace_add('write', lambda *_: self.refresh())
        for label, command in [('Agregar producto', self.add_product), ('Editar', self.edit_product), ('Registrar venta', self.sell_product), ('Eliminar', self.delete_product)]:
            tk.Button(toolbar, text=label, command=command, bg='#2563eb' if label == 'Agregar producto' else '#e5eaf3', fg='white' if label == 'Agregar producto' else '#243b53', relief='flat', padx=12, pady=9, font=('Segoe UI', 9, 'bold'), cursor='hand2').pack(side='left', padx=4)

        columns = ('codigo', 'nombre', 'precio', 'cantidad', 'estado')
        self.table = ttk.Treeview(body, columns=columns, show='headings', selectmode='browse')
        for key, title, width in [('codigo', 'Código', 110), ('nombre', 'Producto', 300), ('precio', 'Precio (COP)', 140), ('cantidad', 'Unidades', 100), ('estado', 'Estado', 130)]:
            self.table.heading(key, text=title)
            self.table.column(key, width=width, anchor='w' if key == 'nombre' else 'center')
        self.table.tag_configure('low', background='#fff2e7')
        self.table.pack(fill='both', expand=True)
        tk.Label(body, text='Los datos se guardan automáticamente en stockflow_datos.json. Selecciona un producto para editarlo, venderlo o eliminarlo.', bg='#f4f6fb', fg='#52677f', font=('Segoe UI', 9)).pack(anchor='w', pady=(12, 0))

    def save(self):
        try:
            DATA_FILE.write_text(json.dumps(self.products, indent=2, ensure_ascii=False), encoding='utf-8')
        except OSError as error:
            messagebox.showerror('Error al guardar', str(error))
            return False
        self.refresh()
        return True

    def refresh(self):
        for item in self.table.get_children():
            self.table.delete(item)
        query = self.search_var.get().strip().lower()
        for product in self.products:
            if query not in (product['codigo'] + ' ' + product['nombre']).lower():
                continue
            qty = product['cantidad']
            state = 'Agotado' if qty == 0 else ('Stock bajo' if qty <= 10 else 'Disponible')
            self.table.insert('', 'end', iid=product['codigo'], values=(product['codigo'], product['nombre'], f"$ {product['precio']:,.0f}", qty, state), tags=('low',) if qty <= 10 else ())
        total = sum(p['precio'] * p['cantidad'] for p in self.products)
        low = sum(p['cantidad'] <= 10 for p in self.products)
        self.summary.config(text=f"{len(self.products)} productos     |     {sum(p['cantidad'] for p in self.products)} unidades     |     Valor inventario: $ {total:,.0f} COP     |     {low} alertas")

    def selected(self):
        selection = self.table.selection()
        if not selection:
            messagebox.showinfo('Seleccionar producto', 'Selecciona primero un producto de la tabla.')
            return None
        return next((p for p in self.products if p['codigo'] == selection[0]), None)

    def product_form(self, title, current=None):
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.geometry('390x340')
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        fields = {}
        for row, (key, label) in enumerate([('codigo', 'Código'), ('nombre', 'Nombre'), ('precio', 'Precio (COP)'), ('cantidad', 'Cantidad')]):
            tk.Label(dialog, text=label, font=('Segoe UI', 10)).grid(row=row * 2, column=0, sticky='w', padx=25, pady=(12, 2))
            entry = ttk.Entry(dialog, width=42)
            entry.grid(row=row * 2 + 1, column=0, padx=25)
            if current:
                entry.insert(0, str(current[key]))
            if key == 'codigo' and current:
                entry.configure(state='disabled')
            fields[key] = entry

        def submit():
            try:
                code = (current['codigo'] if current else fields['codigo'].get().strip().upper())
                name = fields['nombre'].get().strip()
                price = float(fields['precio'].get())
                qty = int(fields['cantidad'].get())
                if not code or not name or price < 0 or qty < 0:
                    raise ValueError('Completa los campos con valores válidos y no negativos.')
                if not current and any(p['codigo'] == code for p in self.products):
                    raise ValueError('Ese código ya existe.')
            except ValueError as error:
                messagebox.showerror('Datos inválidos', str(error), parent=dialog)
                return
            product = {'codigo': code, 'nombre': name, 'precio': price, 'cantidad': qty}
            if current:
                current.update(product)
            else:
                self.products.append(product)
            self.save()
            dialog.destroy()

        tk.Button(dialog, text='Guardar producto', command=submit, bg='#2563eb', fg='white', relief='flat', font=('Segoe UI', 10, 'bold'), padx=16, pady=8).grid(row=8, column=0, pady=16)
        dialog.wait_window()

    def add_product(self):
        self.product_form('Agregar producto')

    def edit_product(self):
        product = self.selected()
        if product:
            self.product_form('Editar producto', product)

    def sell_product(self):
        product = self.selected()
        if not product:
            return
        dialog = tk.Toplevel(self)
        dialog.title('Registrar venta')
        dialog.geometry('350x190')
        dialog.transient(self)
        dialog.grab_set()
        tk.Label(dialog, text=f"Vender: {product['nombre']}\nDisponibles: {product['cantidad']}", font=('Segoe UI', 11)).pack(pady=14)
        qty_entry = ttk.Entry(dialog, width=15)
        qty_entry.pack()
        qty_entry.focus_set()

        def confirm():
            try:
                qty = int(qty_entry.get())
                if qty <= 0 or qty > product['cantidad']:
                    raise ValueError('La cantidad debe ser positiva y no superar el inventario.')
            except ValueError as error:
                messagebox.showerror('Venta inválida', str(error), parent=dialog)
                return
            product['cantidad'] -= qty
            self.save()
            dialog.destroy()
            messagebox.showinfo('Venta registrada', f"Venta: {qty} unidades\nTotal: $ {qty * product['precio']:,.0f} COP")

        tk.Button(dialog, text='Confirmar venta', command=confirm, bg='#2563eb', fg='white', relief='flat', padx=12, pady=8).pack(pady=12)
        dialog.wait_window()

    def delete_product(self):
        product = self.selected()
        if product and messagebox.askyesno('Confirmar eliminación', f"¿Eliminar {product['nombre']} del inventario?"):
            self.products.remove(product)
            self.save()


if __name__ == '__main__':
    StockFlow().mainloop()
