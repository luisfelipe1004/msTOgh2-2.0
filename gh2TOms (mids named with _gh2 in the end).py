from mido import MidiFile, MidiTrack, MetaMessage, Message
import os
import glob

####################################################################################################################################################

# --------------------------------------------
# CONFIGURAÇÃO DE SCRIPT
# --------------------------------------------

exit = '0' # 1 close the script automatically
auto = '0' # 1 remove all the questions
click = '2' # 1 set practice drums / 2 no practice drums
instrument = '1' # 1 guitar/bass / 2 lead/rhythm
metal = '1' # 1 band singer / 2 band keys

####################################################################################################################################################

# --------------------------------------------
# CONFIGURAÇÃO DE MIDI
# --------------------------------------------

# Fretmapping notes
fretmapping_notes = {
    40: 98, 41: 99, 42: 100, 43: 95, 44: 96, 45: 97,  # expert GHL
    46: 86, 47: 87, 48: 88, 49: 83, 50: 84, 51: 85,  # hard GHL
    52: 74, 53: 75, 54: 76, 55: 71, 56: 72, 57: 73,  # medium GHL
    58: 62, 59: 63,  # easy GHL
    
    105:60, # Face-Off (PLAYER 1) - EASY 5th NOTE
    106:61 # Face-Off (PLAYER 2) - EASY 6th NOTE
    }

# GUITAR/BASS/COOP/RHYTHM notes
instrument_notes = {
    60:60, 61:61, 62:62, 63:63, 64:64, # easy
    72:72, 73:73, 74:74, 75:75, 76:76, # medium
    84:84, 85:85, 86:86, 87:87, 88:88, # hard
    96:96, 97:97, 98:98, 99:99, 100:100, # expert
    103:116 #star power
    }

####################################################################################################################################################

# --------------------------------------------
# Funções básicas de manipulação de MIDI
# --------------------------------------------

####################################################################################################################################################

def get_track_by_name(midi, track_name):
# Retorna a primeira track com o nome especificado.
    for track in midi.tracks:
        for msg in track:
            if msg.type == "track_name" and msg.name == track_name:
                return track
    return None

####################################################################################################################################################

def delete_track(midi, track_name):
# Deleta a primeira track usando o nome especificado.
    for i, track in enumerate(midi.tracks):
        for msg in track:
            if msg.type == "track_name" and msg.name == track_name:
                del midi.tracks[i]
                print(f"'{track_name}' deleted")
                return True
    print(f"'{track_name}' not found")
    return False

####################################################################################################################################################

def rename_track_by_name(midi, old_name, new_name):
# Renomeia a track que tem o nome old_name para new_name.
    track = get_track_by_name(midi, old_name)
    if track:
        for msg in track:
            if msg.type == "track_name" and msg.name == old_name:
                msg.name = new_name
        print(f"'{old_name}' renamed to '{new_name}'")
        return True
    print(f"'{old_name}' not found")
    return False

####################################################################################################################################################

def ensure_track(midi, track_name):
    # garante que a track exista, criando vazia se não existir
    track = get_track_by_name(midi, track_name)
    if track is None:
        track = MidiTrack([MetaMessage("track_name", name=track_name)])
        midi.tracks.append(track)
    return track

####################################################################################################################################################

def copy_events_only(midi, source_name, target_name):
    # copia apenas eventos que não sejam nota, cria destino vazio se origem não existir
    target = ensure_track(midi, target_name)
    source = get_track_by_name(midi, source_name)
    if source is None:
        print(f"Track '{source_name}' not found, '{target_name}' stays empty.")
        return target
    cumulative_time = 0
    for msg in source:
        cumulative_time += msg.time
        if msg.type not in ["track_name", "note_on", "note_off"]:
            target.append(msg.copy(time=cumulative_time))
            cumulative_time = 0
    print(f"'{source_name}' events copied to '{target_name}'")
    return target

####################################################################################################################################################

def copy_notes_only(midi, source_name, target_name, note_map):
    # copia apenas notas, cria destino vazio se origem não existir
    target = ensure_track(midi, target_name)
    source = get_track_by_name(midi, source_name)
    if source is None:
        print(f"Track '{source_name}' not found, '{target_name}' stays empty.")
        return target
    cumulative_time = 0
    for msg in source:
        cumulative_time += msg.time
        if msg.type in ["note_on", "note_off"] and msg.note in note_map:
            destinos = note_map[msg.note]
            if not isinstance(destinos, (list, tuple)):
                destinos = [destinos]
            for i, new_note in enumerate(destinos):
                target.append(Message(msg.type,
                                      note=new_note,
                                      velocity=msg.velocity,
                                      time=cumulative_time if i == 0 else 0))
            cumulative_time = 0
    print(f"'{source_name}' notes copied to '{target_name}'")
    return target

####################################################################################################################################################

