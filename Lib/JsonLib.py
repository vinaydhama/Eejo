import json
from Lib.SwimDataHolder import MeetHeaderDisplay,HeatDataDisplay,SwimerBoardDetail
from Lib.LogerService import Logger
import re
from typing import Any, Dict, List, Tuple, Union,Optional

import io
import os
import re
import tempfile
import shutil

class PathError(Exception):
    pass

class JsonHelper:

    def append_json_line_async(AppendJsonPath,dataToUpdate):
        with open(AppendJsonPath, "a+") as json_file:
            json_file.write("{}\n".format(json.dumps(dataToUpdate)))
        return

    def GetMeetHeader(data):
        meetHeaderDisplay= MeetHeaderDisplay()
        meetHeaderDisplay.MeetName= data[0]["MeetName"]
        meetHeaderDisplay.MeetDate= data[0]["MeetDate"]
        meetHeaderDisplay.MeetAddress= data[0]["MeetAddress"]
        sjson= json.dumps(meetHeaderDisplay.__dict__)
        print (sjson)
        return sjson



    def get_next_heat_id_from_file(data):
        """
        Expects data['EventDetails'] to be a dict:
        { <eventID>: { "eventID": <eventID>, "HeatList": [ { "HeatID": ..., "HeatStatus": ... }, ... ] }, ... }

        Returns (heat_id, event_id) for the first heat with HeatStatus == 0.
        If none found or malformed, returns (None, None).
        """
        event_details = (data or {}).get("EventDetails", {})  # dict
        if not isinstance(event_details, dict):
            return (None, None)

        # Iterates in dict's iteration order (in CPython 3.7+ this is insertion order)
        for event_id, event in event_details.items():
            heat_list = (event or {}).get("HeatList", [])
            for heat in heat_list or []:
                if (heat_list[heat] or {}).get("HeatStatus") == 0:
                    # Prefer key event_id; if missing, fall back to event["eventID"]
                    return (heat_list[heat].get("HeatID"), event_id if event_id is not None else event.get("eventID"))
        return (None, None)


        # Not used
    def GetNextHeatIDFromFile(data):

        for eventID in range(0,len(data['EventDetails'])):
            for heat in range(0,len (data['EventDetails'][eventID]["HeatList"])):
                heatdata = data['EventDetails'][eventID]["HeatList"][heat]
                if (heatdata["HeatStatus"]==0 ):
                    return heatdata["HeatID"],data['EventDetails'][eventID]["eventID"]
        return 0,0


    
    def GetAllHeatIDsFromFile(data):
        """Extract all keys from HeatList dictionaries inside EventDetails."""
        keys = []
        event_details = data.get("EventDetails", {})
        if not isinstance(event_details, dict):
            return keys

        for event in event_details.values():
            heat_list = event.get("HeatList", {})
            if isinstance(heat_list, dict):
                keys.extend(heat_list.keys())  # Collect all keys
        return keys


    # def GetAllHeatIDsFromFile(data):
    #     HeatIds=[]

    #     for eventID in range(0,len(data['EventDetails'])):
    #         for heat in range(0,len (data['EventDetails'][eventID]["HeatList"])):
    #             heatdata = data['EventDetails'][eventID]["HeatList"][heat]
    #             HeatIds.append(heatdata["HeatID"])
    #     return HeatIds
    
    def updateJsonFile(AppendJsonPath,dataToUpdate):
        jsonFile = open(AppendJsonPath, "r") # Open the JSON file for reading
        data = json.load(jsonFile) # Read the JSON into the buffer
        jsonFile.close() # Close the JSON file

        ## Working with buffered content
        tmp = data["location"]
        data["location"] = path
        data["mode"] = "replay"

        ## Save our changes to JSON file
        jsonFile = open(AppendJsonPath, "w+")
        jsonFile.write(json.dumps(data))
        jsonFile.close()


    def GetHeatDataDisplay(heatIDToDisplay: Any, EventIDToDisplay: Optional[Any], data: Dict[str, Any]):
        """
        Build and return a HeatDataDisplay instance for the requested heat within an event.
        Assumes:
        - data['EventDetails']: dict (or list) of event objects
        - EventHolder['HeatList']: dict (or list) of heat objects
        - heat['BoardList']: list of board/swimmer dicts (per provided sample)

        Returns:
        HeatDataDisplay or None if not found.
        """

        # Basic validation
        if not isinstance(data, dict):
            raise TypeError("`data` must be a dict.")
        if 'EventDetails' not in data:
            raise ValueError("`data` must contain 'EventDetails'.")

        heatDataDisplay = HeatDataDisplay()
        swimerBoardDetails: List[SwimerBoardDetail] = []

        # Iterate events (dict or list)
        for event in _iter_dict_or_list(data.get('EventDetails')):
            if not isinstance(event, dict):
                continue

            event_id = event.get("eventID")
            event_name = event.get("eventName")

            # Optional event filter
            if EventIDToDisplay is not None and event_id != EventIDToDisplay:
                continue

            # Assign event-level fields
            heatDataDisplay.eventID = event_id
            heatDataDisplay.eventName = event_name

            # Iterate heats (dict or list)
            for heat in _iter_dict_or_list(event.get("HeatList")):
                if not isinstance(heat, dict):
                    continue

                if heat.get("HeatID") == heatIDToDisplay:
                    # Populate heat fields
                    heatDataDisplay.HeatID = heatIDToDisplay
                    heatDataDisplay.HeatStartTime = heat.get("HeatStartTime")
                    heatDataDisplay.HeatEndTime = heat.get("HeatEndTime")

                    # BoardList is a LIST (per your sample)
                    for board in _iter_dict_or_list(heat.get("BoardList")):
                        if not isinstance(board, dict):
                            continue

                        # Map known fields from your sample structure
                        swimerBoardDetails.append(
                            SwimerBoardDetail(
                                board.get("BoardID"),
                                board.get("SwimerName"),
                                board.get("SwimerID"),
                                board.get("BoardStatus", 0),   # using actual value if present
                                board.get("SwimStatus", 0),
                                board.get("SwimTimings", 0),   # fill with timing if your class expects it
                                0, 0, 0, 0                      # placeholders for remaining fields
                            )
                        )

                    heatDataDisplay.SwimerBoardDetails = swimerBoardDetails
                    return heatDataDisplay

        # Not found
        return None


