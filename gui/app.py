#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Classe principale dell'applicazione Garmin Trainer.
Gestisce le tab e la navigazione tra di esse.
"""

import tkinter as tk
from tkinter import ttk
import logging
import os

from gui.styles import setup_styles
from gui.login_frame import LoginFrame
from gui.workouts_frame import WorkoutsFrame
from gui.import_export_frame import ImportExportFrame
from gui.zones_frame import ZonesFrame  # Importa la nuova classe
from core.utils import load_config, save_config

class GarminTrainerApp:
    """Classe principale dell'applicazione Garmin Trainer."""
    
    def __init__(self, root):
        """
        Inizializza l'applicazione.
        
        Args:
            root: Root window di Tkinter
        """
        self.root = root
        self.root.title("Garmin Trainer")
        
        # Imposta l'icona dell'applicazione
        try:
            icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icon.png')
            if os.path.exists(icon_path):
                icon = tk.PhotoImage(file=icon_path)
                root.iconphoto(True, icon)
        except Exception as e:
            logging.warning(f"Impossibile caricare l'icona: {str(e)}")
        
        # Configura gli stili
        setup_styles()
        
        # Carica la configurazione
        self.config_file = os.path.join(os.path.dirname(__file__), '..', 'config.json')
        self.config = load_config(self.config_file)
        
        # Crea le variabili per i componenti condivisi
        self.garmin_client = None
        self.status_var = tk.StringVar(value="Pronto")
        
        # Crea il layout principale
        self.setup_ui()
    
    def setup_ui(self):
        """Configura l'interfaccia utente."""
        # Frame principale con padding
        main_frame = ttk.Frame(self.root, padding="10", style='Main.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Notebook (tabs)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Tab Login
        self.login_frame = LoginFrame(self.notebook, self)
        self.notebook.add(self.login_frame, text="Login")
        
        # Tab Allenamenti
        self.workouts_frame = WorkoutsFrame(self.notebook, self)
        self.notebook.add(self.workouts_frame, text="Allenamenti")
        
        # Tab Zone - Aggiungi questa nuova tab
        self.zones_frame = ZonesFrame(self.notebook, self)
        self.notebook.add(self.zones_frame, text="Zone")
        
        # Tab Import/Export
        self.import_export_frame = ImportExportFrame(self.notebook, self)
        self.notebook.add(self.import_export_frame, text="Import/Export")
        
        # Disabilita le tab che richiedono il login
        self.update_tab_state()
        
        # Barra di stato
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X)
        
        status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                              style="Status.TLabel")
        status_label.pack(side=tk.LEFT)
        
        # Versione
        version_label = ttk.Label(status_frame, text="v1.0.0", 
                               style="Status.TLabel")
        version_label.pack(side=tk.RIGHT)
        
        # Binding per gli eventi
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def on_tab_changed(self, event):
        """
        Gestisce il cambio di tab.
        
        Args:
            event: Evento di cambio tab
        """
        tab_id = self.notebook.select()
        tab_index = self.notebook.index(tab_id)
        
        # Azioni specifiche da eseguire quando si cambia tab
        if tab_index == 1:  # Tab Allenamenti
            if self.garmin_client and self.garmin_client.is_logged_in():
                self.workouts_frame.refresh_data()
        elif tab_index == 2:  # Tab Zone
            self.zones_frame.refresh_data()
        elif tab_index == 3:  # Tab Import/Export
            self.import_export_frame.refresh_data()
    
    def update_tab_state(self):
        """Aggiorna lo stato delle tab in base allo stato del login."""
        if self.garmin_client and self.garmin_client.is_logged_in():
            # Abilita tutte le tab
            self.notebook.tab(1, state="normal")  # Allenamenti
            self.notebook.tab(3, state="normal")  # Import/Export
        else:
            # Disabilita le tab che richiedono il login
            self.notebook.tab(1, state="disabled")  # Allenamenti
            self.notebook.tab(3, state="disabled")  # Import/Export
            
            # Assicurati che la tab di login sia selezionata
            self.notebook.select(0)
        
        # La tab Zone è sempre accessibile
        self.notebook.tab(2, state="normal")  # Zone è sempre disponibile
    
    def set_garmin_client(self, client):
        """
        Imposta il client Garmin.
        
        Args:
            client: Istanza di GarminClient
        """
        self.garmin_client = client
        
        # Aggiorna lo stato delle tab
        self.update_tab_state()
        
        # Passa il client alle altre frame
        self.workouts_frame.on_login(client)
        self.import_export_frame.on_login(client)
    
    def set_status(self, message):
        """
        Imposta il messaggio di stato.
        
        Args:
            message: Messaggio da visualizzare
        """
        self.status_var.set(message)
    
    def save_config(self):
        """Salva la configurazione corrente."""
        save_config(self.config, self.config_file)
        logging.info("Configurazione salvata.")