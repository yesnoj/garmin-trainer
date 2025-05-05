#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Funzioni di utilità per l'applicazione Garmin Trainer.
Basato sul file utils.py originale di garmin-planner, con estensioni.
"""

import re
import datetime
import json
import yaml
import os
import pandas as pd
import logging

def hhmmss_to_seconds(s):
    """
    Converte una stringa di tempo in vari formati in secondi.
    
    Formati supportati:
    - hh:mm:ss (es. "1:00:00", "00:00:30")
    - mm:ss (es. "10:00", "01:30")
    - h (es. "1h")
    - m (es. "2m")
    - s (es. "30s")
    
    Args:
        s: Stringa di tempo da convertire.
        
    Returns:
        int: Tempo equivalente in secondi.
        
    Raises:
        TypeError: Se l'input non è una stringa.
        ValueError: Se la stringa non è in un formato valido.
    """
    if not isinstance(s, str):
        raise TypeError("L'input deve essere una stringa.")
        
    s = s.strip()
    
    # Formato: 1h, 2m, 30s
    if re.compile(r'^(\d+)\s*([hms]?)$').match(s):
        m = re.compile(r'^(\d+)\s*([hms]?)$').match(s)
        amount = int(m.group(1))
        unit = m.group(2)
        
        if unit == 'h':
            return 3600 * amount
        if unit == 'm':
            return 60 * amount
        if unit == 's':
            return amount
        return amount
        
    # Formato: 10min
    elif re.compile(r'^(\d+)\s*min$').match(s):
        m = re.compile(r'^(\d+)\s*min$').match(s)
        return 60 * int(m.group(1))
        
    # Formato: mm:ss o hh:mm:ss
    else:    
        parts = s.split(":")
        if len(parts) == 2:
            try:
                return int(parts[0]) * 60 + int(parts[1])
            except ValueError:
                raise ValueError(f"Durata non valida, deve essere in formato mm:ss: {s}")
        elif len(parts) == 3:
            try:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            except ValueError:
                raise ValueError(f"Durata non valida, deve essere in formato hh:mm:ss: {s}")
        else:
            raise ValueError(f"Durata non valida, deve essere in formato mm:ss o hh:mm:ss: {s}")

def seconds_to_mmss(seconds):
    """
    Converte un tempo in secondi in una stringa in formato mm:ss.
    
    Args:
        seconds: Tempo in secondi (int o float).
        
    Returns:
        str: Stringa che rappresenta il tempo in formato mm:ss (es. "10:00", "01:30").
        
    Raises:
        TypeError: Se l'input non è un numero (int o float).
        ValueError: Se l'input è negativo.
    """
    if not isinstance(seconds, (int, float)):
        raise TypeError("L'input deve essere un numero.")
        
    if seconds < 0:
        raise ValueError("L'input deve essere non negativo.")

    mins = int(seconds / 60)
    secs = int(seconds - mins * 60)
    
    return f"{mins:02}:{secs:02}"

def seconds_to_hhmmss(seconds):
    """
    Converte un tempo in secondi in una stringa in formato hh:mm:ss.
    
    Args:
        seconds: Tempo in secondi (int o float).
        
    Returns:
        str: Stringa che rappresenta il tempo in formato hh:mm:ss.
        
    Raises:
        TypeError: Se l'input non è un numero (int o float).
        ValueError: Se l'input è negativo.
    """
    if not isinstance(seconds, (int, float)):
        raise TypeError("L'input deve essere un numero.")
        
    if seconds < 0:
        raise ValueError("L'input deve essere non negativo.")

    hours = int(seconds / 3600)
    mins = int((seconds % 3600) / 60)
    secs = int(seconds % 60)
    
    return f"{hours:02}:{mins:02}:{secs:02}"

def pace_to_kmph(pace):
    """
    Converte una stringa di ritmo in formato mm:ss in chilometri all'ora (km/h).
    
    Args:
        pace: Stringa di ritmo in formato mm:ss (es. "5:00", "6:30").
        
    Returns:
        float: Velocità equivalente in km/h.
        
    Raises:
        ValueError: Se la stringa di ritmo non è in un formato valido.
    """
    seconds = hhmmss_to_seconds(pace)
    km_h = 60 / (seconds / 60)
    return km_h

def pace_to_ms(pace):
    """
    Converte una stringa di ritmo in formato mm:ss in metri al secondo (m/s).
    
    Args:
        pace: Stringa di ritmo in formato mm:ss (es. "5:00", "6:30").
        
    Returns:
        float: Velocità equivalente in m/s.
        
    Raises:
        ValueError: Se la stringa di ritmo non è in un formato valido.
    """
    return pace_to_kmph(pace) * (1000/3600)

def ms_to_pace(ms):
    """
    Converte una velocità in metri al secondo (m/s) in una stringa di ritmo in mm:ss per km.
    
    Args:
        ms: Velocità in m/s (float).
        
    Returns:
        str: Ritmo in formato mm:ss (es. "5:00", "4:30").
        
    Raises:
        TypeError: Se l'input non è un numero (int o float).
        ValueError: Se l'input è zero o negativo.
    """
    if not isinstance(ms, (int, float)):
        raise TypeError("L'input deve essere un numero.")
        
    if ms <= 0:
        raise ValueError("L'input deve essere un numero positivo.")
    
    seconds_per_km = round(1000 / ms)
    return seconds_to_mmss(seconds_per_km)

def dist_to_m(dist_str):
    """
    Converte una stringa di distanza in vari formati in metri.
    
    Formati supportati:
    - <numero>km (es. "10km", "2.5km")
    - <numero>m (es. "100m", "5000m")
    
    Args:
        dist_str: Stringa di distanza da convertire.
        
    Returns:
        int: Distanza equivalente in metri.
        
    Raises:
        TypeError: Se l'input non è una stringa.
        ValueError: Se la stringa non è in un formato valido.
    """
    if not isinstance(dist_str, str):
        raise TypeError("L'input deve essere una stringa.")
        
    dist_str = dist_str.strip()

    m = re.compile(r'^(\d+(?:\.\d+)?)(km|m)$').match(dist_str)
    if not m:
        raise ValueError(
            "Distanza non valida, deve essere in formato <numero>km o <numero>m"
        )

    value = float(m.group(1))
    unit = m.group(2)

    if unit == 'km':
        return int(value * 1000)
    elif unit == 'm':
        return int(value)
    else:
        raise ValueError(f'Unità "{unit}" non supportata')

def dist_time_to_ms(dist_time):
    """
    Estrae il tempo target da una specifica di distanza e tempo.
    
    Args:
      dist_time: Specifica di distanza e tempo, nel formato "<distanza> in <tempo>" 
                 (es. "3000m in 13:48")

    Returns:
      float: Velocità target in m/s
      
    Raises:
        ValueError: Se l'input non è nel formato corretto.
    """
    m = re.compile('^(.+) in (.+)$').match(dist_time)
    if m:
        ms_time = pace_to_ms(m.group(2).strip())
        m_distance = dist_to_m(m.group(1).strip())
        km_distance = m_distance / 1000
        target_pace = ms_time * km_distance
        return target_pace
    else:
        raise ValueError("L'input deve essere nel formato <distanza> in <tempo>.")

def normalize_pace(orig_pace):
    """
    Normalizza una stringa di ritmo nel formato mm:ss o hh:mm:ss con zero-padding.
    
    Args:
        orig_pace: Stringa di ritmo da normalizzare (es. "4:40", "04:4", "12:4:4").
        
    Returns:
        str: Stringa di ritmo normalizzata in formato mm:ss o hh:mm:ss.
        
    Raises:
        ValueError: Se la stringa di input non è in un formato di ritmo valido.
    """
    m = re.compile(r'^\d{1,2}:\d{1,2}:?\d{0,2}$')
    if m.match(orig_pace):
        parts = [int(part) for part in orig_pace.split(":")]
        # I minuti e i secondi devono essere inferiori a 60
        if parts[len(parts)-1] >= 60 or parts[len(parts)-2] >= 60:
            raise ValueError(f'Formato ritmo non valido: {orig_pace}')

        # Aggiungi zero-padding
        padded = [str(part).zfill(2) for part in parts]
        return ":".join(padded)
    else:
        raise ValueError(f'Formato ritmo non valido: {orig_pace}')

def get_pace_range(orig_pace, margins):
    """
    Calcola un intervallo di ritmo basato su un ritmo originale e margini opzionali.
    
    Args:
        orig_pace: Ritmo originale o intervallo di ritmo (es. "04:40", "04:40-04:00").
        margins: Dizionario con margini 'faster' e 'slower' in formato mm:ss.
                 Se None, non vengono applicati margini.
        
    Returns:
        tuple: Limiti di ritmo lento e veloce in secondi (slow_pace_s, fast_pace_s).
        
    Raises:
        ValueError: Se la stringa di ritmo non è in un formato valido.
    """
    # Gestisci il caso in cui il ritmo fornito è già stato convertito in tuple
    if isinstance(orig_pace, tuple):
        if isinstance(orig_pace[0], str) and isinstance(orig_pace[1], str):
            return orig_pace
        else:
            raise ValueError(f'Formato ritmo non valido: {str(orig_pace)}')

    m = re.compile(r'^(\d{1,2}:\d{1,2})(?:-(\d{1,2}:\d{1,2}))?').match(orig_pace)
    if not m:
        raise ValueError(f'Formato ritmo non valido: {orig_pace}')
    
    # Se è stato fornito un solo ritmo (es. 04:40)
    if not m.group(2):
        orig_pace_s = hhmmss_to_seconds(orig_pace)
        # Se abbiamo margini da aggiungere/sottrarre
        if margins:
            fast_margin_s = hhmmss_to_seconds(margins.get('faster', '0'))
            slow_margin_s = hhmmss_to_seconds(margins.get('slower', '0'))
            fast_pace = seconds_to_mmss(orig_pace_s - fast_margin_s)
            slow_pace = seconds_to_mmss(orig_pace_s + slow_margin_s)
            return (slow_pace, fast_pace)
        # Ritmo singolo e nessun margine. Restituiamo lo stesso ritmo per entrambi i limiti.
        else:
            return (orig_pace_s, orig_pace_s)
    # Se ci sono stati forniti entrambi i ritmi, non servono margini aggiuntivi.
    else:
        pace_1 = m.group(1)
        pace_2 = m.group(2)
        return (pace_1, pace_2)

def format_workout_name(week, session, description):
    """
    Formatta il nome di un allenamento secondo la convenzione W00S00 DESCRIZIONE.
    
    Args:
        week: Numero della settimana (int)
        session: Numero della sessione (int)
        description: Descrizione dell'allenamento (str)
        
    Returns:
        str: Nome dell'allenamento formattato
    """
    return f"W{week:02d}S{session:02d} {description}"

def parse_workout_name(name):
    """
    Analizza un nome di allenamento per estrarre settimana, sessione e descrizione.
    
    Args:
        name: Nome dell'allenamento (str)
        
    Returns:
        tuple: (week, session, description) o (None, None, name) se il formato non è standard
    """
    pattern = r'W(\d{2})S(\d{2})\s+(.+)'
    match = re.match(pattern, name)
    
    if match:
        week = int(match.group(1))
        session = int(match.group(2))
        description = match.group(3)
        return (week, session, description)
    else:
        return (None, None, name)

def save_config(config, filename='config.json'):
    """
    Salva la configurazione in un file JSON.
    
    Args:
        config: Dizionario di configurazione
        filename: Nome del file (default: 'config.json')
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Errore nel salvataggio della configurazione: {str(e)}")

