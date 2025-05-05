#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dialog per la creazione e modifica di passi di ripetizione.
"""

import tkinter as tk
from tkinter import ttk
import copy

from ...core.workout import STEP_TYPES
from .step_dialog import StepDialog

class RepeatDialog:
    """Dialog per creare o modificare passi di ripetizione."""
    
    def __init__(self, parent, iterations=None, steps=None, sport_type="running"):
        """
        Inizializza il dialog.
        
        Args:
            parent: Widget genitore
            iterations: Numero di ripetizioni (opzionale)
            steps: Lista di passi della ripetizione (opzionale)
            sport_type: Tipo di sport per adattare le opzioni
        """
        self.parent = parent
        self.iterations = iterations or 3
        self.steps = copy.deepcopy(steps) or []
        self.sport_type = sport_type
        self.result = None
        
        # Crea il dialog
        self.create_dialog()
    
    def create_dialog(self):
        """Crea il dialog."""
        # Finestra top-level
        self.top = tk.Toplevel(self.parent)
        self.top.title("Ripetizioni")
        self.top.geometry("500x500")
        self.top.transient(self.parent)
        self.top.grab_set()
        
        # Imposta lo stato modale
        self.top.focus_set()
        
        # Frame principale con padding
        main_frame = ttk.Frame(self.top, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titolo
        title_label = ttk.Label(
            main_frame, 
            text="Configurazione ripetizioni", 
            style="Heading.TLabel"
        )
        title_label.pack(pady=(0, 20))
        
        # Numero di ripetizioni
        repeat_frame = ttk.Frame(main_frame)
        repeat_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(repeat_frame, text="Numero di ripetizioni:").pack(side=tk.LEFT)
        
        self.iterations_var = tk.IntVar(value=self.iterations)
        iterations_spinbox = ttk.Spinbox(
            repeat_frame, 
            from_=1, 
            to=50, 
            textvariable=self.iterations_var,
            width=5
        )
        iterations_spinbox.pack(side=tk.LEFT, padx=5)
        
        # Passi della ripetizione
        steps_frame = ttk.LabelFrame(main_frame, text="Passi della ripetizione")
        steps_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Toolbar per i passi
        steps_toolbar = ttk.Frame(steps_frame)
        steps_toolbar.pack(fill=tk.X, pady=5)
        
        add_button = ttk.Button(
            steps_toolbar, 
            text="Aggiungi passo", 
            command=self.add_step
        )
        add_button.pack(side=tk.LEFT, padx=5)
        
        edit_button = ttk.Button(
            steps_toolbar, 
            text="Modifica", 
            command=self.edit_step
        )
        edit_button.pack(side=tk.LEFT, padx=5)
        
        delete_button = ttk.Button(
            steps_toolbar, 
            text="Elimina", 
            command=self.delete_step
        )
        delete_button.pack(side=tk.LEFT, padx=5)
        
        move_up_button = ttk.Button(
            steps_toolbar, 
            text="↑", 
            width=2,
            command=self.move_step_up
        )
        move_up_button.pack(side=tk.LEFT, padx=5)
        
        move_down_button = ttk.Button(
            steps_toolbar, 
            text="↓", 
            width=2,
            command=self.move_step_down
        )
        move_down_button.pack(side=tk.LEFT, padx=5)
        
        # Lista dei passi
        steps_list_frame = ttk.Frame(steps_frame)
        steps_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        columns = ("index", "type", "details")
        self.steps_tree = ttk.Treeview(steps_list_frame, columns=columns, show="headings", 
                                      selectmode="browse")
        
        # Definisci le intestazioni
        self.steps_tree.heading("index", text="#")
        self.steps_tree.heading("type", text="Tipo")
        self.steps_tree.heading("details", text="Dettagli")
        
        # Definisci le larghezze delle colonne
        self.steps_tree.column("index", width=30)
        self.steps_tree.column("type", width=100)
        self.steps_tree.column("details", width=330)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(steps_list_frame, orient=tk.VERTICAL, 
                               command=self.steps_tree.yview)
        self.steps_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        self.steps_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Eventi
        self.steps_tree.bind("<Double-1>", self.on_double_click)
        
        # Anteprima della ripetizione
        preview_frame = ttk.LabelFrame(main_frame, text="Anteprima")
        preview_frame.pack(fill=tk.X, pady=10)
        
        self.preview_var = tk.StringVar()
        preview_label = ttk.Label(preview_frame, textvariable=self.preview_var, padding=10)
        preview_label.pack(fill=tk.X)
        
        # Pulsanti
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        save_button = ttk.Button(
            button_frame, 
            text="Salva", 
            command=self.on_save,
            style="Success.TButton",
            width=10
        )
        save_button.pack(side=tk.RIGHT, padx=5)
        
        cancel_button = ttk.Button(
            button_frame, 
            text="Annulla", 
            command=self.on_cancel,
            width=10
        )
        cancel_button.pack(side=tk.RIGHT, padx=5)
        
        # Riempi la lista dei passi
        self.update_steps_list()
        
        # Aggiorna l'anteprima
        self.update_preview()
        
        # Binding per aggiornare l'anteprima quando cambia il numero di ripetizioni
        self.iterations_var.trace_add("write", lambda *args: self.update_preview())
        
        # Attendi che il dialog sia completato
        self.top.wait_window()
    
    def update_steps_list(self):
        """Aggiorna la lista dei passi nella treeview."""
        # Cancella tutti gli elementi
        for item in self.steps_tree.get_children():
            self.steps_tree.delete(item)
        
        # Aggiungi i passi
        for i, step in enumerate(self.steps):
            if isinstance(step, dict) and len(step) == 1:
                step_type = list(step.keys())[0]
                step_detail = step[step_type]
                
                self.steps_tree.insert("", "end", values=(i+1, step_type, step_detail))
    
    def add_step(self):
        """Aggiunge un nuovo passo alla ripetizione."""
        # Apri il dialog per configurare il passo
        dialog = StepDialog(self.top, sport_type=self.sport_type)
        
        if dialog.result:
            step_type, step_detail = dialog.result
            
            # Aggiungi il passo alla lista
            self.steps.append({step_type: step_detail})
            
            # Aggiorna la lista e l'anteprima
            self.update_steps_list()
            self.update_preview()
    
    def edit_step(self):
        """Modifica un passo esistente nella ripetizione."""
        selection = self.steps_tree.selection()
        if not selection:
            return
        
        # Ottieni l'indice del passo selezionato
        index = int(self.steps_tree.item(selection[0], "values")[0]) - 1
        
        # Ottieni il passo
        step = self.steps[index]
        
        if isinstance(step, dict) and len(step) == 1:
            step_type = list(step.keys())[0]
            step_detail = step[step_type]
            
            # Apri il dialog per modificare il passo
            dialog = StepDialog(self.top, step_type=step_type, step_detail=step_detail, 
                              sport_type=self.sport_type)
            
            if dialog.result:
                new_type, new_detail = dialog.result
                
                # Aggiorna il passo
                self.steps[index] = {new_type: new_detail}
                
                # Aggiorna la lista e l'anteprima
                self.update_steps_list()
                self.update_preview()
    
    def delete_step(self):
        """Elimina un passo dalla ripetizione."""
        selection = self.steps_tree.selection()
        if not selection:
            return
        
        # Ottieni l'indice del passo selezionato
        index = int(self.steps_tree.item(selection[0], "values")[0]) - 1
        
        # Chiedi conferma
        if tk.messagebox.askyesno(
            "Conferma", 
            "Sei sicuro di voler eliminare questo passo?",
            parent=self.top
        ):
            # Rimuovi il passo
            self.steps.pop(index)
            
            # Aggiorna la lista e l'anteprima
            self.update_steps_list()
            self.update_preview()
    
    def move_step_up(self):
        """Sposta un passo verso l'alto nella lista."""
        selection = self.steps_tree.selection()
        if not selection:
            return
        
        # Ottieni l'indice del passo selezionato
        index = int(self.steps_tree.item(selection[0], "values")[0]) - 1
        
        # Verifica che non sia già in cima
        if index > 0:
            # Scambia i passi
            self.steps[index], self.steps[index-1] = self.steps[index-1], self.steps[index]
            
            # Aggiorna la lista e l'anteprima
            self.update_steps_list()
            self.update_preview()
            
            # Seleziona il passo spostato
            for item in self.steps_tree.get_children():
                if int(self.steps_tree.item(item, "values")[0]) == index:
                    self.steps_tree.selection_set(item)
                    self.steps_tree.see(item)
                    break
    
    def move_step_down(self):
        """Sposta un passo verso il basso nella lista."""
        selection = self.steps_tree.selection()
        if not selection:
            return
        
        # Ottieni l'indice del passo selezionato
        index = int(self.steps_tree.item(selection[0], "values")[0]) - 1
        
        # Verifica che non sia già in fondo
        if index < len(self.steps) - 1:
            # Scambia i passi
            self.steps[index], self.steps[index+1] = self.steps[index+1], self.steps[index]
            
            # Aggiorna la lista e l'anteprima
            self.update_steps_list()
            self.update_preview()
            
            # Seleziona il passo spostato
            for item in self.steps_tree.get_children():
                if int(self.steps_tree.item(item, "values")[0]) == index + 2:
                    self.steps_tree.selection_set(item)
                    self.steps_tree.see(item)
                    break
    
    def on_double_click(self, event):
        """Gestisce il doppio click su un passo."""
        self.edit_step()
    
    def update_preview(self):
        """Aggiorna l'anteprima della ripetizione."""
        iterations = self.iterations_var.get()
        
        if not self.steps:
            preview = f"Ripetizione di {iterations}x (nessun passo definito)"
        else:
            preview = f"Ripetizione di {iterations}x ("
            
            for i, step in enumerate(self.steps):
                if i > 0:
                    preview += ", "
                
                if isinstance(step, dict) and len(step) == 1:
                    step_type = list(step.keys())[0]
                    preview += step_type
            
            preview += ")"
        
        self.preview_var.set(preview)
    
    def on_save(self):
        """Salva le modifiche alla ripetizione."""
        # Validazione dei dati
        iterations = self.iterations_var.get()
        
        if iterations < 1:
            tk.messagebox.showerror(
                "Errore", 
                "Il numero di ripetizioni deve essere almeno 1.",
                parent=self.top
            )
            return
        
        if not self.steps:
            tk.messagebox.showerror(
                "Errore", 
                "Devi aggiungere almeno un passo alla ripetizione.",
                parent=self.top
            )
            return
        
        # Imposta il risultato
        self.result = (iterations, self.steps)
        
        # Chiudi il dialog
        self.top.destroy()
    
    def on_cancel(self):
        """Annulla le modifiche e chiude il dialog."""
        self.result = None
        self.top.destroy()