#     # Get Swimmer List From Heat List to Timer start
#     def GetHeatDataDisplay(heatIDToDisplay,EventIDToDisplay, data):
#         heatDataDisplay= HeatDataDisplay()
#         swimerBoardDetails=[]
#         for eventID in range(0,len(data['EventDetails'])):
# #             if (data[eventID]["eventID"]==EventIDToDisplay):
#                 EventHolder = data['EventDetails'][eventID]
#                 heatDataDisplay.eventID=EventHolder["eventID"]
#                 heatDataDisplay.eventName=EventHolder["eventName"]
#                 for heat in range(0,len (EventHolder["HeatList"])):			
#                    # print(EventHolder["HeatList"][heat]["HeatID"])
#                     if (EventHolder["HeatList"][heat]["HeatID"]==heatIDToDisplay):
#                         heatDataDisplay.HeatStartTime = EventHolder["HeatList"][heat]["HeatStartTime"]
#                         heatDataDisplay.HeatEndTime = EventHolder["HeatList"][heat]["HeatEndTime"]
#                         heatDataDisplay.HeatID=heatIDToDisplay
#                         for Board in range(0,len (EventHolder["HeatList"][heat]["BoardList"])):
#                             swimerBoardDetails.append(SwimerBoardDetail(EventHolder["HeatList"][heat]["BoardList"][Board]["BoardID"],EventHolder
#                             ["HeatList"][heat]["BoardList"][Board]["SwimerName"],EventHolder["HeatList"][heat]["BoardList"][Board]
#                             ["SwimerID"],0,EventHolder["HeatList"][heat]["BoardList"][Board]["SwimStatus"],0,0,0,0,0))                            
#                         heatDataDisplay.SwimerBoardDetails= swimerBoardDetails
#                         return heatDataDisplay
                    
    


   
from typing import Any, Dict, List, Optional, Iterable

def _iter_dict_or_list(container: Any) -> Iterable:
    """
    Yield dict items from either a dict (values) or a list (elements).
    Safely returns empty iterator if container is None or not iterable as expected.
    """
    if isinstance(container, dict):
        return container.values()
    if isinstance(container, list):
        return container
    return []  # Fallback for None or unexpected types








    # --- Normalization helpers for "modified" meet text (space-delimited tokens) ---