def load_config(filename='config.json'):
    """
    Carica la configurazione da un file JSON.
    
    Args:
        filename: Nome del file (default: 'config.json')
        
    Returns:
        dict: Configurazione caricata o dizionario vuoto in caso di errore
    """
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logging.error(f"Errore nel caricamento della configurazione: {str(e)}")
        return {}

def load_yaml(filename):
    """
    Carica i dati da un file YAML.
    
    Args:
        filename: Nome del file YAML
        
    Returns:
        dict: Dati caricati dal file YAML
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Errore nel caricamento del file YAML: {str(e)}")
        raise

def save_yaml(data, filename):
    """
    Salva i dati in un file YAML.
    
    Args:
        data: Dati da salvare
        filename: Nome del file di destinazione
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
    except Exception as e:
        logging.error(f"Errore nel salvataggio del file YAML: {str(e)}")
        raise

def load_excel(filename):
    """
    Carica i dati da un file Excel.
    
    Args:
        filename: Nome del file Excel
        
    Returns:
        dict: Dati caricati dal file Excel
    """
    try:
        # Legge il foglio di configurazione
        config_df = pd.read_excel(filename, sheet_name='Config')
        config = {}
        
        # Processa i dati di configurazione
        for _, row in config_df.iterrows():
            if pd.notna(row['Chiave']) and pd.notna(row['Valore']):
                config[row['Chiave']] = row['Valore']
        
        # Legge i ritmi, frequenze cardiache e valori di potenza
        paces = {}
        try:
            paces_df = pd.read_excel(filename, sheet_name='Paces')
            for _, row in paces_df.iterrows():
                if pd.notna(row['Nome']) and pd.notna(row['Valore']):
                    paces[row['Nome']] = row['Valore']
        except:
            logging.warning("Foglio 'Paces' non trovato o vuoto.")
        
        heart_rates = {}
        try:
            hr_df = pd.read_excel(filename, sheet_name='HeartRates')
            for _, row in hr_df.iterrows():
                if pd.notna(row['Nome']) and pd.notna(row['Valore']):
                    heart_rates[row['Nome']] = row['Valore']
        except:
            logging.warning("Foglio 'HeartRates' non trovato o vuoto.")
        
        power_values = {}
        try:
            power_df = pd.read_excel(filename, sheet_name='PowerValues')
            for _, row in power_df.iterrows():
                if pd.notna(row['Nome']) and pd.notna(row['Valore']):
                    power_values[row['Nome']] = row['Valore']
        except:
            logging.warning("Foglio 'PowerValues' non trovato o vuoto.")
        
        # Legge gli allenamenti
        workouts_df = pd.read_excel(filename, sheet_name='Workouts')
        workouts = {}
        
        current_workout = None
        current_steps = []
        
        for _, row in workouts_df.iterrows():
            # Nuova riga di allenamento
            if pd.notna(row['Nome']) and row['Nome'].strip():
                # Salva l'allenamento precedente, se esiste
                if current_workout:
                    workouts[current_workout] = current_steps
                
                # Inizia un nuovo allenamento
                current_workout = row['Nome'].strip()
                current_steps = []
                
                # Aggiungi il tipo di sport, se presente
                if pd.notna(row['TipoSport']):
                    current_steps.append({"sport_type": row['TipoSport'].strip()})
                
                # Aggiungi la data, se presente
                if pd.notna(row['Data']):
                    date_str = None
                    if isinstance(row['Data'], str):
                        date_str = row['Data'].strip()
                    elif isinstance(row['Data'], datetime.datetime):
                        date_str = row['Data'].strftime('%Y-%m-%d')
                    
                    if date_str:
                        current_steps.append({"date": date_str})
            
            # Riga di passo normale
            if pd.notna(row['TipoPasso']) and pd.notna(row['Dettagli']):
                step_type = row['TipoPasso'].strip()
                step_details = row['Dettagli'].strip()
                
                # Controlla se è un passo di ripetizione
                if step_type.lower() == 'repeat':
                    # Formato: numero di ripetizioni
                    try:
                        iterations = int(step_details)
                        repeat_step = {
                            "repeat": iterations,
                            "steps": []
                        }
                        current_steps.append(repeat_step)
                    except:
                        logging.warning(f"Formato non valido per ripetizione: {step_details}")
                else:
                    # Aggiungi un passo normale
                    current_steps.append({step_type: step_details})
            
            # Riga di sottopasso di ripetizione
            if pd.isna(row['TipoPasso']) and pd.notna(row['SubTipoPasso']) and pd.notna(row['SubDettagli']):
                sub_type = row['SubTipoPasso'].strip()
                sub_details = row['SubDettagli'].strip()
                
                # Trova l'ultimo passo di ripetizione
                for i in range(len(current_steps) - 1, -1, -1):
                    if isinstance(current_steps[i], dict) and "repeat" in current_steps[i]:
                        current_steps[i]["steps"].append({sub_type: sub_details})
                        break
        
        # Salva l'ultimo allenamento
        if current_workout:
            workouts[current_workout] = current_steps
        
        # Costruisci il risultato finale
        result = {}
        result.update(workouts)
        
        # Aggiungi la configurazione
        result['config'] = {
            'paces': paces,
            'heart_rates': heart_rates,
            'power_values': power_values
        }
        
        # Aggiungi altri campi di configurazione
        for k, v in config.items():
            result['config'][k] = v
        
        return result
    except Exception as e:
        logging.error(f"Errore nel caricamento del file Excel: {str(e)}")
        raise

