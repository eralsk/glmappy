import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, Menu, filedialog
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import daft
import copy
import math
import numpy as np
import io
import json

# Copyright © 2026 Erik Skogsberg-De La O
# Licensed under the MIT License. See LICENSE file in the project root.
# See license.txt and third_party_notices.txt for details.

matplotlib.use("TkAgg")


class DaftGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GLMapPy B1.0")
        self.root.geometry("1200x1000")

        self.nodes = []
        self.edges = []
        self.plates = []

        self.current_font = "serif"
        self.current_font_size = 12
        self.current_font_color = "black"
        self.canvas_width = 10.0
        self.canvas_height = 10.0
        self.canvas_unit = "in"
        self.render_dpi = 100
        self.zoom_level = 1.0

        self.margin_in = 0.5

        self.show_grid_var = tk.BooleanVar(value=False)

        self.font_options = ["serif", "sans-serif", "monospace", "Times New Roman", "Arial"]
        self.unit_options = ["in", "cm", "mm", "px"]
        self.text_color_options = ["black", "white"]
        self.node_shape_options = ["circle", "rectangle"]

        self.history = []
        self.redo_stack = []

        self.edge_styles = {"Solid": "-", "Dashed": "--", "Dotted": ":", "Dash-Dot": "-."}
        self.plate_positions = ["bottom right", "bottom left", "top right", "top left"]

        self.control_frame = ttk.Frame(root, padding="10")
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.preview_frame = tk.Frame(root, bg="#cccccc")
        self.preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.preview_frame.rowconfigure(0, weight=1)
        self.preview_frame.columnconfigure(0, weight=1)

        self.v_scroll = ttk.Scrollbar(self.preview_frame, orient=tk.VERTICAL)
        self.h_scroll = ttk.Scrollbar(self.preview_frame, orient=tk.HORIZONTAL)

        self.viewport = tk.Canvas(self.preview_frame, bg="#cccccc",
                                  yscrollcommand=self.v_scroll.set,
                                  xscrollcommand=self.h_scroll.set,
                                  highlightthickness=0)

        self.v_scroll.config(command=self.viewport.yview)
        self.h_scroll.config(command=self.viewport.xview)

        self.viewport.grid(row=0, column=0, sticky="nsew")
        self.v_scroll.grid(row=0, column=1, sticky="ns")
        self.h_scroll.grid(row=1, column=0, sticky="ew")

        self.paper_label = tk.Label(self.viewport, bg="white", borderwidth=0)
        self.viewport_window = self.viewport.create_window(0, 0, window=self.paper_label, anchor="center")

        self.viewport.bind("<Configure>", self.on_viewport_resize)
        self.paper_label.bind("<Motion>", self.on_mouse_move)
        self.paper_label.bind("<Button-1>", self.on_canvas_click)

        self.current_image = None

        self.status_var = tk.StringVar()
        self.status_var.set("Ready.")
        self.status_bar = ttk.Label(self.preview_frame, textvariable=self.status_var, relief="sunken", anchor="w")
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="ew")

        self.root.bind("<Control-z>", lambda event: self.undo())
        self.root.bind("<Control-y>", lambda event: self.redo())
        self.root.bind("<Control-s>", lambda event: self.save_project())
        self.root.bind("<Control-p>", lambda event: self.open_final_preview())
        self.root.bind("<equal>", lambda event: self.zoom_in())
        self.root.bind("<minus>", lambda event: self.zoom_out())

        self._resize_job = None

        self.create_menu()
        self.setup_controls()
        self.refresh_plot()

        try:
            self.root.iconbitmap("gicon.ico")
        except:
            pass

    def create_menu(self):
        menubar = Menu(self.root)

        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Diagram (Clear)", command=self.clear_all)
        file_menu.add_separator()
        file_menu.add_command(label="Open Project...", command=self.load_project)
        file_menu.add_command(label="Save Project As...", accelerator="Ctrl+S", command=self.save_project)
        file_menu.add_separator()
        file_menu.add_command(label="Export Image As...", command=self.save_export_image)
        file_menu.add_command(label="Preview Export Window...", accelerator="Ctrl+P", command=self.open_final_preview)
        file_menu.add_separator()
        file_menu.add_command(label="Generate Python Code", command=self.generate_code)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=self.undo)
        edit_menu.add_command(label="Redo", accelerator="Ctrl+Y", command=self.redo)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        insert_menu = Menu(menubar, tearoff=0)
        insert_menu.add_command(label="Add Node", command=self.add_node)
        insert_menu.add_command(label="Add Edge", command=self.add_edge)
        insert_menu.add_command(label="Add Plate", command=self.add_plate)
        menubar.add_cascade(label="Insert", menu=insert_menu)

        view_menu = Menu(menubar, tearoff=0)
        view_menu.add_command(label="Refresh Plot", command=self.refresh_plot)
        view_menu.add_separator()
        view_menu.add_command(label="Zoom In (=)", command=self.zoom_in)
        view_menu.add_command(label="Zoom Out (-)", command=self.zoom_out)
        view_menu.add_separator()
        view_menu.add_checkbutton(label="Show Grid", onvalue=True, offvalue=False,
                                  variable=self.show_grid_var, command=self.refresh_plot)
        menubar.add_cascade(label="View", menu=view_menu)

        help_menu = Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def show_about(self):
        messagebox.showinfo("About", "GLMapPy Version BETA 1.0\nFixed-Layout Image Buffer Mode\n\nCopyright (c) 2026 Erik Skogsberg-De La O\nLicensed under the MIT License. See LICENSE file in the project root.")

    def zoom_in(self, event=None):
        if self.zoom_level < 5.0:
            self.zoom_level += 0.2
            self.refresh_plot()

    def zoom_out(self, event=None):
        if self.zoom_level > 0.2:
            self.zoom_level -= 0.2
            self.refresh_plot()

    # -------------------------------------------------------------------------
    # SAVE / LOAD
    # -------------------------------------------------------------------------
    def save_project(self, event=None):
        data = {
            "nodes": self.nodes,
            "edges": self.edges,
            "plates": self.plates,
            "settings": {
                "font": self.current_font,
                "font_size": self.current_font_size,
                "font_color": self.current_font_color,
                "canvas_width": self.canvas_width,
                "canvas_height": self.canvas_height,
                "canvas_unit": self.canvas_unit,
                "show_grid": self.show_grid_var.get()
            }
        }
        file_path = filedialog.asksaveasfilename(defaultextension=".json",
                                                 filetypes=[("GLMapPy Project", "*.json"), ("All Files", "*.*")])
        if file_path:
            try:
                with open(file_path, "w") as f:
                    json.dump(data, f, indent=4)
                messagebox.showinfo("Success", f"Project saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save project:\n{e}")

    def load_project(self):
        file_path = filedialog.askopenfilename(filetypes=[("GLMapPy Project", "*.json"), ("All Files", "*.*")])
        if file_path:
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)

                self.save_state()
                self.nodes = data.get("nodes", [])
                self.edges = data.get("edges", [])
                self.plates = data.get("plates", [])

                settings = data.get("settings", {})
                self.current_font = settings.get("font", "serif")
                self.current_font_size = settings.get("font_size", 12)
                self.current_font_color = settings.get("font_color", "black")
                self.canvas_width = settings.get("canvas_width", 10.0)
                self.canvas_height = settings.get("canvas_height", 10.0)
                self.canvas_unit = settings.get("canvas_unit", "in")
                self.show_grid_var.set(settings.get("show_grid", False))

                self.combo_font.set(self.current_font)
                self.entry_font_size.delete(0, tk.END)
                self.entry_font_size.insert(0, str(self.current_font_size))
                self.combo_font_color.set(self.current_font_color)

                self.entry_canvas_w.delete(0, tk.END)
                self.entry_canvas_w.insert(0, str(self.canvas_width))
                self.entry_canvas_h.delete(0, tk.END)
                self.entry_canvas_h.insert(0, str(self.canvas_height))
                self.combo_unit.set(self.canvas_unit)

                self.refresh_plot()
                messagebox.showinfo("Success", "Project loaded successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load project:\n{e}")

    # -------------------------------------------------------------------------
    # LAYOUT & INTERACTION
    # -------------------------------------------------------------------------
    def on_viewport_resize(self, event):
        self.center_paper()

    def center_paper(self):
        canvas_w = self.viewport.winfo_width()
        canvas_h = self.viewport.winfo_height()
        paper_w = self.paper_label.winfo_reqwidth()
        paper_h = self.paper_label.winfo_reqheight()

        x = max(paper_w / 2, canvas_w / 2)
        y = max(paper_h / 2, canvas_h / 2)

        self.viewport.coords(self.viewport_window, x, y)
        self.viewport.config(scrollregion=self.viewport.bbox("all"))

    def get_grid_unit(self):
        if self.canvas_unit == "cm":
            return 1 / 2.54
        elif self.canvas_unit == "mm":
            return 1 / 25.4
        elif self.canvas_unit == "px":
            return 1 / 100.0
        return 1.0

    def get_coords_from_event(self, event):
        if not self.current_image: return 0, 0

        g_unit = self.get_grid_unit()

        effective_dpi = self.render_dpi * self.zoom_level
        scale_px_per_unit = effective_dpi * g_unit

        margin_px = self.margin_in * effective_dpi

        x_graph = (event.x - margin_px) / scale_px_per_unit

        img_h = self.current_image.height()
        y_from_bottom = img_h - event.y
        y_graph = (y_from_bottom - margin_px) / scale_px_per_unit

        return x_graph, y_graph

    def on_mouse_move(self, event):
        if not self.current_image: return
        x, y = self.get_coords_from_event(event)
        self.status_var.set(f"Cursor: X={x:.2f}, Y={y:.2f} (Zoom: {int(self.zoom_level * 100)}%)")

    def on_canvas_click(self, event):
        if not self.current_image: return
        x, y = self.get_coords_from_event(event)
        self.entry_x.delete(0, tk.END)
        self.entry_x.insert(0, f"{x:.1f}")
        self.entry_y.delete(0, tk.END)
        self.entry_y.insert(0, f"{y:.1f}")
        self.entry_plate_x.delete(0, tk.END)
        self.entry_plate_x.insert(0, f"{x:.1f}")
        self.entry_plate_y.delete(0, tk.END)
        self.entry_plate_y.insert(0, f"{y:.1f}")
        self.status_var.set(f"Set Input to: X={x:.1f}, Y={y:.1f}")

    def on_window_resize(self, event):
        if self._resize_job:
            self.root.after_cancel(self._resize_job)
        self._resize_job = self.root.after(100, self.refresh_plot)

    # -------------------------------------------------------------------------
    # RENDERING PIPELINE
    # -------------------------------------------------------------------------
    def refresh_plot(self):
        plt.rc("font", family=self.current_font, size=self.current_font_size)
        plt.rc("text", color=self.current_font_color)

        g_unit = self.get_grid_unit()
        pgm = daft.PGM(shape=[self.canvas_width, self.canvas_height], origin=[0, 0], grid_unit=g_unit, node_unit=1.0)

        self._populate_pgm(pgm)
        pgm.render()
        self._draw_manual_components(pgm)

        if pgm.ax:
            try:
                spacing = float(self.entry_grid_spacing.get())
            except:
                spacing = 1.0
            if spacing <= 0: spacing = 1.0

            pgm.ax.set_xlim(0, self.canvas_width)
            pgm.ax.set_ylim(0, self.canvas_height)

            pgm.ax.set_frame_on(False)
            pgm.ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)

            # --- GRID ---
            if self.show_grid_var.get():
                pgm.ax.set_xticks(np.arange(0, self.canvas_width + 0.1, spacing))
                pgm.ax.set_yticks(np.arange(0, self.canvas_height + 0.1, spacing))
                pgm.ax.grid(True, linestyle='--', alpha=0.5)
            else:
                pgm.ax.grid(False)
                pgm.ax.axis('off')

            pgm.figure.subplots_adjust(left=0, right=1, top=1, bottom=0)

        # render to memory buffer
        buf = io.BytesIO()
        w_in_content = self.canvas_width * g_unit
        h_in_content = self.canvas_height * g_unit

        total_w_in = w_in_content + (2 * self.margin_in)
        total_h_in = h_in_content + (2 * self.margin_in)

        pgm.figure.set_size_inches(total_w_in, total_h_in)

        frac_left = self.margin_in / total_w_in
        frac_bottom = self.margin_in / total_h_in

        pgm.figure.subplots_adjust(left=frac_left, right=1.0 - frac_left,
                                   bottom=frac_bottom, top=1.0 - frac_bottom)

        effective_dpi = self.render_dpi * self.zoom_level

        pgm.figure.savefig(buf, format='png', dpi=effective_dpi, facecolor='white')
        plt.close(pgm.figure)
        buf.seek(0)

        self.current_image = tk.PhotoImage(data=buf.getvalue())
        buf.close()

        self.paper_label.config(image=self.current_image)
        self.center_paper()

    # -------------------------------------------------------------------------
    # DAFT HELPERS
    # -------------------------------------------------------------------------
    def _populate_pgm(self, pgm):
        for p in self.plates:
            pgm.add_plate(daft.Plate(p['rect'], label=p['label'], position=p['position']))

        for n in self.nodes:
            fill = n.get('fill', 'white')
            if n['observed'] and fill == 'white': fill = "0.95"
            shape = n.get('shape', 'circle')
            aspect = n.get('aspect', 1.0)
            lw = float(n['linewidth'])
            plot_params = {'linewidth': lw, 'facecolor': fill, 'edgecolor': 'black'}
            pgm.add_node(daft.Node(n['name'], n['label'], n['x'], n['y'],
                                   scale=n['scale'], aspect=aspect, shape=shape,
                                   observed=n['observed'], plot_params=plot_params))

        for e in self.edges:
            is_curved = (e.get('rad', 0.0) != 0.0 and e['source'] != e['target'])
            edge_color = e.get('color', 'black')
            if not edge_color: edge_color = 'black'
            if is_curved:
                line_code = self.edge_styles.get(e['style'], "-")
                params = {"head_width": e.get('head_width', 0.25), "head_length": e.get('head_length', 0.3),
                          "color": edge_color, "ec": edge_color, "fc": edge_color}
                if line_code != "-": params["linestyle"] = line_code
                params["connectionstyle"] = f"arc3, rad={e.get('rad')}"
                pgm.add_edge(e['source'], e['target'], plot_params=params)
            else:
                pass

    def _draw_manual_components(self, pgm):
        node_lookup = {n['name']: n for n in self.nodes}
        for e in self.edges:
            is_curved = (e.get('rad', 0.0) != 0.0 and e['source'] != e['target'])
            if not is_curved:
                self.draw_manual_edge(pgm.ax, e, node_lookup)

    def draw_manual_edge(self, ax, edge, node_lookup):
        node_a = node_lookup.get(edge['source'])
        node_b = node_lookup.get(edge['target'])
        if not node_a or not node_b: return

        gap_start = edge.get('gap_start', 0.05)
        gap_end = edge.get('gap_end', 0.05)
        line_code = self.edge_styles.get(edge['style'], "-")
        edge_color = edge.get('color', 'black')
        if not edge_color: edge_color = 'black'
        arrow_style = "<|-|>" if edge.get('double_head') else "-|>"
        hw, hl = edge.get('head_width', 0.25), edge.get('head_length', 0.3)

        if edge['source'] == edge['target']:
            r = 0.4 * node_a['scale']
            r_start, r_end = r + gap_start, r + gap_end
            rad = edge.get('rad', 0.0)
            if rad == 0.0:
                rad = -2.5
            else:
                rad = -abs(rad)
            phi_start, phi_end = math.radians(120), math.radians(60)
            start_p = (node_a['x'] + r_start * math.cos(phi_start), node_a['y'] + r_start * math.sin(phi_start))
            end_p = (node_a['x'] + r_end * math.cos(phi_end), node_a['y'] + r_end * math.sin(phi_end))
            ax.annotate("", xy=end_p, xytext=start_p,
                        arrowprops=dict(arrowstyle=f"{arrow_style},head_width={hw},head_length={hl}",
                                        linestyle=line_code, connectionstyle=f"arc3,rad={rad}", linewidth=1.0,
                                        shrinkA=0, shrinkB=0, color=edge_color))
        else:
            dx, dy = node_b['x'] - node_a['x'], node_b['y'] - node_a['y']
            theta = math.atan2(dy, dx)
            r_a = (0.4 * node_a['scale']) + gap_start
            r_b = (0.4 * node_b['scale']) + gap_end
            start_p = (node_a['x'] + r_a * math.cos(theta), node_a['y'] + r_a * math.sin(theta))
            end_p = (node_b['x'] - r_b * math.cos(theta), node_b['y'] - r_b * math.sin(theta))
            ax.annotate("", xy=end_p, xytext=start_p,
                        arrowprops=dict(arrowstyle=f"{arrow_style},head_width={hw},head_length={hl}",
                                        linestyle=line_code, linewidth=1.0, shrinkA=0, shrinkB=0, color=edge_color))

    # --- Export & Generate ---
    def open_final_preview(self, event=None):
        fig = self.build_final_figure()
        top = tk.Toplevel(self.root)
        top.title("Export Preview")

        fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)

        canvas = FigureCanvasTkAgg(fig, master=top)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        toolbar = NavigationToolbar2Tk(canvas, top)
        toolbar.update()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def save_export_image(self):
        file_types = [('PNG', '*.png'), ('PDF', '*.pdf'), ('SVG', '*.svg'), ('EPS', '*.eps'), ('TIFF', '*.tiff'),
                      ('JPG', '*.jpg'), ('All', '*.*')]
        filename = filedialog.asksaveasfilename(title="Export Image", initialdir="/", filetypes=file_types,
                                                defaultextension=".png")
        if filename:
            try:
                fig = self.build_final_figure()
                # Explicitly manage layout for export - tight
                fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)

                fig.savefig(filename, dpi=300, bbox_inches='tight')
                plt.close(fig)
                messagebox.showinfo("Success", f"Image exported to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed:\n{e}")

    def build_final_figure(self):
        plt.rc("font", family=self.current_font, size=self.current_font_size)
        plt.rc("text", color=self.current_font_color)
        g_unit = self.get_grid_unit()
        pgm = daft.PGM(shape=[self.canvas_width, self.canvas_height], origin=[0, 0], grid_unit=g_unit, node_unit=1.0)
        self._populate_pgm(pgm)
        pgm.render()
        self._draw_manual_components(pgm)
        if pgm.ax:
            pgm.ax.set_xlim(0, self.canvas_width)
            pgm.ax.set_ylim(0, self.canvas_height)
            pgm.ax.set_aspect('equal')
            pgm.ax.axis('off')
        return pgm.figure

    # --- Setup Controls ---
    def setup_controls(self):
        toolbar = ttk.Frame(self.control_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        self.btn_preview = ttk.Button(toolbar, text="Preview / Export (Ctrl+P)", command=self.open_final_preview)
        self.btn_preview.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))
        undo_frame = ttk.Frame(toolbar)
        undo_frame.pack(side=tk.TOP, fill=tk.X)
        self.btn_undo = ttk.Button(undo_frame, text="⟲ Undo (Ctrl+Z)", command=self.undo, state=tk.DISABLED)
        self.btn_undo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        self.btn_redo = ttk.Button(undo_frame, text="Redo ⟳ (Ctrl+Y)", command=self.redo, state=tk.DISABLED)
        self.btn_redo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

        # ZOOM CONTROLS
        zoom_frame = ttk.Frame(toolbar)
        zoom_frame.pack(side=tk.TOP, fill=tk.X, pady=2)
        ttk.Button(zoom_frame, text="Zoom In (+)", command=self.zoom_in).pack(side=tk.LEFT, fill=tk.X, expand=True,
                                                                              padx=(0, 2))
        ttk.Button(zoom_frame, text="Zoom Out (-)", command=self.zoom_out).pack(side=tk.LEFT, fill=tk.X, expand=True,
                                                                                padx=(2, 0))

        settings_frame = ttk.LabelFrame(self.control_frame, text="Global Settings", padding="5")
        settings_frame.pack(fill=tk.X, pady=5)
        row1 = ttk.Frame(settings_frame)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="Font:").pack(side=tk.LEFT)
        self.combo_font = ttk.Combobox(row1, values=self.font_options, state="readonly", width=12)
        self.combo_font.set(self.current_font)
        self.combo_font.pack(side=tk.LEFT, padx=5)
        self.combo_font.bind("<<ComboboxSelected>>", self.on_settings_change)
        ttk.Label(row1, text="Size:").pack(side=tk.LEFT)
        self.entry_font_size = ttk.Entry(row1, width=4)
        self.entry_font_size.insert(0, str(self.current_font_size))
        self.entry_font_size.pack(side=tk.LEFT, padx=5)
        ttk.Label(row1, text="Text:").pack(side=tk.LEFT)
        self.combo_font_color = ttk.Combobox(row1, values=self.text_color_options, state="readonly", width=6)
        self.combo_font_color.set(self.current_font_color)
        self.combo_font_color.pack(side=tk.LEFT, padx=2)
        row2 = ttk.Frame(settings_frame)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="Canvas W:").pack(side=tk.LEFT)
        self.entry_canvas_w = ttk.Entry(row2, width=5)
        self.entry_canvas_w.insert(0, str(self.canvas_width))
        self.entry_canvas_w.pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(row2, text="H:").pack(side=tk.LEFT, padx=(10, 0))
        self.entry_canvas_h = ttk.Entry(row2, width=5)
        self.entry_canvas_h.insert(0, str(self.canvas_height))
        self.entry_canvas_h.pack(side=tk.LEFT, padx=(5, 5))
        self.combo_unit = ttk.Combobox(row2, values=self.unit_options, state="readonly", width=4)
        self.combo_unit.set(self.canvas_unit)
        self.combo_unit.pack(side=tk.LEFT)
        row3 = ttk.Frame(settings_frame)
        row3.pack(fill=tk.X, pady=2)
        # RULER CHECKBOX REMOVED
        ttk.Checkbutton(row3, text="Grid", variable=self.show_grid_var, command=self.refresh_plot).pack(side=tk.LEFT,
                                                                                                        padx=5)
        ttk.Label(row3, text="Spacing:").pack(side=tk.LEFT)
        self.entry_grid_spacing = ttk.Entry(row3, width=4)
        self.entry_grid_spacing.insert(0, "1.0")
        self.entry_grid_spacing.pack(side=tk.LEFT, padx=2)
        ttk.Button(row3, text="Update", command=self.on_settings_change, width=7).pack(side=tk.LEFT, padx=10)
        lbl_frame = ttk.LabelFrame(self.control_frame, text="1. Add Node", padding="5")
        lbl_frame.pack(fill=tk.X, pady=5)
        ttk.Label(lbl_frame, text="Name (ID):").grid(row=0, column=0)
        self.entry_name = ttk.Entry(lbl_frame, width=10)
        self.entry_name.grid(row=0, column=1)
        ttk.Label(lbl_frame, text="Label (LaTeX):").grid(row=1, column=0)
        self.entry_label = ttk.Entry(lbl_frame, width=10)
        self.entry_label.grid(row=1, column=1)
        ttk.Label(lbl_frame, text="X / Y:").grid(row=2, column=0)
        self.entry_x = ttk.Entry(lbl_frame, width=5)
        self.entry_x.grid(row=2, column=1, sticky="W")
        self.entry_y = ttk.Entry(lbl_frame, width=5)
        self.entry_y.grid(row=2, column=1, sticky="E")
        ttk.Label(lbl_frame, text="Scale / LW:").grid(row=3, column=0)
        node_style_frame = ttk.Frame(lbl_frame)
        node_style_frame.grid(row=3, column=1, sticky="w")
        self.entry_scale = ttk.Entry(node_style_frame, width=4)
        self.entry_scale.insert(0, "1.0")
        self.entry_scale.pack(side=tk.LEFT, padx=(0, 2))
        self.entry_node_lw = ttk.Entry(node_style_frame, width=4)
        self.entry_node_lw.insert(0, "1.0")
        self.entry_node_lw.pack(side=tk.LEFT)
        ttk.Label(lbl_frame, text="Shape:").grid(row=4, column=0)
        self.combo_node_shape = ttk.Combobox(lbl_frame, values=self.node_shape_options, state="readonly", width=8)
        self.combo_node_shape.current(0)
        self.combo_node_shape.grid(row=4, column=1, sticky="w")
        ttk.Label(lbl_frame, text="Fill/Aspect:").grid(row=5, column=0)
        fa_frame = ttk.Frame(lbl_frame)
        fa_frame.grid(row=5, column=1, sticky="w")
        self.entry_node_fill = ttk.Entry(fa_frame, width=6)
        self.entry_node_fill.insert(0, "white")
        self.entry_node_fill.pack(side=tk.LEFT, padx=(0, 2))
        self.entry_node_aspect = ttk.Entry(fa_frame, width=4)
        self.entry_node_aspect.insert(0, "1.0")
        self.entry_node_aspect.pack(side=tk.LEFT)
        self.var_observed = tk.BooleanVar()
        ttk.Checkbutton(lbl_frame, text="Observed (Grey)", variable=self.var_observed).grid(row=6, columnspan=2)
        ttk.Button(lbl_frame, text="Add Node", command=self.add_node).grid(row=7, columnspan=2, pady=5)
        edge_frame = ttk.LabelFrame(self.control_frame, text="2. Add Edge", padding="5")
        edge_frame.pack(fill=tk.X, pady=5)
        ttk.Label(edge_frame, text="From (ID):").grid(row=0, column=0)
        self.entry_source = ttk.Entry(edge_frame, width=10)
        self.entry_source.grid(row=0, column=1)
        ttk.Label(edge_frame, text="To (ID):").grid(row=1, column=0)
        self.entry_target = ttk.Entry(edge_frame, width=10)
        self.entry_target.grid(row=1, column=1)
        ttk.Label(edge_frame, text="Style:").grid(row=2, column=0)
        self.combo_edge_style = ttk.Combobox(edge_frame, values=list(self.edge_styles.keys()), state="readonly",
                                             width=10)
        self.combo_edge_style.current(0)
        self.combo_edge_style.grid(row=2, column=1)
        ttk.Label(edge_frame, text="Color:").grid(row=3, column=0)
        self.entry_edge_color = ttk.Entry(edge_frame, width=10)
        self.entry_edge_color.insert(0, "black")
        self.entry_edge_color.grid(row=3, column=1)
        ttk.Label(edge_frame, text="Head W / L:").grid(row=4, column=0)
        wl_frame = ttk.Frame(edge_frame)
        wl_frame.grid(row=4, column=1, sticky="w")
        self.entry_head_w = ttk.Entry(wl_frame, width=4)
        self.entry_head_w.insert(0, "0.25")
        self.entry_head_w.pack(side=tk.LEFT, padx=(0, 2))
        self.entry_head_l = ttk.Entry(wl_frame, width=4)
        self.entry_head_l.insert(0, "0.3")
        self.entry_head_l.pack(side=tk.LEFT)
        ttk.Label(edge_frame, text="Curve/Gaps:").grid(row=5, column=0)
        cg_frame = ttk.Frame(edge_frame)
        cg_frame.grid(row=5, column=1, sticky="w")
        self.entry_curvature = ttk.Entry(cg_frame, width=3)
        self.entry_curvature.insert(0, "0.0")
        self.entry_curvature.pack(side=tk.LEFT, padx=(0, 1))
        self.entry_gap_start = ttk.Entry(cg_frame, width=4)
        self.entry_gap_start.insert(0, "0.05")
        self.entry_gap_start.pack(side=tk.LEFT, padx=(0, 1))
        self.entry_gap_end = ttk.Entry(cg_frame, width=4)
        self.entry_gap_end.insert(0, "0.05")
        self.entry_gap_end.pack(side=tk.LEFT)
        self.var_double_head = tk.BooleanVar()
        ttk.Checkbutton(edge_frame, text="Double Head (<|-|>)", variable=self.var_double_head).grid(row=6, columnspan=2)
        ttk.Button(edge_frame, text="Add Edge", command=self.add_edge).grid(row=7, columnspan=2, pady=5)
        plate_frame = ttk.LabelFrame(self.control_frame, text="3. Add Plate (Box)", padding="5")
        plate_frame.pack(fill=tk.X, pady=5)
        ttk.Label(plate_frame, text="Label:").grid(row=0, column=0)
        self.entry_plate_label = ttk.Entry(plate_frame, width=10)
        self.entry_plate_label.grid(row=0, column=1)
        ttk.Label(plate_frame, text="X / Y:").grid(row=1, column=0)
        self.entry_plate_x = ttk.Entry(plate_frame, width=5)
        self.entry_plate_x.grid(row=1, column=1, sticky="W")
        self.entry_plate_y = ttk.Entry(plate_frame, width=5)
        self.entry_plate_y.grid(row=1, column=1, sticky="E")
        ttk.Label(plate_frame, text="W / H:").grid(row=2, column=0)
        self.entry_plate_w = ttk.Entry(plate_frame, width=5)
        self.entry_plate_w.grid(row=2, column=1, sticky="W")
        self.entry_plate_h = ttk.Entry(plate_frame, width=5)
        self.entry_plate_h.grid(row=2, column=1, sticky="E")
        ttk.Label(plate_frame, text="Pos:").grid(row=3, column=0)
        self.combo_plate_pos = ttk.Combobox(plate_frame, values=self.plate_positions, state="readonly", width=10)
        self.combo_plate_pos.current(0)
        self.combo_plate_pos.grid(row=3, column=1)
        ttk.Button(plate_frame, text="Add Plate", command=self.add_plate).grid(row=5, columnspan=2, pady=5)
        ttk.Button(self.control_frame, text="Clear All", command=self.clear_all).pack(fill=tk.X, pady=20)
        ttk.Button(self.control_frame, text="Generate Python Code", command=self.generate_code).pack(fill=tk.X, pady=5)
        self.txt_output = scrolledtext.ScrolledText(self.control_frame, height=10, width=30, font=("Consolas", 9))
        self.txt_output.pack(fill=tk.BOTH, expand=True)

    # ZOOM LOGIC
    def zoom_in(self, event=None):
        if self.zoom_level < 5.0:
            self.zoom_level += 0.2
            self.refresh_plot()

    def zoom_out(self, event=None):
        if self.zoom_level > 0.2:
            self.zoom_level -= 0.2
            self.refresh_plot()


    def save_state(self):
        snapshot = {
            'nodes': copy.deepcopy(self.nodes), 'edges': copy.deepcopy(self.edges),
            'plates': copy.deepcopy(self.plates), 'font': self.current_font,
            'font_size': self.current_font_size, 'font_color': self.current_font_color,
            'canvas_w': self.canvas_width, 'canvas_h': self.canvas_height, 'unit': self.canvas_unit
        }
        self.history.append(snapshot)
        self.redo_stack.clear()
        self.update_button_states()

    def undo(self):
        if not self.history: return
        self.redo_stack.append({
            'nodes': copy.deepcopy(self.nodes), 'edges': copy.deepcopy(self.edges),
            'plates': copy.deepcopy(self.plates), 'font': self.current_font,
            'font_size': self.current_font_size, 'font_color': self.current_font_color,
            'canvas_w': self.canvas_width, 'canvas_h': self.canvas_height, 'unit': self.canvas_unit
        })
        prev = self.history.pop()
        self.restore_state(prev)

    def redo(self):
        if not self.redo_stack: return
        self.history.append({
            'nodes': copy.deepcopy(self.nodes), 'edges': copy.deepcopy(self.edges),
            'plates': copy.deepcopy(self.plates), 'font': self.current_font,
            'font_size': self.current_font_size, 'font_color': self.current_font_color,
            'canvas_w': self.canvas_width, 'canvas_h': self.canvas_height, 'unit': self.canvas_unit
        })
        next_state = self.redo_stack.pop()
        self.restore_state(next_state)

    def restore_state(self, state):
        self.nodes = state['nodes']
        self.edges = state['edges']
        self.plates = state['plates']
        self.current_font = state.get('font', 'serif')
        self.current_font_size = state.get('font_size', 12)
        self.current_font_color = state.get('font_color', 'black')
        self.canvas_width = state.get('canvas_w', 10.0)
        self.canvas_height = state.get('canvas_h', 10.0)
        self.canvas_unit = state.get('unit', "in")
        self.combo_font.set(self.current_font)
        self.entry_font_size.delete(0, tk.END)
        self.entry_font_size.insert(0, str(self.current_font_size))
        self.combo_font_color.set(self.current_font_color)
        self.entry_canvas_w.delete(0, tk.END)
        self.entry_canvas_w.insert(0, str(self.canvas_width))
        self.entry_canvas_h.delete(0, tk.END)
        self.entry_canvas_h.insert(0, str(self.canvas_height))
        self.combo_unit.set(self.canvas_unit)
        self.refresh_plot()
        self.update_button_states()

    def update_button_states(self):
        self.btn_undo.config(state=tk.NORMAL if self.history else tk.DISABLED)
        self.btn_redo.config(state=tk.NORMAL if self.redo_stack else tk.DISABLED)

    # UI ACTIONS
    def on_settings_change(self, event=None):
        try:
            self.save_state()
            self.current_font = self.combo_font.get()
            self.current_font_size = float(self.entry_font_size.get())
            self.current_font_color = self.combo_font_color.get()
            new_w = float(self.entry_canvas_w.get())
            new_h = float(self.entry_canvas_h.get())
            if new_w > 0 and new_h > 0:
                self.canvas_width = new_w
                self.canvas_height = new_h
            self.canvas_unit = self.combo_unit.get()
            self.refresh_plot()
        except ValueError:
            pass

    def add_node(self):
        try:
            name = self.entry_name.get()
            if not name: return
            self.save_state()
            self.nodes.append({
                'name': name, 'label': self.entry_label.get(),
                'x': float(self.entry_x.get()), 'y': float(self.entry_y.get()),
                'scale': float(self.entry_scale.get()), 'linewidth': float(self.entry_node_lw.get()),
                'observed': self.var_observed.get(), 'fill': self.entry_node_fill.get(),
                'shape': self.combo_node_shape.get(), 'aspect': float(self.entry_node_aspect.get())
            })
            self.refresh_plot()
        except ValueError:
            messagebox.showerror("Error", "Inputs must be numbers")

    def add_edge(self):
        try:
            src = self.entry_source.get()
            tgt = self.entry_target.get()
            if src and tgt:
                self.save_state()
                self.edges.append({
                    'source': src, 'target': tgt, 'style': self.combo_edge_style.get(),
                    'head_width': float(self.entry_head_w.get()), 'head_length': float(self.entry_head_l.get()),
                    'rad': float(self.entry_curvature.get()), 'gap_start': float(self.entry_gap_start.get()),
                    'gap_end': float(self.entry_gap_end.get()), 'double_head': self.var_double_head.get(),
                    'color': self.entry_edge_color.get()
                })
                self.refresh_plot()
        except ValueError:
            messagebox.showerror("Error", "Inputs must be numbers")

    def add_plate(self):
        try:
            self.save_state()
            self.plates.append({
                'rect': [float(self.entry_plate_x.get()), float(self.entry_plate_y.get()),
                         float(self.entry_plate_w.get()), float(self.entry_plate_h.get())],
                'label': self.entry_plate_label.get(), 'position': self.combo_plate_pos.get()
            })
            self.refresh_plot()
        except ValueError:
            messagebox.showerror("Error", "Inputs must be numbers")

    def clear_all(self):
        self.save_state()
        self.nodes = []
        self.edges = []
        self.plates = []
        self.refresh_plot()

    def generate_code(self):
        code = "import daft\nimport math\nfrom matplotlib import rc\nimport matplotlib.pyplot as plt\n\n"
        code += f'rc("font", family="{self.current_font}", size={self.current_font_size})\n'
        code += f'rc("text", color="{self.current_font_color}")\n'
        code += 'rc("text", usetex=False)\n\n'
        g_unit_val = self.get_grid_unit()
        code += f"# Unit: {self.canvas_unit}\npgm = daft.PGM(shape=[{self.canvas_width}, {self.canvas_height}], origin=[0, 0], grid_unit={g_unit_val:.4f})\n\n"
        if self.plates:
            for p in self.plates:
                code += f'pgm.add_plate(daft.Plate({p["rect"]}, label=r"{p["label"]}", position="{p["position"]}"))\n'
        if self.nodes:
            for n in self.nodes:
                fill = n.get('fill', 'white')
                if n['observed'] and fill == 'white': fill = "0.95"
                shape = n.get('shape', 'circle')
                aspect = n.get('aspect', 1.0)
                params = f'plot_params={{"linewidth": {n["linewidth"]}, "facecolor": "{fill}", "edgecolor": "black"}}'
                props = [params]
                if n['observed']: props.append("observed=True")
                if n['scale'] != 1.0: props.append(f"scale={n['scale']}")
                if shape != 'circle': props.append(f'shape="{shape}"')
                if aspect != 1.0: props.append(f'aspect={aspect}')
                props_str = ", ".join(props)
                if props_str: props_str = ", " + props_str
                code += f'pgm.add_node(daft.Node("{n["name"]}", r"{n["label"]}", {n["x"]}, {n["y"]}{props_str}))\n'
        manual_edges = []
        code += "\n# --- Edges ---\n"
        for e in self.edges:
            is_curved = (e.get('rad', 0.0) != 0.0 and e['source'] != e['target'])
            edge_color = e.get('color', 'black')
            if not edge_color: edge_color = 'black'
            if is_curved:
                line_code = self.edge_styles.get(e['style'], "-")
                rad = e.get('rad')
                code += f'pgm.add_edge("{e["source"]}", "{e["target"]}", plot_params={{"linestyle": "{line_code}", "connectionstyle": "arc3, rad={rad}", "color": "{edge_color}", "ec": "{edge_color}", "fc": "{edge_color}"}})\n'
            else:
                manual_edges.append(e)
        if manual_edges:
            code += "\n# --- Manual Edges ---\n"
            code += "pgm.render()\nax = pgm.ax\n"
            code += "coords = {n.name: (n.x, n.y, n.scale) for n in pgm._nodes}\n"
            for e in manual_edges:
                src, tgt = e['source'], e['target']
                gap_start = e.get('gap_start', 0.05)
                gap_end = e.get('gap_end', 0.05)
                line = self.edge_styles.get(e['style'], "-")
                edge_color = e.get('color', 'black')
                if not edge_color: edge_color = 'black'
                astyle = "<|-|>" if e.get('double_head') else "-|>"
                hw, hl = e.get('head_width', 0.25), e.get('head_length', 0.3)
                code += f"\n# Edge {src} -> {tgt}\n"
                code += f"xa, ya, sa = coords['{src}']\n"
                if src == tgt:
                    rad = e.get('rad', 0.0)
                    if rad == 0.0:
                        rad = -2.5
                    else:
                        rad = -abs(rad)
                    code += f"r = 0.4 * sa\nstart = (xa + (r+{gap_start})*math.cos(2.09), ya + (r+{gap_start})*math.sin(2.09))\n"
                    code += f"end = (xa + (r+{gap_end})*math.cos(1.04), ya + (r+{gap_end})*math.sin(1.04))\n"
                    code += f"ax.annotate('', xy=end, xytext=start, arrowprops=dict(arrowstyle='{astyle},head_width={hw},head_length={hl}', linestyle='{line}', connectionstyle='arc3,rad={rad}', shrinkA=0, shrinkB=0, color='{edge_color}'))\n"
                else:
                    code += f"xb, yb, sb = coords['{tgt}']\n"
                    code += f"theta = math.atan2(yb-ya, xb-xa)\n"
                    code += f"start = (xa + (0.4*sa + {gap_start})*math.cos(theta), ya + (0.4*sa + {gap_start})*math.sin(theta))\n"
                    code += f"end = (xb - (0.4*sb + {gap_end})*math.cos(theta), yb - (0.4*sb + {gap_end})*math.sin(theta))\n"
                    code += f"ax.annotate('', xy=end, xytext=start, arrowprops=dict(arrowstyle='{astyle},head_width={hw},head_length={hl}', linestyle='{line}', linewidth=1.0, shrinkA=0, shrinkB=0, color='{edge_color}'))\n"
        code += "\npgm.ax.set_aspect('equal')\npgm.ax.axis('off')\nplt.show()"
        self.txt_output.delete('1.0', tk.END)
        self.txt_output.insert(tk.END, code)

# runtime
if __name__ == "__main__":
    root = tk.Tk()
    app = DaftGUI(root)
    root.mainloop()