# from typing import Any, Dict, List, Optional, Tuple, Union
# import os, re, tempfile

class PathError(Exception):
    pass



from typing import Any, List, Union

class PathError(Exception):
    pass

class ParamUpdateHelper:
    @staticmethod
    def _tokenize_path(path: str) -> List[Union[str, int]]:
        if not path:
            raise PathError("Empty path")
        if path.startswith("/"):
            # JSON Pointer form: /a/b/0/c
            parts = path.split("/")[1:]
            tokens: List[Union[str, int]] = []
            for p in parts:
                p = p.replace("~1", "/").replace("~0", "~")
                tokens.append(int(p) if p.isdigit() else p)
            return tokens

        # Dotted + bracket form: a[0].b.c[2]
        import re
        tokens: List[Union[str, int]] = []
        pattern = re.compile(r'(?P<key>[^.\[\]]+)|\[(?P<idx>\d+)\]')
        for m in pattern.finditer(path):
            if m.group("key") is not None:
                tokens.append(m.group("key"))
            else:
                tokens.append(int(m.group("idx")))
        if not tokens:
            raise PathError(f"Invalid path: {path}")
        return tokens

    @staticmethod
    def set_value_at_path(root: Any, path: str, value: Any) -> None:
        tokens = ParamUpdateHelper._tokenize_path(path)
        cur = root
        for i, t in enumerate(tokens):
            is_last = (i == len(tokens) - 1)
            if isinstance(t, int):
                # --- INT TOKEN: support both list and dict containers ---
                if isinstance(cur, list):
                    # Ensure index exists for lists
                    while t >= len(cur):
                        cur.append({})
                    if is_last:
                        cur[t] = value
                    else:
                        cur = cur[t]

                elif isinstance(cur, dict):
                    # Map index to the nth key (insertion order) for dicts
                    keys = list(cur.keys())
                    if t < 0 or t >= len(keys):
                        raise PathError(f"Dict index {t} out of range (size={len(keys)})")
                    key_at_index = keys[t]
                    if is_last:
                        cur[key_at_index] = value
                    else:
                        nxt_container = cur.get(key_at_index)
                        if nxt_container is None:
                            # Guess container from next token type
                            nxt = tokens[i + 1]
                            cur[key_at_index] = [] if isinstance(nxt, int) else {}
                            nxt_container = cur[key_at_index]
                        cur = nxt_container
                else:
                    raise PathError(f"Expected list or dict for index {t}, got {type(cur).__name__}")

            else:
                # --- STRING TOKEN: dict key access/creation ---
                if not isinstance(cur, dict):
                    raise PathError(f"Expected dict for key '{t}', got {type(cur).__name__}")
                if is_last:
                    cur[t] = value
                else:
                    if t not in cur or cur[t] is None:
                        nxt = tokens[i + 1]
                        cur[t] = [] if isinstance(nxt, int) else {}
                    cur = cur[t]


# class ParamUpdateHelper:
#     # --- Existing methods you already had ---
#     @staticmethod
#     def _tokens(s: str) -> List[str]:
#         # Split on whitespace, keep raw tokens
#         return re.findall(r'\S+', s or '')

#     @staticmethod
#     def _read_kv(tokens: List[str], i: int) -> Tuple[str, Any, int]:
#         """Read a simple key followed by a single value."""
#         k = tokens[i]
#         v = tokens[i+1] if i+1 < len(tokens) else ""
#         return k, v, i + 2

#     @staticmethod
#     def normalize_modified_meet_text(s: str) -> Dict[str, Any]:
#         """
#         (unchanged body – keep your existing implementation)
#         """
#         # ... keep your current implementation here ...
#         # NOTE: replace calls to _tokens/_read_kv with ParamUpdateHelper._tokens/_read_kv
#         # or since we're inside class, call via ParamUpdateHelper._tokens(...)
#         pass  # placeholder – use your existing body

#     # --- Path helpers (moved under class) ---
#     @staticmethod
#     def _tokenize_path(path: str) -> List[Union[str, int]]:
#         if not path:
#             raise PathError("Empty path")
#         # JSON Pointer
#         if path.startswith("/"):
#             parts = path.split("/")[1:]
#             tokens: List[Union[str, int]] = []
#             for p in parts:
#                 p = p.replace("~1", "/").replace("~0", "~")
#                 tokens.append(int(p) if p.isdigit() else p)
#             return tokens

