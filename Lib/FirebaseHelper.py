
from urllib.request import urlopen
import requests
import json
import warnings
from Lib.LogerService import Logger
from Lib.SwimDataHolder import Changeinfo
from pathlib import Path
import os
import shutil
import time
from typing import Any, Dict, List, Optional


class FireBaseHelper:
    # ----------------------------------------------------------------------
    # Public state (unchanged to preserve external API)
    # ----------------------------------------------------------------------
    SwimmerTable = ""            # List of swimmers or raw JSON loaded
    MeetID = "meetID"
    FirebaseJsonData = ""        # Last downloaded event JSON (back-compat)
    MeetName = "DefaultMeet"     # String is safer for URL paths

    # Paths (unchanged names)
    parentpath = os.path.dirname(Path(__file__).parent.absolute())
    FirebaseJSONFilePath = os.path.join(parentpath, "Data", "FirebaseJSONData_Local.json")
    FirebaseSwimmerTable = os.path.join(parentpath, "Data", "FirebaseSwimmerTable.json")
    WriteHeatResultsPath = os.path.join(parentpath, "Data", "HeatExecutionResult.json")
    WriteSwimmerTablePath = os.path.join(parentpath, "Data", "SwimmerTableResults.json")

    # Firebase endpoints (unchanged names)
    strjson = ".json"
    Eventurl = "https://eejo-managerdb-default-rtdb.firebaseio.com/Meets/"
    EventBaseurl = Eventurl + str(MeetName)  # refreshed before use
    SwimmerURL = "https://eejo-managerdb-default-rtdb.firebaseio.com/Swimmers"

    # Change trackers (unchanged name)
    ChangenidentifiedforFirebase: List[Changeinfo] = []

    # ----------------------------------------------------------------------
    # Internal config
    # ----------------------------------------------------------------------
    _HTTP_TIMEOUT_SEC = 10
    _HTTP_RETRIES = 3
    _HTTP_BACKOFF_BASE_SEC = 0.75
    _SESSION: Optional[requests.Session] = None

    # ----------------------------------------------------------------------
    # Internal helpers (unchanged internal names except snake_case)
    # ----------------------------------------------------------------------
    @classmethod
    def _ensure_session(cls) -> requests.Session:
        if cls._SESSION is None:
            s = requests.Session()
            s.headers.update({"Content-Type": "application/json"})
            cls._SESSION = s
        return cls._SESSION

    @classmethod
    def _refresh_event_base_url(cls) -> None:
        cls.EventBaseurl = cls.Eventurl + str(cls.MeetName)

    @staticmethod
    def _ensure_dir(path: str) -> None:
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)

    @classmethod
    def _patch(cls, url: str, payload: Dict[str, Any], desc: str = "") -> Optional[requests.Response]:
        session = cls._ensure_session()
        data = json.dumps(payload, ensure_ascii=False)
        for attempt in range(1, cls._HTTP_RETRIES + 1):
            try:
                r = session.patch(url, data=data, timeout=cls._HTTP_TIMEOUT_SEC)
                Logger.app_log.info("PATCH %s [%s] %s", url, r.status_code, desc)
                return r
            except Exception:
                Logger.app_log.error("PATCH failed (%s) attempt=%s", url, attempt, exc_info=True)
                if attempt < cls._HTTP_RETRIES:
                    time.sleep(cls._HTTP_BACKOFF_BASE_SEC * (2 ** (attempt - 1)))
        return None

    # ----------------------------------------------------------------------
    # Files: copy / create / delete (NEW snake_case)
    # ----------------------------------------------------------------------
    @staticmethod
    def copy_heat_file(src_path: str, dest_path: str) -> bool:
        try:
            if not os.path.exists(src_path):
                Logger.app_log.error("copy_heat_file: source does not exist: %s", src_path)
                return False
            FireBaseHelper._ensure_dir(dest_path)
            if os.path.exists(dest_path):
                os.remove(dest_path)
            shutil.copy(src_path, dest_path)
            return True
        except Exception:
            Logger.app_log.error("copy_heat_file failed", exc_info=True)
            return False

    @staticmethod
    def delete_heat_file(file_path: str) -> bool:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception:
            Logger.app_log.error("delete_heat_file failed", exc_info=True)
            return False

    @staticmethod
    def create_if_file_not_exists(file_path: str) -> bool:
        try:
            FireBaseHelper._ensure_dir(file_path)
            if not os.path.exists(file_path):
                with open(file_path, "w+", encoding="utf-8") as f:
                    f.write("")
            return True
        except Exception:
            Logger.app_log.error("create_if_file_not_exists failed", exc_info=True)
            return False

    # ----------------------------------------------------------------------
    # Network readiness
    # ----------------------------------------------------------------------
    @staticmethod
    def internet_on() -> bool:
        try:
            requests.get("http://clients3.google.com/generate_204", timeout=5)
            return True
        except Exception:
            Logger.app_log.error("internet_on check failed", exc_info=True)
            return False

    # ----------------------------------------------------------------------
    # Firebase: download helpers (NEW snake_case)
    # ----------------------------------------------------------------------
    @staticmethod
    def download_firebase_to_local(url: str, filepath: str):
        try:
            if not (FireBaseHelper.internet_on() and FireBaseHelper.create_if_file_not_exists(filepath)):
                return False
            response = urlopen(url, timeout=FireBaseHelper._HTTP_TIMEOUT_SEC)
            FireBaseHelper.FirebaseJsonData = json.loads(response.read())
            with open(filepath, "w+", encoding="utf-8") as f:
                json.dump(FireBaseHelper.FirebaseJsonData, f, ensure_ascii=False)
            return FireBaseHelper.FirebaseJsonData
        except Exception:
            Logger.app_log.error("download_firebase_to_local failed", exc_info=True)
            return False

    @staticmethod
    def download_firebase_to_local_v2(url: str, filepath: str):
        try:
            if not (FireBaseHelper.internet_on() and FireBaseHelper.create_if_file_not_exists(filepath)):
                return False
            response = urlopen(url, timeout=FireBaseHelper._HTTP_TIMEOUT_SEC)
            FireBaseHelper.SwimmerTable = json.loads(response.read())
            with open(filepath, "w+", encoding="utf-8") as f:
                json.dump(FireBaseHelper.SwimmerTable, f, ensure_ascii=False)
            return FireBaseHelper.SwimmerTable
        except Exception:
            Logger.app_log.error("download_firebase_to_local_v2 failed", exc_info=True)
            return False

    # Alias kept as a *new* snake_case public name
    download_firebase_to_local_swimmer = download_firebase_to_local_v2

    # ----------------------------------------------------------------------
    # Change detection (NEW snake_case)
    # ----------------------------------------------------------------------
    @staticmethod
    def generate_time_update_lists_for_firebase(LocalData, FirebaseData):
        try:
            if LocalData is None or FirebaseData is None:
                return [], []
            firebase_changes: List[Changeinfo] = []
            local_changes: List[Changeinfo] = []
            for event in range(0, len(LocalData)):
                heat_list_L = LocalData[event].get("HeatList", [])
                heat_list_F = FirebaseData[event].get("HeatList", []) if event < len(FirebaseData) else []
                for heat in range(0, len(heat_list_L)):
                    boards_L = heat_list_L[heat].get("BoardList", [])
                    boards_F = heat_list_F[heat].get("BoardList", []) if heat < len(heat_list_F) else []
                    for board in range(0, len(boards_L)):
                        Lb = boards_L[board]
                        Fb = boards_F[board] if board < len(boards_F) else {}
                        if Lb.get("SwimTimings") != Fb.get("SwimTimings"):
                            firebase_changes.append(Changeinfo(event, heat, board, Lb.get("SwimTimings"), 0))
                        if Lb.get("SwimerID") != Fb.get("SwimerID"):
                            local_changes.append(Changeinfo(event, heat, board, 1, 0))
            FireBaseHelper.ChangenidentifiedforFirebase = firebase_changes
            return firebase_changes, local_changes
        except Exception:
            Logger.app_log.error("generate_time_update_lists_for_firebase failed", exc_info=True)
            return [], []

    @staticmethod
    def generate_heat_update_lists_for_firebase(LocalData, FirebaseData) -> List[Changeinfo]:
        try:
            changes: List[Changeinfo] = []
            if LocalData is None or FirebaseData is None:
                return changes
            for event in range(0, len(LocalData)):
                heat_list_L = LocalData[event].get("HeatList", [])
                heat_list_F = FirebaseData[event].get("HeatList", []) if event < len(FirebaseData) else []
                for heat in range(0, len(heat_list_L)):
                    Lh = heat_list_L[heat]
                    Fh = heat_list_F[heat] if heat < len(heat_list_F) else {}
                    if Lh.get("HeatStartTime", 0) != 0:
                        if Lh.get("HeatID") == Fh.get("HeatID"):
                            if Lh != Fh:
                                changes.append(Changeinfo(event, heat, Lh, 0, 0))
            FireBaseHelper.ChangenidentifiedforFirebase = changes
            return changes
        except Exception:
            Logger.app_log.error("generate_heat_update_lists_for_firebase failed", exc_info=True)
            return []

    # ----------------------------------------------------------------------
    # Append writers (NEW snake_case)
    # ----------------------------------------------------------------------
    @staticmethod
    def append_heat_result(path: str, data_to_update: Dict[str, Any]) -> None:
        try:
            FireBaseHelper._ensure_dir(path)
            with open(path, "a+", encoding="utf-8") as json_file:
                json_file.write("{}\n".format(json.dumps(data_to_update, ensure_ascii=False)))
        except Exception:
            Logger.app_log.error("append_heat_result failed", exc_info=True)

    @staticmethod
    def append_swimmer_results(path: str, data_to_update: Dict[str, Any]) -> None:
        try:
            FireBaseHelper._ensure_dir(path)
            with open(path, "a+", encoding="utf-8") as json_file:
                json_file.write("{}\n".format(json.dumps(data_to_update, ensure_ascii=False)))
        except Exception:
            Logger.app_log.error("append_swimmer_results failed", exc_info=True)

    # ----------------------------------------------------------------------
    # Sync single / full (NEW snake_case)
    # ----------------------------------------------------------------------
    @staticmethod
    def start_syncing_single_heat(_write_path, change_info_obj) -> None:
        try:
            if not FireBaseHelper.internet_on():
                return
            FireBaseHelper._refresh_event_base_url()
            if getattr(change_info_obj, "WriteStatus", 0) == 0:
                base = FireBaseHelper.EventBaseurl
                url = f"{base}/{change_info_obj.eventID}/HeatList/{change_info_obj.heatID}/BoardList/{change_info_obj.boardID}.json"
                current_url = f"{base}/{change_info_obj.eventID}/HeatList/{change_info_obj.heatID}/BoardList/{change_info_obj.boardID}/SwimTimings.json"
                response = urlopen(current_url, timeout=FireBaseHelper._HTTP_TIMEOUT_SEC)
                current = json.loads(response.read())
                if change_info_obj.SwimTimings != current:
                    FireBaseHelper._patch(url, {"SwimTimings": change_info_obj.SwimTimings}, desc="Single board timings")
                else:
                    change_info_obj.WriteStatus = 1
                    FireBaseHelper.ChangenidentifiedforFirebase.append(change_info_obj)
        except Exception:
            Logger.app_log.error("start_syncing_single_heat failed", exc_info=True)

    @staticmethod
    def start_syncing_full_data(LocalData, FirebaseData) -> None:
        try:
            if not FireBaseHelper.internet_on():
                return
            FireBaseHelper._refresh_event_base_url()
            FireBaseHelper.ChangenidentifiedforFirebase = []
            FireBaseHelper.generate_heat_update_lists_for_firebase(LocalData, FirebaseData)
            for sync in FireBaseHelper.ChangenidentifiedforFirebase:
                if getattr(sync, "WriteStatus", 0) == 0:
                    url = f"{FireBaseHelper.EventBaseurl}/EventDetails/{sync.eventID}/HeatList/{sync.heatID}.json"
                    payload = sync.data if isinstance(sync.data, dict) else {}
                    FireBaseHelper._patch(url, payload, desc="Full heat update")
        except Exception:
            Logger.app_log.error("start_syncing_full_data failed", exc_info=True)

    # ----------------------------------------------------------------------
    # JSON I/O (NEW snake_case)
    # ----------------------------------------------------------------------
    @staticmethod
    def prepare_heat_results_to_local_json_db(HeatIDToUpdate, heatDataDisplay, data):
        try:
            events = data.get("EventDetails", []) if isinstance(data, dict) else []
            for eventID in range(0, len(events)):
                event = events[eventID]
                for heat in range(0, len(event.get("HeatList", []))):
                    heat_obj = event["HeatList"][heat]
                    if HeatIDToUpdate == heat_obj.get("HeatID"):
                        heat_obj["HeatStartTime"] = getattr(heatDataDisplay, "HeatStartTime", 0)
                        heat_obj["HeatEndTime"] = getattr(heatDataDisplay, "HeatEndTime", 0)
                        boards = heat_obj.get("BoardList", [])
                        for idx in range(0, len(boards)):
                            boards[idx]["SwimTimings"] = heatDataDisplay.SwimerBoardDetails[idx].timerValue
                            boards[idx]["SwimStatus"] = heatDataDisplay.SwimerBoardDetails[idx].swimerStatus
                        return data, heat_obj, heat, eventID
            return data, -1, -1, -1
        except Exception:
            Logger.app_log.error("prepare_heat_results_to_local_json_db failed", exc_info=True)
            return None

    @staticmethod
    def format_heat_result_file_to_proper_json_and_read(path: str):
        try:
            if FireBaseHelper.create_if_file_not_exists(path):
                with open(path, "r", encoding="utf-8") as file:
                    filedata = file.read()
                    filedata = filedata.replace("}\n{", "},{").replace("\n", "").replace("\\'", "'")
                    filedata = "[" + filedata + "]" if filedata.strip() else "[]"
                    return json.loads(filedata)
        except Exception:
            Logger.app_log.error("format_heat_result_file_to_proper_json_and_read failed", exc_info=True)
        return []

    @staticmethod
    def get_json_from_file(path: str) -> Optional[Any]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            Logger.app_log.error("get_json_from_file failed", exc_info=True)
            return None

    @staticmethod
    def set_json_to_file(data: Any, path: str) -> None:
        try:
            if FireBaseHelper.create_if_file_not_exists(path):
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
        except Exception:
            Logger.app_log.error("set_json_to_file failed", exc_info=True)

    # ----------------------------------------------------------------------
    # Swimmer Records (NEW snake_case)
    # ----------------------------------------------------------------------
    @staticmethod
    def update_heat_result_to_firebase_swim_record(updated_heat: Dict[str, Any]) -> None:
        try:
            EvetID = updated_heat["HeatID"][: updated_heat["HeatID"].rfind("_")]
            for board in updated_heat.get("BoardList", []):
                FireBaseHelper.set_results_to_swimmer_record(
                    board.get("SwimerName"),
                    "MeetID",
                    EvetID,
                    updated_heat.get("HeatEndTime"),
                    board.get("SwimTimings"),
                )
        except Exception:
            Logger.app_log.error("update_heat_result_to_firebase_swim_record failed", exc_info=True)

    @staticmethod
    def update_heat_result_to_firebase(updated_heat_data: Dict[str, Any], heatindex: int, eventIndex: int) -> None:
        try:
            FireBaseHelper._refresh_event_base_url()
            if FireBaseHelper.internet_on():
                url = f"{FireBaseHelper.EventBaseurl}/EventDetails/{eventIndex}/HeatList/{heatindex}.json"
                FireBaseHelper._patch(url, updated_heat_data, desc="Single heat update")
            else:
                time.sleep(2)
        except Exception:
            Logger.app_log.error("update_heat_result_to_firebase failed", exc_info=True)

    @staticmethod
    def set_results_to_swimmer_record(SwName: str, MeetID: str, EvetID: str, HeatDateTime: Any, timeings: Any) -> None:
        try:
            if not FireBaseHelper.internet_on():
                return
            swimmers: List[Dict[str, Any]] = FireBaseHelper.SwimmerTable if isinstance(FireBaseHelper.SwimmerTable, list) else []
            for idx in range(0, len(swimmers)):
                if swimmers[idx].get("Name") == SwName:
                    FireBaseHelper._refresh_event_base_url()
                    urltoAdd = FireBaseHelper.SwimmerURL + "/" + str(idx) + FireBaseHelper.strjson
                    swimmers[idx].setdefault("MeetResults", []).append(
                        {
                            "EventID": EvetID,
                            "HeatDateTime": HeatDateTime,
                            "MeetID": FireBaseHelper.MeetID,
                            "MyNotes": "Notes",
                            "timeings": timeings,
                        }
                    )
                    session = FireBaseHelper._ensure_session()
                    data = json.dumps(swimmers[idx], ensure_ascii=False)
                    for attempt in range(1, FireBaseHelper._HTTP_RETRIES + 1):
                        try:
                            r = session.patch(urltoAdd, data=data, timeout=FireBaseHelper._HTTP_TIMEOUT_SEC)
                            Logger.app_log.info("PATCH %s [%s] swimmer record", urltoAdd, r.status_code)
                            break
                        except Exception:
                            Logger.app_log.error("PATCH swimmer record failed attempt=%s", attempt, exc_info=True)
                            if attempt < FireBaseHelper._HTTP_RETRIES:
                                time.sleep(FireBaseHelper._HTTP_BACKOFF_BASE_SEC * (2 ** (attempt - 1)))
                    break
        except Exception:
            Logger.app_log.error("set_results_to_swimmer_record failed", exc_info=True)

    @staticmethod
    def sync_firebase_full_sw_data_with_latest_results(SyncedJsonData: Any, SwimmerTable: List[Dict[str, Any]]) -> bool:
        try:
            if SyncedJsonData is None:
                return False
            record_added = False
            for event in SyncedJsonData:
                for heat in event.get("HeatList", []):
                    for board in heat.get("BoardList", []):
                        for swimmer in SwimmerTable:
                            if swimmer.get("ID") == board.get("SwimerID"):
                                duplicate = False
                                for records in swimmer.get("MeetResults", []):
                                    if (
                                        records.get("EventID") == event.get("eventID")
                                        and records.get("MeetID") == FireBaseHelper.MeetID
                                        and records.get("HeatDateTime") == heat.get("HeatEndTime")
                                        and records.get("timeings") == board.get("SwimTimings")
                                    ):
                                        duplicate = True
                                        break
                                if not duplicate:
                                    FireBaseHelper.set_results_to_swimmer_record(
                                        swimmer.get("ID"),
                                        FireBaseHelper.MeetID,
                                        event.get("eventID"),
                                        heat.get("HeatEndTime"),
                                        board.get("SwimTimings"),
                                    )
                                    record_added = True
            return record_added
        except Exception:
            Logger.app_log.error("sync_firebase_full_sw_data_with_latest_results failed", exc_info=True)
            return False

    @staticmethod
    def sync_file_with_previous_results(JsonDataFromFirebase: Dict[str, Any], PreviousResultData: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            if PreviousResultData is None or JsonDataFromFirebase is None:
                return JsonDataFromFirebase
            events = JsonDataFromFirebase.get("EventDetails", [])
            for prev in PreviousResultData:
                for event_index in range(0, len(events)):
                    heats = events[event_index].get("HeatList", [])
                    for heat_index in range(0, len(heats)):
                        fh = heats[heat_index]
                        if prev.get("HeatID") == fh.get("HeatID"):
                            if prev != fh:
                                events[event_index]["HeatList"][heat_index] = prev
                                Logger.app_log.info("Merged previous heat: %s", prev.get("HeatID"))
            return JsonDataFromFirebase
        except Exception:
            Logger.app_log.error("sync_file_with_previous_results failed", exc_info=True)
            return JsonDataFromFirebase

    # ----------------------------------------------------------------------
    # Backward-compatible wrappers (OLD names) with deprecation warnings
    # ----------------------------------------------------------------------

    # --- Files
    @staticmethod
    def CopyHeatFile(FileSourcePath: str, FileDestPath: str) -> bool:
        warnings.warn("CopyHeatFile is deprecated; use copy_heat_file", DeprecationWarning, stacklevel=2)
        return FireBaseHelper.copy_heat_file(FileSourcePath, FileDestPath)

    @staticmethod
    def DeleteHeatFile(file_path: str) -> bool:
        warnings.warn("DeleteHeatFile is deprecated; use delete_heat_file", DeprecationWarning, stacklevel=2)
        return FireBaseHelper.delete_heat_file(file_path)

    @staticmethod
    def CreateifFiledontExists(file_path: str) -> bool:
        warnings.warn("CreateifFiledontExists is deprecated; use create_if_file_not_exists", DeprecationWarning, stacklevel=2)
        return FireBaseHelper.create_if_file_not_exists(file_path)

    # --- Downloads
    @staticmethod
    def DownloadFirebaseToLocal(url: str, Filepath: str):
        warnings.warn("DownloadFirebaseToLocal is deprecated; use download_firebase_to_local", DeprecationWarning, stacklevel=2)
        return FireBaseHelper.download_firebase_to_local(url, Filepath)

    @staticmethod
    def DownloadFirebaseToLocal_v2(url: str, Filepath: str):
        warnings.warn("DownloadFirebaseToLocal_v2 is deprecated; use download_firebase_to_local_v2", DeprecationWarning, stacklevel=2)
        return FireBaseHelper.download_firebase_to_local_v2(url, Filepath)

    DownloadFirebaseToLocal_Swimmer = download_firebase_to_local_v2  # legacy alias retained

    # --- Change detection
    @staticmethod
    def generateTimeUpdateListsforFirebase(LocalData, FirebaseData):
        warnings.warn("generateTimeUpdateListsforFirebase is deprecated; use generate_time_update_lists_for_firebase", DeprecationWarning, stacklevel=2)
        return FireBaseHelper.generate_time_update_lists_for_firebase(LocalData, FirebaseData)

    @staticmethod
    def generateHeatUpdateListsforFirebase(LocalData, FirebaseData) -> List[Changeinfo]:
        warnings.warn("generateHeatUpdateListsforFirebase is deprecated; use generate_heat_update_lists_for_firebase", DeprecationWarning, stacklevel=2)
        return FireBaseHelper.generate_heat_update_lists_for_firebase(LocalData, FirebaseData)

    # --- Append writers
    @staticmethod
    def AppendHeatResult(AppendJsonPath: str, dataToUpdate: Dict[str, Any]) -> None:
        warnings.warn("AppendHeatResult is deprecated; use append_heat_result", DeprecationWarning, stacklevel=2)
        return FireBaseHelper.append_heat_result(AppendJsonPath, dataToUpdate)

    @staticmethod
    def AppendSwimmerResults(AppendJsonPath: str, dataToUpdate: Dict[str, Any]) -> None:
        warnings.warn("AppendSwimmerResults is deprecated; use append_swimmer_results", DeprecationWarning, stacklevel=2)
        return FireBaseHelper.append_swimmer_results(AppendJsonPath, dataToUpdate)

    # --- Sync
    @staticmethod
    def StartSyncingSingleHeat(WriteHeatResultsPath, Changeinfoobj) -> None:
        warnings.warn("StartSyncingSingleHeat is deprecated; use start_syncing_single_heat", DeprecationWarning, stacklevel=2)
        return FireBaseHelper.start_syncing_single_heat(WriteHeatResultsPath, Changeinfoobj)

    @staticmethod
    def StartSyncingfullData(LocalData, FirebaseData) -> None:
        warnings.warn("StartSyncingfullData is deprecated; use start_syncing_full_data", DeprecationWarning, stacklevel=2)
        return FireBaseHelper.start_syncing_full_data(LocalData, FirebaseData)

    # --- JSON I/O
    @staticmethod
    def PrepareHeatResultstoLocalJSONDB(HeatIDToUpdate, heatDataDisplay, data):
        warnings.warn("PrepareHeatResultstoLocalJSONDB is deprecated; use prepare_heat_results_to_local_json_db", DeprecationWarning, stacklevel=2)
        return FireBaseHelper.prepare_heat_results_to_local_json_db(HeatIDToUpdate, heatDataDisplay, data)

    @staticmethod
    def FormatHeatresultFiletoProperJSONandRead(ReadJsonPath: str):
        warnings.warn("FormatHeatresultFiletoProperJSONandRead is deprecated; use format_heat_result_file_to_proper_json_and_read", DeprecationWarning, stacklevel=2)
        return FireBaseHelper.format_heat_result_file_to_proper_json_and_read(ReadJsonPath)

    @staticmethod
    def GetJSONFromFile(ReadJsonPath: str) -> Optional[Any]:
        warnings.warn("GetJSONFromFile is deprecated; use get_json_from_file", DeprecationWarning, stacklevel=2)
        return FireBaseHelper.get_json_from_file(ReadJsonPath)

    @staticmethod
    def SetJSONToFile(data: Any, WriteJsonPath: str) -> None:
        warnings.warn("SetJSONToFile is deprecated; use set_json_to_file", DeprecationWarning, stacklevel=2)
        return FireBaseHelper.set_json_to_file(data, WriteJsonPath)

    # --- Swimmer records
    @staticmethod
    def UpdateHeatResultToFirebaseSwimRecord(UpdatedHeat: Dict[str, Any]) -> None:
        warnings.warn("UpdateHeatResultToFirebaseSwimRecord is deprecated; use update_heat_result_to_firebase_swim_record", DeprecationWarning, stacklevel=2)
        return FireBaseHelper.update_heat_result_to_firebase_swim_record(UpdatedHeat)

    @staticmethod
    def UpdateHeatResultToFirebase(UpdtatedHeatData: Dict[str, Any], heatindex: int, eventIndex: int) -> None:
        warnings.warn("UpdateHeatResultToFirebase is deprecated; use update_heat_result_to_firebase", DeprecationWarning, stacklevel=2)
        return FireBaseHelper.update_heat_result_to_firebase(UpdtatedHeatData, heatindex, eventIndex)

    @staticmethod
    def SetResultsToSwimmerRecord(SwName: str, MeetID: str, EvetID: str, HeatDateTime: Any, timeings: Any) -> None:
        warnings.warn("SetResultsToSwimmerRecord is deprecated; use set_results_to_swimmer_record", DeprecationWarning, stacklevel=2)
        return FireBaseHelper.set_results_to_swimmer_record(SwName, MeetID, EvetID, HeatDateTime, timeings)

    @staticmethod
    def SyncFirebasefullSwDatawithlatestResults(SyncedJsonData: Any, SwimmerTable: List[Dict[str, Any]]) -> bool:
        warnings.warn("SyncFirebasefullSwDatawithlatestResults is deprecated; use sync_firebase_full_sw_data_with_latest_results", DeprecationWarning, stacklevel=2)
        return FireBaseHelper.sync_firebase_full_sw_data_with_latest_results(SyncedJsonData, SwimmerTable)

    @staticmethod
    def SyncFileWithpreviousResults(JsonDataFromFirebase: Dict[str, Any], PreviousResultData: List[Dict[str, Any]]) -> Dict[str, Any]:
        warnings.warn("SyncFileWithpreviousResults is deprecated; use sync_file_with_previous_results", DeprecationWarning, stacklevel=2)
        return FireBaseHelper.sync_file_with_previous_results(JsonDataFromFirebase,PreviousResultData)