def merge_tracks(midi, name_a, name_b, merged_name="MERGED"):
    # mescla mesmo se uma ou ambas as tracks faltarem (gera vazia se preciso)
    track_a = get_track_by_name(midi, name_a)
    track_b = get_track_by_name(midi, name_b)
    if track_a is None and track_b is None:
        merged = MidiTrack([MetaMessage("track_name", name=merged_name)])
        midi.tracks.append(merged)
        print(f"No '{name_a}' or '{name_b}' to merge; created empty '{merged_name}'.")
        return merged
    events = []
    for track in (track_a, track_b):
        if track is None:
            continue
        abs_time = 0
        for msg in track:
            abs_time += msg.time
            if msg.type != "track_name":
                events.append((abs_time, msg))
    merged = MidiTrack([MetaMessage("track_name", name=merged_name)])
    prev = 0
    for t, msg in sorted(events, key=lambda x: x[0]):
        merged.append(msg.copy(time=t - prev))
        prev = t
    midi.tracks.append(merged)
    print(f"Merged '{name_a}' + '{name_b}' into '{merged_name}'")
    return merged

####################################################################################################################################################

# --------------------------------------------
# Processamento em batch
# --------------------------------------------

if __name__ == "__main__":
    midi_files = [f for f in glob.glob("*_gh2.mid") if not f.endswith("_ms.mid")]

    if not midi_files:
        print("No MIDI Files Found in This Folder.")
    else:
        for input_path in midi_files:
            print(f"Processing: {input_path}")
            midi = MidiFile(input_path)

####################################################################################################################################################

            # --------------------------------------------
            # Exemplos para construir scripts MIDI
            # --------------------------------------------
            '''
            # Exemplo 1 Deletar Tracks
            delete_track(midi, "TRACK NAME")

            # Exemplo 2: Renomear track
            rename_track_by_name(midi, "TRACK OLD NAME", "TRACK NEW NAME")

            # Exemplo 3: Copiar apenas eventos de uma track para outra (sem copiar as notas)
            copy_events_only(midi, "TRACK 1", "TRACK 2")

            # Exemplo 4: Copiar apenas notas de uma track para outra (sem copiar eventos)
            copy_notes_only(midi, "TRACK 1", "TRACK 2", note_map={96:36, 97:37})

            # Exemplo 5: Mesclar tracks
            merge_tracks(midi, "TRACK 1", "TRACK 2", merged_name="NEW TRACK")
            '''

####################################################################################################################################################

            # -----------
            # PART GUITAR
            # -----------
            # Copiar eventos do PART GUITAR para PART GUITAR EVENTS
            copy_events_only(midi, "PART GUITAR", "PART GUITAR EVENTS")
            
            # Copiar notas de PART GUITAR para PART GUITAR NOTES
            copy_notes_only(midi, "PART GUITAR", "PART GUITAR NOTES", note_map= instrument_notes)
            
            # Copiar a nota BIG-NOTE (laranja) do PART GUITAR para BIG-NOTE
            copy_notes_only(midi, "PART GUITAR", "BIG-NOTE", note_map={110:100})
            
            # Copiar notas do PART GUITAR para PART GUITAR GHL
            copy_notes_only(midi, "PART GUITAR", "PART GUITAR GHL", note_map= fretmapping_notes)
            # Deletar o PART GUITAR
            delete_track(midi, "PART GUITAR")
            
            # Mesclar os PART GUITAR temporários
            merge_tracks(midi, "PART GUITAR EVENTS", "PART GUITAR NOTES", merged_name="PART GUITAR")
            # Deletar os PART GUITAR temporários
            delete_track(midi, "PART GUITAR EVENTS")
            delete_track(midi, "PART GUITAR NOTES")

####################################################################################################################################################

            # -----------
            # PART BASS
            # -----------
            # Copiar eventos do PART BASS para PART BASS EVENTS
            copy_events_only(midi, "PART BASS", "PART BASS EVENTS")
            
            # Copiar notas de PART BASS para PART BASS NOTES
            copy_notes_only(midi, "PART BASS", "PART BASS NOTES", note_map= instrument_notes)
            
            # Copiar notas do PART BASS para PART BASS GHL
            copy_notes_only(midi, "PART BASS", "PART BASS GHL", note_map= fretmapping_notes)
            # Deletar o PART BASS
            delete_track(midi, "PART BASS")
            
            # Mesclar os PART BASS temporários
            merge_tracks(midi, "PART BASS EVENTS", "PART BASS NOTES", merged_name="PART BASS")
            # Deletar os PART BASS temporários e BAND BASS
            delete_track(midi, "PART BASS EVENTS")
            delete_track(midi, "PART BASS NOTES")
            delete_track(midi, "BAND BASS")

