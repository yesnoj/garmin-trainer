#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Definizione delle classi per gli allenamenti supportati dall'applicazione.
Estende la classe Workout originale per supportare più tipi di sport.
"""

# Tipi di sport supportati
SPORT_TYPES = {
    "running": 1,
    "cycling": 2,
    "swimming": 5,
    "strength_training": 3,
    "cardio": 9,
    "flexibility_training": 26,
    "other": 4
}

# Tipi di passo
STEP_TYPES = {
    "warmup": 1, 
    "cooldown": 2, 
    "interval": 3, 
    "recovery": 4, 
    "rest": 5, 
    "repeat": 6, 
    "other": 7
}

# Condizioni di fine
END_CONDITIONS = {
    "lap.button": 1,
    "time": 2,
    "distance": 3,
    "calories": 4,
    "heart.rate": 5,
    "power": 6,
    "iterations": 7,
    "cadence": 12
}

# Tipi di target
TARGET_TYPES = {
    "no.target": 1,
    "power.zone": 2,
    "cadence.zone": 3,
    "heart.rate.zone": 4,
    "speed.zone": 5,
    "pace.zone": 6,
    "custom": 7
}

class Workout:
    """Classe che rappresenta un allenamento per qualsiasi tipo di sport"""
    
    def __init__(self, sport_type, name, description=None):
        """
        Inizializza un nuovo allenamento.
        
        Args:
            sport_type: Tipo di sport (chiave da SPORT_TYPES)
            name: Nome dell'allenamento
            description: Descrizione opzionale dell'allenamento
        """
        self.sport_type = sport_type
        self.workout_name = name
        self.description = description
        self.workout_steps = []
        self.scheduled_date = None

    def add_step(self, step):
        """
        Aggiunge un passo all'allenamento.
        
        Args:
            step: Oggetto WorkoutStep da aggiungere
        """
        if step.order == 0:
            step.order = len(self.workout_steps) + 1
        self.workout_steps.append(step)

    def dist_to_time(self):
        """
        Converte i passi con condizione di fine in distanza a condizione di fine in tempo.
        Utile per allenamenti indoor (tapis roulant, rulli, ecc.).
        """
        for ws in self.workout_steps:
            ws.dist_to_time()

    def garminconnect_json(self):
        """
        Genera la rappresentazione JSON per l'API di Garmin Connect.
        
        Returns:
            dict: Rappresentazione JSON dell'allenamento
        """
        # Verifica che il tipo di sport sia supportato
        if self.sport_type not in SPORT_TYPES:
            raise ValueError(f"Tipo di sport non supportato: {self.sport_type}")
            
        return {
            "sportType": {
                "sportTypeId": SPORT_TYPES[self.sport_type],
                "sportTypeKey": self.sport_type,
            },
            "workoutName": self.workout_name,
            "description": self.description,
            "workoutSegments": [
                {
                    "segmentOrder": 1,
                    "sportType": {
                        "sportTypeId": SPORT_TYPES[self.sport_type],
                        "sportTypeKey": self.sport_type,
                    },
                    "workoutSteps": [step.garminconnect_json() for step in self.workout_steps],
                }
            ],
        }
    
    def set_scheduled_date(self, date):
        """
        Imposta la data pianificata per l'allenamento.
        
        Args:
            date: Data pianificata (stringa YYYY-MM-DD o oggetto datetime)
        """
        if isinstance(date, str):
            self.scheduled_date = date
        else:
            self.scheduled_date = date.strftime('%Y-%m-%d')
            
    def get_scheduled_date(self):
        """
        Ottiene la data pianificata.
        
        Returns:
            str: Data pianificata in formato YYYY-MM-DD o None
        """
        return self.scheduled_date
    
    def get_total_distance(self):
        """
        Calcola la distanza totale dell'allenamento in metri.
        
        Returns:
            float: Distanza totale in metri o None se non calcolabile
        """
        total = 0
        has_distance = False
        
        for step in self.workout_steps:
            step_distance = step.get_distance()
            if step_distance is not None:
                total += step_distance
                has_distance = True
        
        return total if has_distance else None
    
    def get_total_duration(self):
        """
        Calcola la durata totale dell'allenamento in secondi.
        
        Returns:
            int: Durata totale in secondi o None se non calcolabile
        """
        total = 0
        has_duration = False
        
        for step in self.workout_steps:
            step_duration = step.get_duration()
            if step_duration is not None:
                total += step_duration
                has_duration = True
        
        return total if has_duration else None
    
    def get_step_count(self):
        """
        Ottiene il numero di passi nell'allenamento.
        
        Returns:
            int: Numero di passi
        """
        count = 0
        for step in self.workout_steps:
            if step.step_type == 'repeat':
                count += len(step.workout_steps) * step.end_condition_value
            else:
                count += 1
        return count

class WorkoutStep:
    """Classe che rappresenta un passo di un allenamento"""
    
    def __init__(
        self,
        order,
        step_type,
        description='',
        end_condition="lap.button",
        end_condition_value=None,
        target=None,
    ):
        """
        Inizializza un nuovo passo di allenamento.
        
        Args:
            order: Ordine del passo nell'allenamento
            step_type: Tipo di passo (chiave da STEP_TYPES)
            description: Descrizione del passo
            end_condition: Condizione di fine (chiave da END_CONDITIONS)
            end_condition_value: Valore per la condizione di fine
            target: Oggetto Target o None se nessun target
        """
        self.order = order
        self.step_type = step_type
        self.description = description
        self.end_condition = end_condition
        self.end_condition_value = end_condition_value
        self.target = target or Target()
        self.child_step_id = 1 if self.step_type == 'repeat' else None
        self.workout_steps = []

    def add_step(self, step):
        """
        Aggiunge un sotto-passo (per passi di tipo repeat).
        
        Args:
            step: Oggetto WorkoutStep da aggiungere come sotto-passo
        """
        step.child_step_id = self.child_step_id
        if step.order == 0:
            step.order = len(self.workout_steps) + 1
        self.workout_steps.append(step)

    def end_condition_unit(self):
        """
        Determina l'unità di misura per la condizione di fine.
        
        Returns:
            dict: Informazioni sull'unità di misura o None
        """
        if self.end_condition == 'distance':
            if isinstance(self.end_condition_value, str) and "km" in self.end_condition_value:
                return {"unitKey": "kilometer"}
            else:
                return {"unitKey": "meter"}
        elif self.end_condition == 'time':
            return {"unitKey": "second"}
        else:
            return None

    def parsed_end_condition_value(self):
        """
        Analizza e converte il valore della condizione di fine nel formato richiesto.
        
        Returns:
            int/float/str: Valore convertito
        """
        # Gestione distanza
        if self.end_condition == 'distance':
            if isinstance(self.end_condition_value, str):
                if "km" in self.end_condition_value:
                    return int(float(self.end_condition_value.replace("km", "")) * 1000)
                elif "m" in self.end_condition_value:
                    return int(float(self.end_condition_value.replace("m", "")))
            return self.end_condition_value
        
        # Gestione tempo
        elif self.end_condition == 'time':
            if isinstance(self.end_condition_value, str) and ":" in self.end_condition_value:
                parts = self.end_condition_value.split(":")
                if len(parts) == 2:  # mm:ss
                    m, s = [int(x) for x in parts]
                    return m * 60 + s
                elif len(parts) == 3:  # hh:mm:ss
                    h, m, s = [int(x) for x in parts]
                    return h * 3600 + m * 60 + s
            elif isinstance(self.end_condition_value, str) and "min" in self.end_condition_value:
                return int(float(self.end_condition_value.replace("min", "")) * 60)
            elif isinstance(self.end_condition_value, str) and "s" in self.end_condition_value:
                return int(float(self.end_condition_value.replace("s", "")))
            
        # Default
        return self.end_condition_value

    def dist_to_time(self):
        """
        Converte la condizione di fine da distanza a tempo quando possibile.
        Utile per allenamenti indoor.
        """
        if self.end_condition == 'distance' and self.target.target == 'pace.zone':
            # Calcola il ritmo medio (m/s)
            target_pace_ms = (self.target.from_value + self.target.to_value) / 2
            # Converti distanza in metri a secondi stimati
            dist_value = self.parsed_end_condition_value()
            end_condition_sec = int(dist_value / target_pace_ms)
            # Arrotonda ai 10 secondi più vicini
            end_condition_sec = int(round(end_condition_sec/10, 0) * 10)
            # Aggiorna la condizione di fine
            self.end_condition = 'time'
            self.end_condition_value = f'{end_condition_sec:.0f}'
        elif self.end_condition == 'iterations' and len(self.workout_steps) > 0:
            for ws in self.workout_steps:
                ws.dist_to_time()

    def garminconnect_json(self):
        """
        Genera la rappresentazione JSON per l'API di Garmin Connect.
        
        Returns:
            dict: Rappresentazione JSON del passo
        """
        base_json = {
            "type": 'RepeatGroupDTO' if self.step_type == 'repeat' else 'ExecutableStepDTO',
            "stepId": None,
            "stepOrder": self.order,
            "childStepId": self.child_step_id,
            "stepType": {
                "stepTypeId": STEP_TYPES[self.step_type],
                "stepTypeKey": self.step_type,
            },
            "endCondition": {
                "conditionTypeKey": self.end_condition,
                "conditionTypeId": END_CONDITIONS[self.end_condition],
            },
            "endConditionValue": self.parsed_end_condition_value(),
        }

        # Aggiungi i sotto-passi per le ripetizioni
        if len(self.workout_steps) > 0:
            base_json["workoutSteps"] = [step.garminconnect_json() for step in self.workout_steps]

        # Gestione specifica per i passi di tipo repeat
        if self.step_type == 'repeat':
            base_json['smartRepeat'] = True
            base_json['numberOfIterations'] = self.end_condition_value
        else:
            # Aggiungi dettagli specifici per i passi normali
            base_json.update({
                "description": self.description,
                "preferredEndConditionUnit": self.end_condition_unit(),
                "endConditionCompare": None,
                "endConditionZone": None,
                **self.target.garminconnect_json(),
            })
            
        return base_json
    
    def get_distance(self):
        """
        Calcola la distanza del passo in metri, se applicabile.
        
        Returns:
            float: Distanza in metri o None
        """
        if self.end_condition == 'distance':
            return float(self.parsed_end_condition_value())
        elif self.step_type == 'repeat' and self.end_condition == 'iterations':
            total = 0
            has_distance = False
            for substep in self.workout_steps:
                substep_distance = substep.get_distance()
                if substep_distance is not None:
                    total += substep_distance
                    has_distance = True
            if has_distance:
                return total * self.end_condition_value
        return None
    
    def get_duration(self):
        """
        Calcola la durata del passo in secondi, se applicabile.
        
        Returns:
            int: Durata in secondi o None
        """
        if self.end_condition == 'time':
            return int(self.parsed_end_condition_value())
        elif self.step_type == 'repeat' and self.end_condition == 'iterations':
            total = 0
            has_duration = False
            for substep in self.workout_steps:
                substep_duration = substep.get_duration()
                if substep_duration is not None:
                    total += substep_duration
                    has_duration = True
            if has_duration:
                return total * self.end_condition_value
        return None
    
    def format_end_condition(self):
        """
        Formatta la condizione di fine in un formato leggibile.
        
        Returns:
            str: Condizione di fine formattata
        """
        if self.end_condition == 'lap.button':
            return "Pulsante lap"
        elif self.end_condition == 'distance':
            dist = self.parsed_end_condition_value()
            if dist >= 1000:
                return f"{dist/1000:.2f} km"
            else:
                return f"{dist} m"
        elif self.end_condition == 'time':
            sec = self.parsed_end_condition_value()
            if sec >= 3600:
                h = sec // 3600
                m = (sec % 3600) // 60
                s = sec % 60
                return f"{h}:{m:02d}:{s:02d}"
            else:
                m = sec // 60
                s = sec % 60
                return f"{m}:{s:02d}"
        elif self.end_condition == 'iterations':
            return f"{self.end_condition_value} ripetizioni"
        return str(self.end_condition)

class Target:
    """Classe che rappresenta un target per un passo di allenamento"""
    
    def __init__(self, target="no.target", to_value=None, from_value=None, zone=None):
        """
        Inizializza un nuovo target.
        
        Args:
            target: Tipo di target (chiave da TARGET_TYPES)
            to_value: Valore superiore del target
            from_value: Valore inferiore del target
            zone: Numero di zona (se applicabile)
        """
        self.target = target
        self.to_value = to_value
        self.from_value = from_value
        self.zone = zone
        self.zone_name = None

    def garminconnect_json(self):
        """
        Genera la rappresentazione JSON per l'API di Garmin Connect.
        
        Returns:
            dict: Rappresentazione JSON del target
        """
        return {
            "targetType": {
                "workoutTargetTypeId": TARGET_TYPES[self.target],
                "workoutTargetTypeKey": self.target,
            },
            "targetValueOne": self.to_value,
            "targetValueTwo": self.from_value,
            "zoneNumber": self.zone,
        }
    
    def format_target(self):
        """
        Formatta il target in un formato leggibile.
        
        Returns:
            str: Target formattato
        """
        if self.target == "no.target":
            return "Nessun target"
        elif self.target == "pace.zone":
            if self.zone is not None:
                return f"Zona ritmo {self.zone}"
            elif self.from_value is not None and self.to_value is not None:
                # Converti m/s a min/km
                from_pace = 1000 / (self.from_value * 60)  # min/km
                to_pace = 1000 / (self.to_value * 60)  # min/km
                from_min = int(from_pace)
                from_sec = int((from_pace - from_min) * 60)
                to_min = int(to_pace)
                to_sec = int((to_pace - to_min) * 60)
                return f"{from_min}:{from_sec:02d}-{to_min}:{to_sec:02d} min/km"
            return "Target ritmo personalizzato"
        elif self.target == "heart.rate.zone":
            if self.zone is not None:
                return f"Zona FC {self.zone}"
            elif self.from_value is not None and self.to_value is not None:
                return f"{self.from_value}-{self.to_value} bpm"
            return "Target FC personalizzato"
        elif self.target == "power.zone":
            if self.zone is not None:
                return f"Zona potenza {self.zone}"
            elif self.from_value is not None and self.to_value is not None:
                return f"{self.from_value}-{self.to_value} W"
            return "Target potenza personalizzato"
        elif self.target == "speed.zone":
            if self.zone is not None:
                return f"Zona velocità {self.zone}"
            elif self.from_value is not None and self.to_value is not None:
                # Converti m/s a km/h
                from_speed = self.from_value * 3.6
                to_speed = self.to_value * 3.6
                return f"{from_speed:.1f}-{to_speed:.1f} km/h"
            return "Target velocità personalizzato"
        elif self.target == "cadence.zone":
            if self.from_value is not None and self.to_value is not None:
                return f"{self.from_value}-{self.to_value} rpm"
            return "Target cadenza personalizzato"
        return str(self.target)