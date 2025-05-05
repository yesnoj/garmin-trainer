#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Frame per l'importazione e l'esportazione degli allenamenti.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
import threading
import os
import json
import datetime

from core.utils import load_yaml, save_yaml, load_excel, save_excel, create_excel_template
from core.workout import Workout, WorkoutStep, Target

class ImportExportFrame(ttk.Frame):
    """Frame per l'importazione e l'esportazione degli allenamenti."""
    
    def __init__(self, parent, controller):
        """
        Inizializza il frame di import/export.
        
        Args:
            parent: Widget genitore
            controller: Controller dell'applicazione
        """
        super().__init__(parent)
        self.controller = controller
        self.garmin_client = None
        
        # Inizializza l'interfaccia
        self.init_ui()
    
    def init_ui(self):
        """Inizializza l'interfaccia utente."""
        # Frame principale con padding
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titolo
        title_label = ttk.Label(
            main_frame, 
            text="Importazione ed Esportazione", 
            style="Heading.TLabel"
        )
        title_label.pack(pady=(0, 20))
        
        # Notebook per le diverse opzioni
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab per l'importazione
        import_frame = ttk.Frame(notebook, padding=10)
        notebook.add(import_frame, text="Importa")
        
        # Tab per l'esportazione
        export_frame = ttk.Frame(notebook, padding=10)
        notebook.add(export_frame, text="Esporta")
        
        # Tab per i template
        template_frame = ttk.Frame(notebook, padding=10)
        notebook.add(template_frame, text="Template")
        
        # Configura il tab di importazione
        self.setup_import_tab(import_frame)
        
        # Configura il tab di esportazione
        self.setup_export_tab(export_frame)
        
        # Configura il tab dei template
        self.setup_template_tab(template_frame)
        
        # Etichetta per lo stato
        self.status_var = tk.StringVar(value="Pronto")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, 
                             style="Status.TLabel")
        status_label.pack(anchor=tk.W, pady=10)
    
    def setup_import_tab(self, parent):
        """
        Configura la tab di importazione.
        
        Args:
            parent: Widget genitore
        """
        # Frame per l'importazione da YAML
        yaml_frame = ttk.LabelFrame(parent, text="Importa da YAML", padding=10)
        yaml_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Percorso file YAML
        yaml_path_frame = ttk.Frame(yaml_frame)
        yaml_path_frame.pack(fill=tk.X, pady=5)
        
        self.yaml_path_var = tk.StringVar()
        yaml_path_entry = ttk.Entry(yaml_path_frame, textvariable=self.yaml_path_var, width=40)
        yaml_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        yaml_browse_button = ttk.Button(
            yaml_path_frame, 
            text="Sfoglia", 
            command=lambda: self.browse_file(self.yaml_path_var, [("YAML files", "*.yaml;*.yml")])
        )
        yaml_browse_button.pack(side=tk.LEFT)
        
        # Opzioni di importazione YAML
        yaml_options_frame = ttk.Frame(yaml_frame)
        yaml_options_frame.pack(fill=tk.X, pady=5)
        
        self.yaml_overwrite_var = tk.BooleanVar(value=True)
        yaml_overwrite_check = ttk.Checkbutton(
            yaml_options_frame, 
            text="Sovrascrivi allenamenti esistenti con lo stesso nome", 
            variable=self.yaml_overwrite_var
        )
        yaml_overwrite_check.pack(anchor=tk.W)
        
        # Pulsante per importare YAML
        yaml_import_button = ttk.Button(
            yaml_frame, 
            text="Importa da YAML", 
            command=self.import_yaml,
            style="Info.TButton"
        )
        yaml_import_button.pack(anchor=tk.E, pady=(5, 0))
        
        # Frame per l'importazione da Excel
        excel_frame = ttk.LabelFrame(parent, text="Importa da Excel", padding=10)
        excel_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Percorso file Excel
        excel_path_frame = ttk.Frame(excel_frame)
        excel_path_frame.pack(fill=tk.X, pady=5)
        
        self.excel_path_var = tk.StringVar()
        excel_path_entry = ttk.Entry(excel_path_frame, textvariable=self.excel_path_var, width=40)
        excel_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        excel_browse_button = ttk.Button(
            excel_path_frame, 
            text="Sfoglia", 
            command=lambda: self.browse_file(self.excel_path_var, [("Excel files", "*.xlsx")])
        )
        excel_browse_button.pack(side=tk.LEFT)
        
        # Opzioni di importazione Excel
        excel_options_frame = ttk.Frame(excel_frame)
        excel_options_frame.pack(fill=tk.X, pady=5)
        
        self.excel_overwrite_var = tk.BooleanVar(value=True)
        excel_overwrite_check = ttk.Checkbutton(
            excel_options_frame, 
            text="Sovrascrivi allenamenti esistenti con lo stesso nome", 
            variable=self.excel_overwrite_var
        )
        excel_overwrite_check.pack(anchor=tk.W)
        
        # Pulsante per importare Excel
        excel_import_button = ttk.Button(
            excel_frame, 
            text="Importa da Excel", 
            command=self.import_excel,
            style="Info.TButton"
        )
        excel_import_button.pack(anchor=tk.E, pady=(5, 0))
        
        # Istruzioni
        instructions_frame = ttk.LabelFrame(parent, text="Istruzioni")
        instructions_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        instructions_text = (
            "Importa allenamenti da un file YAML o Excel.\n\n"
            "I file devono essere nel formato corretto. Puoi creare un file di esempio "
            "dalla scheda 'Template'.\n\n"
            "Gli allenamenti importati saranno aggiunti alla lista degli allenamenti "
            "disponibili. Se esiste già un allenamento con lo stesso nome, puoi "
            "scegliere se sovrascriverlo o meno."
        )
        
        instructions_label = ttk.Label(
            instructions_frame, 
            text=instructions_text,
            wraplength=500, 
            justify=tk.LEFT
        )
        instructions_label.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    
    def setup_export_tab(self, parent):
        """
        Configura la tab di esportazione.
        
        Args:
            parent: Widget genitore
        """
        # Frame per l'esportazione in YAML
        yaml_frame = ttk.LabelFrame(parent, text="Esporta in YAML", padding=10)
        yaml_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Percorso file YAML
        yaml_path_frame = ttk.Frame(yaml_frame)
        yaml_path_frame.pack(fill=tk.X, pady=5)
        
        self.yaml_export_path_var = tk.StringVar()
        yaml_path_entry = ttk.Entry(yaml_path_frame, textvariable=self.yaml_export_path_var, width=40)
        yaml_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        yaml_browse_button = ttk.Button(
            yaml_path_frame, 
            text="Sfoglia", 
            command=lambda: self.browse_save_file(self.yaml_export_path_var, [("YAML files", "*.yaml")])
        )
        yaml_browse_button.pack(side=tk.LEFT)
        
        # Filtro per l'esportazione YAML
        yaml_filter_frame = ttk.Frame(yaml_frame)
        yaml_filter_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(yaml_filter_frame, text="Filtro:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.yaml_filter_var = tk.StringVar()
        yaml_filter_entry = ttk.Entry(yaml_filter_frame, textvariable=self.yaml_filter_var, width=20)
        yaml_filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Pulsante per esportare YAML
        yaml_export_button = ttk.Button(
            yaml_frame, 
            text="Esporta in YAML", 
            command=self.export_yaml,
            style="Info.TButton"
        )
        yaml_export_button.pack(anchor=tk.E, pady=(5, 0))
        
        # Frame per l'esportazione in Excel
        excel_frame = ttk.LabelFrame(parent, text="Esporta in Excel", padding=10)
        excel_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Percorso file Excel
        excel_path_frame = ttk.Frame(excel_frame)
        excel_path_frame.pack(fill=tk.X, pady=5)
        
        self.excel_export_path_var = tk.StringVar()
        excel_path_entry = ttk.Entry(excel_path_frame, textvariable=self.excel_export_path_var, width=40)
        excel_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        excel_browse_button = ttk.Button(
            excel_path_frame, 
            text="Sfoglia", 
            command=lambda: self.browse_save_file(self.excel_export_path_var, [("Excel files", "*.xlsx")])
        )
        excel_browse_button.pack(side=tk.LEFT)
        
        # Filtro per l'esportazione Excel
        excel_filter_frame = ttk.Frame(excel_frame)
        excel_filter_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(excel_filter_frame, text="Filtro:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.excel_filter_var = tk.StringVar()
        excel_filter_entry = ttk.Entry(excel_filter_frame, textvariable=self.excel_filter_var, width=20)
        excel_filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Pulsante per esportare Excel
        excel_export_button = ttk.Button(
            excel_frame, 
            text="Esporta in Excel", 
            command=self.export_excel,
            style="Info.TButton"
        )
        excel_export_button.pack(anchor=tk.E, pady=(5, 0))
        
        # Istruzioni
        instructions_frame = ttk.LabelFrame(parent, text="Istruzioni")
        instructions_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        instructions_text = (
            "Esporta allenamenti in un file YAML o Excel.\n\n"
            "Puoi applicare un filtro per esportare solo gli allenamenti che contengono "
            "il testo specificato nel nome.\n\n"
            "Il file esportato può essere utilizzato per importare gli allenamenti in un "
            "secondo momento, o per condividerli con altri utenti."
        )
        
        instructions_label = ttk.Label(
            instructions_frame, 
            text=instructions_text,
            wraplength=500, 
            justify=tk.LEFT
        )
        instructions_label.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    
    def setup_template_tab(self, parent):
        """
        Configura la tab dei template.
        
        Args:
            parent: Widget genitore
        """
        # Frame per il template Excel
        excel_template_frame = ttk.LabelFrame(parent, text="Template Excel", padding=10)
        excel_template_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Percorso file template Excel
        excel_path_frame = ttk.Frame(excel_template_frame)
        excel_path_frame.pack(fill=tk.X, pady=5)
        
        self.excel_template_path_var = tk.StringVar()
        excel_path_entry = ttk.Entry(excel_path_frame, textvariable=self.excel_template_path_var, width=40)
        excel_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        excel_browse_button = ttk.Button(
            excel_path_frame, 
            text="Sfoglia", 
            command=lambda: self.browse_save_file(self.excel_template_path_var, [("Excel files", "*.xlsx")])
        )
        excel_browse_button.pack(side=tk.LEFT)
        
        # Pulsante per creare il template Excel
        excel_template_button = ttk.Button(
            excel_template_frame, 
            text="Crea template Excel", 
            command=self.create_excel_template,
            style="Info.TButton"
        )
        excel_template_button.pack(anchor=tk.E, pady=(5, 0))
        
        # Frame per il template YAML
        yaml_template_frame = ttk.LabelFrame(parent, text="Template YAML", padding=10)
        yaml_template_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Percorso file template YAML
        yaml_path_frame = ttk.Frame(yaml_template_frame)
        yaml_path_frame.pack(fill=tk.X, pady=5)
        
        self.yaml_template_path_var = tk.StringVar()
        yaml_path_entry = ttk.Entry(yaml_path_frame, textvariable=self.yaml_template_path_var, width=40)
        yaml_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        yaml_browse_button = ttk.Button(
            yaml_path_frame, 
            text="Sfoglia", 
            command=lambda: self.browse_save_file(self.yaml_template_path_var, [("YAML files", "*.yaml")])
        )
        yaml_browse_button.pack(side=tk.LEFT)
        
        # Pulsante per creare il template YAML
        yaml_template_button = ttk.Button(
            yaml_template_frame, 
            text="Crea template YAML", 
            command=self.create_yaml_template,
            style="Info.TButton"
        )
        yaml_template_button.pack(anchor=tk.E, pady=(5, 0))
        
        # Istruzioni
        instructions_frame = ttk.LabelFrame(parent, text="Istruzioni")
        instructions_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        instructions_text = (
            "Crea un file template per l'importazione e l'esportazione degli allenamenti.\n\n"
            "Il template contiene alcuni esempi di allenamenti per corsa, ciclismo e nuoto, "
            "e può essere utilizzato come base per creare nuovi allenamenti.\n\n"
            "Puoi modificare il template con un editor di testo (YAML) o con Excel, "
            "e poi importarlo per creare nuovi allenamenti."
        )
        
        instructions_label = ttk.Label(
            instructions_frame, 
            text=instructions_text,
            wraplength=500, 
            justify=tk.LEFT
        )
        instructions_label.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    
    def browse_file(self, var, file_types):
        """
        Apre un dialog per selezionare un file.
        
        Args:
            var: Variabile in cui memorizzare il percorso
            file_types: Tipi di file da mostrare
        """
        filename = filedialog.askopenfilename(
            title="Seleziona file",
            filetypes=file_types
        )
        
        if filename:
            var.set(filename)
    
    def browse_save_file(self, var, file_types):
        """
        Apre un dialog per selezionare un file da salvare.
        
        Args:
            var: Variabile in cui memorizzare il percorso
            file_types: Tipi di file da mostrare
        """
        filename = filedialog.asksaveasfilename(
            title="Salva file",
            filetypes=file_types,
            defaultextension=file_types[0][1].split(";")[0].replace("*", "")
        )
        
        if filename:
            var.set(filename)
    
    def import_yaml(self):
        """Importa allenamenti da un file YAML."""
        # Verifica che ci sia un percorso valido
        yaml_path = self.yaml_path_var.get().strip()
        if not yaml_path:
            messagebox.showerror(
                "Errore", 
                "Specifica un file YAML da importare.", 
                parent=self
            )
            return
        
        # Verifica che il file esista
        if not os.path.exists(yaml_path):
            messagebox.showerror(
                "Errore", 
                f"Il file '{yaml_path}' non esiste.", 
                parent=self
            )
            return
        
        # Chiedi conferma
        if not messagebox.askyesno(
            "Conferma", 
            "Sei sicuro di voler importare gli allenamenti da questo file?", 
            parent=self
        ):
            return
        
        # Avvia l'importazione in un thread separato
        threading.Thread(
            target=self._import_yaml_thread,
            args=(yaml_path, self.yaml_overwrite_var.get()),
            daemon=True
        ).start()
        
        # Aggiorna lo stato
        self.status_var.set(f"Importazione in corso da {yaml_path}...")
    
    def _import_yaml_thread(self, yaml_path, overwrite):
        """
        Thread separato per l'importazione da YAML.
        
        Args:
            yaml_path: Percorso del file YAML
            overwrite: Se True, sovrascrive gli allenamenti esistenti
        """
        try:
            # Carica il file YAML
            data = load_yaml(yaml_path)
            
            # Estrai gli allenamenti e la configurazione
            config = data.pop('config', {})
            workouts = []
            
            # Converti in oggetti Workout
            for name, steps in data.items():
                # Estrai il tipo di sport dagli step
                sport_type = "running"  # Default
                date = None
                
                for step in steps:
                    if isinstance(step, dict):
                        if 'sport_type' in step:
                            sport_type = step['sport_type']
                        elif 'date' in step:
                            date = step['date']
                
                # Crea l'allenamento
                workout = Workout(sport_type, name)
                
                # Imposta la data
                if date:
                    workout.set_scheduled_date(date)
                
                # Converti i passi
                self._convert_steps_to_workout(workout, steps)
                
                # Aggiungi l'allenamento alla lista
                workouts.append(workout)
            
            # Salva la configurazione
            if config:
                # Aggiorna la configurazione esistente con i nuovi valori
                for k, v in config.items():
                    self.controller.config.setdefault('workout_config', {})[k] = v
                
                # Salva la configurazione
                self.controller.save_config()
            
            # Integra gli allenamenti in quelli esistenti
            for workout in workouts:
                # Verifica se esiste già un allenamento con lo stesso nome
                existing_idx = None
                for i, w in enumerate(self.controller.workouts_frame.workouts):
                    if w.workout_name == workout.workout_name:
                        existing_idx = i
                        break
                
                if existing_idx is not None:
                    # Se esiste già un allenamento con lo stesso nome
                    if overwrite:
                        # Sostituisci l'allenamento esistente
                        self.controller.workouts_frame.workouts[existing_idx] = workout
                else:
                    # Aggiungi il nuovo allenamento
                    self.controller.workouts_frame.workouts.append(workout)
            
            # Aggiorna la lista degli allenamenti
            self.after(0, self.controller.workouts_frame.update_workouts_list)
            
            # Aggiorna lo stato
            self.after(0, lambda: self.status_var.set(
                f"Importati {len(workouts)} allenamenti da {yaml_path}"
            ))
            
            # Mostra un messaggio di conferma
            self.after(0, lambda: messagebox.showinfo(
                "Importazione completata", 
                f"Sono stati importati {len(workouts)} allenamenti.", 
                parent=self
            ))
        
        except Exception as e:
            logging.error(f"Errore nell'importazione da YAML: {str(e)}")
            
            # Aggiorna lo stato
            self.after(0, lambda: self.status_var.set(
                f"Errore nell'importazione da {yaml_path}"
            ))
            
            # Mostra un messaggio di errore
            error_msg = str(e)  # Cattura il valore di 'e' fuori dalla lambda
            self.after(0, lambda: messagebox.showerror(
                "Errore", 
                f"Si è verificato un errore durante l'importazione:\n{error_msg}", 
                parent=self
            ))


    def import_excel(self):
        """Importa allenamenti da un file Excel."""
        # Verifica che ci sia un percorso valido
        excel_path = self.excel_path_var.get().strip()
        if not excel_path:
            messagebox.showerror(
                "Errore", 
                "Specifica un file Excel da importare.", 
                parent=self
            )
            return
        
        # Verifica che il file esista
        if not os.path.exists(excel_path):
            messagebox.showerror(
                "Errore", 
                f"Il file '{excel_path}' non esiste.", 
                parent=self
            )
            return
        
        # Chiedi conferma
        if not messagebox.askyesno(
            "Conferma", 
            "Sei sicuro di voler importare gli allenamenti da questo file?", 
            parent=self
        ):
            return
        
        # Avvia l'importazione in un thread separato
        threading.Thread(
            target=self._import_excel_thread,
            args=(excel_path, self.excel_overwrite_var.get()),
            daemon=True
        ).start()
        
        # Aggiorna lo stato
        self.status_var.set(f"Importazione in corso da {excel_path}...")
    
    def _import_excel_thread(self, excel_path, overwrite):
        """
        Thread separato per l'importazione da Excel.
        
        Args:
            excel_path: Percorso del file Excel
            overwrite: Se True, sovrascrive gli allenamenti esistenti
        """
        try:
            # Carica il file Excel
            data = load_excel(excel_path)
            
            # Estrai gli allenamenti e la configurazione
            config = data.pop('config', {})
            workouts = []
            
            # Converti in oggetti Workout
            for name, steps in data.items():
                # Estrai il tipo di sport dagli step
                sport_type = "running"  # Default
                date = None
                
                for step in steps:
                    if isinstance(step, dict):
                        if 'sport_type' in step:
                            sport_type = step['sport_type']
                        elif 'date' in step:
                            date = step['date']
                
                # Crea l'allenamento
                workout = Workout(sport_type, name)
                
                # Imposta la data
                if date:
                    workout.set_scheduled_date(date)
                
                # Converti i passi
                self._convert_steps_to_workout(workout, steps)
                
                # Aggiungi l'allenamento alla lista
                workouts.append(workout)
            
            # Salva la configurazione
            if config:
                # Aggiorna la configurazione esistente con i nuovi valori
                for k, v in config.items():
                    self.controller.config.setdefault('workout_config', {})[k] = v
                
                # Salva la configurazione
                self.controller.save_config()
            
            # Integra gli allenamenti in quelli esistenti
            for workout in workouts:
                # Verifica se esiste già un allenamento con lo stesso nome
                existing_idx = None
                for i, w in enumerate(self.controller.workouts_frame.workouts):
                    if w.workout_name == workout.workout_name:
                        existing_idx = i
                        break
                
                if existing_idx is not None:
                    # Se esiste già un allenamento con lo stesso nome
                    if overwrite:
                        # Sostituisci l'allenamento esistente
                        self.controller.workouts_frame.workouts[existing_idx] = workout
                else:
                    # Aggiungi il nuovo allenamento
                    self.controller.workouts_frame.workouts.append(workout)
            
            # Aggiorna la lista degli allenamenti
            self.after(0, self.controller.workouts_frame.update_workouts_list)
            
            # Aggiorna lo stato
            self.after(0, lambda: self.status_var.set(
                f"Importati {len(workouts)} allenamenti da {excel_path}"
            ))
            
            # Mostra un messaggio di conferma
            self.after(0, lambda: messagebox.showinfo(
                "Importazione completata", 
                f"Sono stati importati {len(workouts)} allenamenti.", 
                parent=self
            ))
        
        except Exception as e:
            logging.error(f"Errore nell'importazione da Excel: {str(e)}")
            
            # Aggiorna lo stato
            self.after(0, lambda: self.status_var.set(
                f"Errore nell'importazione da {excel_path}"
            ))
            
            # Mostra un messaggio di errore
            self.after(0, lambda: messagebox.showerror(
                "Errore", 
                f"Si è verificato un errore durante l'importazione:\n{str(e)}", 
                parent=self
            ))
    
    def _convert_steps_to_workout(self, workout, steps):
        """
        Converte gli step dal formato YAML/Excel in oggetti WorkoutStep.
        
        Args:
            workout: Oggetto Workout a cui aggiungere gli step
            steps: Lista di step in formato YAML/Excel
        """
        for step in steps:
            if not isinstance(step, dict):
                continue
                
            if 'sport_type' in step or 'date' in step:
                # Salta i metadati
                continue
                
            if 'repeat' in step and 'steps' in step:
                # Passo di ripetizione
                iterations = step['repeat']
                substeps = step['steps']
                
                # Crea il passo di ripetizione
                repeat_step = WorkoutStep(
                    0,  # Sarà assegnato automaticamente
                    "repeat",
                    "",
                    "iterations",
                    iterations
                )
                
                # Converti e aggiungi i sottopassi
                for substep in substeps:
                    if isinstance(substep, dict) and len(substep) == 1:
                        substep_type = list(substep.keys())[0]
                        substep_detail = substep[substep_type]
                        
                        # Estrai condizione di fine e valore (semplificato)
                        end_condition = "lap.button"
                        end_value = None
                        description = ""
                        target = None
                        
                        # Estrai la condizione di fine
                        if substep_detail.startswith("lap-button"):
                            end_condition = "lap.button"
                            end_value = None
                        elif "min" in substep_detail or ":" in substep_detail and " @ " not in substep_detail:
                            end_condition = "time"
                            end_value = substep_detail.split(" ")[0]
                        elif "km" in substep_detail or "m" in substep_detail and "min" not in substep_detail:
                            end_condition = "distance"
                            end_value = substep_detail.split(" ")[0]
                        
                        # Estrai il target
                        if " @ " in substep_detail:
                            target_type = "pace.zone"
                            target_value = substep_detail.split(" @ ")[1].split(" -- ")[0] if " -- " in substep_detail else substep_detail.split(" @ ")[1]
                            # Crea un target appropriato (semplificato)
                            target = Target(target_type, 3.8, 4.2)  # Valori di esempio
                        elif " @hr " in substep_detail:
                            target_type = "heart.rate.zone"
                            target_value = substep_detail.split(" @hr ")[1].split(" -- ")[0] if " -- " in substep_detail else substep_detail.split(" @hr ")[1]
                            # Crea un target appropriato (semplificato)
                            target = Target(target_type, 140, 160)  # Valori di esempio
                        elif " @pwr " in substep_detail:
                            target_type = "power.zone"
                            target_value = substep_detail.split(" @pwr ")[1].split(" -- ")[0] if " -- " in substep_detail else substep_detail.split(" @pwr ")[1]
                            # Crea un target appropriato (semplificato)
                            target = Target(target_type, 200, 250)  # Valori di esempio
                        
                        # Estrai la descrizione
                        if " -- " in substep_detail:
                            description = substep_detail.split(" -- ")[1]
                        
                        # Crea il passo
                        substep_obj = WorkoutStep(
                            0,  # Sarà assegnato automaticamente
                            substep_type,
                            description,
                            end_condition,
                            end_value,
                            target
                        )
                        
                        # Aggiungi il sottopasso alla ripetizione
                        repeat_step.add_step(substep_obj)
                
                # Aggiungi il passo di ripetizione all'allenamento
                workout.add_step(repeat_step)
            
            elif len(step) == 1:
                # Passo normale
                step_type = list(step.keys())[0]
                step_detail = step[step_type]
                
                # Estrai condizione di fine e valore
                end_condition = "lap.button"
                end_value = None
                description = ""
                target = None
                
                # Estrai la condizione di fine
                if step_detail.startswith("lap-button"):
                    end_condition = "lap.button"
                    end_value = None
                elif "min" in step_detail or ":" in step_detail and " @ " not in step_detail:
                    end_condition = "time"
                    end_value = step_detail.split(" ")[0]
                elif "km" in step_detail or "m" in step_detail and "min" not in step_detail:
                    end_condition = "distance"
                    end_value = step_detail.split(" ")[0]
                
                # Estrai il target
                if " @ " in step_detail:
                    target_type = "pace.zone"
                    target_value = step_detail.split(" @ ")[1].split(" -- ")[0] if " -- " in step_detail else step_detail.split(" @ ")[1]
                    # Crea un target appropriato (semplificato)
                    target = Target(target_type, 3.8, 4.2)  # Valori di esempio
                elif " @hr " in step_detail:
                    target_type = "heart.rate.zone"
                    target_value = step_detail.split(" @hr ")[1].split(" -- ")[0] if " -- " in step_detail else step_detail.split(" @hr ")[1]
                    # Crea un target appropriato (semplificato)
                    target = Target(target_type, 140, 160)  # Valori di esempio
                elif " @pwr " in step_detail:
                    target_type = "power.zone"
                    target_value = step_detail.split(" @pwr ")[1].split(" -- ")[0] if " -- " in step_detail else step_detail.split(" @pwr ")[1]
                    # Crea un target appropriato (semplificato)
                    target = Target(target_type, 200, 250)  # Valori di esempio
                
                # Estrai la descrizione
                if " -- " in step_detail:
                    description = step_detail.split(" -- ")[1]
                
                # Crea il passo
                step_obj = WorkoutStep(
                    0,  # Sarà assegnato automaticamente
                    step_type,
                    description,
                    end_condition,
                    end_value,
                    target
                )
                
                # Aggiungi il passo all'allenamento
                workout.add_step(step_obj)
    
    def export_yaml(self):
        """Esporta allenamenti in un file YAML."""
        # Verifica che ci sia un percorso valido
        yaml_path = self.yaml_export_path_var.get().strip()
        if not yaml_path:
            messagebox.showerror(
                "Errore", 
                "Specifica un file YAML di destinazione.", 
                parent=self
            )
            return
        
        # Chiedi conferma se il file esiste già
        if os.path.exists(yaml_path):
            if not messagebox.askyesno(
                "Conferma", 
                f"Il file '{yaml_path}' esiste già. Sovrascrivere?", 
                parent=self
            ):
                return
        
        # Avvia l'esportazione in un thread separato
        threading.Thread(
            target=self._export_yaml_thread,
            args=(yaml_path, self.yaml_filter_var.get().strip()),
            daemon=True
        ).start()
        
        # Aggiorna lo stato
        self.status_var.set(f"Esportazione in corso su {yaml_path}...")
    
    def _export_yaml_thread(self, yaml_path, filter_text):
        """
        Thread separato per l'esportazione in YAML.
        
        Args:
            yaml_path: Percorso del file YAML
            filter_text: Testo per filtrare gli allenamenti
        """
        try:
            # Prepara i dati da esportare
            data = {}
            
            # Aggiungi la configurazione
            if 'workout_config' in self.controller.config:
                data['config'] = self.controller.config['workout_config']
            
            # Filtra gli allenamenti
            workouts = self.controller.workouts_frame.workouts
            filtered_workouts = [
                w for w in workouts 
                if not filter_text or filter_text.lower() in w.workout_name.lower()
            ]
            
            # Converti gli allenamenti in formato YAML
            for workout in filtered_workouts:
                # Crea la lista di step
                steps = []
                
                # Aggiungi i metadati
                steps.append({"sport_type": workout.sport_type})
                
                if workout.get_scheduled_date():
                    steps.append({"date": workout.get_scheduled_date()})
                
                # Converti gli step
                for step in workout.workout_steps:
                    if step.step_type == "repeat":
                        # Passo di ripetizione
                        repeat_step = {
                            "repeat": step.end_condition_value,
                            "steps": []
                        }
                        
                        # Converti i sottopassi
                        for substep in step.workout_steps:
                            # Crea il dettaglio del sottopasso
                            substep_detail = self._format_step_detail(substep)
                            
                            # Aggiungi il sottopasso
                            repeat_step["steps"].append({substep.step_type: substep_detail})
                        
                        # Aggiungi il passo di ripetizione
                        steps.append(repeat_step)
                    else:
                        # Passo normale
                        step_detail = self._format_step_detail(step)
                        
                        # Aggiungi il passo
                        steps.append({step.step_type: step_detail})
                
                # Aggiungi l'allenamento ai dati
                data[workout.workout_name] = steps
            
            # Salva il file YAML
            save_yaml(data, yaml_path)
            
            # Aggiorna lo stato
            self.after(0, lambda: self.status_var.set(
                f"Esportati {len(filtered_workouts)} allenamenti su {yaml_path}"
            ))
            
            # Mostra un messaggio di conferma
            self.after(0, lambda: messagebox.showinfo(
                "Esportazione completata", 
                f"Sono stati esportati {len(filtered_workouts)} allenamenti.", 
                parent=self
            ))
        
        except Exception as e:
            logging.error(f"Errore nell'esportazione in YAML: {str(e)}")
            
            # Aggiorna lo stato
            self.after(0, lambda: self.status_var.set(
                f"Errore nell'esportazione su {yaml_path}"
            ))
            
            # Mostra un messaggio di errore
            self.after(0, lambda: messagebox.showerror(
                "Errore", 
                f"Si è verificato un errore durante l'esportazione:\n{str(e)}", 
                parent=self
            ))
    
    def _format_step_detail(self, step):
        """
        Formatta i dettagli di un passo per l'esportazione.
        
        Args:
            step: Oggetto WorkoutStep
            
        Returns:
            str: Dettagli formattati
        """
        result = ""
        
        # Condizione di fine
        if step.end_condition == "lap.button":
            result = "lap-button"
        elif step.end_condition == "time":
            value = step.end_condition_value
            if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
                # Converti secondi in formato mm:ss o hh:mm:ss
                seconds = int(value)
                if seconds < 60:
                    result = f"{seconds}s"
                elif seconds < 3600:
                    minutes = seconds // 60
                    seconds = seconds % 60
                    if seconds == 0:
                        result = f"{minutes}min"
                    else:
                        result = f"{minutes}:{seconds:02d}"
                else:
                    hours = seconds // 3600
                    minutes = (seconds % 3600) // 60
                    seconds = seconds % 60
                    result = f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                result = str(value)
                
        elif step.end_condition == "distance":
            value = step.end_condition_value
            if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
                # Converti metri in formato Xkm o Xm
                meters = int(value)
                if meters >= 1000:
                    km = meters / 1000
                    result = f"{km}km"
                else:
                    result = f"{meters}m"
            else:
                result = str(value)
        else:
            result = str(step.end_condition_value)
        
        # Target
        if step.target and step.target.target != "no.target":
            target_type = step.target.target
            
            if target_type == "pace.zone":
                result += " @ Z3"  # Semplificato
            elif target_type == "heart.rate.zone":
                result += " @hr Z2_HR"  # Semplificato
            elif target_type == "power.zone":
                result += " @pwr Z3"  # Semplificato
        
        # Descrizione
        if step.description:
            result += f" -- {step.description}"
        
        return result
    
    def export_excel(self):
        """Esporta allenamenti in un file Excel."""
        # Verifica che ci sia un percorso valido
        excel_path = self.excel_export_path_var.get().strip()
        if not excel_path:
            messagebox.showerror(
                "Errore", 
                "Specifica un file Excel di destinazione.", 
                parent=self
            )
            return
        
        # Chiedi conferma se il file esiste già
        if os.path.exists(excel_path):
            if not messagebox.askyesno(
                "Conferma", 
                f"Il file '{excel_path}' esiste già. Sovrascrivere?", 
                parent=self
            ):
                return
        
        # Avvia l'esportazione in un thread separato
        threading.Thread(
            target=self._export_excel_thread,
            args=(excel_path, self.excel_filter_var.get().strip()),
            daemon=True
        ).start()
        
        # Aggiorna lo stato
        self.status_var.set(f"Esportazione in corso su {excel_path}...")
    
    def _export_excel_thread(self, excel_path, filter_text):
        """
        Thread separato per l'esportazione in Excel.
        
        Args:
            excel_path: Percorso del file Excel
            filter_text: Testo per filtrare gli allenamenti
        """
        try:
            # Prepara i dati da esportare
            data = {}
            
            # Aggiungi la configurazione
            if 'workout_config' in self.controller.config:
                data['config'] = self.controller.config['workout_config']
            
            # Filtra gli allenamenti
            workouts = self.controller.workouts_frame.workouts
            filtered_workouts = [
                w for w in workouts 
                if not filter_text or filter_text.lower() in w.workout_name.lower()
            ]
            
            # Converti gli allenamenti in formato Excel
            for workout in filtered_workouts:
                # Crea la lista di step
                steps = []
                
                # Aggiungi i metadati
                steps.append({"sport_type": workout.sport_type})
                
                if workout.get_scheduled_date():
                    steps.append({"date": workout.get_scheduled_date()})
                
                # Converti gli step
                for step in workout.workout_steps:
                    if step.step_type == "repeat":
                        # Passo di ripetizione
                        repeat_step = {
                            "repeat": step.end_condition_value,
                            "steps": []
                        }
                        
                        # Converti i sottopassi
                        for substep in step.workout_steps:
                            # Crea il dettaglio del sottopasso
                            substep_detail = self._format_step_detail(substep)
                            
                            # Aggiungi il sottopasso
                            repeat_step["steps"].append({substep.step_type: substep_detail})
                        
                        # Aggiungi il passo di ripetizione
                        steps.append(repeat_step)
                    else:
                        # Passo normale
                        step_detail = self._format_step_detail(step)
                        
                        # Aggiungi il passo
                        steps.append({step.step_type: step_detail})
                
                # Aggiungi l'allenamento ai dati
                data[workout.workout_name] = steps
            
            # Salva il file Excel
            save_excel(data, excel_path)
            
            # Aggiorna lo stato
            self.after(0, lambda: self.status_var.set(
                f"Esportati {len(filtered_workouts)} allenamenti su {excel_path}"
            ))
            
            # Mostra un messaggio di conferma
            self.after(0, lambda: messagebox.showinfo(
                "Esportazione completata", 
                f"Sono stati esportati {len(filtered_workouts)} allenamenti.", 
                parent=self
            ))
        
        except Exception as e:
            logging.error(f"Errore nell'esportazione in Excel: {str(e)}")
            
            # Aggiorna lo stato
            self.after(0, lambda: self.status_var.set(
                f"Errore nell'esportazione su {excel_path}"
            ))
            
            # Mostra un messaggio di errore
            self.after(0, lambda: messagebox.showerror(
                "Errore", 
                f"Si è verificato un errore durante l'esportazione:\n{str(e)}", 
                parent=self
            ))
    
    def create_excel_template(self):
        """Crea un file template Excel."""
        # Verifica che ci sia un percorso valido
        excel_path = self.excel_template_path_var.get().strip()
        if not excel_path:
            messagebox.showerror(
                "Errore", 
                "Specifica un file Excel di destinazione.", 
                parent=self
            )
            return
        
        # Chiedi conferma se il file esiste già
        if os.path.exists(excel_path):
            if not messagebox.askyesno(
                "Conferma", 
                f"Il file '{excel_path}' esiste già. Sovrascrivere?", 
                parent=self
            ):
                return
        
        try:
            # Crea il template
            create_excel_template(excel_path)
            
            # Aggiorna lo stato
            self.status_var.set(f"Template Excel creato su {excel_path}")
            
            # Mostra un messaggio di conferma
            messagebox.showinfo(
                "Template creato", 
                f"Il template Excel è stato creato su '{excel_path}'.", 
                parent=self
            )
        
        except Exception as e:
            logging.error(f"Errore nella creazione del template Excel: {str(e)}")
            
            # Aggiorna lo stato
            self.status_var.set(f"Errore nella creazione del template Excel")
            
            # Mostra un messaggio di errore
            messagebox.showerror(
                "Errore", 
                f"Si è verificato un errore durante la creazione del template:\n{str(e)}", 
                parent=self
            )
    
    def create_yaml_template(self):
        """Crea un file template YAML."""
        # Verifica che ci sia un percorso valido
        yaml_path = self.yaml_template_path_var.get().strip()
        if not yaml_path:
            messagebox.showerror(
                "Errore", 
                "Specifica un file YAML di destinazione.", 
                parent=self
            )
            return
        
        # Chiedi conferma se il file esiste già
        if os.path.exists(yaml_path):
            if not messagebox.askyesno(
                "Conferma", 
                f"Il file '{yaml_path}' esiste già. Sovrascrivere?", 
                parent=self
            ):
                return
        
        try:
            # Crea un template di esempio
            data = {
                'config': {
                    'margins': {
                        'faster': '0:03',
                        'slower': '0:03',
                        'power_up': 10,
                        'power_down': 10,
                        'hr_up': 5,
                        'hr_down': 5
                    },
                    'name_prefix': '',
                    'athlete_name': 'Atleta',
                    'paces': {
                        'Z1': '6:30',
                        'Z2': '6:00',
                        'Z3': '5:30',
                        'Z4': '5:00',
                        'Z5': '4:30',
                        'recovery': '7:00',
                        'threshold': '5:10',
                        'marathon': '5:20'
                    },
                    'heart_rates': {
                        'max_hr': 180,
                        'Z1_HR': '110-130',
                        'Z2_HR': '130-150',
                        'Z3_HR': '150-165',
                        'Z4_HR': '165-175',
                        'Z5_HR': '175-185'
                    },
                    'power_values': {
                        'ftp': 250,
                        'Z1': '125-175',
                        'Z2': '175-215',
                        'Z3': '215-250',
                        'Z4': '250-300',
                        'Z5': '300-375',
                        'threshold': '235-265',
                        'sweet_spot': '220-235'
                    }
                },
                'W01S01 Easy run': [
                    {'sport_type': 'running'},
                    {'date': (datetime.date.today() + datetime.timedelta(days=7)).strftime('%Y-%m-%d')},
                    {'warmup': '10min @ Z1_HR'},
                    {'interval': '30min @ Z2'},
                    {'cooldown': '5min @ Z1_HR'}
                ],
                'W01S02 Short intervals': [
                    {'sport_type': 'running'},
                    {'date': (datetime.date.today() + datetime.timedelta(days=9)).strftime('%Y-%m-%d')},
                    {'warmup': '15min @ Z1_HR'},
                    {'repeat': 5, 'steps': [
                        {'interval': '400m @ Z5'},
                        {'recovery': '2min @ Z1_HR'}
                    ]},
                    {'cooldown': '10min @ Z1_HR'}
                ],
                'W01S03 Long slow run': [
                    {'sport_type': 'running'},
                    {'date': (datetime.date.today() + datetime.timedelta(days=11)).strftime('%Y-%m-%d')},
                    {'warmup': '10min @ Z1_HR'},
                    {'interval': '45min @ Z2'},
                    {'cooldown': '5min @ Z1_HR'}
                ],
                'W02S01 Easy ride': [
                    {'sport_type': 'cycling'},
                    {'date': (datetime.date.today() + datetime.timedelta(days=14)).strftime('%Y-%m-%d')},
                    {'warmup': '15min @hr Z1_HR'},
                    {'interval': '45min @pwr Z2'},
                    {'cooldown': '10min @hr Z1_HR'}
                ],
                'W02S02 Sweet Spot': [
                    {'sport_type': 'cycling'},
                    {'date': (datetime.date.today() + datetime.timedelta(days=16)).strftime('%Y-%m-%d')},
                    {'warmup': '20min @hr Z1_HR'},
                    {'repeat': 3, 'steps': [
                        {'interval': '12min @pwr sweet_spot'},
                        {'recovery': '3min @hr Z1_HR'}
                    ]},
                    {'cooldown': '15min @hr Z1_HR'}
                ],
                'W03S01 Easy swim': [
                    {'sport_type': 'swimming'},
                    {'date': (datetime.date.today() + datetime.timedelta(days=21)).strftime('%Y-%m-%d')},
                    {'warmup': '200m @ Z1_HR'},
                    {'interval': '600m @ Z2'},
                    {'cooldown': '100m @ Z1_HR'}
                ],
                'W03S02 Technique focus': [
                    {'sport_type': 'swimming'},
                    {'date': (datetime.date.today() + datetime.timedelta(days=23)).strftime('%Y-%m-%d')},
                    {'warmup': '200m @ Z1_HR'},
                    {'repeat': 4, 'steps': [
                        {'interval': '50m @ Z3 -- Tecnica bracciata'},
                        {'interval': '50m @ Z3 -- Tecnica gambata'},
                        {'recovery': '20s @ Z1_HR'}
                    ]},
                    {'cooldown': '100m @ Z1_HR'}
                ]
            }
            
            # Salva il file YAML
            save_yaml(data, yaml_path)
            
            # Aggiorna lo stato
            self.status_var.set(f"Template YAML creato su {yaml_path}")
            
            # Mostra un messaggio di conferma
            messagebox.showinfo(
                "Template creato", 
                f"Il template YAML è stato creato su '{yaml_path}'.", 
                parent=self
            )
        
        except Exception as e:
            logging.error(f"Errore nella creazione del template YAML: {str(e)}")
            
            # Aggiorna lo stato
            self.status_var.set(f"Errore nella creazione del template YAML")
            
            # Mostra un messaggio di errore
            messagebox.showerror(
                "Errore", 
                f"Si è verificato un errore durante la creazione del template:\n{str(e)}", 
                parent=self
            )
    
    def refresh_data(self):
        """Aggiorna i dati dell'interfaccia."""
        pass
    
    def on_login(self, client):
        """
        Gestisce l'evento di login completato.
        
        Args:
            client: Istanza di GarminClient con login effettuato
        """
        self.garmin_client = client