####################################################################################################################################################

            # -----------
            # PART GUITAR COOP
            # -----------
            # Copiar eventos do PART GUITAR COOP para PART GUITAR COOP EVENTS
            copy_events_only(midi, "PART GUITAR COOP", "PART GUITAR COOP EVENTS")
            
            # Copiar notas de PART GUITAR COOP para PART GUITAR COOP NOTES
            copy_notes_only(midi, "PART GUITAR COOP", "PART GUITAR COOP NOTES", note_map= instrument_notes)
            
            # Copiar notas do PART GUITAR COOP para PART GUITAR COOP GHL
            copy_notes_only(midi, "PART GUITAR COOP", "PART GUITAR COOP GHL", note_map= fretmapping_notes)
            # Deletar o PART GUITAR COOP
            delete_track(midi, "PART GUITAR COOP")
            
            # Mesclar os PART GUITAR COOP temporários
            merge_tracks(midi, "PART GUITAR COOP EVENTS", "PART GUITAR COOP NOTES", merged_name="PART GUITAR COOP")
            # Deletar os PART GUITAR COOP temporários
            delete_track(midi, "PART GUITAR COOP EVENTS")
            delete_track(midi, "PART GUITAR COOP NOTES")

####################################################################################################################################################

            # -----------
            # PART RHYTHM
            # -----------
            # Copiar eventos do PART RHYTHM para PART RHYTHM EVENTS
            copy_events_only(midi, "PART RHYTHM", "PART RHYTHM EVENTS")
            
            # Copiar notas de PART RHYTHM para PART RHYTHM NOTES
            copy_notes_only(midi, "PART RHYTHM", "PART RHYTHM NOTES", note_map= instrument_notes)
            
            # Copiar notas do PART RHYTHM para PART RHYTHM GHL
            copy_notes_only(midi, "PART RHYTHM", "PART RHYTHM GHL", note_map= fretmapping_notes)
            # Deletar o PART RHYTHM
            delete_track(midi, "PART RHYTHM")
            
            # Mesclar os PART RHYTHM temporários
            merge_tracks(midi, "PART RHYTHM EVENTS", "PART RHYTHM NOTES", merged_name="PART RHYTHM")
            # Deletar os PART RHYTHM temporários
            delete_track(midi, "PART RHYTHM EVENTS")
            delete_track(midi, "PART RHYTHM NOTES")

####################################################################################################################################################

            # -----------
            # PART DRUMS
            # -----------
            # Copiar eventos do BAND DRUMS para PART DRUMS EVENTS
            copy_events_only(midi, "BAND DRUMS", "PART DRUMS EVENTS")
            # Copiar notas de BAND DRUMS para DRUM CYMBAL
            copy_notes_only(midi, "BAND DRUMS", "DRUM CYMBAL", note_map={37:100})
            # Copiar notas de TRIGGERS para DRUM NOTES
            copy_notes_only(midi, "TRIGGERS", "DRUM NOTES", note_map={24:96, 25:97, 26:98})
            # Mesclar notas de DRUM temporários
            merge_tracks(midi, "DRUM CYMBAL", "DRUM NOTES", merged_name="PART DRUMS NOTES")
            # Mesclar os PART DRUMS temporários
            merge_tracks(midi, "PART DRUMS EVENTS", "PART DRUMS NOTES", merged_name="PART DRUMS")
            # Deletar os DRUMS antigos e temporários
            delete_track(midi, "BAND DRUMS")
            delete_track(midi, "PART DRUMS EVENTS")
            delete_track(midi, "DRUM CYMBAL")
            delete_track(midi, "DRUM NOTES")
            delete_track(midi, "PART DRUMS NOTES")

####################################################################################################################################################

            # -----------
            # PART KEYS EVENTS
            # -----------
            # Mesclar BAND SINGER e BAND KEYS para track temporária
            merge_tracks(midi, "BAND SINGER", "BAND KEYS", merged_name="KEYS EVENTS")
            # Deletar as tracks antigas
            delete_track(midi, "BAND SINGER")
            delete_track(midi, "BAND KEYS")

####################################################################################################################################################

            # -----------
            # PART KEYS NOTES
            # -----------
            # Copiar notas de TRIGGERS para TEMP KEYS NOTES
            copy_notes_only(midi, "TRIGGERS", "TEMP KEYS NOTES", note_map= {48:96, 49:97, 50:98, 52:99})
            # Mesclar BIG-NOTE e TEMP KEYS NOTES
            merge_tracks(midi, "BIG-NOTE", "TEMP KEYS NOTES", merged_name="KEYS NOTES")
            # Mesclar os KEYS temporários
            merge_tracks(midi, "KEYS EVENTS", "KEYS NOTES", merged_name="PART KEYS")
            # Deletar os TRIGGER temporários
            delete_track(midi, "TRIGGERS")
            delete_track(midi, "TEMP KEYS NOTES")
            delete_track(midi, "BIG-NOTE")
            delete_track(midi, "KEYS NOTES")
            delete_track(midi, "KEYS EVENTS")

####################################################################################################################################################

            # --------------------------------------------
            # Finalização
            # --------------------------------------------
            # Salvar arquivo processado
            base, ext = os.path.splitext(input_path)
            output_path = f"{base}_ms.mid"
            midi.save(output_path)
            print(f"Saved as: {output_path}\n")
            # Pause de arquivo batch, mas no python (gambiarra)

if (exit == '0'):
    print("Press Enter to Exit")
    exit = input()

####################################################################################################################################################