#         # key[index] dotted form: Key[0].SubKey[1] etc.
#         tokens: List[Union[str, int]] = []
#         pattern = re.compile(r'(?P<key>[^.\[\]]+)|\[(?P<idx>\d+)\]')
#         for m in pattern.finditer(path):
#             if m.group("key") is not None:
#                 tokens.append(m.group("key"))
#             else:
#                 tokens.append(int(m.group("idx")))
#         if not tokens:
#             raise PathError(f"Invalid path: {path}")
#         return tokens

#     @staticmethod
#     def set_value_at_path(root: Any, path: str, value: Any) -> None:
#         tokens = ParamUpdateHelper._tokenize_path(path)
#         cur = root
#         for i, t in enumerate(tokens):
#             is_last = (i == len(tokens) - 1)
#             if isinstance(t, int):
#                 if not isinstance(cur, list):
#                     raise PathError(f"Expected list for index {t}")
#                 while t >= len(cur):
#                     cur.append({})
#                 if is_last:
#                     cur[t] = value
#                 else:
#                     cur = cur[t]
#             else:
#                 if not isinstance(cur, dict):
#                     raise PathError(f"Expected dict for key '{t}'")
#                 if is_last:
#                     cur[t] = value
#                 else:
#                     if t not in cur or cur[t] is None:
#                         nxt = tokens[i + 1]
#                         cur[t] = [] if isinstance(nxt, int) else {}
#                     cur = cur[t]

#     # --- Event/Heat index helpers (moved and upgraded) ---
#     @staticmethod
#     def find_event_index(data: Dict[str, Any], event_id: str) -> int:
#         """
#         Returns the 0-based index of the event with `event_id`:
#         - If EventDetails is a dict keyed by IDs: index by insertion order of keys.
#         - If EventDetails is a list of objects: index by ev['eventID'].
#         - Returns -1 if not found.
#         """
#         src = data.get("EventDetails")

#         # Dict/object case: keys are IDs
#         if isinstance(src, dict):
#             try:
#                 return list(src.keys()).index(event_id)
#             except ValueError:
#                 return -1

#         # List/array case
#         if isinstance(src, list):
#             for idx, ev in enumerate(src):
#                 if isinstance(ev, dict) and ev.get("eventID") == event_id:
#                     return idx
#             return -1

#         return -1

#     @staticmethod
#     def find_heat_index(ev_obj: Dict[str, Any], heat_id: str) -> int:
#         """
#         Returns the 0-based index of the heat with `heat_id`:
#         - If HeatList is a dict keyed by IDs: index by insertion order of keys.
#         - If HeatList is a list of objects: index by h['HeatID'].
#         - Returns -1 if not found.
#         """
#         src = ev_obj.get("HeatList")

#         if isinstance(src, dict):
#             try:
#                 return list(src.keys()).index(heat_id)
#             except ValueError:
#                 return -1

#         if isinstance(src, list):
#             for idx, h in enumerate(src):
#                 if isinstance(h, dict) and h.get("HeatID") == heat_id:
#                     return idx
#             return -1

#         return -1

#     # --- (Optional) getters, useful at call sites ---
#     @staticmethod
#     def get_event(data: Dict[str, Any], event_id: str) -> Optional[Dict[str, Any]]:
#         src = data.get("EventDetails")
#         if isinstance(src, dict):
#             return src.get(event_id)
#         if isinstance(src, list):
#             return next(
#                 (ev for ev in src if isinstance(ev, dict) and ev.get("eventID") == event_id),
#                 None,
#             )
#         return None

#     @staticmethod
#     def get_heat(ev_obj: Dict[str, Any], heat_id: str) -> Optional[Dict[str, Any]]:
#         src = ev_obj.get("HeatList")
#         if isinstance(src, dict):
#             return src.get(heat_id)
#         if isinstance(src, list):
#             return next(
#                 (h for h in src if isinstance(h, dict) and h.get("HeatID") == heat_id),
#                 None,
#             )
#         return None

