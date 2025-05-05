#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Frame per la gestione degli allenamenti.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import threading
import datetime
import re
import os

from ..core.utils import format_workout_name, parse_workout_name
from ..core.workout import Workout, WorkoutStep, Target
from .workout_editor import WorkoutEditor
from .styles import SPORT_ICONS, STEP_ICONS, COLORS

class WorkoutsFrame(ttk.Frame):
    """Frame per la gestione degli allenamenti."""
    
    def __init__(self, parent, controller):
        """
        Inizializza il frame degli allenamenti.
        
        Args:
            parent: Widget genitore
            controller: Controller dell'applicazione
        """
        super().__init__(parent)
        self.controller = controller
        self.garmin_client = None
        
        # Lista degli allenamenti
        self.workouts = []
        
        # Allenamento corrente nell'editor
        self.current_workout = None
        
        # Dizionario per memorizzare gli ID degli allenamenti in Garmin Connect
        self.workout_ids = {}
        
        # Filtri
        self.sport_filter_var = tk.StringVar(value="Tutti")
        self.search_var = tk.StringVar()
        self.week_filter_var = tk.StringVar(value="Tutte")
        
        # Inizializza l'interfaccia
        self.init_ui()
    
    def init_ui(self):
        """Inizializza l'interfaccia utente."""
        # Frame principale con padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Dividi lo schermo in due parti (lista e editor)
        self.paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Crea il pannello sinistro (lista)
        left_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(left_frame, weight=30)
        
        # Crea il pannello destro (editor)
        right_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(right_frame, weight=70)
        
        # Configura il pannello sinistro (lista allenamenti)
        self.create_workouts_list(left_frame)
        
        # Configura il pannello destro (editor allenamento)
        self.workout_editor = WorkoutEditor(right_frame, self)
        
        # Disabilita l'editor inizialmente
        self.workout_editor.disable_editor()
    
    def create_workouts_list(self, parent):
        """
        Crea la lista degli allenamenti.
        
        Args:
            parent: Widget genitore
        """
        # Container con bordo
        list_frame = ttk.LabelFrame(parent, text="Allenamenti disponibili")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Barra degli strumenti
        toolbar = ttk.Frame(list_frame)
        toolbar.pack(fill=tk.X, pady=5)
        
        # Filtro per tipo di sport
        ttk.Label(toolbar, text="Sport:").pack(side=tk.LEFT, padx=(0, 5))
        
        sport_combo = ttk.Combobox(
            toolbar, 
            textvariable=self.sport_filter_var,
            values=["Tutti", "Corsa", "Ciclismo", "Nuoto", "Altri"],
            width=10,
            state="readonly"
        )
        sport_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # Binding per applicare il filtro
        sport_combo.bind("<<ComboboxSelected>>", self.apply_filters)
        
        # Filtro per settimana
        ttk.Label(toolbar, text="Settimana:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.week_combo = ttk.Combobox(
            toolbar, 
            textvariable=self.week_filter_var,
            values=["Tutte"],
            width=10,
            state="readonly"
        )
        self.week_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # Binding per applicare il filtro
        self.week_combo.bind("<<ComboboxSelected>>", self.apply_filters)
        
        # Campo di ricerca
        ttk.Label(toolbar, text="Cerca:").pack(side=tk.LEFT, padx=(0, 5))
        
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=15)
        search_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        # Binding per applicare il filtro durante la digitazione
        self.search_var.trace_add("write", lambda *args: self.apply_filters())
        
        # Pulsante per cancellare la ricerca
        clear_button = ttk.Button(
            toolbar, 
            text="✕", 
            width=2,
            command=self.clear_search
        )
        clear_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Pulsante di refresh
        refresh_button = ttk.Button(
            toolbar, 
            text="↻", 
            width=2,
            command=self.refresh_data
        )
        refresh_button.pack(side=tk.RIGHT, padx=5)
        
        # Frame per la lista con scrollbar
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Crea la treeview per la lista
        columns = ("name", "sport", "date", "steps")
        self.workout_tree = ttk.Treeview(
            list_container, 
            columns=columns, 
            show="headings", 
            selectmode="browse"
        )
        
        # Definisci le intestazioni
        self.workout_tree.heading("name", text="Nome")
        self.workout_tree.heading("sport", text="Sport")
        self.workout_tree.heading("date", text="Data")
        self.workout_tree.heading("steps", text="Passi")
        
        # Definisci le larghezze delle colonne
        self.workout_tree.column("name", width=200)
        self.workout_tree.column("sport", width=70)
        self.workout_tree.column("date", width=80)
        self.workout_tree.column("steps", width=50)
        
        # Aggiungi scrollbar
        scrollbar = ttk.Scrollbar(
            list_container, 
            orient=tk.VERTICAL, 
            command=self.workout_tree.yview
        )
        self.workout_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.workout_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Associa eventi
        self.workout_tree.bind("<<TreeviewSelect>>", self.on_workout_select)
        self.workout_tree.bind("<Double-1>", self.on_workout_double_click)
        
        # Pulsanti sotto la lista
        button_frame = ttk.Frame(list_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        # Pulsante per nuovo allenamento
        new_button = ttk.Button(
            button_frame, 
            text="Nuovo", 
            command=self.new_workout
        )
        new_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Pulsante per duplicare un allenamento
        copy_button = ttk.Button(
            button_frame, 
            text="Duplica", 
            command=self.copy_workout
        )
        copy_button.pack(side=tk.LEFT, padx=5)
        
        # Pulsante per eliminare un allenamento
        delete_button = ttk.Button(
            button_frame, 
            text="Elimina", 
            command=self.delete_workout
        )
        delete_button.pack(side=tk.LEFT, padx=5)
        
        # Pulsante per sincronizzare con Garmin Connect
        sync_button = ttk.Button(
            button_frame, 
            text="Sincronizza", 
            command=self.sync_workouts,
            style="Info.TButton"
        )
        sync_button.pack(side=tk.RIGHT, padx=5)
    
    def clear_search(self):
        """Cancella il campo di ricerca."""
        self.search_var.set("")
    
    def on_workout_select(self, event=None):
        """
        Gestisce la selezione di un allenamento dalla lista.
        
        Args:
            event: Evento di selezione (opzionale)
        """
        selection = self.workout_tree.selection()
        if not selection:
            return
        
        # Ottieni l'indice dell'allenamento selezionato
        item_id = selection[0]
        index = self.workout_tree.index(item_id)
        
        # Ottieni l'allenamento
        filtered_workouts = self.get_filtered_workouts()
        if index < len(filtered_workouts):
            workout = filtered_workouts[index]
            
            # Carica l'allenamento nell'editor
            self.workout_editor.load_workout(workout)
            
            # Memorizza l'allenamento corrente
            self.current_workout = workout
    
    def on_workout_double_click(self, event):
        """
        Gestisce il doppio click su un allenamento.
        
        Args:
            event: Evento di doppio click
        """
        self.on_workout_select(event)
    
    def apply_filters(self, event=None):
        """
        Applica i filtri alla lista degli allenamenti.
        
        Args:
            event: Evento di cambio filtro (opzionale)
        """
        self.update_workouts_list()
    
    def get_filtered_workouts(self):
        """
        Ottiene gli allenamenti filtrati in base ai criteri selezionati.
        
        Returns:
            list: Lista degli allenamenti filtrati
        """
        filtered = []
        
        # Ottieni i valori dei filtri
        sport_filter = self.sport_filter_var.get()
        week_filter = self.week_filter_var.get()
        search_text = self.search_var.get().lower()
        
        for workout in self.workouts:
            # Filtra per tipo di sport
            if sport_filter != "Tutti":
                sport_type = workout.sport_type
                
                if sport_filter == "Corsa" and sport_type != "running":
                    continue
                elif sport_filter == "Ciclismo" and sport_type != "cycling":
                    continue
                elif sport_filter == "Nuoto" and sport_type != "swimming":
                    continue
                elif sport_filter == "Altri" and sport_type in ["running", "cycling", "swimming"]:
                    continue
            
            # Filtra per settimana
            if week_filter != "Tutte":
                week, _, _ = parse_workout_name(workout.workout_name)
                if week is None or f"W{week:02d}" != week_filter:
                    continue
            
            # Filtra per testo di ricerca
            if search_text:
                if search_text not in workout.workout_name.lower():
                    continue
            
            # Se l'allenamento passa tutti i filtri, aggiungilo all'elenco
            filtered.append(workout)
        
        return filtered
    
    def update_workouts_list(self):
        """Aggiorna la lista degli allenamenti nella treeview."""
        # Memorizza la selezione corrente
        selection = self.workout_tree.selection()
        selected_id = selection[0] if selection else None
        
        # Rimuovi tutti gli elementi
        for item in self.workout_tree.get_children():
            self.workout_tree.delete(item)
        
        # Ottieni gli allenamenti filtrati
        filtered_workouts = self.get_filtered_workouts()
        
        # Aggiungi gli allenamenti filtrati
        for workout in filtered_workouts:
            # Formatta il tipo di sport
            sport_display = workout.sport_type.capitalize()
            
            # Ottieni la data, se disponibile
            date_display = workout.get_scheduled_date() or ""
            
            # Conta il numero di passi
            step_count = workout.get_step_count()
            
            # Inserisci l'allenamento nella lista
            item_id = self.workout_tree.insert(
                "", 
                "end", 
                values=(workout.workout_name, sport_display, date_display, step_count)
            )
            
            # Applica un tag in base al tipo di sport per una formattazione aggiuntiva
            self.workout_tree.item(item_id, tags=(workout.sport_type,))
        
        # Ripristina la selezione, se possibile
        if selected_id:
            try:
                self.workout_tree.selection_set(selected_id)
                self.workout_tree.see(selected_id)
            except:
                pass
        
        # Aggiorna le opzioni del filtro per settimana
        self.update_week_filter_options()
    
    def update_week_filter_options(self):
        """Aggiorna le opzioni del filtro per settimana."""
        # Raccogli tutte le settimane disponibili
        weeks = set()
        
        for workout in self.workouts:
            week, _, _ = parse_workout_name(workout.workout_name)
            if week is not None:
                weeks.add(f"W{week:02d}")
        
        # Ordina le settimane
        sorted_weeks = sorted(list(weeks))
        
        # Aggiorna le opzioni del combobox
        self.week_combo['values'] = ["Tutte"] + sorted_weeks
    
    def new_workout(self):
        """Crea un nuovo allenamento."""
        # Crea un nuovo allenamento vuoto
        workout = Workout("running", "Nuovo allenamento")
        
        # Aggiungi alcuni passi di esempio
        warmup = WorkoutStep(1, "warmup", "Riscaldamento", "time", "10min")
        workout.add_step(warmup)
        
        interval = WorkoutStep(2, "interval", "Intervallo", "distance", "400m", 
                             Target("pace.zone", 3.8, 4.2))
        workout.add_step(interval)
        
        cooldown = WorkoutStep(3, "cooldown", "Defaticamento", "time", "5min")
        workout.add_step(cooldown)
        
        # Carica l'allenamento nell'editor
        self.workout_editor.load_workout(workout)
        
        # Imposta l'allenamento corrente
        self.current_workout = workout
    
    def copy_workout(self):
        """Duplica l'allenamento selezionato."""
        selection = self.workout_tree.selection()
        if not selection:
            messagebox.showwarning(
                "Nessuna selezione", 
                "Seleziona un allenamento da duplicare.",
                parent=self
            )
            return
        
        # Ottieni l'indice dell'allenamento selezionato
        item_id = selection[0]
        index = self.workout_tree.index(item_id)
        
        # Ottieni l'allenamento
        filtered_workouts = self.get_filtered_workouts()
        if index < len(filtered_workouts):
            original = filtered_workouts[index]
            
            # Estrai settimana, sessione e descrizione dal nome
            week, session, description = parse_workout_name(original.workout_name)
            
            # Crea un nuovo nome
            if week is not None and session is not None:
                # Usa lo stesso formato ma incrementa la sessione
                new_name = format_workout_name(week, session + 1, f"Copia di {description}")
            else:
                # Aggiungi semplicemente un prefisso
                new_name = f"Copia di {original.workout_name}"
            
            # Crea un nuovo allenamento come copia
            workout = Workout(original.sport_type, new_name, original.description)
            
            # Copia i passi
            for step in original.workout_steps:
                # Crea una copia del passo (questa è una semplificazione, in realtà 
                # servirebbe una copia più profonda con tutti i substep)
                new_step = WorkoutStep(
                    step.order,
                    step.step_type,
                    step.description,
                    step.end_condition,
                    step.end_condition_value,
                    step.target
                )
                
                # Copia i substep per i passi di tipo repeat
                for substep in step.workout_steps:
                    new_substep = WorkoutStep(
                        substep.order,
                        substep.step_type,
                        substep.description,
                        substep.end_condition,
                        substep.end_condition_value,
                        substep.target
                    )
                    new_step.add_step(new_substep)
                
                # Aggiungi il passo al nuovo allenamento
                workout.add_step(new_step)
            
            # Aggiungi il nuovo allenamento alla lista
            self.workouts.append(workout)
            
            # Aggiorna la lista
            self.update_workouts_list()
            
            # Seleziona il nuovo allenamento
            for i, w in enumerate(self.get_filtered_workouts()):
                if w.workout_name == new_name:
                    item_id = self.workout_tree.get_children()[i]
                    self.workout_tree.selection_set(item_id)
                    self.workout_tree.see(item_id)
                    self.on_workout_select()
                    break
            
            # Mostra un messaggio di conferma
            messagebox.showinfo(
                "Allenamento duplicato", 
                f"L'allenamento '{original.workout_name}' è stato duplicato.",
                parent=self
            )
    
    def delete_workout(self):
        """Elimina l'allenamento selezionato."""
        selection = self.workout_tree.selection()
        if not selection:
            messagebox.showwarning(
                "Nessuna selezione", 
                "Seleziona un allenamento da eliminare.",
                parent=self
            )
            return
        
        # Ottieni l'indice dell'allenamento selezionato
        item_id = selection[0]
        index = self.workout_tree.index(item_id)
        
        # Ottieni l'allenamento
        filtered_workouts = self.get_filtered_workouts()
        if index < len(filtered_workouts):
            workout = filtered_workouts[index]
            
            # Chiedi conferma
            if not messagebox.askyesno(
                "Conferma eliminazione", 
                f"Sei sicuro di voler eliminare l'allenamento '{workout.workout_name}'?",
                parent=self
            ):
                return
            
            # Rimuovi l'allenamento dalla lista
            self.workouts.remove(workout)
            
            # Aggiorna la lista
            self.update_workouts_list()
            
            # Pulisci l'editor
            self.workout_editor.clear_editor()
            self.workout_editor.disable_editor()
            
            # Mostra un messaggio di conferma
            messagebox.showinfo(
                "Allenamento eliminato", 
                f"L'allenamento '{workout.workout_name}' è stato eliminato.",
                parent=self
            )
    
    def sync_workouts(self):
        """Sincronizza gli allenamenti con Garmin Connect."""
        if not self.garmin_client:
            messagebox.showerror(
                "Errore", 
                "Non sei connesso a Garmin Connect.",
                parent=self
            )
            return
        
        # Crea un dialog personalizzato
        sync_dialog = tk.Toplevel(self)
        sync_dialog.title("Sincronizza con Garmin Connect")
        sync_dialog.geometry("400x300")
        sync_dialog.transient(self)
        sync_dialog.grab_set()
        
        # Configurazione del dialog
        ttk.Label(
            sync_dialog, 
            text="Scegli cosa sincronizzare:", 
            style="Heading.TLabel"
        ).pack(pady=(10, 20))
        
        # Opzioni
        sync_var = tk.IntVar(value=1)
        ttk.Radiobutton(
            sync_dialog, 
            text="Carica tutti gli allenamenti su Garmin Connect", 
            variable=sync_var, 
            value=1
        ).pack(anchor=tk.W, padx=20, pady=5)
        
        ttk.Radiobutton(
            sync_dialog, 
            text="Carica solo l'allenamento selezionato", 
            variable=sync_var, 
            value=2
        ).pack(anchor=tk.W, padx=20, pady=5)
        
        ttk.Radiobutton(
            sync_dialog, 
            text="Scarica allenamenti da Garmin Connect", 
            variable=sync_var, 
            value=3
        ).pack(anchor=tk.W, padx=20, pady=5)
        
        # Separatore
        ttk.Separator(sync_dialog, orient='horizontal').pack(fill='x', padx=20, pady=10)
        
        # Flag per sovrascrittura
        replace_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            sync_dialog, 
            text="Sovrascrivi allenamenti esistenti con lo stesso nome", 
            variable=replace_var
        ).pack(anchor=tk.W, padx=20, pady=5)
        
        # Flag per pianificazione
        schedule_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            sync_dialog, 
            text="Pianifica gli allenamenti nelle date specificate", 
            variable=schedule_var
        ).pack(anchor=tk.W, padx=20, pady=5)
        
        # Pulsanti
        button_frame = ttk.Frame(sync_dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Variabile per il risultato
        result = {"action": None, "replace": False, "schedule": False}
        
        def on_ok():
            result["action"] = sync_var.get()
            result["replace"] = replace_var.get()
            result["schedule"] = schedule_var.get()
            sync_dialog.destroy()
        
        def on_cancel():
            result["action"] = None
            sync_dialog.destroy()
        
        ttk.Button(
            button_frame, 
            text="OK", 
            command=on_ok,
            style="Success.TButton"
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Annulla", 
            command=on_cancel
        ).pack(side=tk.LEFT, padx=5)
        
        # Attendi la chiusura del dialog
        self.wait_window(sync_dialog)
        
        # Se l'utente ha annullato
        if result["action"] is None:
            return
        
        # Esegui l'azione richiesta
        if result["action"] == 1:
            # Carica tutti gli allenamenti
            self.upload_all_workouts(result["replace"], result["schedule"])
        elif result["action"] == 2:
            # Carica solo l'allenamento selezionato
            self.upload_selected_workout(result["replace"], result["schedule"])
        elif result["action"] == 3:
            # Scarica allenamenti
            self.download_workouts()
    
    def upload_all_workouts(self, replace=False, schedule=True):
        """
        Carica tutti gli allenamenti su Garmin Connect.
        
        Args:
            replace: Se True, sostituisce gli allenamenti esistenti
            schedule: Se True, pianifica gli allenamenti nelle date specificate
        """
        if not self.workouts:
            messagebox.showinfo(
                "Informazione", 
                "Nessun allenamento da caricare.",
                parent=self
            )
            return
        
        # Conferma
        if not messagebox.askyesno(
            "Conferma", 
            f"Stai per caricare {len(self.workouts)} allenamenti su Garmin Connect. Continuare?", 
            parent=self
        ):
            return
        
        # Crea un thread separato per il caricamento
        threading.Thread(
            target=self._upload_workouts_thread,
            args=(self.workouts, replace, schedule),
            daemon=True
        ).start()
    
    def upload_selected_workout(self, replace=False, schedule=True):
        """
        Carica l'allenamento selezionato su Garmin Connect.
        
        Args:
            replace: Se True, sostituisce gli allenamenti esistenti
            schedule: Se True, pianifica gli allenamenti nelle date specificate
        """
        selection = self.workout_tree.selection()
        if not selection:
            messagebox.showwarning(
                "Nessuna selezione", 
                "Seleziona un allenamento da caricare.",
                parent=self
            )
            return
        
        # Ottieni l'indice dell'allenamento selezionato
        item_id = selection[0]
        index = self.workout_tree.index(item_id)
        
        # Ottieni l'allenamento
        filtered_workouts = self.get_filtered_workouts()
        if index < len(filtered_workouts):
            workout = filtered_workouts[index]
            
            # Conferma
            if not messagebox.askyesno(
                "Conferma", 
                f"Stai per caricare l'allenamento '{workout.workout_name}' su Garmin Connect. Continuare?", 
                parent=self
            ):
                return
            
            # Crea un thread separato per il caricamento
            threading.Thread(
                target=self._upload_workouts_thread,
                args=([workout], replace, schedule),
                daemon=True
            ).start()
    
    def _upload_workouts_thread(self, workouts, replace, schedule):
        """
        Thread separato per il caricamento degli allenamenti su Garmin Connect.
        
        Args:
            workouts: Lista degli allenamenti da caricare
            replace: Se True, sostituisce gli allenamenti esistenti
            schedule: Se True, pianifica gli allenamenti nelle date specificate
        """
        try:
            # Ottieni la lista degli allenamenti esistenti su Garmin Connect
            existing_workouts = self.garmin_client.list_workouts()
            
            # Crea un dizionario nome -> id per gli allenamenti esistenti
            existing_map = {}
            for workout in existing_workouts:
                existing_map[workout["workoutName"]] = workout["workoutId"]
            
            # Mostra una finestra di progresso
            self.after(0, lambda: self._show_progress_dialog(workouts))
            
            # Conta successi/errori
            self.success_count = 0
            self.error_count = 0
            self.scheduled_count = 0
            
            # Per ogni allenamento
            for i, workout in enumerate(workouts):
                try:
                    # Aggiorna lo stato
                    self.after(0, lambda: self._update_progress(
                        i + 1, 
                        len(workouts), 
                        workout.workout_name, 
                        "Caricamento in corso..."
                    ))
                    
                    # ID dell'allenamento su Garmin (sarà impostato dopo il caricamento)
                    workout_id = None
                    
                    # Carica o aggiorna l'allenamento
                    if workout.workout_name in existing_map and replace:
                        # Aggiorna l'allenamento esistente
                        workout_id = existing_map[workout.workout_name]
                        self.garmin_client.update_workout(workout_id, workout)
                        
                        # Salva l'ID
                        self.workout_ids[workout.workout_name] = workout_id
                    else:
                        # Crea un nuovo allenamento
                        response = self.garmin_client.add_workout(workout)
                        
                        # Estrai l'ID dal nuovo allenamento creato
                        if response and "workoutId" in response:
                            workout_id = response["workoutId"]
                            
                            # Salva l'ID
                            self.workout_ids[workout.workout_name] = workout_id
                    
                    # Pianifica l'allenamento se è stata specificata una data
                    if schedule and workout.get_scheduled_date() and workout_id:
                        try:
                            self.after(0, lambda: self._update_progress(
                                i + 1, 
                                len(workouts), 
                                workout.workout_name, 
                                f"Pianificazione per il {workout.get_scheduled_date()}..."
                            ))
                            
                            # Pianifica l'allenamento
                            self.garmin_client.schedule_workout(workout_id, workout.get_scheduled_date())
                            self.scheduled_count += 1
                        except Exception as sch_err:
                            logging.error(f"Errore nella pianificazione dell'allenamento '{workout.workout_name}': {str(sch_err)}")
                    
                    self.success_count += 1
                    
                except Exception as e:
                    logging.error(f"Errore nel caricamento dell'allenamento '{workout.workout_name}': {str(e)}")
                    self.error_count += 1
            
            # Chiudi la finestra di progresso
            self.after(0, self._close_progress)
            
            # Mostra il risultato
            result_msg = f"Caricati {self.success_count} allenamenti su Garmin Connect."
            if self.scheduled_count > 0:
                result_msg += f"\nPianificati {self.scheduled_count} allenamenti nelle date specificate."
            
            if self.error_count == 0:
                self.after(0, lambda: messagebox.showinfo(
                    "Completato", 
                    result_msg, 
                    parent=self
                ))
            else:
                self.after(0, lambda: messagebox.showwarning(
                    "Completato con errori", 
                    f"{result_msg}\nSi sono verificati {self.error_count} errori. Controlla il log per i dettagli.", 
                    parent=self
                ))
        
        except Exception as e:
            # Chiudi la finestra di progresso
            self.after(0, self._close_progress)
            
            # Mostra errore
            self.after(0, lambda: messagebox.showerror(
                "Errore", 
                f"Si è verificato un errore durante il caricamento degli allenamenti: {str(e)}", 
                parent=self
            ))
    
    def _show_progress_dialog(self, workouts):
        """
        Mostra una finestra di progresso per il caricamento degli allenamenti.
        
        Args:
            workouts: Lista degli allenamenti da caricare
        """
        # Finestra top-level
        self.progress_window = tk.Toplevel(self)
        self.progress_window.title("Caricamento in corso")
        self.progress_window.geometry("400x150")
        self.progress_window.transient(self)
        self.progress_window.grab_set()
        
        # Aggiunge padding
        frame = ttk.Frame(self.progress_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Label per lo stato
        self.status_var = tk.StringVar(value="Caricamento in corso...")
        status_label = ttk.Label(frame, textvariable=self.status_var)
        status_label.pack(pady=(0, 10))
        
        # Barra di progresso
        self.progress = ttk.Progressbar(
            frame, 
            mode='determinate', 
            length=350, 
            maximum=len(workouts)
        )
        self.progress.pack(pady=10)
        
        # Label secondaria per il messaggio di pianificazione
        self.substatus_var = tk.StringVar(value="")
        substatus_label = ttk.Label(frame, textvariable=self.substatus_var)
        substatus_label.pack(pady=5)
    
    def _update_progress(self, current, total, name, substatus=""):
        """
        Aggiorna la finestra di progresso.
        
        Args:
            current: Numero dell'allenamento corrente
            total: Numero totale di allenamenti
            name: Nome dell'allenamento corrente
            substatus: Messaggio secondario (opzionale)
        """
        if hasattr(self, 'progress_window') and self.progress_window.winfo_exists():
            self.status_var.set(f"Caricamento {current}/{total}: {name}")
            self.substatus_var.set(substatus)
            self.progress['value'] = current
    
    def _close_progress(self):
        """Chiude la finestra di progresso."""
        if hasattr(self, 'progress_window') and self.progress_window.winfo_exists():
            self.progress_window.destroy()
    
    def download_workouts(self):
        """Scarica gli allenamenti da Garmin Connect."""
        if not self.garmin_client:
            messagebox.showerror(
                "Errore", 
                "Non sei connesso a Garmin Connect.",
                parent=self
            )
            return
        
        try:
            # Ottieni la lista degli allenamenti
            remote_workouts = self.garmin_client.list_workouts()
            
            # Verifica se ci sono allenamenti
            if not remote_workouts:
                messagebox.showinfo(
                    "Informazione", 
                    "Nessun allenamento trovato su Garmin Connect.", 
                    parent=self
                )
                return
            
            # Dialog per selezionare gli allenamenti da scaricare
            select_dialog = tk.Toplevel(self)
            select_dialog.title("Seleziona allenamenti da scaricare")
            select_dialog.geometry("600x400")
            select_dialog.transient(self)
            select_dialog.grab_set()
            
            # Label informativa
            ttk.Label(
                select_dialog, 
                text=f"Trovati {len(remote_workouts)} allenamenti su Garmin Connect",
                style="Heading.TLabel"
            ).pack(pady=(10, 0))
            
            ttk.Label(
                select_dialog, 
                text="Seleziona gli allenamenti da scaricare:",
                style="Instructions.TLabel"
            ).pack(pady=(0, 10))
            
            # Frame per la lista
            list_frame = ttk.Frame(select_dialog)
            list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # Crea la lista con checkbox
            columns = ("select", "name", "sport", "created")
            tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="none")
            
            # Definisci le intestazioni
            tree.heading("select", text="")
            tree.heading("name", text="Nome")
            tree.heading("sport", text="Sport")
            tree.heading("created", text="Data creazione")
            
            # Larghezze colonne
            tree.column("select", width=30, stretch=False)
            tree.column("name", width=300)
            tree.column("sport", width=100)
            tree.column("created", width=150)
            
            # Scrollbar
            scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            # Pack
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Dizionario per tenere traccia delle selezioni
            selected = {}
            
            # Funzione per invertire la selezione
            def toggle_selection(event):
                item = tree.identify_row(event.y)
                if item:
                    workout_id = tree.item(item, "tags")[0]  # Usa i tag per memorizzare l'ID
                    selected[workout_id] = not selected.get(workout_id, False)
                    
                    # Aggiorna il segno di spunta
                    current_values = list(tree.item(item, "values"))
                    current_values[0] = "✓" if selected[workout_id] else ""
                    tree.item(item, values=current_values)
            
            # Associa l'evento di click
            tree.bind("<ButtonRelease-1>", toggle_selection)
            
            # Aggiungi gli allenamenti
            for wo in remote_workouts:
                workout_id = wo["workoutId"]
                name = wo["workoutName"]
                sport = wo.get("sportType", {}).get("sportTypeKey", "unknown")
                
                # Formatta il tipo di sport
                sport_display = sport.capitalize()
                
                # Data di creazione
                created_date = wo.get("createdDate", "")
                if created_date:
                    try:
                        # Convert timestamp to date
                        created_date = datetime.datetime.fromtimestamp(created_date / 1000.0).strftime('%Y-%m-%d')
                    except:
                        pass
                
                # Inizialmente non selezionato
                selected[workout_id] = False
                
                # Aggiungi alla lista
                tree.insert("", "end", values=("", name, sport_display, created_date), tags=(workout_id,))
            
            # Pulsanti per selezionare/deselezionare tutti
            select_buttons = ttk.Frame(select_dialog)
            select_buttons.pack(fill=tk.X, padx=10, pady=5)
            
            def select_all():
                for item in tree.get_children():
                    workout_id = tree.item(item, "tags")[0]
                    selected[workout_id] = True
                    
                    # Aggiorna il segno di spunta
                    current_values = list(tree.item(item, "values"))
                    current_values[0] = "✓"
                    tree.item(item, values=current_values)
            
            def select_none():
                for item in tree.get_children():
                    workout_id = tree.item(item, "tags")[0]
                    selected[workout_id] = False
                    
                    # Aggiorna il segno di spunta
                    current_values = list(tree.item(item, "values"))
                    current_values[0] = ""
                    tree.item(item, values=current_values)
            
            ttk.Button(select_buttons, text="Seleziona tutti", command=select_all).pack(side=tk.LEFT, padx=5)
            ttk.Button(select_buttons, text="Deseleziona tutti", command=select_none).pack(side=tk.LEFT, padx=5)
            
            # Pulsanti OK/Cancel
            button_frame = ttk.Frame(select_dialog)
            button_frame.pack(fill=tk.X, padx=10, pady=10)
            
            # Variabile per memorizzare il risultato
            result = {"confirmed": False, "selected": {}}
            
            def on_ok():
                result["confirmed"] = True
                result["selected"] = selected.copy()
                select_dialog.destroy()
            
            def on_cancel():
                select_dialog.destroy()
            
            ttk.Button(
                button_frame, 
                text="Scarica selezionati", 
                command=on_ok,
                style="Success.TButton"
            ).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(
                button_frame, 
                text="Annulla", 
                command=on_cancel
            ).pack(side=tk.LEFT, padx=5)
            
            # Attendi la chiusura del dialog
            self.wait_window(select_dialog)
            
            # Se l'utente ha annullato o non ha selezionato nulla
            if not result["confirmed"]:
                return
            
            # Conta quanti allenamenti sono stati selezionati
            selected_workouts = [wid for wid, sel in result["selected"].items() if sel]
            
            if not selected_workouts:
                messagebox.showinfo(
                    "Informazione", 
                    "Nessun allenamento selezionato.", 
                    parent=self
                )
                return
            
            # Conferma
            if not messagebox.askyesno(
                "Conferma", 
                f"Stai per scaricare {len(selected_workouts)} allenamenti da Garmin Connect. Continuare?", 
                parent=self
            ):
                return
            
            # Crea un thread separato per il download
            threading.Thread(
                target=self._download_workouts_thread,
                args=(selected_workouts, remote_workouts),
                daemon=True
            ).start()
        
        except Exception as e:
            logging.error(f"Errore nel download degli allenamenti: {str(e)}")
            messagebox.showerror(
                "Errore", 
                f"Si è verificato un errore durante il download degli allenamenti: {str(e)}", 
                parent=self
            )
    
    def _download_workouts_thread(self, selected_workouts, remote_workouts):
        """
        Thread separato per il download degli allenamenti da Garmin Connect.
        
        Args:
            selected_workouts: Lista degli ID degli allenamenti da scaricare
            remote_workouts: Lista completa degli allenamenti remoti
        """
        try:
            # Crea un dizionario ID -> nome per gli allenamenti remoti
            remote_map = {}
            for workout in remote_workouts:
                remote_map[workout["workoutId"]] = workout
            
            # Mostra una finestra di progresso
            self.after(0, lambda: self._show_progress_dialog(selected_workouts))
            
            # Conta successi/errori
            self.success_count = 0
            self.error_count = 0
            
            # Per ogni allenamento selezionato
            for i, workout_id in enumerate(selected_workouts):
                # Nome dell'allenamento
                name = remote_map.get(workout_id, {}).get("workoutName", f"Allenamento {workout_id}")
                
                try:
                    # Aggiorna lo stato
                    self.after(0, lambda: self._update_progress(i + 1, len(selected_workouts), name))
                    
                    # Ottieni i dettagli dell'allenamento
                    workout_detail = self.garmin_client.get_workout(workout_id)
                    
                    # Converti in formato interno
                    workout = self._convert_garmin_to_internal(workout_detail)
                    
                    # Aggiungi alla lista degli allenamenti
                    if workout:
                        # Aggiungi l'allenamento alla lista
                        self.workouts.append(workout)
                        
                        # Memorizza l'ID dell'allenamento
                        self.workout_ids[workout.workout_name] = workout_id
                        
                        self.success_count += 1
                
                except Exception as e:
                    logging.error(f"Errore nel download dell'allenamento '{name}': {str(e)}")
                    self.error_count += 1
            
            # Chiudi la finestra di progresso
            self.after(0, self._close_progress)
            
            # Aggiorna la lista degli allenamenti
            self.after(0, self.update_workouts_list)
            
            # Mostra il risultato
            if self.error_count == 0:
                self.after(0, lambda: messagebox.showinfo(
                    "Completato", 
                    f"Scaricati {self.success_count} allenamenti da Garmin Connect.", 
                    parent=self
                ))
            else:
                self.after(0, lambda: messagebox.showwarning(
                    "Completato con errori", 
                    f"Scaricati {self.success_count} allenamenti da Garmin Connect.\n"
                    f"Si sono verificati {self.error_count} errori. Controlla il log per i dettagli.", 
                    parent=self
                ))
        
        except Exception as e:
            # Chiudi la finestra di progresso
            self.after(0, self._close_progress)
            
            # Mostra errore
            self.after(0, lambda: messagebox.showerror(
                "Errore", 
                f"Si è verificato un errore durante il download degli allenamenti: {str(e)}", 
                parent=self
            ))
    
    def _convert_garmin_to_internal(self, garmin_workout):
        """
        Converte un allenamento dal formato Garmin al formato interno.
        
        Args:
            garmin_workout: Allenamento nel formato Garmin
            
        Returns:
            Workout: Allenamento nel formato interno
        """
        try:
            # Estrai le informazioni di base
            name = garmin_workout.get("workoutName", "Allenamento sconosciuto")
            description = garmin_workout.get("description", "")
            sport_type = garmin_workout.get("sportType", {}).get("sportTypeKey", "running")
            
            # Crea un nuovo allenamento
            workout = Workout(sport_type, name, description)
            
            # Estrai i passi
            for segment in garmin_workout.get("workoutSegments", []):
                for step in segment.get("workoutSteps", []):
                    self._convert_garmin_step(step, workout)
            
            return workout
        
        except Exception as e:
            logging.error(f"Errore nella conversione dell'allenamento: {str(e)}")
            return None
    
    def _convert_garmin_step(self, garmin_step, workout, parent_step=None):
        """
        Converte un passo dal formato Garmin al formato interno.
        
        Args:
            garmin_step: Passo nel formato Garmin
            workout: Allenamento a cui aggiungere il passo
            parent_step: Passo genitore per gli step di ripetizione (opzionale)
            
        Returns:
            WorkoutStep: Passo nel formato interno
        """
        try:
            # Estrai le informazioni di base
            step_order = garmin_step.get("stepOrder", 0)
            step_type_key = garmin_step.get("stepType", {}).get("stepTypeKey", "other")
            
            # Descrizione
            description = garmin_step.get("description", "")
            
            # Condizione di fine
            end_condition_key = garmin_step.get("endCondition", {}).get("conditionTypeKey", "lap.button")
            end_condition_value = garmin_step.get("endConditionValue")
            
            # Target
            target_type_key = garmin_step.get("targetType", {}).get("workoutTargetTypeKey", "no.target")
            target_value_one = garmin_step.get("targetValueOne")
            target_value_two = garmin_step.get("targetValueTwo")
            zone_number = garmin_step.get("zoneNumber")
            
            # Crea il target
            target = Target(target_type_key, target_value_one, target_value_two, zone_number)
            
            # Se è un gruppo di ripetizioni
            if garmin_step.get("type") == "RepeatGroupDTO":
                # Crea il passo di ripetizione
                repeat_step = WorkoutStep(
                    step_order,
                    "repeat",
                    description,
                    "iterations",
                    garmin_step.get("numberOfIterations", 1),
                    Target()
                )
                
                # Aggiungi i sottopassi
                for substep in garmin_step.get("workoutSteps", []):
                    self._convert_garmin_step(substep, workout, repeat_step)
                
                # Aggiungi il passo di ripetizione all'allenamento
                if parent_step:
                    parent_step.add_step(repeat_step)
                else:
                    workout.add_step(repeat_step)
                
                return repeat_step
            
            # Passo normale
            else:
                # Gestisci il valore della condizione di fine
                if end_condition_key == "time" and isinstance(end_condition_value, (int, float)):
                    # Converti secondi in formato mm:ss o hh:mm:ss
                    if end_condition_value < 60:
                        end_condition_value = f"{end_condition_value}s"
                    elif end_condition_value < 3600:
                        minutes = end_condition_value // 60
                        seconds = end_condition_value % 60
                        if seconds == 0:
                            end_condition_value = f"{minutes}min"
                        else:
                            end_condition_value = f"{minutes}:{seconds:02d}"
                    else:
                        hours = end_condition_value // 3600
                        minutes = (end_condition_value % 3600) // 60
                        seconds = end_condition_value % 60
                        end_condition_value = f"{hours}:{minutes:02d}:{seconds:02d}"
                
                elif end_condition_key == "distance" and isinstance(end_condition_value, (int, float)):
                    # Converti metri in formato Xkm o Xm
                    if end_condition_value >= 1000:
                        km = end_condition_value / 1000
                        end_condition_value = f"{km}km"
                    else:
                        end_condition_value = f"{int(end_condition_value)}m"
                
                # Crea il passo
                step = WorkoutStep(
                    step_order,
                    step_type_key,
                    description,
                    end_condition_key,
                    end_condition_value,
                    target
                )
                
                # Aggiungi il passo all'allenamento o al passo genitore
                if parent_step:
                    parent_step.add_step(step)
                else:
                    workout.add_step(step)
                
                return step
        
        except Exception as e:
            logging.error(f"Errore nella conversione del passo: {str(e)}")
            return None
    
    def refresh_data(self):
        """Aggiorna i dati dagli allenamenti locali."""
        # Aggiorna la lista degli allenamenti
        self.update_workouts_list()
    
    def on_login(self, client):
        """
        Gestisce l'evento di login completato.
        
        Args:
            client: Istanza di GarminClient con login effettuato
        """
        self.garmin_client = client
        
        # Scarica automaticamente gli allenamenti
        threading.Thread(target=self._load_initial_workouts, daemon=True).start()
    

    def _load_initial_workouts(self):
            """Carica automaticamente gli allenamenti iniziali da Garmin Connect."""
            try:
                # Ottieni la lista degli allenamenti
                remote_workouts = self.garmin_client.list_workouts()
                
                # Verifica se ci sono allenamenti
                if not remote_workouts:
                    self.after(0, lambda: self.controller.set_status("Nessun allenamento trovato su Garmin Connect."))
                    return
                
                # Allenamenti a cui siamo interessati (limita a massimo 10 per velocizzare il caricamento iniziale)
                selected_workouts = remote_workouts[:10]
                
                # Conta successi/errori
                success_count = 0
                error_count = 0
                
                # Imposta lo stato
                self.after(0, lambda: self.controller.set_status("Caricamento iniziale degli allenamenti da Garmin Connect..."))
                
                # Per ogni allenamento
                for workout in selected_workouts:
                    try:
                        # Ottieni l'ID dell'allenamento
                        workout_id = workout.get("workoutId")
                        
                        if not workout_id:
                            continue
                        
                        # Ottieni i dettagli dell'allenamento
                        workout_detail = self.garmin_client.get_workout(workout_id)
                        
                        # Converti in formato interno
                        internal_workout = self._convert_garmin_to_internal(workout_detail)
                        
                        if internal_workout:
                            # Aggiungi l'allenamento alla lista
                            self.workouts.append(internal_workout)
                            
                            # Memorizza l'ID dell'allenamento
                            self.workout_ids[internal_workout.workout_name] = workout_id
                            
                            success_count += 1
                    
                    except Exception as e:
                        logging.error(f"Errore nel caricamento dell'allenamento {workout.get('workoutName', 'sconosciuto')}: {str(e)}")
                        error_count += 1
                
                # Aggiorna la lista degli allenamenti
                self.after(0, self.update_workouts_list)
                
                # Aggiorna lo stato
                if success_count > 0:
                    self.after(0, lambda: self.controller.set_status(
                        f"Caricati {success_count} allenamenti da Garmin Connect"
                    ))
                else:
                    self.after(0, lambda: self.controller.set_status(
                        "Nessun allenamento caricato da Garmin Connect"
                    ))
            
            except Exception as e:
                logging.error(f"Errore nel caricamento degli allenamenti iniziali: {str(e)}")
                self.after(0, lambda: self.controller.set_status(
                    f"Errore nel caricamento degli allenamenti: {str(e)}"
                ))

    def _configure_treeview_tags(self):
        """Configura i tag per la formattazione della treeview."""
        style = ttk.Style()
        for sport_type, color in self.sport_colors.items():
            style.configure(f"Treeview.{sport_type}.Row", background=color)
            self.workout_tree.tag_configure(sport_type, background=color)
        
        for step_type, color in self.step_colors.items():
            self.steps_tree.tag_configure(step_type, background=color)

    def _configure_drag_and_drop(self):
        """Configura il drag and drop per la treeview."""
        self.workout_tree.bind("<ButtonPress-1>", self.on_workout_tree_press)
        self.workout_tree.bind("<B1-Motion>", self.on_workout_tree_motion)
        self.workout_tree.bind("<ButtonRelease-1>", self.on_workout_tree_release)
        
        self.drag_data = {"item": None, "index": -1}

    def on_workout_tree_press(self, event):
        """Gestisce il click sulla treeview degli allenamenti."""
        # Identifica l'item cliccato
        item = self.workout_tree.identify_row(event.y)
        if not item:
            return
        
        # Seleziona l'item
        self.workout_tree.selection_set(item)
        
        # Memorizza l'item e l'indice per il drag and drop
        self.drag_data["item"] = item
        self.drag_data["index"] = self.workout_tree.index(item)

    def on_workout_tree_motion(self, event):
        """Gestisce il movimento del mouse con pulsante premuto nella treeview degli allenamenti."""
        # Verifica che ci sia un item selezionato
        if not self.drag_data["item"]:
            return
        
        # Aggiorna il cursore per indicare il drag and drop
        self.workout_tree.config(cursor="exchange")

    def on_workout_tree_release(self, event):
        """Gestisce il rilascio del pulsante del mouse nella treeview degli allenamenti."""
        # Verifica che ci sia un item selezionato
        if not self.drag_data["item"]:
            return
        
        # Identifica l'item su cui è stato rilasciato
        target_item = self.workout_tree.identify_row(event.y)
        
        # Verifica che sia stato rilasciato su un item valido e diverso dall'item di origine
        if target_item and target_item != self.drag_data["item"]:
            # Ottieni gli indici
            source_index = self.drag_data["index"]
            target_index = self.workout_tree.index(target_item)
            
            # Sposta l'allenamento nella lista
            workouts = self.get_filtered_workouts()
            if 0 <= source_index < len(workouts) and 0 <= target_index < len(workouts):
                # Ottieni gli allenamenti
                source_workout = workouts[source_index]
                
                # Trova gli indici reali nella lista completa
                source_real_index = self.workouts.index(source_workout)
                
                # Rimuovi l'allenamento dalla posizione originale
                self.workouts.pop(source_real_index)
                
                # Trova la nuova posizione
                if target_index < source_index:
                    # Se l'allenamento viene spostato verso l'alto
                    target_workout = workouts[target_index]
                    target_real_index = self.workouts.index(target_workout)
                    self.workouts.insert(target_real_index, source_workout)
                else:
                    # Se l'allenamento viene spostato verso il basso
                    target_workout = workouts[target_index]
                    target_real_index = self.workouts.index(target_workout)
                    self.workouts.insert(target_real_index + 1, source_workout)
                
                # Aggiorna la lista
                self.update_workouts_list()
                
                # Seleziona l'item spostato
                for i, workout in enumerate(self.get_filtered_workouts()):
                    if workout == source_workout:
                        item = self.workout_tree.get_children()[i]
                        self.workout_tree.selection_set(item)
                        self.workout_tree.see(item)
                        break
        
        # Ripristina il cursore
        self.workout_tree.config(cursor="")
        
        # Resetta i dati di drag and drop
        self.drag_data = {"item": None, "index": -1}