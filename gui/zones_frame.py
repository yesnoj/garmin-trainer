#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Frame per la gestione delle zone di allenamento.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import json

class ZonesFrame(ttk.Frame):
    """Frame per la gestione delle zone di allenamento."""
    
    def __init__(self, parent, controller):
        """
        Inizializza il frame delle zone.
        
        Args:
            parent: Widget genitore
            controller: Controller dell'applicazione
        """
        super().__init__(parent)
        self.controller = controller
        
        # Aggiungi la definizione dei margini di default
        self.default_margins = {
            'faster': '0:03',
            'slower': '0:03',
            'power_up': '10',
            'power_down': '10',
            'hr_up': '5',
            'hr_down': '5'
        }
        
        # Zone di default
        self.default_paces = {
            "Z1": "6:30",
            "Z2": "6:00",
            "Z3": "5:30",
            "Z4": "5:00",
            "Z5": "4:30",
            "recovery": "7:00",
            "threshold": "5:10",
            "marathon": "5:20",
            "race_pace": "5:10"
        }
        
        self.default_heart_rates = {
            "max_hr": "180",
            "Z1_HR": "62-76% max_hr",
            "Z2_HR": "76-85% max_hr",
            "Z3_HR": "85-91% max_hr",
            "Z4_HR": "91-95% max_hr",
            "Z5_HR": "95-100% max_hr"
        }
        
        self.default_power_values = {
            "ftp": "250",
            "Z1": "125-175",
            "Z2": "175-215",
            "Z3": "215-250",
            "Z4": "250-300",
            "Z5": "300-375",
            "Z6": "375+",
            "recovery": "<125",
            "threshold": "235-265",
            "sweet_spot": "220-235"
        }
        
        # Descrizioni predefinite per le zone
        self.default_pace_descriptions = {
            "Z1": "Allenamento aerobico leggero",
            "Z2": "Allenamento aerobico base",
            "Z3": "Allenamento aerobico medio",
            "Z4": "Soglia anaerobica",
            "Z5": "VO2max e potenza",
            "recovery": "Recupero attivo",
            "threshold": "Soglia anaerobica (individualizzata)",
            "marathon": "Ritmo maratona",
            "race_pace": "Ritmo gara"
        }
        
        self.default_hr_descriptions = {
            "max_hr": "FC massima",
            "Z1_HR": "Zona recupero", 
            "Z2_HR": "Zona aerobica base",
            "Z3_HR": "Zona aerobica intensiva",
            "Z4_HR": "Zona soglia anaerobica",
            "Z5_HR": "Zona massimale"
        }
        
        self.default_power_descriptions = {
            "ftp": "Functional Threshold Power",
            "Z1": "Recupero attivo",
            "Z2": "Resistenza di base",
            "Z3": "Soglia aerobica",
            "Z4": "Soglia anaerobica",
            "Z5": "Capacità anaerobica",
            "Z6": "Potenza massima",
            "recovery": "Recupero",
            "threshold": "Soglia funzionale",
            "sweet_spot": "Sweet Spot"
        }
        
        # Variabili per i valori delle zone
        self.paces = {}
        self.heart_rates = {}
        self.power_values = {}
        
        # Descrizioni personalizzate
        self.pace_descriptions = {}
        self.hr_descriptions = {}
        self.power_descriptions = {}
        
        # Widgets per ogni zona
        self.pace_widgets = {}
        self.hr_widgets = {}
        self.power_widgets = {}
        
        # Frame scrollabili per ogni tipo di zona
        self.pace_frame = None
        self.hr_frame = None
        self.power_frame = None
        
        # Inizializza l'interfaccia
        self.init_ui()
        
        # Carica le zone dalla configurazione
        self.load_zones_from_config()
    
    def init_ui(self):
        """Inizializza l'interfaccia utente."""
        # Frame principale con padding
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titolo
        title_label = ttk.Label(
            main_frame, 
            text="Gestione Zone", 
            style="Heading.TLabel"
        )
        title_label.pack(pady=(0, 20))
        
        # Notebook per le diverse categorie di zone
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab per i ritmi
        pace_tab = ttk.Frame(notebook, padding=10)
        notebook.add(pace_tab, text="Ritmi")
        
        # Tab per le frequenze cardiache
        hr_tab = ttk.Frame(notebook, padding=10)
        notebook.add(hr_tab, text="Frequenza Cardiaca")
        
        # Tab per le potenze
        power_tab = ttk.Frame(notebook, padding=10)
        notebook.add(power_tab, text="Potenza")
        
        # Tab per i margini (NUOVA)
        margins_tab = ttk.Frame(notebook, padding=10)
        notebook.add(margins_tab, text="Margini")
        
        # Configura ogni tab
        self.setup_pace_tab(pace_tab)
        self.setup_hr_tab(hr_tab)
        self.setup_power_tab(power_tab)
        self.setup_margins_tab(margins_tab)
        
        # Pulsanti
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        save_button = ttk.Button(
            button_frame, 
            text="Salva", 
            command=self.save_zones,
            style="Success.TButton",
            width=15
        )
        save_button.pack(side=tk.RIGHT, padx=5)
        
        reset_button = ttk.Button(
            button_frame, 
            text="Ripristina Default", 
            command=self.reset_to_defaults,
            width=15
        )
        reset_button.pack(side=tk.LEFT, padx=5)
        
        # Etichetta di stato
        self.status_var = tk.StringVar(value="Pronto")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, 
                             style="Status.TLabel")
        status_label.pack(anchor=tk.W, pady=10)
    
    def setup_pace_tab(self, parent):
        """
        Configura la tab dei ritmi.
        
        Args:
            parent: Widget genitore
        """
        # Frame scrollabile
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # Memorizza il frame per poterlo aggiornare dopo
        self.pace_frame = scrollable_frame
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Titolo
        ttk.Label(
            scrollable_frame, 
            text="Ritmi (min:sec per km)", 
            style="Subheading.TLabel"
        ).grid(row=0, column=0, columnspan=4, pady=10, sticky="w")
        
        # Intestazioni
        ttk.Label(scrollable_frame, text="Nome", style="Instructions.TLabel").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(scrollable_frame, text="Valore", style="Instructions.TLabel").grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(scrollable_frame, text="Descrizione", style="Instructions.TLabel").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        ttk.Label(scrollable_frame, text="Azioni", style="Instructions.TLabel").grid(row=1, column=3, padx=5, pady=5, sticky="w")
        
        # Crea i campi di input per ogni zona
        row = 2
        for name, value in self.default_paces.items():
            ttk.Label(scrollable_frame, text=name).grid(row=row, column=0, padx=5, pady=5, sticky="w")
            
            # Campo per il valore
            value_entry = ttk.Entry(scrollable_frame, width=10)
            value_entry.grid(row=row, column=1, padx=5, pady=5, sticky="w")
            value_entry.insert(0, value)  # Valore predefinito
            
            # Campo per la descrizione
            description = self.default_pace_descriptions.get(name, "")
            desc_entry = ttk.Entry(scrollable_frame, width=30)
            desc_entry.grid(row=row, column=2, padx=5, pady=5, sticky="w")
            desc_entry.insert(0, description)
            
            # Pulsante per eliminare
            delete_btn = ttk.Button(
                scrollable_frame, 
                text="🗑️", 
                width=3,
                command=lambda n=name: self.delete_pace(n)
            )
            delete_btn.grid(row=row, column=3, padx=5, pady=5, sticky="w")
            
            # Salva i widget per recuperare i valori più tardi
            self.pace_widgets[name] = {
                "value_entry": value_entry, 
                "desc_entry": desc_entry, 
                "row": row, 
                "delete_btn": delete_btn
            }
            
            row += 1
        
        # Pulsante per aggiungere una nuova zona
        add_frame = ttk.Frame(scrollable_frame)
        add_frame.grid(row=row, column=0, columnspan=4, pady=10, sticky="w")
        
        self.new_pace_name = tk.StringVar()
        self.new_pace_value = tk.StringVar()
        self.new_pace_desc = tk.StringVar()
        
        ttk.Label(add_frame, text="Nuovo:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(add_frame, textvariable=self.new_pace_name, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Label(add_frame, text="Valore:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(add_frame, textvariable=self.new_pace_value, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Label(add_frame, text="Descrizione:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(add_frame, textvariable=self.new_pace_desc, width=20).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            add_frame, 
            text="Aggiungi", 
            command=self.add_new_pace,
            style="Small.TButton"
        ).pack(side=tk.LEFT, padx=5)
    
    def setup_hr_tab(self, parent):
        """
        Configura la tab delle frequenze cardiache.
        
        Args:
            parent: Widget genitore
        """
        # Frame scrollabile
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # Memorizza il frame per poterlo aggiornare dopo
        self.hr_frame = scrollable_frame
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Titolo
        ttk.Label(
            scrollable_frame, 
            text="Frequenze Cardiache (bpm o % max)", 
            style="Subheading.TLabel"
        ).grid(row=0, column=0, columnspan=4, pady=10, sticky="w")
        
        # Intestazioni
        ttk.Label(scrollable_frame, text="Nome", style="Instructions.TLabel").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(scrollable_frame, text="Valore", style="Instructions.TLabel").grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(scrollable_frame, text="Descrizione", style="Instructions.TLabel").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        ttk.Label(scrollable_frame, text="Azioni", style="Instructions.TLabel").grid(row=1, column=3, padx=5, pady=5, sticky="w")
        
        # Crea i campi di input per ogni zona
        row = 2
        for name, value in self.default_heart_rates.items():
            ttk.Label(scrollable_frame, text=name).grid(row=row, column=0, padx=5, pady=5, sticky="w")
            
            # Campo per il valore
            value_entry = ttk.Entry(scrollable_frame, width=15)
            value_entry.grid(row=row, column=1, padx=5, pady=5, sticky="w")
            value_entry.insert(0, value)  # Valore predefinito
            
            # Campo per la descrizione
            description = self.default_hr_descriptions.get(name, "")
            desc_entry = ttk.Entry(scrollable_frame, width=30)
            desc_entry.grid(row=row, column=2, padx=5, pady=5, sticky="w")
            desc_entry.insert(0, description)
            
            # Pulsante per eliminare
            delete_btn = ttk.Button(
                scrollable_frame, 
                text="🗑️", 
                width=3,
                command=lambda n=name: self.delete_hr(n)
            )
            delete_btn.grid(row=row, column=3, padx=5, pady=5, sticky="w")
            
            # Salva i widget per recuperare i valori più tardi
            self.hr_widgets[name] = {
                "value_entry": value_entry, 
                "desc_entry": desc_entry, 
                "row": row, 
                "delete_btn": delete_btn
            }
            
            row += 1
        
        # Pulsante per aggiungere una nuova zona
        add_frame = ttk.Frame(scrollable_frame)
        add_frame.grid(row=row, column=0, columnspan=4, pady=10, sticky="w")
        
        self.new_hr_name = tk.StringVar()
        self.new_hr_value = tk.StringVar()
        self.new_hr_desc = tk.StringVar()
        
        ttk.Label(add_frame, text="Nuovo:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(add_frame, textvariable=self.new_hr_name, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Label(add_frame, text="Valore:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(add_frame, textvariable=self.new_hr_value, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Label(add_frame, text="Descrizione:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(add_frame, textvariable=self.new_hr_desc, width=20).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            add_frame, 
            text="Aggiungi", 
            command=self.add_new_hr,
            style="Small.TButton"
        ).pack(side=tk.LEFT, padx=5)
    
    def setup_power_tab(self, parent):
        """
        Configura la tab delle potenze.
        
        Args:
            parent: Widget genitore
        """
        # Frame scrollabile
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # Memorizza il frame per poterlo aggiornare dopo
        self.power_frame = scrollable_frame
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Titolo
        ttk.Label(
            scrollable_frame, 
            text="Potenze (watt o intervalli)", 
            style="Subheading.TLabel"
        ).grid(row=0, column=0, columnspan=4, pady=10, sticky="w")
        
        # Intestazioni
        ttk.Label(scrollable_frame, text="Nome", style="Instructions.TLabel").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(scrollable_frame, text="Valore", style="Instructions.TLabel").grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(scrollable_frame, text="Descrizione", style="Instructions.TLabel").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        ttk.Label(scrollable_frame, text="Azioni", style="Instructions.TLabel").grid(row=1, column=3, padx=5, pady=5, sticky="w")
        
        # Crea i campi di input per ogni zona
        row = 2
        for name, value in self.default_power_values.items():
            ttk.Label(scrollable_frame, text=name).grid(row=row, column=0, padx=5, pady=5, sticky="w")
            
            # Campo per il valore
            value_entry = ttk.Entry(scrollable_frame, width=15)
            value_entry.grid(row=row, column=1, padx=5, pady=5, sticky="w")
            value_entry.insert(0, value)  # Valore predefinito
            
            # Campo per la descrizione
            description = self.default_power_descriptions.get(name, "")
            desc_entry = ttk.Entry(scrollable_frame, width=30)
            desc_entry.grid(row=row, column=2, padx=5, pady=5, sticky="w")
            desc_entry.insert(0, description)
            
            # Pulsante per eliminare
            delete_btn = ttk.Button(
                scrollable_frame, 
                text="🗑️", 
                width=3,
                command=lambda n=name: self.delete_power(n)
            )
            delete_btn.grid(row=row, column=3, padx=5, pady=5, sticky="w")
            
            # Salva i widget per recuperare i valori più tardi
            self.power_widgets[name] = {
                "value_entry": value_entry, 
                "desc_entry": desc_entry, 
                "row": row, 
                "delete_btn": delete_btn
            }
            
            row += 1
        
        # Pulsante per aggiungere una nuova zona
        add_frame = ttk.Frame(scrollable_frame)
        add_frame.grid(row=row, column=0, columnspan=4, pady=10, sticky="w")
        
        self.new_power_name = tk.StringVar()
        self.new_power_value = tk.StringVar()
        self.new_power_desc = tk.StringVar()
        
        ttk.Label(add_frame, text="Nuovo:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(add_frame, textvariable=self.new_power_name, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Label(add_frame, text="Valore:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(add_frame, textvariable=self.new_power_value, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Label(add_frame, text="Descrizione:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(add_frame, textvariable=self.new_power_desc, width=20).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            add_frame, 
            text="Aggiungi", 
            command=self.add_new_power,
            style="Small.TButton"
        ).pack(side=tk.LEFT, padx=5)
    
    def delete_pace(self, name):
        """Elimina una zona di ritmo."""
        # Chiedi conferma
        if not messagebox.askyesno(
            "Conferma eliminazione", 
            f"Sei sicuro di voler eliminare la zona '{name}'?",
            parent=self
        ):
            return
        
        # Controlla se il widget esiste
        if name in self.pace_widgets:
            # Ottieni i dati del widget
            widget_data = self.pace_widgets[name]
            row = widget_data["row"]
            
            # Rimuovi tutti i widget dalla riga
            for widget in self.pace_frame.grid_slaves(row=row):
                widget.destroy()
            
            # Rimuovi il widget dalla lista
            del self.pace_widgets[name]
            
            # Aggiorna lo stato
            self.status_var.set(f"Zona '{name}' eliminata")
    
    def delete_hr(self, name):
        """Elimina una zona di frequenza cardiaca."""
        # Previeni l'eliminazione di max_hr che è una zona chiave
        if name == "max_hr":
            messagebox.showwarning(
                "Impossibile eliminare", 
                f"La zona '{name}' è necessaria per i calcoli e non può essere eliminata.",
                parent=self
            )
            return
        
        # Chiedi conferma
        if not messagebox.askyesno(
            "Conferma eliminazione", 
            f"Sei sicuro di voler eliminare la zona '{name}'?",
            parent=self
        ):
            return
        
        # Controlla se il widget esiste
        if name in self.hr_widgets:
            # Ottieni i dati del widget
            widget_data = self.hr_widgets[name]
            row = widget_data["row"]
            
            # Rimuovi tutti i widget dalla riga
            for widget in self.hr_frame.grid_slaves(row=row):
                widget.destroy()
            
            # Rimuovi il widget dalla lista
            del self.hr_widgets[name]
            
            # Aggiorna lo stato
            self.status_var.set(f"Zona '{name}' eliminata")
    
    def delete_power(self, name):
        """Elimina una zona di potenza."""
        # Previeni l'eliminazione di ftp che è una zona chiave
        if name == "ftp":
            messagebox.showwarning(
                "Impossibile eliminare", 
                f"La zona '{name}' è necessaria per i calcoli e non può essere eliminata.",
                parent=self
            )
            return
        
        # Chiedi conferma
        if not messagebox.askyesno(
            "Conferma eliminazione", 
            f"Sei sicuro di voler eliminare la zona '{name}'?",
            parent=self
        ):
            return
        
        # Controlla se il widget esiste
        if name in self.power_widgets:
            # Ottieni i dati del widget
            widget_data = self.power_widgets[name]
            row = widget_data["row"]
            
            # Rimuovi tutti i widget dalla riga
            for widget in self.power_frame.grid_slaves(row=row):
                widget.destroy()
            
            # Rimuovi il widget dalla lista
            del self.power_widgets[name]
            
            # Aggiorna lo stato
            self.status_var.set(f"Zona '{name}' eliminata")
    
    def add_new_pace(self):
        """Aggiunge una nuova zona di ritmo."""
        name = self.new_pace_name.get().strip()
        value = self.new_pace_value.get().strip()
        description = self.new_pace_desc.get().strip()
        
        if not name or not value:
            messagebox.showwarning(
                "Valori mancanti", 
                "Specifica almeno il nome e il valore della nuova zona.",
                parent=self
            )
            return
        
        if name in self.pace_widgets:
            messagebox.showwarning(
                "Nome duplicato", 
                f"La zona '{name}' esiste già.",
                parent=self
            )
            return
        
        # Trova la prossima riga disponibile
        next_row = max([data["row"] for data in self.pace_widgets.values()], default=1) + 1
        
        # Aggiungi la nuova zona alla griglia
        ttk.Label(self.pace_frame, text=name).grid(row=next_row, column=0, padx=5, pady=5, sticky="w")
        
        # Campo per il valore
        value_entry = ttk.Entry(self.pace_frame, width=10)
        value_entry.grid(row=next_row, column=1, padx=5, pady=5, sticky="w")
        value_entry.insert(0, value)
        
        # Campo per la descrizione
        desc_entry = ttk.Entry(self.pace_frame, width=30)
        desc_entry.grid(row=next_row, column=2, padx=5, pady=5, sticky="w")
        desc_entry.insert(0, description)
        
        # Pulsante per eliminare
        delete_btn = ttk.Button(
            self.pace_frame, 
            text="🗑️", 
            width=3,
            command=lambda n=name: self.delete_pace(n)
        )
        delete_btn.grid(row=next_row, column=3, padx=5, pady=5, sticky="w")
        
        # Salva i widget
        self.pace_widgets[name] = {
            "value_entry": value_entry,
            "desc_entry": desc_entry,
            "row": next_row,
            "delete_btn": delete_btn
        }
        
        # Sposta il frame di aggiunta alla riga successiva
        add_frame = self.pace_frame.grid_slaves(row=next_row-1, column=0)[0].master
        add_frame.grid(row=next_row+1, column=0, columnspan=4, pady=10, sticky="w")
        
        # Pulisci i campi
        self.new_pace_name.set("")
        self.new_pace_value.set("")
        self.new_pace_desc.set("")
        
        # Aggiorna lo stato
        self.status_var.set(f"Zona '{name}' aggiunta")
    
    def add_new_hr(self):
        """Aggiunge una nuova zona di frequenza cardiaca."""
        name = self.new_hr_name.get().strip()
        value = self.new_hr_value.get().strip()
        description = self.new_hr_desc.get().strip()
        
        if not name or not value:
            messagebox.showwarning(
                "Valori mancanti", 
                "Specifica almeno il nome e il valore della nuova zona.",
                parent=self
            )
            return
        
        if name in self.hr_widgets:
            messagebox.showwarning(
                "Nome duplicato", 
                f"La zona '{name}' esiste già.",
                parent=self
            )
            return
        
        # Trova la prossima riga disponibile
        next_row = max([data["row"] for data in self.hr_widgets.values()], default=1) + 1
        
        # Aggiungi la nuova zona alla griglia
        ttk.Label(self.hr_frame, text=name).grid(row=next_row, column=0, padx=5, pady=5, sticky="w")
        
        # Campo per il valore
        value_entry = ttk.Entry(self.hr_frame, width=15)
        value_entry.grid(row=next_row, column=1, padx=5, pady=5, sticky="w")
        value_entry.insert(0, value)
        
        # Campo per la descrizione
        desc_entry = ttk.Entry(self.hr_frame, width=30)
        desc_entry.grid(row=next_row, column=2, padx=5, pady=5, sticky="w")
        desc_entry.insert(0, description)
        
        # Pulsante per eliminare
        delete_btn = ttk.Button(
            self.hr_frame, 
            text="🗑️", 
            width=3,
            command=lambda n=name: self.delete_hr(n)
        )
        delete_btn.grid(row=next_row, column=3, padx=5, pady=5, sticky="w")
        
        # Salva i widget
        self.hr_widgets[name] = {
            "value_entry": value_entry,
            "desc_entry": desc_entry,
            "row": next_row,
            "delete_btn": delete_btn
        }
        
        # Sposta il frame di aggiunta alla riga successiva
        add_frame = self.hr_frame.grid_slaves(row=next_row-1, column=0)[0].master
        add_frame.grid(row=next_row+1, column=0, columnspan=4, pady=10, sticky="w")
        
        # Pulisci i campi
        self.new_hr_name.set("")
        self.new_hr_value.set("")
        self.new_hr_desc.set("")
        
        # Aggiorna lo stato
        self.status_var.set(f"Zona '{name}' aggiunta")
    
    def add_new_power(self):
        """Aggiunge una nuova zona di potenza."""
        name = self.new_power_name.get().strip()
        value = self.new_power_value.get().strip()
        description = self.new_power_desc.get().strip()
        
        if not name or not value:
            messagebox.showwarning(
                "Valori mancanti", 
                "Specifica almeno il nome e il valore della nuova zona.",
                parent=self
            )
            return
        
        if name in self.power_widgets:
            messagebox.showwarning(
                "Nome duplicato", 
                f"La zona '{name}' esiste già.",
                parent=self
            )
            return
        
        # Trova la prossima riga disponibile
        next_row = max([data["row"] for data in self.power_widgets.values()], default=1) + 1
        
        # Aggiungi la nuova zona alla griglia
        ttk.Label(self.power_frame, text=name).grid(row=next_row, column=0, padx=5, pady=5, sticky="w")
        
        # Campo per il valore
        value_entry = ttk.Entry(self.power_frame, width=15)
        value_entry.grid(row=next_row, column=1, padx=5, pady=5, sticky="w")
        value_entry.insert(0, value)
        
        # Campo per la descrizione
        desc_entry = ttk.Entry(self.power_frame, width=30)
        desc_entry.grid(row=next_row, column=2, padx=5, pady=5, sticky="w")
        desc_entry.insert(0, description)
        
        # Pulsante per eliminare
        delete_btn = ttk.Button(
            self.power_frame, 
            text="🗑️", 
            width=3,
            command=lambda n=name: self.delete_power(n)
        )
        delete_btn.grid(row=next_row, column=3, padx=5, pady=5, sticky="w")
        
        # Salva i widget
        self.power_widgets[name] = {
            "value_entry": value_entry,
            "desc_entry": desc_entry,
            "row": next_row,
            "delete_btn": delete_btn
        }
        
        # Sposta il frame di aggiunta alla riga successiva
        add_frame = self.power_frame.grid_slaves(row=next_row-1, column=0)[0].master
        add_frame.grid(row=next_row+1, column=0, columnspan=4, pady=10, sticky="w")
        
        # Pulisci i campi
        self.new_power_name.set("")
        self.new_power_value.set("")
        self.new_power_desc.set("")
        
        # Aggiorna lo stato
        self.status_var.set(f"Zona '{name}' aggiunta")
    
    def load_zones_from_config(self):
        """Carica i valori delle zone dalla configurazione."""
        try:
            # Ottieni i valori dalla configurazione
            if 'workout_config' in self.controller.config:
                config = self.controller.config['workout_config']
                
                # Carica i valori delle zone
                self._load_pace_zones(config)
                self._load_hr_zones(config)
                self._load_power_zones(config)
                
                # Carica le descrizioni se presenti
                self._load_descriptions(config)
                
                # Carica i margini
                self._load_margins(config)
            
            # Aggiorna lo stato
            self.status_var.set("Zone caricate dalla configurazione")
        except Exception as e:
            logging.error(f"Errore nel caricamento delle zone: {str(e)}")
            self.status_var.set("Errore nel caricamento delle zone")
    
    def _load_margins(self, config):
        """Carica i margini dalla configurazione."""
        if 'margins' in config:
            margins = config['margins']
            for name, value in margins.items():
                if name in self.margin_widgets:
                    self.margin_widgets[name].delete(0, tk.END)
                    self.margin_widgets[name].insert(0, str(value))

    def _load_pace_zones(self, config):
        """Carica le zone di ritmo dalla configurazione."""
        if 'paces' in config:
            # Prima, elimina tutte le zone esistenti tranne quelle predefinite
            for name in list(self.pace_widgets.keys()):
                if name not in self.default_paces:
                    widget_data = self.pace_widgets[name]
                    row = widget_data["row"]
                    
                    # Rimuovi tutti i widget dalla riga
                    for widget in self.pace_frame.grid_slaves(row=row):
                        widget.destroy()
                    
                    # Rimuovi il widget dalla lista
                    del self.pace_widgets[name]
            
            # Aggiorna i valori per le zone predefinite
            for name, value in config['paces'].items():
                if name in self.pace_widgets:
                    value_entry = self.pace_widgets[name]["value_entry"]
                    value_entry.delete(0, tk.END)
                    value_entry.insert(0, value)
                # Se la zona non esiste, aggiungila
                elif name not in self.default_paces:  # solo per zone non predefinite
                    # Trova la prossima riga disponibile
                    next_row = max([data["row"] for data in self.pace_widgets.values()], default=1) + 1
                    
                    # Aggiungi la nuova zona alla griglia
                    ttk.Label(self.pace_frame, text=name).grid(row=next_row, column=0, padx=5, pady=5, sticky="w")
                    
                    # Campo per il valore
                    value_entry = ttk.Entry(self.pace_frame, width=10)
                    value_entry.grid(row=next_row, column=1, padx=5, pady=5, sticky="w")
                    value_entry.insert(0, value)
                    
                    # Campo per la descrizione
                    desc_entry = ttk.Entry(self.pace_frame, width=30)
                    desc_entry.grid(row=next_row, column=2, padx=5, pady=5, sticky="w")
                    desc_entry.insert(0, "")  # Descrizione vuota per default
                    
                    # Pulsante per eliminare
                    delete_btn = ttk.Button(
                        self.pace_frame, 
                        text="🗑️", 
                        width=3,
                        command=lambda n=name: self.delete_pace(n)
                    )
                    delete_btn.grid(row=next_row, column=3, padx=5, pady=5, sticky="w")
                    
                    # Salva i widget
                    self.pace_widgets[name] = {
                        "value_entry": value_entry,
                        "desc_entry": desc_entry,
                        "row": next_row,
                        "delete_btn": delete_btn
                    }
            
            # Sposta il frame di aggiunta all'ultima riga
            last_row = max([data["row"] for data in self.pace_widgets.values()], default=1) + 1
            try:
                add_frame = None
                for widget in self.pace_frame.winfo_children():
                    if isinstance(widget, ttk.Frame):
                        add_frame = widget
                        break
                
                if add_frame:
                    add_frame.grid(row=last_row, column=0, columnspan=4, pady=10, sticky="w")
            except Exception as e:
                logging.error(f"Errore nel riposizionamento del frame di aggiunta: {str(e)}")
    
    def _load_hr_zones(self, config):
        """Carica le zone di frequenza cardiaca dalla configurazione."""
        if 'heart_rates' in config:
            # Prima, elimina tutte le zone esistenti tranne quelle predefinite
            for name in list(self.hr_widgets.keys()):
                if name not in self.default_heart_rates and name != "max_hr":
                    widget_data = self.hr_widgets[name]
                    row = widget_data["row"]
                    
                    # Rimuovi tutti i widget dalla riga
                    for widget in self.hr_frame.grid_slaves(row=row):
                        widget.destroy()
                    
                    # Rimuovi il widget dalla lista
                    del self.hr_widgets[name]
            
            for name, value in config['heart_rates'].items():
                if name in self.hr_widgets:
                    value_entry = self.hr_widgets[name]["value_entry"]
                    value_entry.delete(0, tk.END)
                    value_entry.insert(0, str(value))
                # Se la zona non esiste, aggiungila
                elif name not in self.default_heart_rates:  # solo per zone non predefinite
                    # Trova la prossima riga disponibile
                    next_row = max([data["row"] for data in self.hr_widgets.values()], default=1) + 1
                    
                    # Aggiungi la nuova zona alla griglia
                    ttk.Label(self.hr_frame, text=name).grid(row=next_row, column=0, padx=5, pady=5, sticky="w")
                    
                    # Campo per il valore
                    value_entry = ttk.Entry(self.hr_frame, width=15)
                    value_entry.grid(row=next_row, column=1, padx=5, pady=5, sticky="w")
                    value_entry.insert(0, str(value))
                    
                    # Campo per la descrizione
                    desc_entry = ttk.Entry(self.hr_frame, width=30)
                    desc_entry.grid(row=next_row, column=2, padx=5, pady=5, sticky="w")
                    desc_entry.insert(0, "")  # Descrizione vuota per default
                    
                    # Pulsante per eliminare
                    delete_btn = ttk.Button(
                        self.hr_frame, 
                        text="🗑️", 
                        width=3,
                        command=lambda n=name: self.delete_hr(n)
                    )
                    delete_btn.grid(row=next_row, column=3, padx=5, pady=5, sticky="w")
                    
                    # Salva i widget
                    self.hr_widgets[name] = {
                        "value_entry": value_entry,
                        "desc_entry": desc_entry,
                        "row": next_row,
                        "delete_btn": delete_btn
                    }
            
            # Sposta il frame di aggiunta all'ultima riga
            last_row = max([data["row"] for data in self.hr_widgets.values()], default=1) + 1
            try:
                add_frame = None
                for widget in self.hr_frame.winfo_children():
                    if isinstance(widget, ttk.Frame):
                        add_frame = widget
                        break
                
                if add_frame:
                    add_frame.grid(row=last_row, column=0, columnspan=4, pady=10, sticky="w")
            except Exception as e:
                logging.error(f"Errore nel riposizionamento del frame di aggiunta: {str(e)}")
    
    def _load_power_zones(self, config):
        """Carica le zone di potenza dalla configurazione."""
        if 'power_values' in config:
            # Prima, elimina tutte le zone esistenti tranne quelle predefinite
            for name in list(self.power_widgets.keys()):
                if name not in self.default_power_values and name != "ftp":
                    widget_data = self.power_widgets[name]
                    row = widget_data["row"]
                    
                    # Rimuovi tutti i widget dalla riga
                    for widget in self.power_frame.grid_slaves(row=row):
                        widget.destroy()
                    
                    # Rimuovi il widget dalla lista
                    del self.power_widgets[name]
            
            for name, value in config['power_values'].items():
                if name in self.power_widgets:
                    value_entry = self.power_widgets[name]["value_entry"]
                    value_entry.delete(0, tk.END)
                    value_entry.insert(0, str(value))
                # Se la zona non esiste, aggiungila
                elif name not in self.default_power_values:  # solo per zone non predefinite
                    # Trova la prossima riga disponibile
                    next_row = max([data["row"] for data in self.power_widgets.values()], default=1) + 1
                    
                    # Aggiungi la nuova zona alla griglia
                    ttk.Label(self.power_frame, text=name).grid(row=next_row, column=0, padx=5, pady=5, sticky="w")
                    
                    # Campo per il valore
                    value_entry = ttk.Entry(self.power_frame, width=15)
                    value_entry.grid(row=next_row, column=1, padx=5, pady=5, sticky="w")
                    value_entry.insert(0, str(value))
                    
                    # Campo per la descrizione
                    desc_entry = ttk.Entry(self.power_frame, width=30)
                    desc_entry.grid(row=next_row, column=2, padx=5, pady=5, sticky="w")
                    desc_entry.insert(0, "")  # Descrizione vuota per default
                    
                    # Pulsante per eliminare
                    delete_btn = ttk.Button(
                        self.power_frame, 
                        text="🗑️", 
                        width=3,
                        command=lambda n=name: self.delete_power(n)
                    )
                    delete_btn.grid(row=next_row, column=3, padx=5, pady=5, sticky="w")
                    
                    # Salva i widget
                    self.power_widgets[name] = {
                        "value_entry": value_entry,
                        "desc_entry": desc_entry,
                        "row": next_row,
                        "delete_btn": delete_btn
                    }
            
            # Sposta il frame di aggiunta all'ultima riga
            last_row = max([data["row"] for data in self.power_widgets.values()], default=1) + 1
            try:
                add_frame = None
                for widget in self.power_frame.winfo_children():
                    if isinstance(widget, ttk.Frame):
                        add_frame = widget
                        break
                
                if add_frame:
                    add_frame.grid(row=last_row, column=0, columnspan=4, pady=10, sticky="w")
            except Exception as e:
                logging.error(f"Errore nel riposizionamento del frame di aggiunta: {str(e)}")
    
    def _load_descriptions(self, config):
        """Carica le descrizioni delle zone dalla configurazione."""
        if 'zone_descriptions' in config:
            descriptions = config['zone_descriptions']
            
            # Carica le descrizioni dei ritmi
            if 'paces' in descriptions:
                for name, desc in descriptions['paces'].items():
                    if name in self.pace_widgets:
                        desc_entry = self.pace_widgets[name]["desc_entry"]
                        desc_entry.delete(0, tk.END)
                        desc_entry.insert(0, desc)
            
            # Carica le descrizioni delle frequenze cardiache
            if 'heart_rates' in descriptions:
                for name, desc in descriptions['heart_rates'].items():
                    if name in self.hr_widgets:
                        desc_entry = self.hr_widgets[name]["desc_entry"]
                        desc_entry.delete(0, tk.END)
                        desc_entry.insert(0, desc)
            
            # Carica le descrizioni delle potenze
            if 'power_values' in descriptions:
                for name, desc in descriptions['power_values'].items():
                    if name in self.power_widgets:
                        desc_entry = self.power_widgets[name]["desc_entry"]
                        desc_entry.delete(0, tk.END)
                        desc_entry.insert(0, desc)
    
    def reset_to_defaults(self):
        """Ripristina i valori predefiniti per tutte le zone."""
        if not messagebox.askyesno(
            "Conferma", 
            "Sei sicuro di voler ripristinare tutte le zone ai valori predefiniti?\n"
            "Questa operazione rimuoverà anche tutte le zone personalizzate.",
            parent=self
        ):
            return
        
        try:
            # Rimuovi tutte le zone esistenti
            self._clear_all_zones()
            
            # Ricarica l'interfaccia dall'inizio
            for widget in self.winfo_children():
                widget.destroy()
            
            # Re-inizializza i dizionari
            self.pace_widgets = {}
            self.hr_widgets = {}
            self.power_widgets = {}
            
            # Re-inizializza l'interfaccia
            self.init_ui()
            
            # Carica i valori predefiniti
            # ... (il tuo codice esistente per caricare i valori predefiniti)
            
            # Carica i margini predefiniti
            for name, value in self.default_margins.items():
                if name in self.margin_widgets:
                    self.margin_widgets[name].delete(0, tk.END)
                    self.margin_widgets[name].insert(0, value)
            
            # Aggiorna lo stato
            self.status_var.set("Zone ripristinate ai valori predefiniti")
        
        except Exception as e:
            logging.error(f"Errore nel ripristino delle zone: {str(e)}")
            self.status_var.set("Errore nel ripristino delle zone")

    def _clear_all_zones(self):
        """Cancella tutte le zone."""
        # Pulisci la configurazione delle zone
        if 'workout_config' in self.controller.config:
            if 'paces' in self.controller.config['workout_config']:
                self.controller.config['workout_config']['paces'] = {}
            if 'heart_rates' in self.controller.config['workout_config']:
                self.controller.config['workout_config']['heart_rates'] = {}
            if 'power_values' in self.controller.config['workout_config']:
                self.controller.config['workout_config']['power_values'] = {}
            if 'zone_descriptions' in self.controller.config['workout_config']:
                self.controller.config['workout_config']['zone_descriptions'] = {}
            if 'margins' in self.controller.config['workout_config']:
                self.controller.config['workout_config']['margins'] = self.default_margins.copy()
        
    def _clear_all_zones(self):
        """Cancella tutte le zone."""
        # Pulisci la configurazione delle zone
        if 'workout_config' in self.controller.config:
            if 'paces' in self.controller.config['workout_config']:
                self.controller.config['workout_config']['paces'] = {}
            if 'heart_rates' in self.controller.config['workout_config']:
                self.controller.config['workout_config']['heart_rates'] = {}
            if 'power_values' in self.controller.config['workout_config']:
                self.controller.config['workout_config']['power_values'] = {}
            if 'zone_descriptions' in self.controller.config['workout_config']:
                self.controller.config['workout_config']['zone_descriptions'] = {}
    
    def save_zones(self):
        """Salva i valori delle zone nella configurazione."""
        try:
            # Raccogli i valori attuali
            paces = {}
            pace_descriptions = {}
            for name, widget_data in self.pace_widgets.items():
                paces[name] = widget_data["value_entry"].get()
                pace_descriptions[name] = widget_data["desc_entry"].get()
            
            heart_rates = {}
            hr_descriptions = {}
            for name, widget_data in self.hr_widgets.items():
                heart_rates[name] = widget_data["value_entry"].get()
                hr_descriptions[name] = widget_data["desc_entry"].get()
            
            power_values = {}
            power_descriptions = {}
            for name, widget_data in self.power_widgets.items():
                power_values[name] = widget_data["value_entry"].get()
                power_descriptions[name] = widget_data["desc_entry"].get()
            
            # Raccogli i valori dei margini
            margins = {}
            for name, widget in self.margin_widgets.items():
                margins[name] = widget.get()
            
            # Aggiorna la configurazione
            if 'workout_config' not in self.controller.config:
                self.controller.config['workout_config'] = {}
            
            self.controller.config['workout_config']['paces'] = paces
            self.controller.config['workout_config']['heart_rates'] = heart_rates
            self.controller.config['workout_config']['power_values'] = power_values
            self.controller.config['workout_config']['margins'] = margins  # Aggiungi i margini
            
            # Salva anche le descrizioni
            zone_descriptions = {
                'paces': pace_descriptions,
                'heart_rates': hr_descriptions,
                'power_values': power_descriptions
            }
            
            self.controller.config['workout_config']['zone_descriptions'] = zone_descriptions
            
            # Salva la configurazione
            self.controller.save_config()
            
            # Aggiorna lo stato
            self.status_var.set("Zone salvate con successo")
            
            # Notifica all'utente
            messagebox.showinfo(
                "Salvataggio completato", 
                "I valori delle zone e i margini sono stati salvati con successo.",
                parent=self
            )
        
        except Exception as e:
            logging.error(f"Errore nel salvataggio delle zone: {str(e)}")
            self.status_var.set("Errore nel salvataggio delle zone")
            
            # Notifica all'utente
            messagebox.showerror(
                "Errore", 
                f"Si è verificato un errore durante il salvataggio: {str(e)}",
                parent=self
            )
    
    def setup_margins_tab(self, parent):
        """
        Configura la tab dei margini.
        
        Args:
            parent: Widget genitore
        """
        # Frame scrollabile
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # Memorizza il frame per poterlo aggiornare dopo
        self.margins_frame = scrollable_frame
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Titolo
        ttk.Label(
            scrollable_frame, 
            text="Margini per i calcoli", 
            style="Subheading.TLabel"
        ).grid(row=0, column=0, columnspan=3, pady=10, sticky="w")
        
        # Descrizione
        description_text = (
            "I margini vengono utilizzati per calcolare gli intervalli di valori per ciascuna zona. "
            "Ad esempio, se un ritmo di gara è 5:00 min/km, con i margini 'faster' e 'slower' di 0:03, "
            "l'intervallo sarà 4:57-5:03 min/km."
        )
        ttk.Label(
            scrollable_frame, 
            text=description_text,
            wraplength=400
        ).grid(row=1, column=0, columnspan=3, pady=10, sticky="w")
        
        # Intestazioni
        ttk.Label(scrollable_frame, text="Margine", style="Instructions.TLabel").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(scrollable_frame, text="Valore", style="Instructions.TLabel").grid(row=2, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(scrollable_frame, text="Descrizione", style="Instructions.TLabel").grid(row=2, column=2, padx=5, pady=5, sticky="w")
        
        # Descrizioni per i margini
        margin_descriptions = {
            'faster': "Margine di velocità in più (min:sec per ritmo)",
            'slower': "Margine di velocità in meno (min:sec per ritmo)",
            'power_up': "Margine di potenza in più (watt)",
            'power_down': "Margine di potenza in meno (watt)",
            'hr_up': "Margine di frequenza cardiaca in più (bpm)",
            'hr_down': "Margine di frequenza cardiaca in meno (bpm)"
        }
        
        # Crea i campi di input per ogni margine
        row = 3
        self.margin_widgets = {}
        
        for name, value in self.default_margins.items():
            ttk.Label(scrollable_frame, text=name).grid(row=row, column=0, padx=5, pady=5, sticky="w")
            
            # Campo per il valore
            value_entry = ttk.Entry(scrollable_frame, width=10)
            value_entry.grid(row=row, column=1, padx=5, pady=5, sticky="w")
            value_entry.insert(0, value)  # Valore predefinito
            
            description = margin_descriptions.get(name, "")
            ttk.Label(scrollable_frame, text=description).grid(row=row, column=2, padx=5, pady=5, sticky="w")
            
            # Salva il widget
            self.margin_widgets[name] = value_entry
            
            row += 1

    def refresh_data(self):
        """Aggiorna i dati dalle impostazioni."""
        self.load_zones_from_config()