#     # --- stream rewrite helper (kept outside or moved here) ---
#     @staticmethod
#     def stream_rewrite_patch(
#         file_path: str,
#         event_id: str,
#         heat_id: str,
#         field: str,  # e.g., "HeatNotes"
#         new_value: str,
#         chunk_size: int = 1024 * 1024
#     ) -> None:
#         """
#         Low-memory streaming rewrite. (body unchanged from your implementation)
#         """
#         b_event = re.compile(rb'"eventID"\s*:\s*"' + re.escape(event_id.encode()) + rb'"')
#         b_heat  = re.compile(rb'"HeatID"\s*:\s*"' + re.escape(heat_id.encode()) + rb'"')
#         b_key   = re.compile(rb'"' + field.encode() + rb'"\s*:\s*"')
#         b_quote = re.compile(rb'"')

#         carry = b""
#         patched = False
#         dir_name = os.path.dirname(file_path) or "."
#         fd, tmp_path = tempfile.mkstemp(prefix="json_patch_", suffix=".tmp", dir=dir_name)
#         os.close(fd)
#         with open(file_path, "rb") as src, open(tmp_path, "wb") as dst:
#             while True:
#                 chunk = src.read(chunk_size)
#                 if not chunk:
#                     if carry:
#                         dst.write(carry)
#                         carry = b""
#                     break
#                 buf = carry + chunk
#                 if patched:
#                     dst.write(buf)
#                     carry = b""
#                     continue
#                 m_event = b_event.search(buf)
#                 if not m_event:
#                     keep = max(0, len(buf) - 2048)
#                     dst.write(buf[:keep])
#                     carry = buf[keep:]
#                     continue
#                 m_heat = b_heat.search(buf, m_event.end())
#                 if not m_heat:
#                     dst.write(buf[:m_event.end()])
#                     carry = buf[m_event.end():]
#                     continue
#                 m_key = b_key.search(buf, m_heat.end())
#                 if not m_key:
#                     dst.write(buf[:m_heat.end()])
#                     carry = buf[m_heat.end():]
#                     continue
#                 val_start = m_key.end()
#                 m_close = b_quote.search(buf, val_start)
#                 if not m_close:
#                     dst.write(buf[:val_start])
#                     carry = buf[val_start:]
#                     continue
#                 dst.write(buf[:val_start])
#                 dst.write(new_value.encode("utf-8"))
#                 dst.write(buf[m_close.start():])
#                 patched = True
#                 carry = b""
#         if not patched:
#             os.remove(tmp_path)
#             raise ValueError(
#                 f"Could not locate eventID='{event_id}', heatID='{heat_id}', field='{field}' to patch"
#             )
#         # Atomic replace
#         os.replace(tmp_path, file_path)




# class ParamUpdateHelper:
    
#     def _tokens(s: str) -> List[str]:
#         # Split on whitespace, keep raw tokens
#         return re.findall(r'\S+', s or '')

#     def _read_kv(tokens: List[str], i: int) -> Tuple[str, Any, int]:
#         """Read a simple key followed by a single value."""
#         k = tokens[i]; v = tokens[i+1] if i+1 < len(tokens) else ""
#         return k, v, i + 2

#     def normalize_modified_meet_text(s: str) -> Dict[str, Any]:
#         """
#         Converts space-delimited text (your modified file format) into a structured dict.
#         Handles:
#         - Boards
#         - BoardSettings.IOSettings (Side-A/Side-B arrays, PrimerySide)
#         - BoardSettings.CommSettings (COM_Windows, COM_Pi, SlaveID, StopBit, Baud, bytesize, mode, Parity, stopbits)
#         - EventList
#         - EventDetails: events with eventID + HeatList entries (each with BoardList of boards)
#         This is heuristic and designed around your sample file.
#         """
#         t = _tokens(s)
#         n = len(t)
#         i = 0
#         result: Dict[str, Any] = {"BoardSettings": {"IOSettings": {}, "CommSettings": {}},
#                                 "EventList": [], "EventDetails": []}

#         # Collect top-level boards count, meet header fields, etc., as we see them
#         while i < n:
#             tok = t[i]

#             # Boards <num>
#             if tok == "Boards" and i+1 < n and t[i+1].isdigit():
#                 result["Boards"] = int(t[i+1]); i += 2; continue

