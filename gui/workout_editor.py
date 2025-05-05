#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Editor per la creazione e modifica degli allenamenti.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import re
import logging

from core.utils import format_workout_name, parse_workout_name
from core.workout import Workout, WorkoutStep, Target
from gui.dialogs.step_dialog import StepDialog
from gui.dialogs.repeat_dialog import RepeatDialog
from gui.styles import COLORS, STEP_ICONS, SPORT_ICONS

class WorkoutEditor(ttk.Frame):
    """Editor per la creazione e modifica degli allenamenti."""
    
    def __init__(self, parent, controller):
        """
        Inizializza l'editor di allenamenti.
        
        Args:
            parent: Widget genitore
            controller: WorkoutsFrame che contiene l'editor
        """

        super().__init__(parent)
        self.controller = controller
        self.parent = parent
        self.workouts = []
        # Workout corrente
        self.current_workout = None
        
        # Variabili
        self.name_var = tk.StringVar()
        self.week_var = tk.StringVar(value="01")
        self.session_var = tk.StringVar(value="01")
        self.description_var = tk.StringVar()
        self.sport_var = tk.StringVar(value="running")
        self.date_var = tk.StringVar()
        
        # Configurazione visuale per i tipi di sport
        self.sport_colors = {
            "running": COLORS["running"],
            "cycling": COLORS["cycling"],
            "swimming": COLORS["swimming"],
            "strength_training": COLORS["strength_training"],
            "cardio": COLORS["cardio"],
            "flexibility_training": COLORS["flexibility_training"],
            "other": COLORS["other_sport"]
        }
        
        # Inizializza l'interfaccia
        self.init_ui()
    
    def init_ui(self):
        """Inizializza l'interfaccia utente."""
        # Frame principale con bordo
        main_frame = ttk.LabelFrame(self, text="Editor allenamento")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Frame per le proprietà dell'allenamento
        properties_frame = ttk.Frame(main_frame, padding=10)
        properties_frame.pack(fill=tk.X)
        
        # Nome allenamento
        name_frame = ttk.Frame(properties_frame)
        name_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(name_frame, text="Nome:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        name_entry = ttk.Entry(name_frame, textvariable=self.name_var, width=40)
        name_entry.grid(row=0, column=1, sticky=tk.W+tk.E, columnspan=3, padx=(0, 5))
        
        # Settimana, Sessione, Descrizione
        week_frame = ttk.Frame(properties_frame)
        week_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(week_frame, text="Settimana:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        week_entry = ttk.Entry(week_frame, textvariable=self.week_var, width=5)
        week_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 5))
        
        ttk.Label(week_frame, text="Sessione:").grid(row=0, column=2, sticky=tk.W, padx=(10, 5))
        session_entry = ttk.Entry(week_frame, textvariable=self.session_var, width=5)
        session_entry.grid(row=0, column=3, sticky=tk.W, padx=(0, 5))
        
        ttk.Label(week_frame, text="Descrizione:").grid(row=0, column=4, sticky=tk.W, padx=(10, 5))
        description_entry = ttk.Entry(week_frame, textvariable=self.description_var, width=25)
        description_entry.grid(row=0, column=5, sticky=tk.W+tk.E, padx=(0, 5))
        
        # Sport e Data
        sport_frame = ttk.Frame(properties_frame)
        sport_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(sport_frame, text="Sport:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        sport_options = [
            "running", 
            "cycling", 
            "swimming", 
            "strength_training", 
            "cardio", 
            "flexibility_training", 
            "other"
        ]
        
        sport_combo = ttk.Combobox(
            sport_frame, 
            textvariable=self.sport_var, 
            values=sport_options,
            width=15,
            state="readonly"
        )
        sport_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 15))
        
        # Associa evento di cambio
        sport_combo.bind("<<ComboboxSelected>>", self.on_sport_change)
        
        ttk.Label(sport_frame, text="Data:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        date_entry = ttk.Entry(sport_frame, textvariable=self.date_var, width=12)
        date_entry.grid(row=0, column=3, sticky=tk.W, padx=(0, 5))
        
        # Pulsante calendario
        calendar_button = ttk.Button(
            sport_frame, 
            text="📅", 
            width=3,
            command=self.show_calendar
        )
        calendar_button.grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        
        # Pulsante per aggiornare nome
        update_name_button = ttk.Button(
            sport_frame, 
            text="Aggiorna nome", 
            command=self.update_workout_name
        )
        update_name_button.grid(row=0, column=5, sticky=tk.E, padx=(10, 0))
        
        # Canvas per visualizzare graficamente i passi
        canvas_frame = ttk.LabelFrame(main_frame, text="Anteprima allenamento")
        canvas_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.canvas = tk.Canvas(canvas_frame, bg=COLORS["bg_light"], highlightthickness=0, height=140)
        self.canvas.pack(fill=tk.X, expand=True, padx=5, pady=5)
        
        # Aggiungi binding per drag and drop
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_press)
        self.canvas.bind("<B1-Motion>", self.on_canvas_motion)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        # Inizializza i dati per il drag and drop
        self.canvas_drag_data = {
            "item": None,
            "index": -1,
            "start_x": 0,
            "start_y": 0
        }
        
        # Statistiche dell'allenamento
        stats_frame = ttk.Frame(main_frame, padding=(10, 0))
        stats_frame.pack(fill=tk.X)
        
        self.stats_var = tk.StringVar(value="Durata stimata: -- | Distanza stimata: --")
        stats_label = ttk.Label(stats_frame, textvariable=self.stats_var)
        stats_label.pack(side=tk.LEFT)
        
        # Frame per gli step dell'allenamento
        steps_frame = ttk.LabelFrame(main_frame, text="Passi dell'allenamento")
        steps_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Toolbar per gli step
        steps_toolbar = ttk.Frame(steps_frame)
        steps_toolbar.pack(fill=tk.X, pady=5)
        
        # Pulsanti per gestire gli step
        self.add_step_button = ttk.Button(
            steps_toolbar, 
            text="Aggiungi passo", 
            command=self.add_step
        )
        self.add_step_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.add_repeat_button = ttk.Button(
            steps_toolbar, 
            text="Aggiungi ripetizione", 
            command=self.add_repeat
        )
        self.add_repeat_button.pack(side=tk.LEFT, padx=5)
        
        self.edit_step_button = ttk.Button(
            steps_toolbar, 
            text="Modifica", 
            command=self.edit_step
        )
        self.edit_step_button.pack(side=tk.LEFT, padx=5)
        
        self.delete_step_button = ttk.Button(
            steps_toolbar, 
            text="Elimina", 
            command=self.delete_step
        )
        self.delete_step_button.pack(side=tk.LEFT, padx=5)
        
        self.move_up_button = ttk.Button(
            steps_toolbar, 
            text="↑", 
            width=3,
            command=self.move_step_up
        )
        self.move_up_button.pack(side=tk.LEFT, padx=5)
        
        self.move_down_button = ttk.Button(
            steps_toolbar, 
            text="↓", 
            width=3,
            command=self.move_step_down
        )
        self.move_down_button.pack(side=tk.LEFT, padx=5)
        
        # Lista degli step
        steps_list_frame = ttk.Frame(steps_frame)
        steps_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Crea treeview per gli step
        columns = ("index", "type", "details")
        self.steps_tree = ttk.Treeview(
            steps_list_frame, 
            columns=columns, 
            show="headings", 
            selectmode="browse"
        )
        
        # Definisci le intestazioni
        self.steps_tree.heading("index", text="#")
        self.steps_tree.heading("type", text="Tipo")
        self.steps_tree.heading("details", text="Dettagli")
        
        # Definisci le larghezze delle colonne
        self.steps_tree.column("index", width=30)
        self.steps_tree.column("type", width=100)
        self.steps_tree.column("details", width=400)
        
        # Aggiungi scrollbar
        scrollbar = ttk.Scrollbar(
            steps_list_frame, 
            orient=tk.VERTICAL, 
            command=self.steps_tree.yview
        )
        self.steps_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.steps_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Associa eventi
        self.steps_tree.bind("<Double-1>", self.on_step_double_click)
        self.steps_tree.bind("<<TreeviewSelect>>", self.on_step_select)
        
        # Pulsanti di azione
        action_frame = ttk.Frame(main_frame, padding=10)
        action_frame.pack(fill=tk.X)
        
        self.save_button = ttk.Button(
            action_frame, 
            text="Salva allenamento", 
            command=self.save_workout,
            style="Success.TButton"
        )
        self.save_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.cancel_button = ttk.Button(
            action_frame, 
            text="Annulla modifiche", 
            command=self.cancel_edit
        )
        self.cancel_button.pack(side=tk.LEFT, padx=5)
    
    def disable_editor(self):
        """Disabilita l'editor."""
        for widget in [
            self.add_step_button, 
            self.add_repeat_button, 
            self.edit_step_button, 
            self.delete_step_button,
            self.move_up_button,
            self.move_down_button,
            self.save_button,
            self.cancel_button
        ]:
            widget['state'] = 'disabled'
    
    def enable_editor(self):
        """Abilita l'editor."""
        for widget in [
            self.add_step_button, 
            self.add_repeat_button,
            self.save_button,
            self.cancel_button
        ]:
            widget['state'] = 'normal'
        
        # Abilita i pulsanti di modifica solo se ci sono step
        has_steps = hasattr(self, 'current_workout') and self.current_workout and self.current_workout.workout_steps
        for widget in [
            self.edit_step_button, 
            self.delete_step_button,
            self.move_up_button,
            self.move_down_button
        ]:
            widget['state'] = 'normal' if has_steps else 'disabled'
    
    def load_workout(self, workout):
        """
        Carica un allenamento nell'editor.
        
        Args:
            workout: Allenamento da caricare
        """
        # Memorizza l'allenamento corrente
        self.current_workout = workout
        
        # Imposta i valori nei campi
        self.name_var.set(workout.workout_name)
        
        # Estrai settimana, sessione e descrizione dal nome
        week, session, description = parse_workout_name(workout.workout_name)
        
        if week is not None and session is not None:
            self.week_var.set(f"{week:02d}")
            self.session_var.set(f"{session:02d}")
            self.description_var.set(description)
        else:
            # Nome non standard
            self.week_var.set("01")
            self.session_var.set("01")
            self.description_var.set(workout.workout_name)
        
        # Imposta il tipo di sport
        self.sport_var.set(workout.sport_type)
        
        # Imposta la data pianificata, se presente
        self.date_var.set(workout.get_scheduled_date() or "")
        
        # Aggiorna la lista degli step
        self.update_steps_tree()
        
        # Aggiorna il canvas
        self.draw_workout()
        
        # Aggiorna le statistiche
        self.update_workout_stats()
        
        # Abilita l'editor
        self.enable_editor()
    
    def clear_editor(self):
        """Pulisce l'editor."""
        # Cancella i valori nei campi
        self.name_var.set("")
        self.week_var.set("01")
        self.session_var.set("01")
        self.description_var.set("")
        self.sport_var.set("running")
        self.date_var.set("")
        
        # Cancella l'allenamento corrente
        self.current_workout = None
        
        # Cancella la lista degli step
        for item in self.steps_tree.get_children():
            self.steps_tree.delete(item)
        
        # Cancella il canvas
        self.canvas.delete("all")
        
        # Aggiorna le statistiche
        self.update_workout_stats()
    
    def update_workout_name(self):
        """Aggiorna il nome dell'allenamento in base ai campi settimana, sessione e descrizione."""
        # Verifica se i campi sono validi
        try:
            week = int(self.week_var.get())
            session = int(self.session_var.get())
        except ValueError:
            messagebox.showerror(
                "Errore", 
                "Settimana e sessione devono essere numeri validi.",
                parent=self
            )
            return
        
        description = self.description_var.get().strip()
        if not description:
            messagebox.showerror(
                "Errore", 
                "La descrizione non può essere vuota.",
                parent=self
            )
            return
        
        # Crea il nuovo nome
        new_name = format_workout_name(week, session, description)
        self.name_var.set(new_name)
        
        # Aggiorna anche il nome nell'allenamento corrente
        if self.current_workout:
            self.current_workout.workout_name = new_name
    
    def update_steps_tree(self):
        """Aggiorna la lista degli step nella treeview."""
        # Cancella tutti gli elementi
        for item in self.steps_tree.get_children():
            self.steps_tree.delete(item)
        
        # Verifica che ci sia un allenamento corrente
        if not self.current_workout:
            return
        
        # Funzione ricorsiva per aggiungere step e substep
        def add_steps_to_tree(steps, parent="", prefix=""):
            for i, step in enumerate(steps):
                # Prepara i valori per l'inserimento nella treeview
                values = []
                
                # Indice
                index_text = f"{prefix}{i + 1}" if prefix else str(i + 1)
                values.append(index_text)
                
                # Tipo di passo
                step_type = step.step_type
                values.append(step_type)
                
                # Dettagli del passo
                details = self.format_step_details(step)
                values.append(details)
                
                # Inserisci nella treeview
                item = self.steps_tree.insert(parent, "end", values=values, tags=(step_type,))
                
                # Se è un passo di tipo repeat, aggiungi i sottopassi
                if step_type == "repeat" and step.workout_steps:
                    # Espandi sempre l'elemento della ripetizione
                    self.steps_tree.item(item, open=True)
                    
                    # Richiama ricorsivamente per aggiungere i sottopassi
                    new_prefix = f"{index_text}." if prefix else f"{i + 1}."
                    add_steps_to_tree(step.workout_steps, item, new_prefix)
        
        # Aggiungi gli step principali e ricorsivamente i sottopassi
        add_steps_to_tree(self.current_workout.workout_steps)
        
        # Abilita/disabilita i pulsanti di modifica
        if self.current_workout and self.current_workout.workout_steps:
            for widget in [
                self.edit_step_button, 
                self.delete_step_button,
                self.move_up_button,
                self.move_down_button
            ]:
                widget['state'] = 'normal'
        else:
            for widget in [
                self.edit_step_button, 
                self.delete_step_button,
                self.move_up_button,
                self.move_down_button
            ]:
                widget['state'] = 'disabled'
    
    def format_step_details(self, step):
        """
        Formatta i dettagli di un passo per la visualizzazione.
        
        Args:
            step: Passo da formattare
            
        Returns:
            str: Dettagli formattati
        """
        # Tipo di passo
        step_type = step.step_type
        
        # Per i passi di tipo repeat, mostra il numero di ripetizioni
        if step_type == "repeat":
            return f"{step.end_condition_value} ripetizioni"
        
        # Per gli altri tipi di passo, mostra condizione di fine e target
        result = []
        
        # Condizione di fine
        if step.end_condition == "lap.button":
            result.append("Pulsante lap")
        elif step.end_condition == "time":
            value = step.end_condition_value
            if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
                # Converti secondi in formato mm:ss o hh:mm:ss
                seconds = int(value)
                if seconds < 60:
                    result.append(f"{seconds}s")
                elif seconds < 3600:
                    minutes = seconds // 60
                    seconds = seconds % 60
                    if seconds == 0:
                        result.append(f"{minutes}min")
                    else:
                        result.append(f"{minutes}:{seconds:02d}")
                else:
                    hours = seconds // 3600
                    minutes = (seconds % 3600) // 60
                    seconds = seconds % 60
                    result.append(f"{hours}:{minutes:02d}:{seconds:02d}")
            else:
                result.append(str(value))
                
        elif step.end_condition == "distance":
            value = step.end_condition_value
            if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
                # Converti metri in formato Xkm o Xm
                meters = int(value)
                if meters >= 1000:
                    km = meters / 1000
                    result.append(f"{km}km")
                else:
                    result.append(f"{meters}m")
            else:
                result.append(str(value))
        else:
            result.append(step.end_condition_value)
        
        # Target
        if step.target and step.target.target != "no.target":
            result.append(step.target.format_target())
        
        # Descrizione
        if step.description:
            result.append(f"-- {step.description}")
        
        return " ".join(result)
    
    def on_login(self, client):
        """
        Gestisce l'evento di login completato.
        
        Args:
            client: Istanza di GarminClient con login effettuato
        """
        # Salva il riferimento al client Garmin
        self.garmin_client = client
        
        # Aggiorna l'interfaccia utente se necessario
        self.refresh_data()
        
    def refresh_data(self):
        """Aggiorna i dati dell'interfaccia."""
        # Qui puoi aggiungere il codice per aggiornare l'interfaccia con i dati da Garmin
        pass

    def add_step(self):
        """Aggiunge un nuovo passo all'allenamento."""
        # Verifica che ci sia un allenamento corrente
        if not self.current_workout:
            return
        
        # Apri il dialog per configurare il passo
        dialog = StepDialog(self, sport_type=self.current_workout.sport_type)
        
        if dialog.result:
            step_type, step_detail = dialog.result
            
            # Estrai condizione di fine e valore
            end_condition = "lap.button"
            end_value = None
            description = ""
            target = None
            
            # Estrai la condizione di fine
            if step_detail.startswith("lap-button"):
                end_condition = "lap.button"
                end_value = None
            elif "min" in step_detail or ":" in step_detail and " @ " not in step_detail and " @hr " not in step_detail and " @pwr " not in step_detail:
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
            step = WorkoutStep(
                0,  # Sarà assegnato automaticamente
                step_type,
                description,
                end_condition,
                end_value,
                target
            )
            
            # Aggiungi il passo all'allenamento
            self.current_workout.add_step(step)
            
            # Aggiorna la lista degli step
            self.update_steps_tree()
            
            # Aggiorna il canvas
            self.draw_workout()
            
            # Aggiorna le statistiche
            self.update_workout_stats()
    
    def add_repeat(self):
        """Aggiunge un passo di ripetizione all'allenamento."""
        # Verifica che ci sia un allenamento corrente
        if not self.current_workout:
            return
        
        # Apri il dialog per configurare la ripetizione
        dialog = RepeatDialog(self, sport_type=self.current_workout.sport_type)
        
        if dialog.result:
            iterations, steps = dialog.result
            
            # Crea il passo di ripetizione
            repeat_step = WorkoutStep(
                0,  # Sarà assegnato automaticamente
                "repeat",
                "",
                "iterations",
                iterations
            )
            
            # Aggiungi i sottopassi
            for step in steps:
                if isinstance(step, dict) and len(step) == 1:
                    step_type = list(step.keys())[0]
                    step_detail = step[step_type]
                    
                    # Estrai condizione di fine e valore (semplificato)
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
                    substep = WorkoutStep(
                        0,  # Sarà assegnato automaticamente
                        step_type,
                        description,
                        end_condition,
                        end_value,
                        target
                    )
                    
                    # Aggiungi il sottopasso alla ripetizione
                    repeat_step.add_step(substep)
            
            # Aggiungi il passo di ripetizione all'allenamento
            self.current_workout.add_step(repeat_step)
            
            # Aggiorna la lista degli step
            self.update_steps_tree()
            
            # Aggiorna il canvas
            self.draw_workout()
            
            # Aggiorna le statistiche
            self.update_workout_stats()
    
    def edit_step(self):
        """Modifica lo step selezionato."""
        # Verifica che ci sia un allenamento corrente
        if not self.current_workout:
            return
        
        # Ottieni l'item selezionato
        selection = self.steps_tree.selection()
        if not selection:
            messagebox.showwarning(
                "Nessuna selezione", 
                "Seleziona un passo da modificare.",
                parent=self
            )
            return
        
        # Ottieni l'indice del passo selezionato
        item_id = selection[0]
        item_values = self.steps_tree.item(item_id, "values")
        index_str = item_values[0]
        
        # Ottieni il percorso completo dell'indice
        index_path = [int(x) for x in index_str.split(".")]
        
        # Funzione ricorsiva per trovare il passo corrispondente
        def find_step(steps, path, current_depth=0):
            if current_depth >= len(path):
                return None
            
            current_index = path[current_depth] - 1  # Converti in indice 0-based
            
            if current_index < 0 or current_index >= len(steps):
                return None
            
            step = steps[current_index]
            
            if current_depth == len(path) - 1:
                # Abbiamo raggiunto la profondità desiderata, restituisci il passo
                return step
            elif step.step_type == "repeat" and current_depth < len(path) - 1:
                # Continua la ricerca nei sottopassi
                return find_step(step.workout_steps, path, current_depth + 1)
            
            return None
        
        # Funzione per trovare il passo genitore
        def find_parent_step(steps, path, current_depth=0):
            if current_depth >= len(path) - 1:
                return steps, path[-1] - 1  # Restituisci la lista contenente il passo e l'indice 0-based
            
            current_index = path[current_depth] - 1  # Converti in indice 0-based
            
            if current_index < 0 or current_index >= len(steps):
                return None, -1
            
            step = steps[current_index]
            
            if step.step_type == "repeat":
                # Continua la ricerca nei sottopassi
                return find_parent_step(step.workout_steps, path, current_depth + 1)
            
            return None, -1
        
        # Trova il passo da modificare
        step = find_step(self.current_workout.workout_steps, index_path)
        
        if step is None:
            messagebox.showerror(
                "Errore", 
                "Impossibile trovare il passo selezionato.",
                parent=self
            )
            return
        
        # Gestisci il tipo di passo
        if step.step_type == "repeat":
            # Apri il dialog per le ripetizioni
            dialog = RepeatDialog(
                self, 
                iterations=step.end_condition_value,
                steps=[{s.step_type: self.format_step_details(s)} for s in step.workout_steps],
                sport_type=self.current_workout.sport_type
            )
            
            if dialog.result:
                iterations, steps = dialog.result
                
                # Aggiorna il numero di ripetizioni
                step.end_condition_value = iterations
                
                # Aggiorna i sottopassi
                step.workout_steps = []
                
                # Aggiungi i nuovi sottopassi
                for substep_dict in steps:
                    if isinstance(substep_dict, dict) and len(substep_dict) == 1:
                        substep_type = list(substep_dict.keys())[0]
                        substep_detail = substep_dict[substep_type]
                        
                        # Crea un nuovo passo con i dettagli forniti
                        substep = self._create_step_from_details(substep_type, substep_detail)
                        
                        # Aggiungi il sottopasso alla ripetizione
                        step.add_step(substep)
                
                # Aggiorna la lista degli step
                self.update_steps_tree()
                
                # Aggiorna il canvas
                self.draw_workout()
                
                # Aggiorna le statistiche
                self.update_workout_stats()
        else:
            # Apri il dialog per i passi normali
            dialog = StepDialog(
                self, 
                step_type=step.step_type, 
                step_detail=self.format_step_details(step),
                sport_type=self.current_workout.sport_type
            )
            
            if dialog.result:
                step_type, step_detail = dialog.result
                
                # Crea un nuovo passo con i dettagli forniti
                new_step = self._create_step_from_details(step_type, step_detail)
                
                # Aggiorna il passo esistente con i nuovi valori
                step.step_type = new_step.step_type
                step.description = new_step.description
                step.end_condition = new_step.end_condition
                step.end_condition_value = new_step.end_condition_value
                step.target = new_step.target
                
                # Aggiorna la lista degli step
                self.update_steps_tree()
                
                # Aggiorna il canvas
                self.draw_workout()
                
                # Aggiorna le statistiche
                self.update_workout_stats()

    def _create_step_from_details(self, step_type, step_detail):
        """
        Crea un oggetto WorkoutStep dai dettagli forniti.
        
        Args:
            step_type: Tipo di passo
            step_detail: Dettagli del passo in formato stringa
            
        Returns:
            WorkoutStep: Nuovo passo configurato
        """
        # Estrai condizione di fine e valore
        end_condition = "lap.button"
        end_value = None
        description = ""
        target = None
        
        # Estrai la condizione di fine
        if step_detail.startswith("lap-button"):
            end_condition = "lap.button"
            end_value = None
        elif "min" in step_detail or ":" in step_detail and " @ " not in step_detail and " @hr " not in step_detail and " @pwr " not in step_detail:
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
        return WorkoutStep(
            0,  # Sarà assegnato automaticamente
            step_type,
            description,
            end_condition,
            end_value,
            target
        )

    def delete_step(self):
        """Elimina lo step selezionato."""
        # Verifica che ci sia un allenamento corrente
        if not self.current_workout:
            return
        
        # Ottieni l'item selezionato
        selection = self.steps_tree.selection()
        if not selection:
            messagebox.showwarning(
                "Nessuna selezione", 
                "Seleziona un passo da eliminare.",
                parent=self
            )
            return
        
        # Ottieni l'indice del passo selezionato
        item_id = selection[0]
        item_values = self.steps_tree.item(item_id, "values")
        index_str = item_values[0]
        
        # Chiedi conferma
        if not messagebox.askyesno(
            "Conferma eliminazione", 
            f"Sei sicuro di voler eliminare il passo {index_str}?",
            parent=self
        ):
            return
        
        # Ottieni il percorso completo dell'indice
        index_path = [int(x) for x in index_str.split(".")]
        
        # Funzione per trovare la lista che contiene il passo e il suo indice
        def find_parent_container(steps, path, current_depth=0):
            if current_depth >= len(path) - 1:
                # Siamo arrivati al livello del genitore
                return steps, path[-1] - 1  # Indice 0-based
            
            current_index = path[current_depth] - 1  # Indice 0-based
            
            if current_index < 0 or current_index >= len(steps):
                return None, -1
            
            step = steps[current_index]
            
            if step.step_type == "repeat":
                # Continua la ricerca nei sottopassi
                return find_parent_container(step.workout_steps, path, current_depth + 1)
            
            return None, -1
        
        # Trova il contenitore e l'indice del passo da eliminare
        container, index = find_parent_container(self.current_workout.workout_steps, index_path)
        
        if container is not None and 0 <= index < len(container):
            # Rimuovi il passo dalla lista
            container.pop(index)
            
            # Aggiorna la lista degli step
            self.update_steps_tree()
            
            # Aggiorna il canvas
            self.draw_workout()
            
            # Aggiorna le statistiche
            self.update_workout_stats()
        else:
            messagebox.showerror(
                "Errore", 
                "Impossibile trovare il passo da eliminare.",
                parent=self
            )

    def move_step_up(self):
        """Sposta lo step selezionato verso l'alto."""
        # Verifica che ci sia un allenamento corrente
        if not self.current_workout:
            return
        
        # Ottieni l'item selezionato
        selection = self.steps_tree.selection()
        if not selection:
            return
        
        # Ottieni l'indice del passo selezionato
        item_id = selection[0]
        item_values = self.steps_tree.item(item_id, "values")
        index_str = item_values[0]
        
        # Ottieni il percorso completo dell'indice
        index_path = [int(x) for x in index_str.split(".")]
        
        # Funzione per trovare la lista che contiene il passo e il suo indice
        def find_parent_container(steps, path, current_depth=0):
            if current_depth >= len(path) - 1:
                # Siamo arrivati al livello del genitore
                return steps, path[-1] - 1  # Indice 0-based
            
            current_index = path[current_depth] - 1  # Indice 0-based
            
            if current_index < 0 or current_index >= len(steps):
                return None, -1
            
            step = steps[current_index]
            
            if step.step_type == "repeat":
                # Continua la ricerca nei sottopassi
                return find_parent_container(step.workout_steps, path, current_depth + 1)
            
            return None, -1
        
        # Trova il contenitore e l'indice del passo da spostare
        container, index = find_parent_container(self.current_workout.workout_steps, index_path)
        
        if container is not None and 0 < index < len(container):
            # Scambia il passo con quello sopra
            container[index], container[index-1] = container[index-1], container[index]
            
            # Aggiorna la lista degli step
            self.update_steps_tree()
            
            # Aggiorna il canvas
            self.draw_workout()
            
            # Prova a selezionare il passo spostato
            # Costruisci il nuovo indice
            new_index_path = index_path.copy()
            new_index_path[-1] -= 1
            new_index_str = ".".join(str(x) for x in new_index_path)
            
            # Cerca l'item con il nuovo indice
            for item in self.steps_tree.get_children():
                self._find_and_select_item_by_index(item, new_index_str)
        
    def _find_and_select_item_by_index(self, item, target_index):
        """
        Cerca ricorsivamente e seleziona un item con un dato indice.
        
        Args:
            item: Item corrente da controllare
            target_index: Indice target da cercare
        """
        # Controlla l'item corrente
        values = self.steps_tree.item(item, "values")
        if values and values[0] == target_index:
            self.steps_tree.selection_set(item)
            self.steps_tree.see(item)
            return True
        
        # Controlla i figli dell'item
        for child in self.steps_tree.get_children(item):
            if self._find_and_select_item_by_index(child, target_index):
                return True
        
        return False

    def move_step_down(self):
        """Sposta lo step selezionato verso il basso."""
        # Verifica che ci sia un allenamento corrente
        if not self.current_workout:
            return
        
        # Ottieni l'item selezionato
        selection = self.steps_tree.selection()
        if not selection:
            return
        
        # Ottieni l'indice del passo selezionato
        item_id = selection[0]
        item_values = self.steps_tree.item(item_id, "values")
        index_str = item_values[0]
        
        # Ottieni il percorso completo dell'indice
        index_path = [int(x) for x in index_str.split(".")]
        
        # Funzione per trovare la lista che contiene il passo e il suo indice
        def find_parent_container(steps, path, current_depth=0):
            if current_depth >= len(path) - 1:
                # Siamo arrivati al livello del genitore
                return steps, path[-1] - 1  # Indice 0-based
            
            current_index = path[current_depth] - 1  # Indice 0-based
            
            if current_index < 0 or current_index >= len(steps):
                return None, -1
            
            step = steps[current_index]
            
            if step.step_type == "repeat":
                # Continua la ricerca nei sottopassi
                return find_parent_container(step.workout_steps, path, current_depth + 1)
            
            return None, -1
        
        # Trova il contenitore e l'indice del passo da spostare
        container, index = find_parent_container(self.current_workout.workout_steps, index_path)
        
        if container is not None and 0 <= index < len(container) - 1:
            # Scambia il passo con quello sotto
            container[index], container[index+1] = container[index+1], container[index]
            
            # Aggiorna la lista degli step
            self.update_steps_tree()
            
            # Aggiorna il canvas
            self.draw_workout()
            
            # Prova a selezionare il passo spostato
            # Costruisci il nuovo indice
            new_index_path = index_path.copy()
            new_index_path[-1] += 1
            new_index_str = ".".join(str(x) for x in new_index_path)
            
            # Cerca l'item con il nuovo indice
            for item in self.steps_tree.get_children():
                self._find_and_select_item_by_index(item, new_index_str)
    
    def on_step_double_click(self, event):
        """Gestisce il doppio click su uno step."""
        # Forza l'aggiornamento delle zone prima di modificare lo step
        try:
            # Ottieni i valori aggiornati delle zone dalla configurazione
            if hasattr(self.controller, 'controller') and hasattr(self.controller.controller, 'zones_frame'):
                self.controller.controller.zones_frame.refresh_data()
        except Exception as e:
            logging.error(f"Errore nell'aggiornamento delle zone: {str(e)}")
        
        # Modifica lo step
        self.edit_step()
    
    def on_step_select(self, event):
        """Gestisce la selezione di uno step."""
        # Aggiorna il canvas con lo step selezionato evidenziato
        selection = self.steps_tree.selection()
        if selection:
            item_id = selection[0]
            item_values = self.steps_tree.item(item_id, "values")
            index_str = item_values[0]
            
            # Verifica se si tratta di un passo principale o di un sottopasso
            if "." in index_str:
                # Sottopasso di una ripetizione
                main_index, sub_index = map(int, index_str.split("."))
                main_index -= 1  # Converti in indice 0-based
                
                # Evidenzia il passo principale corrispondente
                self.draw_workout(highlight_index=main_index)
            else:
                # Passo principale
                index = int(index_str) - 1  # Converti in indice 0-based
                
                # Evidenzia il passo
                self.draw_workout(highlight_index=index)
        else:
            # Se non c'è selezione, disegna senza evidenziazione
            self.draw_workout()
    
    def update_workout_stats(self):
        """Aggiorna le statistiche dell'allenamento."""
        if not self.current_workout:
            self.stats_var.set("Durata stimata: -- | Distanza stimata: --")
            return
        
        # Ottieni durata e distanza totali
        total_duration = self.current_workout.get_total_duration()
        total_distance = self.current_workout.get_total_distance()
        
        # Formatta durata
        if total_duration is not None:
            if total_duration < 60:
                duration_str = f"{total_duration}s"
            elif total_duration < 3600:
                minutes = total_duration // 60
                seconds = total_duration % 60
                duration_str = f"{minutes}:{seconds:02d} min"
            else:
                hours = total_duration // 3600
                minutes = (total_duration % 3600) // 60
                seconds = total_duration % 60
                duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            duration_str = "--"
        
        # Formatta distanza
        if total_distance is not None:
            if total_distance < 1000:
                distance_str = f"{total_distance}m"
            else:
                distance_str = f"{total_distance/1000:.2f}km"
        else:
            distance_str = "--"
        
        # Aggiorna la label
        self.stats_var.set(f"Durata stimata: {duration_str} | Distanza stimata: {distance_str}")
    
    def on_canvas_press(self, event):
        """Gestisce il click sul canvas per iniziare il drag-and-drop."""
        # Verifica che ci sia un allenamento corrente
        if not self.current_workout or not self.current_workout.workout_steps:
            return
        
        # Canvas dimensions
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        # Se il canvas non è ancora inizializzato correttamente, forza l'aggiornamento
        if width <= 1 or height <= 1:
            self.canvas.update_idletasks()
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
        
        margin = 5
        draw_width = width - 2 * margin
        
        # Calcola il centro e la zona cliccabile
        center_y = height // 2
        click_zone_height = 80  # Zona cliccabile più ampia
        
        # Verifica se il click è nella zona degli step (fascia centrale)
        if center_y - click_zone_height/2 <= event.y <= center_y + click_zone_height/2:
            # Calcola la larghezza di ciascun blocco e determina quale è stato cliccato
            base_width = draw_width / len(self.current_workout.workout_steps)
            
            # Calcola l'indice dello step cliccato (correzione per i margini)
            relative_x = event.x - margin
            step_index = int(relative_x / base_width)
            
            # Verifica e limita l'indice per sicurezza
            if 0 <= step_index < len(self.current_workout.workout_steps):
                # Seleziona anche nella TreeView
                try:
                    # Trova l'item corrispondente
                    for item in self.steps_tree.get_children():
                        item_values = self.steps_tree.item(item, "values")
                        if item_values and int(item_values[0]) == step_index + 1:
                            self.steps_tree.selection_set(item)
                            self.steps_tree.see(item)
                            break
                except:
                    pass
                
                # Memorizza i dettagli dell'elemento per il trascinamento
                self.canvas_drag_data = {
                    "item": self.current_workout.workout_steps[step_index],
                    "index": step_index,
                    "start_x": event.x,
                    "start_y": event.y,
                    "current_x": event.x,
                    "current_y": event.y
                }
                
                # Ridisegna con l'elemento evidenziato
                self.draw_workout(highlight_index=step_index)
                return
        
        # Se arriviamo qui, nessuno step è stato selezionato
        self.canvas_drag_data = {
            "item": None,
            "index": -1,
            "start_x": 0,
            "start_y": 0
        }
    
    def on_canvas_motion(self, event):
        """Gestisce il movimento del mouse durante il drag-and-drop nel canvas."""
        # Solo se abbiamo un elemento selezionato
        if self.canvas_drag_data["item"] is not None:
            # Aggiorna la posizione corrente
            self.canvas_drag_data["current_x"] = event.x
            self.canvas_drag_data["current_y"] = event.y
            
            # Canvas dimensions
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            margin = 5
            draw_width = width - 2 * margin
            
            # Calcola la larghezza di base per ogni step
            base_width = draw_width / max(1, len(self.current_workout.workout_steps))
            
            # Determina la nuova posizione in base alla coordinata x
            x = event.x
            new_index = int((x - margin) / base_width)
            
            # Limita l'indice all'intervallo valido
            new_index = max(0, min(new_index, len(self.current_workout.workout_steps) - 1))
            
            # Ridisegna il grafico con l'indicatore di trascinamento
            self.draw_workout(drag_from=self.canvas_drag_data["index"], drag_to=new_index)
    
    def on_canvas_release(self, event):
        """Gestisce il rilascio del mouse per completare il drag-and-drop nel canvas."""
        # Solo se abbiamo un elemento selezionato
        if self.canvas_drag_data["item"] is not None:
            # Canvas dimensions
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            margin = 5
            draw_width = width - 2 * margin
            
            # Calcola la larghezza di base per ogni step
            base_width = draw_width / max(1, len(self.current_workout.workout_steps))
            
            # Determina la nuova posizione in base alla coordinata x
            x = event.x
            new_index = int((x - margin) / base_width)
            
            # Limita l'indice all'intervallo valido
            new_index = max(0, min(new_index, len(self.current_workout.workout_steps) - 1))
            
            # Sposta l'elemento solo se la posizione è cambiata
            if new_index != self.canvas_drag_data["index"]:
                source_index = self.canvas_drag_data["index"]
                
                # Esegui lo spostamento nella lista di step
                step = self.current_workout.workout_steps.pop(source_index)
                self.current_workout.workout_steps.insert(new_index, step)
                
                # Aggiorna la lista e l'anteprima
                self.update_steps_tree()
                self.draw_workout(highlight_index=new_index)
                
                # Seleziona l'elemento spostato nella lista
                try:
                    # Trova l'item corrispondente
                    for item in self.steps_tree.get_children():
                        item_values = self.steps_tree.item(item, "values")
                        if item_values and int(item_values[0]) == new_index + 1:
                            self.steps_tree.selection_set(item)
                            self.steps_tree.see(item)
                            break
                except:
                    pass
            else:
                # Se non c'è stato spostamento, ridisegna semplicemente senza evidenziazione
                self.draw_workout()
                
            # Resetta i dati di trascinamento
            self.canvas_drag_data = {
                "item": None,
                "index": -1,
                "start_x": 0,
                "start_y": 0
            }
    
    def draw_workout(self, highlight_index=None, drag_from=None, drag_to=None):
        """
        Disegna una rappresentazione visiva dell'allenamento sul canvas.
        
        Args:
            highlight_index: Indice dello step da evidenziare (opzionale)
            drag_from: Indice dello step da cui si sta trascinando (opzionale)
            drag_to: Indice dello step in cui si sta trascinando (opzionale)
        """
        # Verifica che ci sia un allenamento corrente
        if not self.current_workout:
            return
        
        # Cancella il canvas
        self.canvas.delete("all")
        
        # Canvas dimensions
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if width <= 1 or height <= 1:  # Canvas not yet realized
            self.canvas.update_idletasks()
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            
            # If still not realized, use default dimensions
            if width <= 1:
                width = 700
            if height <= 1:
                height = 150
        
        # Margin
        margin = 5
        
        # Available drawing area
        draw_width = width - 2 * margin
        
        # Se non ci sono step da disegnare
        if not self.current_workout.workout_steps:
            # Disegna un messaggio di istruzioni
            self.canvas.create_text(
                width // 2, height // 2,
                text="Aggiungi passi all'allenamento per visualizzarli qui",
                fill=COLORS["text_dark"],
                font=("Arial", 10)
            )
            return
        
        # Calcola la larghezza di base per ogni step
        base_width = draw_width / len(self.current_workout.workout_steps)
        
        # Posizione Y centrale
        y = height // 2
        
        # Se stiamo trascinando, disegna un indicatore per la posizione target
        if drag_from is not None and drag_to is not None:
            # Calcola la posizione x dell'indicatore di trascinamento
            indicator_x = margin + drag_to * base_width
            
            # Disegna una linea verticale per indicare dove verrà inserito l'elemento
            self.canvas.create_line(
                indicator_x, y - 30, 
                indicator_x, y + 30,
                fill=COLORS["accent"], width=2, dash=(6, 4)
            )
        
        # Disegna gli step
        for i, step in enumerate(self.current_workout.workout_steps):
            x = margin + i * base_width
            
            # Calcola se questo step deve essere evidenziato
            is_highlighted = (i == highlight_index)
            
            # Salta temporaneamente il disegno dell'elemento che stiamo trascinando
            if i == drag_from:
                continue
            
            outline_width = 2 if is_highlighted else 0
            outline_color = COLORS["accent"] if is_highlighted else ""
            
            # Ottieni il colore per il tipo di passo
            step_color = COLORS.get(step.step_type, COLORS["other"])
            
            if step.step_type == "repeat":
                # Repeat step (special drawing)
                # Draw repeat box
                repeat_width = base_width
                repeat_x = x
                repeat_y = y - 30
                
                self.canvas.create_rectangle(
                    repeat_x, repeat_y, 
                    repeat_x + repeat_width, repeat_y + 60,
                    fill=COLORS["bg_light"],
                    outline=step_color, 
                    width=2, 
                    dash=(5, 2)
                )
                
                # Draw repeat label
                iterations = step.end_condition_value
                substep_count = len(step.workout_steps)
                
                self.canvas.create_text(
                    repeat_x + 10, repeat_y - 10,
                    text=f"{STEP_ICONS['repeat']} {iterations}×",
                    fill=step_color, 
                    font=("Arial", 10, "bold"),
                    anchor=tk.W
                )
                
                # Draw substeps
                sub_width = repeat_width / max(1, substep_count)
                sub_x = x
                
                for j, substep in enumerate(step.workout_steps):
                    # Color for this type
                    sub_color = COLORS.get(substep.step_type, COLORS["other"])
                    
                    # Draw box
                    self.canvas.create_rectangle(
                        sub_x, y - 20, 
                        sub_x + sub_width, y + 20,
                        fill=sub_color, 
                        outline=outline_color, 
                        width=outline_width
                    )
                    
                    # Draw text
                    self.canvas.create_text(
                        sub_x + sub_width // 2, y,
                        text=f"{STEP_ICONS.get(substep.step_type, '📝')} {j+1}",
                        fill=COLORS["text_light"],
                        font=("Arial", 9, "bold")
                    )
                    
                    # Draw separator between substeps (except last)
                    if j < substep_count - 1:
                        self.canvas.create_line(
                            sub_x + sub_width, y - 20,
                            sub_x + sub_width, y + 20,
                            fill="white", width=1
                        )
                    
                    sub_x += sub_width
            else:
                # Regular step
                # Draw box
                self.canvas.create_rectangle(
                    x, y - 20, 
                    x + base_width, y + 20,
                    fill=step_color, 
                    outline=outline_color, 
                    width=outline_width
                )
                
                # Draw icon and number
                self.canvas.create_text(
                    x + base_width // 2, y,
                    text=f"{STEP_ICONS.get(step.step_type, '📝')} {i+1}",
                    fill=COLORS["text_light"],
                    font=("Arial", 9, "bold")
                )
            
            # Draw separators between steps (vertical line)
            if i < len(self.current_workout.workout_steps) - 1:
                self.canvas.create_line(
                    x + base_width, y - 22,
                    x + base_width, y + 22,
                    fill="#333333", width=1, dash=(2, 2)
                )
        
        # If dragging, draw the dragged element
        if drag_from is not None and self.canvas_drag_data.get("current_x") and self.canvas_drag_data.get("current_y"):
            # Get the dragged step
            step = self.current_workout.workout_steps[drag_from]
            
            # Calculate box dimensions
            box_width = base_width
            box_height = 40
            
            # Calculate box position centered on cursor
            box_x = self.canvas_drag_data["current_x"] - box_width // 2
            box_y = self.canvas_drag_data["current_y"] - box_height // 2
            
            # Get color and icon
            step_color = COLORS.get(step.step_type, COLORS["other"])
            step_icon = STEP_ICONS.get(step.step_type, "📝")
            
            # Draw semi-transparent box
            self.canvas.create_rectangle(
                box_x, box_y,
                box_x + box_width, box_y + box_height,
                fill=self.lighten_color(step_color),
                outline=COLORS["accent"],
                width=2
            )
            
            # Draw step info
            self.canvas.create_text(
                box_x + box_width // 2, box_y + box_height // 2,
                text=f"{step_icon} {drag_from + 1}",
                fill=COLORS["text_dark"],
                font=("Arial", 9, "bold")
            )
    
    def lighten_color(self, hex_color):
        """
        Rende più chiaro un colore hexadecimale mescolandolo con bianco.
        
        Args:
            hex_color: Colore hex da schiarire
            
        Returns:
            str: Colore hex schiarito
        """
        try:
            # Convert hex to RGB
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            
            # Lighten by blending with white
            r = int(r * 0.6 + 255 * 0.4)
            g = int(g * 0.6 + 255 * 0.4)
            b = int(b * 0.6 + 255 * 0.4)
            
            # Convert back to hex
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return "#FFFFFF"  # Fallback to white
    
    def show_calendar(self):
        """Mostra un selettore di data."""
        try:
            # Prova a importare tkcalendar
            from tkcalendar import Calendar
            
            # Crea una finestra top-level
            top = tk.Toplevel(self)
            top.title("Seleziona data")
            top.geometry("350x300")
            top.transient(self)
            top.grab_set()
            
            # Data iniziale
            if self.date_var.get():
                try:
                    initial_date = datetime.datetime.strptime(self.date_var.get(), "%Y-%m-%d").date()
                except ValueError:
                    initial_date = datetime.date.today()
            else:
                initial_date = datetime.date.today()
            
            # Crea il calendario
            cal = Calendar(top, selectmode='day', year=initial_date.year, 
                          month=initial_date.month, day=initial_date.day,
                          date_pattern="yyyy-mm-dd")
            cal.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Funzione per selezionare la data
            def select_date():
                self.date_var.set(cal.get_date())
                
                # Aggiorna anche la data nell'allenamento corrente
                if self.current_workout:
                    self.current_workout.set_scheduled_date(cal.get_date())
                
                top.destroy()
            
            # Pulsante per confermare
            ttk.Button(top, text="Seleziona", command=select_date).pack(pady=10)
            
        except ImportError:
            # Se tkcalendar non è disponibile, usa un semplice dialogo
            date_str = tk.simpledialog.askstring(
                "Data", 
                "Inserisci la data (YYYY-MM-DD):", 
                parent=self, 
                initialvalue=self.date_var.get()
            )
            
            if date_str:
                try:
                    # Verifica che sia una data valida
                    datetime.datetime.strptime(date_str, "%Y-%m-%d")
                    self.date_var.set(date_str)
                    
                    # Aggiorna anche la data nell'allenamento corrente
                    if self.current_workout:
                        self.current_workout.set_scheduled_date(date_str)
                        
                except ValueError:
                    messagebox.showerror(
                        "Errore", 
                        "Formato data non valido. Usa YYYY-MM-DD.", 
                        parent=self
                    )
    
    def on_sport_change(self, event=None):
        """Gestisce il cambio di tipo di sport."""
        if not self.current_workout:
            return
        
        # Ottieni il nuovo tipo di sport
        sport_type = self.sport_var.get()
        
        # Aggiorna il tipo di sport nell'allenamento
        self.current_workout.sport_type = sport_type
    
    def save_workout(self):
        """Salva le modifiche all'allenamento."""
        if not self.current_workout:
            return
        
        # Verifica che il nome non sia vuoto
        if not self.name_var.get().strip():
            messagebox.showerror(
                "Errore", 
                "Il nome dell'allenamento non può essere vuoto.", 
                parent=self
            )
            return
        
        # Aggiorna il nome dell'allenamento
        self.current_workout.workout_name = self.name_var.get().strip()
        
        # Aggiorna il tipo di sport
        self.current_workout.sport_type = self.sport_var.get()
        
        # Aggiorna la data pianificata
        self.current_workout.set_scheduled_date(self.date_var.get().strip())
        
        # Aggiorna l'allenamento nella lista
        found = False
        for i, workout in enumerate(self.controller.workouts):
            if workout is self.current_workout:
                found = True
                break
        
        # Se l'allenamento non è già nella lista, aggiungilo
        if not found:
            self.controller.workouts.append(self.current_workout)
        
        # Aggiorna la lista degli allenamenti
        self.controller.update_workouts_list()
        
        # Mostra un messaggio di conferma
        messagebox.showinfo(
            "Allenamento salvato", 
            f"L'allenamento '{self.current_workout.workout_name}' è stato salvato.", 
            parent=self
        )
    
    def update_workouts_list(self):
        """
        Aggiorna la lista degli allenamenti nell'interfaccia.
        """
        # Qui puoi implementare il codice per aggiornare una lista o una tabella
        # che mostra gli allenamenti disponibili
        
        # Se hai una Treeview o un altro widget per mostrare gli allenamenti:
        # 1. Cancella tutti gli elementi esistenti
        # 2. Aggiungi gli elementi dalla lista self.workouts
        
        # Esempio di base (adatta secondo i tuoi widget):
        if hasattr(self, 'workouts_tree'):
            # Cancella tutti gli elementi esistenti
            for item in self.workouts_tree.get_children():
                self.workouts_tree.delete(item)
            
            # Aggiungi i nuovi elementi
            for i, workout in enumerate(self.workouts):
                values = [i+1, workout.workout_name, workout.sport_type, workout.get_scheduled_date() or ""]
                self.workouts_tree.insert("", "end", values=values)

    
    def cancel_edit(self):
        """Annulla le modifiche correnti."""
        # Verifica se ci sono modifiche da annullare
        if not self.current_workout:
            return
        
        # Chiedi conferma
        if messagebox.askyesno(
            "Annulla modifiche", 
            "Sei sicuro di voler annullare le modifiche correnti?", 
            parent=self
        ):
            # Trova l'allenamento originale nella lista
            original = None
            for workout in self.controller.workouts:
                if workout is self.current_workout:
                    original = workout
                    break
            
            # Se l'allenamento è nella lista, ricaricalo
            if original:
                self.load_workout(original)
            else:
                # Altrimenti, pulisci l'editor
                self.clear_editor()
                self.disable_editor()