def save_excel(data, filename):
    """
    Salva i dati in un file Excel.
    
    Args:
        data: Dati da salvare
        filename: Nome del file di destinazione
    """
    try:
        # Crea un writer Excel
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Estrai la configurazione
            config = data.get('config', {})
            
            # Foglio di configurazione generale
            config_data = []
            for k, v in config.items():
                if k not in ['paces', 'heart_rates', 'power_values']:
                    config_data.append({'Chiave': k, 'Valore': v})
            
            config_df = pd.DataFrame(config_data)
            config_df.to_excel(writer, sheet_name='Config', index=False)
            
            # Foglio dei ritmi
            paces = config.get('paces', {})
            paces_data = [{'Nome': k, 'Valore': v} for k, v in paces.items()]
            paces_df = pd.DataFrame(paces_data)
            paces_df.to_excel(writer, sheet_name='Paces', index=False)
            
            # Foglio delle frequenze cardiache
            hr = config.get('heart_rates', {})
            hr_data = [{'Nome': k, 'Valore': v} for k, v in hr.items()]
            hr_df = pd.DataFrame(hr_data)
            hr_df.to_excel(writer, sheet_name='HeartRates', index=False)
            
            # Foglio dei valori di potenza
            power = config.get('power_values', {})
            power_data = [{'Nome': k, 'Valore': v} for k, v in power.items()]
            power_df = pd.DataFrame(power_data)
            power_df.to_excel(writer, sheet_name='PowerValues', index=False)
            
            # Prepara i dati degli allenamenti
            workouts_data = []
            
            for name, steps in data.items():
                if name != 'config':
                    # Prima riga: nome e tipo di sport
                    row = {'Nome': name, 'TipoPasso': None, 'Dettagli': None}
                    
                    # Trova il tipo di sport e la data
                    sport_type = None
                    date = None
                    
                    for i, step in enumerate(steps):
                        if isinstance(step, dict):
                            if 'sport_type' in step:
                                sport_type = step['sport_type']
                            elif 'date' in step:
                                date = step['date']
                    
                    row['TipoSport'] = sport_type
                    row['Data'] = date
                    
                    workouts_data.append(row)
                    
                    # Aggiungi i passi
                    for step in steps:
                        if isinstance(step, dict):
                            if 'sport_type' in step or 'date' in step:
                                # Salta i metadati già processati
                                continue
                                
                            if 'repeat' in step and 'steps' in step:
                                # Passo di ripetizione
                                iterations = step['repeat']
                                workouts_data.append({
                                    'Nome': None,
                                    'TipoPasso': 'repeat',
                                    'Dettagli': str(iterations),
                                    'TipoSport': None,
                                    'Data': None,
                                    'SubTipoPasso': None,
                                    'SubDettagli': None
                                })
                                
                                # Aggiungi i sotto-passi
                                for substep in step['steps']:
                                    if isinstance(substep, dict) and len(substep) == 1:
                                        sub_type = list(substep.keys())[0]
                                        sub_detail = substep[sub_type]
                                        workouts_data.append({
                                            'Nome': None,
                                            'TipoPasso': None,
                                            'Dettagli': None,
                                            'TipoSport': None,
                                            'Data': None,
                                            'SubTipoPasso': sub_type,
                                            'SubDettagli': sub_detail
                                        })
                            elif len(step) == 1:
                                # Passo normale
                                step_type = list(step.keys())[0]
                                step_detail = step[step_type]
                                workouts_data.append({
                                    'Nome': None,
                                    'TipoPasso': step_type,
                                    'Dettagli': step_detail,
                                    'TipoSport': None,
                                    'Data': None,
                                    'SubTipoPasso': None,
                                    'SubDettagli': None
                                })
            
            # Crea il DataFrame degli allenamenti
            workouts_df = pd.DataFrame(workouts_data)
            workouts_df.to_excel(writer, sheet_name='Workouts', index=False)
    
    except Exception as e:
        logging.error(f"Errore nel salvataggio del file Excel: {str(e)}")
        raise