#             # BoardSettings IOSettings ...
#             if tok == "BoardSettings":
#                 i += 1
#                 while i < n:
#                     if t[i] == "IOSettings":
#                         i += 1
#                         # Side-A <ints...> until non-int or next tag
#                         if i < n and t[i] == "Side-A":
#                             i += 1
#                             side_a: List[int] = []
#                             while i < n and re.fullmatch(r'-?\d+', t[i]):
#                                 side_a.append(int(t[i])); i += 1
#                             result["BoardSettings"]["IOSettings"]["Side-A"] = side_a
#                         # Side-B <ints...>
#                         if i < n and t[i] == "Side-B":
#                             i += 1
#                             side_b: List[int] = []
#                             while i < n and re.fullmatch(r'-?\d+', t[i]):
#                                 side_b.append(int(t[i])); i += 1
#                             result["BoardSettings"]["IOSettings"]["Side-B"] = side_b
#                         # PrimerySide <true/false>
#                         if i < n and t[i] == "PrimerySide":
#                             _, prim, i = _read_kv(t, i)
#                             result["BoardSettings"]["IOSettings"]["PrimerySide"] = (str(prim).lower() == "true")
#                         # next might be CommSettings
#                         continue

#                     if t[i] == "CommSettings":
#                         i += 1
#                         # Read simple key/value pairs until we hit a non-Comm key
#                         comm = result["BoardSettings"]["CommSettings"]
#                         while i+1 < n and t[i] not in ("EventDetails","EventList","LiveBoard","SwimmerDetails"):
#                             key = t[i]; val = t[i+1]; i += 2
#                             comm[key] = val
#                         continue

#                     # Break BoardSettings section when next major tag
#                     if t[i] in ("EventDetails","EventList","LiveBoard","SwimmerDetails","MeetName","MeetDate","MeetAddress"):
#                         break
#                     i += 1
#                 continue

#             # Meet header fields (if present)
#             if tok in ("MeetName","MeetDate","MeetAddress"):
#                 key, val, i = _read_kv(t, i)
#                 result[key] = val
#                 continue

#             # EventList: subsequent tokens (event IDs) until a control tag
#             if tok == "EventList":
#                 i += 1
#                 while i < n and re.match(r'^\d+|[A-Za-z0-9_]+$', t[i]):
#                     # stop if we hit known tag prefix like 'GroupDetails' etc.
#                     if t[i] in ("GroupDetails","LiveBoard","SwimmerDetails","EventDetails"):
#                         break
#                     result["EventList"].append(t[i]); i += 1
#                 continue

#             # EventDetails <eventID> eventID <same> ...
#             if tok == "EventDetails":
#                 i += 1
#                 if i < n:
#                     ev_id = t[i]; i += 1
#                     ev_obj: Dict[str, Any] = {"eventID": ev_id, "eventName": "", "eventStatus": 0, "HeatList": []}

#                     # Parse per-event metadata
#                     # Expect: eventID <same> eventName <maybe empty> eventStatus <num> HeatList ...
#                     while i < n:
#                         if t[i] == "eventID" and i+1 < n:
#                             i += 2  # skip
#                             continue
#                         if t[i] == "eventName":
#                             # may be missing value; guard
#                             if i+1 < n and t[i+1] not in ("eventStatus","HeatList","EventDetails"):
#                                 ev_obj["eventName"] = t[i+1]; i += 2
#                             else:
#                                 i += 1
#                             continue
#                         if t[i] == "eventStatus" and i+1 < n and re.fullmatch(r'\d+', t[i+1]):
#                             ev_obj["eventStatus"] = int(t[i+1]); i += 2; continue

#                         # Each Heat: HeatList <heatID> BoardList ... until HeatEndTime
#                         if t[i] == "HeatList" and i+1 < n:
#                             heat_id = t[i+1]; i += 2
#                             heat_obj: Dict[str, Any] = {"HeatID": heat_id, "BoardList": [], "HeatNotes": ""}
#                             # BoardList entries
#                             if i < n and t[i] == "BoardList":
#                                 i += 1
#                                 # Consume board rows: BoardID <id> BoardStatus <s> SwimStatus <s> SwimTimings <s> SwimerID <id> SwimerName <name>
#                                 while i < n and t[i] == "BoardID":
#                                     board: Dict[str, Any] = {}
#                                     # BoardID
#                                     board["BoardID"] = int(t[i+1]) if i+1 < n and t[i+1].isdigit() else t[i+1]; i += 2
#                                     # BoardStatus
#                                     if i < n and t[i] == "BoardStatus":
#                                         board["BoardStatus"] = int(t[i+1]) if i+1 < n and re.fullmatch(r'\d+', t[i+1]) else t[i+1]; i += 2
#                                     # SwimStatus
#                                     if i < n and t[i] == "SwimStatus":
#                                         board["SwimStatus"] = int(t[i+1]) if i+1 < n and re.fullmatch(r'\d+', t[i+1]) else t[i+1]; i += 2
#                                     # SwimTimings
#                                     if i < n and t[i] == "SwimTimings":
#                                         # float or int
#                                         board["SwimTimings"] = float(t[i+1]) if i+1 < n and re.fullmatch(r'\d+(\.\d+)?', t[i+1]) else t[i+1]; i += 2
#                                     # SwimerID
#                                     if i < n and t[i] == "SwimerID":
#                                         board["SwimerID"] = t[i+1]; i += 2
#                                     # SwimerName
#                                     if i < n and t[i] == "SwimerName":
#                                         board["SwimerName"] = t[i+1]; i += 2

#                                     heat_obj["BoardList"].append(board)

#                             # HeatEndTime HeatID <same> HeatStartTime HeatStatus <num> HeatNotes
#                             # Consume these if present; store HeatNotes token following HeatNotes (optional)
#                             if i < n and t[i] == "HeatEndTime":
#                                 i += 1
#                                 if i < n and t[i] == "HeatID": i += 2
#                                 if i < n and t[i] == "HeatStartTime": i += 2
#                                 if i < n and t[i] == "HeatStatus": i += 2
#                                 if i < n and t[i] == "HeatNotes":
#                                     i += 1
#                                     # HeatNotes may be immediate next token if not another tag
#                                     if i < n and t[i] not in ("HeatList","EventDetails","EventList","GroupDetails"):
#                                         heat_obj["HeatNotes"] = t[i]; i += 1

#                             ev_obj["HeatList"].append(heat_obj)
#                             continue

#                         # End of current event block when next major tag
#                         if t[i] in ("EventDetails","EventList","GroupDetails","LiveBoard","SwimmerDetails","MeetName","MeetDate","MeetAddress"):
#                             break
#                         i += 1

#                     result["EventDetails"].append(ev_obj)
#                 continue

#             # Stop scanning on large sections we don’t need to normalize further here
#             i += 1

#         # --- Path setter (from earlier answer) ---
    

#     def _tokenize_path(path: str) -> List[Union[str, int]]:
#         if not path: raise PathError("Empty path")
#         if path.startswith("/"):  # JSON Pointer
#             parts = path.split("/")[1:]
#             tokens = []
#             for p in parts:
#                 p = p.replace("~1", "/").replace("~0", "~")
#                 tokens.append(int(p) if p.isdigit() else p)
#             return tokens
#         tokens = []
#         pattern = re.compile(r'(?P<key>[^.\[\]]+)|\[(?P<idx>\d+)\]')
#         for m in pattern.finditer(path):
#             if m.group("key") is not None: tokens.append(m.group("key"))
#             else: tokens.append(int(m.group("idx")))
#         if not tokens: raise PathError(f"Invalid path: {path}")
#         return tokens

#     def set_value_at_path(root: Any, path: str, value: Any) -> None:
#         tokens = _tokenize_path(path)
#         cur = root
#         for i, t in enumerate(tokens):
#             is_last = (i == len(tokens)-1)
#             if isinstance(t, int):
#                 if not isinstance(cur, list): raise PathError(f"Expected list for index {t}")
#                 while t >= len(cur): cur.append({})
#                 if is_last: cur[t] = value
#                 else: cur = cur[t]
#             else:
#                 if not isinstance(cur, dict): raise PathError(f"Expected dict for key '{t}'")
#                 if is_last: cur[t] = value
#                 else:
#                     if t not in cur or cur[t] is None:
#                         # guess container by next token
#                         nxt = tokens[i+1]
#                         cur[t] = [] if isinstance(nxt, int) else {}
#                     cur = cur[t]

#     # --- Helpers to locate an event and (optionally) a heat index ---
#     def find_event_index(data: Dict[str, Any], event_id: str) -> int:
#         evs = data.get("EventDetails", [])
#         for idx, ev in enumerate(evs):
#             if isinstance(ev, dict) and ev.get("eventID") == event_id:
#                 return idx
#         return -1

#     def find_heat_index(ev_obj: Dict[str, Any], heat_id: str) -> int:
#         heats = ev_obj.get("HeatList", [])
#         for idx, h in enumerate(heats):
#             if isinstance(h, dict) and h.get("HeatID") == heat_id:
#                 return idx
#         return -1