def create_excel_template(filename):
    """
    Crea un file Excel template per gli allenamenti.
    
    Args:
        filename: Nome del file di destinazione
    """
    try:
        # Crea un writer Excel
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Foglio Config
            config_df = pd.DataFrame([
                {'Chiave': 'name_prefix', 'Valore': ''},
                {'Chiave': 'athlete_name', 'Valore': 'Atleta'},
                {'Chiave': 'race_day', 'Valore': (datetime.date.today() + datetime.timedelta(days=90)).strftime('%Y-%m-%d')},
                {'Chiave': 'margins', 'Valore': '{"faster": "0:03", "slower": "0:03"}'}
            ])
            config_df.to_excel(writer, sheet_name='Config', index=False)
            
            # Foglio Paces
            paces_df = pd.DataFrame([
                {'Nome': 'Z1', 'Valore': '6:30'},
                {'Nome': 'Z2', 'Valore': '6:00'},
                {'Nome': 'Z3', 'Valore': '5:30'},
                {'Nome': 'Z4', 'Valore': '5:00'},
                {'Nome': 'Z5', 'Valore': '4:30'},
                {'Nome': 'recovery', 'Valore': '7:00'},
                {'Nome': 'threshold', 'Valore': '5:10'},
                {'Nome': 'marathon', 'Valore': '5:20'}
            ])
            paces_df.to_excel(writer, sheet_name='Paces', index=False)
            
            # Foglio HeartRates
            hr_df = pd.DataFrame([
                {'Nome': 'max_hr', 'Valore': 180},
                {'Nome': 'Z1_HR', 'Valore': '110-130'},
                {'Nome': 'Z2_HR', 'Valore': '130-150'},
                {'Nome': 'Z3_HR', 'Valore': '150-165'},
                {'Nome': 'Z4_HR', 'Valore': '165-175'},
                {'Nome': 'Z5_HR', 'Valore': '175-185'}
            ])
            hr_df.to_excel(writer, sheet_name='HeartRates', index=False)
            
            # Foglio PowerValues
            power_df = pd.DataFrame([
                {'Nome': 'ftp', 'Valore': 250},
                {'Nome': 'Z1', 'Valore': '125-175'},
                {'Nome': 'Z2', 'Valore': '175-215'},
                {'Nome': 'Z3', 'Valore': '215-250'},
                {'Nome': 'Z4', 'Valore': '250-300'},
                {'Nome': 'Z5', 'Valore': '300-375'},
                {'Nome': 'threshold', 'Valore': '235-265'},
                {'Nome': 'sweet_spot', 'Valore': '220-235'}
            ])
            power_df.to_excel(writer, sheet_name='PowerValues', index=False)
            
            # Foglio Workouts
            workouts_data = [
                # Esempio di allenamento corsa
                {'Nome': 'W01S01 Easy run', 'TipoPasso': None, 'Dettagli': None, 'SubTipoPasso': None, 'SubDettagli': None, 'TipoSport': 'running', 'Data': (datetime.date.today() + datetime.timedelta(days=7)).strftime('%Y-%m-%d')},
                {'Nome': None, 'TipoPasso': 'warmup', 'Dettagli': '10min @ Z1_HR', 'SubTipoPasso': None, 'SubDettagli': None, 'TipoSport': None, 'Data': None},
                {'Nome': None, 'TipoPasso': 'interval', 'Dettagli': '30min @ Z2', 'SubTipoPasso': None, 'SubDettagli': None, 'TipoSport': None, 'Data': None},
                {'Nome': None, 'TipoPasso': 'cooldown', 'Dettagli': '5min @ Z1_HR', 'SubTipoPasso': None, 'SubDettagli': None, 'TipoSport': None, 'Data': None},
                
                # Esempio di allenamento con ripetute
                {'Nome': 'W01S02 Short intervals', 'TipoPasso': None, 'Dettagli': None, 'SubTipoPasso': None, 'SubDettagli': None, 'TipoSport': 'running', 'Data': (datetime.date.today() + datetime.timedelta(days=9)).strftime('%Y-%m-%d')},
                {'Nome': None, 'TipoPasso': 'warmup', 'Dettagli': '10min @ Z1_HR', 'SubTipoPasso': None, 'SubDettagli': None, 'TipoSport': None, 'Data': None},
                {'Nome': None, 'TipoPasso': 'repeat', 'Dettagli': '5', 'SubTipoPasso': None, 'SubDettagli': None, 'TipoSport': None, 'Data': None},
                {'Nome': None, 'TipoPasso': None, 'Dettagli': None, 'SubTipoPasso': 'interval', 'SubDettagli': '400m @ Z5', 'TipoSport': None, 'Data': None},
                {'Nome': None, 'TipoPasso': None, 'Dettagli': None, 'SubTipoPasso': 'recovery', 'SubDettagli': '1min @ Z1_HR', 'TipoSport': None, 'Data': None},
                {'Nome': None, 'TipoPasso': 'cooldown', 'Dettagli': '5min @ Z1_HR', 'SubTipoPasso': None, 'SubDettagli': None, 'TipoSport': None, 'Data': None},
                
                # Esempio di allenamento bici
                {'Nome': 'W02S01 Cycling workout', 'TipoPasso': None, 'Dettagli': None, 'SubTipoPasso': None, 'SubDettagli': None, 'TipoSport': 'cycling', 'Data': (datetime.date.today() + datetime.timedelta(days=14)).strftime('%Y-%m-%d')},
                {'Nome': None, 'TipoPasso': 'warmup', 'Dettagli': '15min @hr Z1_HR', 'SubTipoPasso': None, 'SubDettagli': None, 'TipoSport': None, 'Data': None},
                {'Nome': None, 'TipoPasso': 'interval', 'Dettagli': '30min @pwr Z3', 'SubTipoPasso': None, 'SubDettagli': None, 'TipoSport': None, 'Data': None},
                {'Nome': None, 'TipoPasso': 'cooldown', 'Dettagli': '10min @hr Z1_HR', 'SubTipoPasso': None, 'SubDettagli': None, 'TipoSport': None, 'Data': None},
                
                # Esempio di allenamento nuoto
                {'Nome': 'W03S01 Swim workout', 'TipoPasso': None, 'Dettagli': None, 'SubTipoPasso': None, 'SubDettagli': None, 'TipoSport': 'swimming', 'Data': (datetime.date.today() + datetime.timedelta(days=21)).strftime('%Y-%m-%d')},
                {'Nome': None, 'TipoPasso': 'warmup', 'Dettagli': '200m @ Z1_HR', 'SubTipoPasso': None, 'SubDettagli': None, 'TipoSport': None, 'Data': None},
                {'Nome': None, 'TipoPasso': 'interval', 'Dettagli': '600m @ Z3', 'SubTipoPasso': None, 'SubDettagli': None, 'TipoSport': None, 'Data': None},
                {'Nome': None, 'TipoPasso': 'cooldown', 'Dettagli': '100m @ Z1_HR', 'SubTipoPasso': None, 'SubDettagli': None, 'TipoSport': None, 'Data': None}
            ]
            
            workouts_df = pd.DataFrame(workouts_data)
            workouts_df.to_excel(writer, sheet_name='Workouts', index=False)
    
    except Exception as e:
        logging.error(f"Errore nella creazione del template Excel: {str(e)}")
        raise