#     # --- NEW route: can ingest modified meet text or JSON; updates by path OR (eventID, heatID/heatIndex) ---

    
    

#     def stream_rewrite_patch(
#         file_path: str,
#         event_id: str,
#         heat_id: str,
#         field: str,          # e.g., "HeatNotes"
#         new_value: str,
#         chunk_size: int = 1024 * 1024
#     ) -> None:
#         """
#         Low-memory streaming rewrite:
#         - Reads `file_path` in chunks.
#         - Locates the heat under `event_id` -> `heat_id`, then rewrites `<field>` value.
#         - Writes to a temp file and atomically replaces the original.
#         Assumptions:
#         - JSON is reasonably formatted (quotes around strings; no exotic escaping).
#         - Works well with your meet files that have clear markers for event/heat blocks.
#         """
#         # Precompile byte regexes
#         b_event = re.compile(rb'"eventID"\s*:\s*"' + re.escape(event_id.encode()) + rb'"')
#         b_heat  = re.compile(rb'"HeatID"\s*:\s*"'   + re.escape(heat_id.encode()) + rb'"')
#         b_key   = re.compile(rb'"' + field.encode() + rb'"\s*:\s*"')
#         b_quote = re.compile(rb'"')

#         # We keep a small rollover buffer so tokens spanning chunk boundaries are seen.
#         carry = b""
#         patched = False

#         dir_name = os.path.dirname(file_path) or "."
#         fd, tmp_path = tempfile.mkstemp(prefix="json_patch_", suffix=".tmp", dir=dir_name)
#         os.close(fd)  # We'll re-open with text mode for writing

#         with open(file_path, "rb") as src, open(tmp_path, "wb") as dst:
#             while True:
#                 chunk = src.read(chunk_size)
#                 if not chunk:
#                     # flush any remaining carry
#                     if carry:
#                         dst.write(carry)
#                         carry = b""
#                     break

#                 buf = carry + chunk

#                 # If already patched, just pass-through
#                 if patched:
#                     dst.write(buf)
#                     carry = b""
#                     continue

#                 # 1) Find event marker
#                 m_event = b_event.search(buf)
#                 if not m_event:
#                     # No event marker here; write safely keeping a small tail as carry to avoid splitting tokens
#                     keep = max(0, len(buf) - 2048)
#                     dst.write(buf[:keep])
#                     carry = buf[keep:]
#                     continue

#                 # 2) From event marker forward, find heat marker
#                 m_heat = b_heat.search(buf, m_event.end())
#                 if not m_heat:
#                     # Write up to event marker and carry rest
#                     dst.write(buf[:m_event.end()])
#                     carry = buf[m_event.end():]
#                     continue

#                 # 3) From heat marker forward, find field key
#                 m_key = b_key.search(buf, m_heat.end())
#                 if not m_key:
#                     dst.write(buf[:m_heat.end()])
#                     carry = buf[m_heat.end():]
#                     continue

#                 # 4) Find the start and end of the quoted value right after key
#                 val_start = m_key.end()
#                 m_close = b_quote.search(buf, val_start)
#                 if not m_close:
#                     # carry rest until we see closing quote
#                     dst.write(buf[:val_start])
#                     carry = buf[val_start:]
#                     continue

#                 # Now we can patch: write everything up to value start, then the new value, then rest after old value
#                 dst.write(buf[:val_start])
#                 dst.write(new_value.encode("utf-8"))  # write new bytes
#                 dst.write(buf[m_close.start():])      # include closing quote and the rest
#                 patched = True
#                 carry = b""  # we consumed the whole buffer for a deterministic rewrite

#             # End loop

#         # Atomically replace original
#         if not patched:
#             # If we never patched, remove temp file
#             os.remove(tmp_path)
#             raise ValueError(f"Could not locate eventID='{event_id}', heatID='{heat_id}', field='{field}' to patch")

#             # Replace the original file atomically


            
# # Streaming rewrite patch: changes length freely and keeps memory use low
# stream_rewrite_patch(
#     file_path="/data/Shivamogga_Swim_Meet_2025.json",
#     event_id="50_FS_G03_B",
#        heat_id="50_FS_G03_B_1",
#     field="HeatNotes",
#     new_value="Re-seeded: lane 3 moved to lane 5; call-up @ 09:12"
