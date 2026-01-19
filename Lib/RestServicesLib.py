
from __future__ import annotations
from fastapi import FastAPI, Request, Query, Body
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from jinja2 import TemplateNotFound
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import socket
import time
import os

# Project libs (unchanged)
from Lib.StopwatchLib import StopTimerService
from Lib.SwimDataHolder import HeatDataDisplay, TimerStatus
from Lib.JsonLib import JsonHelper, PathError, ParamUpdateHelper
from Lib.FirebaseHelper import FireBaseHelper
from Lib.ModbusLib import ModbusLibcls
from Lib.LogerService import Logger
from Lib.UtilityFunctions import UtilityFunctions



class RestServicecls:
    """
    FastAPI replacement of your Flask REST service while keeping
    the same public surface (routes, parameters, states).
    """

    # ---- App & runtime state ----
    host_name: str = "0.0.0.0"
    port: int = 5002
    app = FastAPI(title="Eejo Timer REST", version="2.0-fastapi")

    # CORS: open as before (adjust for production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Templates (adjust to your repository structure)
    # Example: PROJECT_ROOT / "Eejo" / "templates"
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    _TEMPLATE_DIR = PROJECT_ROOT / "Eejo" / "templates"
    if not _TEMPLATE_DIR.exists():  # fallback to local "templates" beside this file
        _TEMPLATE_DIR = Path(__file__).parent / "templates"
    templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))

    # State mirrored from your original class
    StopTimerServiceclsobj = StopTimerService()
    InitStatus: int = 0
    NextSetHeatID: str = "WaitingToStart"
    AutoFindHeat: int = 1
    TimerState: str = ""
    TimerStateMessage: str = ""
    Synced_JSONData: Optional[Dict[str, Any]] = None
    hostIP: str = ""

    # -----------------------------
    # Utility helpers
    # -----------------------------
    @staticmethod
    def _ok(payload: Dict[str, Any], status: int = 200) -> JSONResponse:
        return JSONResponse(payload, status_code=status)

    @staticmethod
    def _err(message: str, status: int = 500) -> JSONResponse:
        Logger.app_log.error(message)
        return JSONResponse({"status": "error", "message": message}, status_code=status)

    @staticmethod
    async def _get_param(request: Request, key: str, default: Optional[Any] = None) -> Optional[Any]:
        """
        Read a param from query string or JSON body to remain backward compatible
        with clients that send GET or POST JSON.
        """
        # Query string
        if key in request.query_params:
            return request.query_params.get(key)
        # JSON body (if any)
        try:
            body = await request.json()
            if isinstance(body, dict):
                return body.get(key, default)
        except Exception:
            pass
        return default

    @staticmethod
    def _ensure_json_obj(json_str_or_obj: Any) -> Dict[str, Any]:
        if isinstance(json_str_or_obj, dict):
            return json_str_or_obj
        import json as _json
        return _json.loads(json_str_or_obj)

    @staticmethod
    def _parse_event_id_from_heat_name(heat_name: str, event_list: List[str]) -> int:
        if not heat_name or "_" not in heat_name:
            return 0
        last_us = heat_name.rfind("_")
        trimmed = heat_name[:last_us] if last_us != -1 else heat_name
        try:
            return event_list.index(trimmed) + 1 if trimmed in event_list else 0
        except Exception:
            return 0

    @staticmethod
    def _build_board_status_and_time(heat_data: HeatDataDisplay) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        if not heat_data or not hasattr(heat_data, "SwimerBoardDetails"):
            return result
        for board in heat_data.SwimerBoardDetails:
            result.append(
                {
                    "BoardID": board.boardId,
                    "Time": board.timerValue,
                    "Status": board.swimerStatus,
                    "LockStatus": board.LockTime,
                }
            )
        return result

    @staticmethod
    def _get_swimmer_clubs(sw_names: List[str], synced_json: Dict[str, Any]) -> List[str]:
        clubs: List[str] = []
        for name in sw_names:
            clubs.append(
                synced_json.get("SwimmerDetails", {}).get(name, {}).get("Club", "Undefined")
            )
        return clubs

    @staticmethod
    def _safe_heat_display() -> Optional[HeatDataDisplay]:
        try:
            return StopTimerService.heatDataDisplay
        except Exception:
            return None

    @staticmethod
    def GetRestIP() -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            RestServicecls.hostIP = s.getsockname()[0]
            s.close()
        except Exception:
            try:
                RestServicecls.hostIP = socket.gethostbyname(socket.gethostname())
            except Exception:
                RestServicecls.hostIP = "0.0.0.0"
        return RestServicecls.hostIP

    # -----------------------------
    # Data IO helpers
    # -----------------------------
    @staticmethod
    def ReadHeatFromLocalDisk(HeatFileDiskpath: str):
        return FireBaseHelper.get_json_from_file(HeatFileDiskpath)

    @staticmethod
    def ReadHeatFromLocalFile(HeatFileName: str):
        parent = os.path.dirname(Path(__file__).parent.absolute())
        full_path = os.path.join(parent, "Data", "Heats", HeatFileName)
        return FireBaseHelper.get_json_from_file(full_path)

    @staticmethod
    def LoadHeatFromLocalFile(HeatFileName: str):
        parent = os.path.dirname(Path(__file__).parent.absolute())
        full_path = os.path.join(parent, "Data", "Heats", HeatFileName)
        FireBaseHelper.FirebaseJsonData = FireBaseHelper.get_json_from_file(full_path)
        return FireBaseHelper.FirebaseJsonData

    @staticmethod
    def SaveHeatFileToLocalFile(HeatData: str, FileNametoSave: str, path: str = "") -> JSONResponse:
        try:
            payload = RestServicecls._ensure_json_obj(HeatData)
            parent = os.path.dirname(Path(__file__).parent.absolute())
            dest_path = os.path.join(parent, "Data", "Heats", FileNametoSave) if path == "" else path
            FireBaseHelper.create_if_file_not_exists(dest_path)
            FireBaseHelper.set_json_to_file(payload, dest_path)
            return RestServicecls._ok({"SaveHeatFileToLocalFile": "OK"})
        except Exception as e:
            Logger.app_log.exception("Failed to save heat file")
            return RestServicecls._err(str(e))

    # -----------------------------
    # Data sync paths
    # -----------------------------
    @staticmethod
    def LoadDataFromLocalFile(FileNametoRead: str, OverWriteOption: int = 0, HeatFilepathToRead: str = "") -> Dict[str, Any]:
        StopTimerService.HeatStatus = TimerStatus.WaitingToStart
        parent = os.path.dirname(Path(__file__).parent.absolute())
        if HeatFilepathToRead == "":
            HeatFilepathToRead = os.path.join(parent, "Data", "Heats", FileNametoRead)
        if OverWriteOption == 0:
            FireBaseHelper.delete_heat_file(FireBaseHelper.FirebaseJSONFilePath)
            FireBaseHelper.delete_heat_file(FireBaseHelper.FirebaseSwimmerTable)
            FireBaseHelper.delete_heat_file(FireBaseHelper.WriteHeatResultsPath)
            FireBaseHelper.copy_heat_file(HeatFilepathToRead, FireBaseHelper.FirebaseJSONFilePath)
            Synced_JSONData = FireBaseHelper.get_json_from_file(FireBaseHelper.FirebaseJSONFilePath)
        elif OverWriteOption == 1:
            s = time.gmtime()
            FirebaseJSONFilePath_bak = os.path.join(parent, "Backup",
                FireBaseHelper.FirebaseJsonData["MeetName"] + "_" + time.strftime("%Y_%m_%d_%H_%M_%S", s) + ".json")
            FirebaseSwimmerTable_bak = os.path.join(parent, "Backup",
                FireBaseHelper.FirebaseJsonData["MeetName"] + "_SwTable_" + time.strftime("%Y_%m_%d_%H_%M_%S", s) + ".json")
            WriteHeatResultsPath_bak = os.path.join(parent, "Backup",
                FireBaseHelper.FirebaseJsonData["MeetName"] + "_HeatEx_" + time.strftime("%Y_%m_%d_%H_%M_%S", s) + ".json")
            FireBaseHelper.copy_heat_file(FireBaseHelper.FirebaseJSONFilePath, FirebaseJSONFilePath_bak)
            FireBaseHelper.copy_heat_file(FireBaseHelper.FirebaseSwimmerTable, FirebaseSwimmerTable_bak)
            FireBaseHelper.copy_heat_file(FireBaseHelper.WriteHeatResultsPath, WriteHeatResultsPath_bak)
            FireBaseHelper.delete_heat_file(FireBaseHelper.FirebaseJSONFilePath)
            FireBaseHelper.delete_heat_file(FireBaseHelper.FirebaseSwimmerTable)
            FireBaseHelper.delete_heat_file(FireBaseHelper.WriteHeatResultsPath)
            FireBaseHelper.copy_heat_file(HeatFilepathToRead, FireBaseHelper.FirebaseJSONFilePath)
            Synced_JSONData = FireBaseHelper.get_json_from_file(FireBaseHelper.FirebaseJSONFilePath)
        elif OverWriteOption == 2:
            FireBaseHelper.copy_heat_file(HeatFilepathToRead, FireBaseHelper.FirebaseJSONFilePath)
            Synced_JSONData = FireBaseHelper.get_json_from_file(FireBaseHelper.FirebaseJSONFilePath)
            PreviousLocalResultData = FireBaseHelper.FormatHeatresultFiletoProperJSONandRead(FireBaseHelper.WriteHeatResultsPath)
            Synced_JSONData = FireBaseHelper.sync_file_with_previous_results(Synced_JSONData, PreviousLocalResultData)
        else:
            FireBaseHelper.copy_heat_file(HeatFilepathToRead, FireBaseHelper.FirebaseJSONFilePath)
            Synced_JSONData = FireBaseHelper.get_json_from_file(FireBaseHelper.FirebaseJSONFilePath)
        RestServicecls.InitStatus = 0
        RestServicecls.Synced_JSONData = Synced_JSONData
        return Synced_JSONData

    @staticmethod
    def LoaDataFromFirebaseData(URLToSync: str, OverWriteOption: int = 0) -> Dict[str, Any]:
        StopTimerService.HeatStatus = TimerStatus.WaitingToStart
        parent = os.path.dirname(Path(__file__).parent.absolute())
        s = time.gmtime()
        if OverWriteOption == 0:
            FireBaseHelper.delete_heat_file(FireBaseHelper.FirebaseJSONFilePath)
            FireBaseHelper.delete_heat_file(FireBaseHelper.FirebaseSwimmerTable)
            FireBaseHelper.delete_heat_file(FireBaseHelper.WriteHeatResultsPath)
            FireBaseHelper.DownloadFirebaseToLocal(URLToSync + FireBaseHelper.strjson, FireBaseHelper.FirebaseJSONFilePath)
            Synced_JSONData = FireBaseHelper.get_json_from_file(FireBaseHelper.FirebaseJSONFilePath)
        elif OverWriteOption == 1:
            FirebaseJSONFilePath_bak = os.path.join(parent, "Backup",
                FireBaseHelper.FirebaseJsonData["MeetName"] + "_" + time.strftime("%Y_%m_%d_%H_%M_%S", s) + ".json")
            FirebaseSwimmerTable_bak = os.path.join(parent, "Backup",
                FireBaseHelper.FirebaseJsonData["MeetName"] + "_SwTable_" + time.strftime("%Y_%m_%d_%H_%M_%S", s) + ".json")
            WriteHeatResultsPath_bak = os.path.join(parent, "Backup",
                FireBaseHelper.FirebaseJsonData["MeetName"] + "_HeatEx_" + time.strftime("%Y_%m_%d_%H_%M_%S", s) + ".json")
            FireBaseHelper.copy_heat_file(FireBaseHelper.FirebaseJSONFilePath, FirebaseJSONFilePath_bak)
            FireBaseHelper.copy_heat_file(FireBaseHelper.FirebaseSwimmerTable, FirebaseSwimmerTable_bak)
            FireBaseHelper.copy_heat_file(FireBaseHelper.WriteHeatResultsPath, WriteHeatResultsPath_bak)
            FireBaseHelper.delete_heat_file(FireBaseHelper.FirebaseJSONFilePath)
            FireBaseHelper.delete_heat_file(FireBaseHelper.FirebaseSwimmerTable)
            FireBaseHelper.delete_heat_file(FireBaseHelper.WriteHeatResultsPath)
            FireBaseHelper.DownloadFirebaseToLocal(URLToSync + FireBaseHelper.strjson, FireBaseHelper.FirebaseJSONFilePath)
            Synced_JSONData = FireBaseHelper.get_json_from_file(FireBaseHelper.FirebaseJSONFilePath)
        elif OverWriteOption == 2:
            FireBaseHelper.DownloadFirebaseToLocal(URLToSync + FireBaseHelper.strjson, FireBaseHelper.FirebaseJSONFilePath)
            PreviousLocalResultData = FireBaseHelper.FormatHeatresultFiletoProperJSONandRead(FireBaseHelper.WriteHeatResultsPath)
            Synced_JSONData = FireBaseHelper.sync_file_with_previous_results(FireBaseHelper.FirebaseJsonData, PreviousLocalResultData)
        RestServicecls.Synced_JSONData = Synced_JSONData
        RestServicecls.InitStatus = 0
        return Synced_JSONData

    @staticmethod
    def InitTimerStart() -> Dict[str, Any]:
        Synced_JSONData: Dict[str, Any] = {}
        try:
            StopTimerService.HeatStatus = TimerStatus.WaitingToStart
            FireBaseHelper.FirebaseJsonData = FireBaseHelper.get_json_from_file(FireBaseHelper.FirebaseJSONFilePath)
            if FireBaseHelper.FirebaseJsonData is not None:
                RestServicecls.init_ComServices(FireBaseHelper.FirebaseJsonData["BoardSettings"])
                FireBaseHelper.MeetName = FireBaseHelper.FirebaseJsonData["FireBaseName"]
                FireBaseHelper.EventBaseurl = FireBaseHelper.Eventurl +FireBaseHelper.MeetName
                FireBaseHelper.SwimmerTable = FireBaseHelper.get_json_from_file(FireBaseHelper.FirebaseSwimmerTable)
                PreviousLocalResultData = FireBaseHelper.FormatHeatresultFiletoProperJSONandRead(FireBaseHelper.WriteHeatResultsPath)
                parent = os.path.dirname(Path(__file__).parent.absolute())
                s = time.gmtime()
                FirebaseJSONFilePath_bak = os.path.join(parent, "Backup",
                    FireBaseHelper.FirebaseJsonData["MeetName"] + "_" + time.strftime("%Y_%m_%d_%H_%M_%S", s) + ".json")
                FirebaseSwimmerTable_bak = os.path.join(parent, "Backup",
                    FireBaseHelper.FirebaseJsonData["MeetName"] + "_SwTable_" + time.strftime("%Y_%m_%d_%H_%M_%S", s) + ".json")
                WriteHeatResultsPath_bak = os.path.join(parent, "Backup",
                    FireBaseHelper.FirebaseJsonData["MeetName"] + "_HeatEx_" + time.strftime("%Y_%m_%d_%H_%M_%S", s) + ".json")
                # Backups
                FireBaseHelper.copy_heat_file(FireBaseHelper.FirebaseJSONFilePath, FirebaseJSONFilePath_bak)
                FireBaseHelper.copy_heat_file(FireBaseHelper.FirebaseSwimmerTable, FirebaseSwimmerTable_bak)
                FireBaseHelper.copy_heat_file(FireBaseHelper.WriteHeatResultsPath, WriteHeatResultsPath_bak)
                Synced_JSONData = FireBaseHelper.FirebaseJsonData
                Synced_JSONData = FireBaseHelper.sync_file_with_previous_results(FireBaseHelper.FirebaseJsonData, PreviousLocalResultData)
                # Clear and recreate current files
                FireBaseHelper.delete_heat_file(FireBaseHelper.FirebaseJSONFilePath)
                FireBaseHelper.delete_heat_file(FireBaseHelper.FirebaseSwimmerTable)
                FireBaseHelper.delete_heat_file(FireBaseHelper.WriteHeatResultsPath)
                FireBaseHelper.create_if_file_not_exists(FireBaseHelper.FirebaseJSONFilePath)
                FireBaseHelper.set_json_to_file(Synced_JSONData, FireBaseHelper.FirebaseJSONFilePath)
                FireBaseHelper.create_if_file_not_exists(FireBaseHelper.WriteHeatResultsPath)
                # Full data sync to Firebase
                FireBaseHelper.StartSyncingfullData(Synced_JSONData, FireBaseHelper.FirebaseJsonData)
        except Exception:
            Logger.app_log.exception("InitTimerStart failed")
        return Synced_JSONData

    @staticmethod
    def GetNextHeatID(data: Dict[str, Any]) -> Tuple[str, str]:
        if RestServicecls.AutoFindHeat == 1:
            HeatID, EventID = JsonHelper.get_next_heat_id_from_file(data)
        else:
            HeatID = RestServicecls.NextSetHeatID
            EventID = ""
        RestServicecls.NextSetHeatID = HeatID
        RestServicecls.TimerState = "State"
        RestServicecls.TimerStateMessage = "NewHeat"
        return HeatID, EventID

    @staticmethod
    def init_ComServices(BoardSettingsJson: Dict[str, Any]) -> None:
        try:
            ModbusLibcls.ConnecttoDevice(BoardSettingsJson["CommSettings"])
            SideA = BoardSettingsJson["IOSettings"]["Side-A"]
            SideB = BoardSettingsJson["IOSettings"]["Side-B"]
            PrimarySide = BoardSettingsJson["IOSettings"]["PrimerySide"]
            StopTimerService.SIDE_A_SwBits = SideA
            StopTimerService.SIDE_B_SwBits = SideB
            StopTimerService.StopWatchInputPins = SideB if PrimarySide else SideA
            StopTimerService.MODSwitchBits = StopTimerService.StopWatchInputPins
            Logger.app_log.info("Modbus device connected.")
        except Exception as e:
            Logger.app_log.error("Modbus connection failed", exc_info=e)


app = RestServicecls.app  # FastAPI app alias for uvicorn

# -----------------------------
# Routes (FastAPI)
# -----------------------------
@app.get("/SetUpdateSettings")
def SetUpdateSettings():
    Logger.app_log.info("SetUpdateSettings called")
    return RestServicecls._ok({"status": "OK"})


@app.get("/getAvailableHeatNames")
def getAvailableHeatNames():
    try:
        parent = os.path.dirname(Path(__file__).parent.absolute())
        heats_dir = os.path.join(parent, "Data", "Heats")
        heat_files = [f for f in os.listdir(heats_dir) if f.endswith(".EejoHeat")]
        return RestServicecls._ok({"HeatFiles": heat_files})
    except Exception as e:
        Logger.app_log.exception("Failed to list heat files")
        return RestServicecls._err(str(e))


@app.get("/")
def index(request: Request):
    try:
        return RestServicecls.templates.TemplateResponse("LiveDisplayPage.html", {"request": request})
    except TemplateNotFound:
        Logger.app_log.error("LiveDisplayPage.html not found in %s", RestServicecls._TEMPLATE_DIR)
        return HTMLResponse(
            f"<h2>Template not found</h2><p>Looked in: {RestServicecls._TEMPLATE_DIR}</p>",
            status_code=500
        )


@app.get("/TimeKeeper")
def TimeKeeper(request: Request):
    return RestServicecls.templates.TemplateResponse("TimeKeeper.html", {"request": request})


@app.get("/MeetEditor")
def MeetEditor(request: Request):
    try:
        return RestServicecls.templates.TemplateResponse("MeetReportGenerator.html", {"request": request})
    except Exception:
        Logger.app_log.exception("MeetEditor template error")
        return RestServicecls._err("Template error", 500)


@app.get("/LiveControl")
def LiveCtrl(request: Request):
    return RestServicecls.templates.TemplateResponse("EejoTimerControl.html", {"request": request})


@app.get("/Reports")
def Reports(request: Request):
    return RestServicecls.templates.TemplateResponse("MultiSelectTest.html", {"request": request})


@app.get("/GetHeatHeader")
def GetHeatHeader():
    heat_data = RestServicecls._safe_heat_display()
    if not heat_data:
        return RestServicecls._err("No heat loaded", 404)
    header = {
        "eventID": heat_data.eventID,
        "EventName": heat_data.eventName,
        "HeatID": heat_data.HeatID,
        "HeatStartTime": heat_data.HeatStartTime,
        "HeatEndTime": heat_data.HeatEndTime,
    }
    return RestServicecls._ok({"HeatDetails": header})


@app.get("/DownloadFBToLoaclFile")
def DownloadFBToLoaclFile():
    try:
        FireBaseHelper.DownloadFirebaseToLocal(FireBaseHelper.EventBaseurl + FireBaseHelper.strjson,
                                               FireBaseHelper.JSONFilePath)
        return RestServicecls._ok({'HeatDetails': f"Downloading successful at {FireBaseHelper.JSONFilePath}"})
    except Exception as ex:
        Logger.app_log.exception("DownloadFBToLoaclFile failed")
        return RestServicecls._err(str(ex), 500)


@app.get("/GetTimerState")
def GetTimerState():
    try:
        return RestServicecls._ok({'TimerState': str(RestServicecls.TimerState),
                                   'Message': str(RestServicecls.TimerStateMessage)})
    except Exception as ex:
        Logger.app_log.exception("GetTimerState failed")
        return RestServicecls._err(str(ex), 500)







@app.post("/UpdateParam")
async def UpdateParam(
    request: Request,
    payload: dict = Body(..., description="""
        Accepts either:
         1) {"path": "...", "value": ...}  # global or nested path (dot/bracket or JSON Pointer)
         2) {"eventID": "...", "heatID": "...", "pathUnderHeat": "BoardList[2].SwimerName", "value": "..."}
         3) {"eventID": "...", "heatIndex": 0, "pathUnderHeat": "BoardList[0].SwimTimings", "value": 12.34}
         4) {"modifiedText": "..."}  # to load/normalize a full meet in modified format
    """)
):
    """
    - If 'modifiedText' is present, normalize & set as active JSON.
    - Else, update either:
       a) an absolute path in the active JSON, or
       b) an event's heat by eventID + (heatID or heatIndex) and a relative path inside that heat.
    Persists to FirebaseJSONFilePath and updates Synced_JSONData.
    """
    try:
        data = RestServicecls.Synced_JSONData
        if data is None:
            # fallback from file
            data = FireBaseHelper.get_json_from_file(FireBaseHelper.FirebaseJSONFilePath)

        # Option 4: full ingest from modified text
        if "modifiedText" in payload and isinstance(payload["modifiedText"], str):
            normalized = ParamUpdateHelper.normalize_modified_meet_text(payload["modifiedText"])
            RestServicecls.Synced_JSONData = normalized
            FireBaseHelper.create_if_file_not_exists(FireBaseHelper.FirebaseJSONFilePath)
            FireBaseHelper.set_json_to_file(normalized, FireBaseHelper.FirebaseJSONFilePath)
            return RestServicecls._ok({"status": "ingested", "EventCount": len(normalized.get("EventDetails", []))}, 200)

        if not isinstance(data, (dict, list)):
            return RestServicecls._err("Active JSON must be an object/list", 400)

        # Option 1: direct path update
        if "path" in payload and "value" in payload:
            ParamUpdateHelper.set_value_at_path(data, payload["path"], payload["value"])
        # Option 2/3: event/heat‑relative update
        elif "eventID" in payload and "pathUnderHeat" in payload and "value" in payload:
            ev_i = ParamUpdateHelper.find_event_index(data, payload["eventID"])
            if ev_i < 0: return RestServicecls._err(f"eventID '{payload['eventID']}' not found", 404)
            ev = data["EventDetails"][ev_i]
            # Resolve heat
            if "heatID" in payload:
                h_i = ParamUpdateHelper.find_heat_index(ev, payload["heatID"])
                if h_i < 0: return RestServicecls._err(f"heatID '{payload['heatID']}' not found", 404)
            else:
                h_i = int(payload.get("heatIndex", -1))
                if h_i < 0 or h_i >= len(ev.get("HeatList", [])):
                    return RestServicecls._err("Invalid heatIndex", 400)
            # Apply relative path inside the chosen heat object
            rel_path = f"EventDetails[{ev_i}].HeatList[{h_i}].{payload['pathUnderHeat']}"
            ParamUpdateHelper.set_value_at_path(data, rel_path, payload["value"])
        else:
            return RestServicecls._err("Provide either {path,value}, or {eventID, (heatID|heatIndex), pathUnderHeat, value}, or {modifiedText}", 400)

        # Persist
        RestServicecls.Synced_JSONData = data
        FireBaseHelper.create_if_file_not_exists(FireBaseHelper.FirebaseJSONFilePath)
        FireBaseHelper.set_json_to_file(data, FireBaseHelper.FirebaseJSONFilePath)

        return RestServicecls._ok({"status": "success"}, 200)
    except PathError as pe:
        return RestServicecls._err(f"Path error: {pe}", 400)
    except Exception as ex:
        Logger.app_log.exception("UpdateParam failed")
        return RestServicecls._err(str(ex), 500)








@app.post("/SetLiveHeatDataCommands")
async def SetLiveHeatDataCommands(request: Request):
    try:
        commandname = await RestServicecls._get_param(request, 'CmdName', '')
        data = (await request.json()) if request.headers.get("content-type", "").startswith("application/json") else {}
        if not commandname:
            return RestServicecls._err("CmdName required", 400)

        if commandname == 'SetRunningHeatData':
            RestServicecls.InitStatus = 1
            RestServicecls.Synced_JSONData = data
            RestServicecls.InitStatus = 0
            StopTimerService.StartRestcommand = 3
            StopTimerService.set_heat_status(TimerStatus.WaitingToStart)
            FireBaseHelper.create_if_file_not_exists(FireBaseHelper.FirebaseJSONFilePath)
            FireBaseHelper.set_json_to_file(RestServicecls.Synced_JSONData, FireBaseHelper.FirebaseJSONFilePath)
            StopTimerService.ResetTimer()
            return RestServicecls._ok({"status": "success", "data": {}}, 200)
        
        elif commandname == 'SetSelectedData':
            RestServicecls.InitStatus = 1
            RestServicecls.Synced_JSONData = data
            RestServicecls.InitStatus = 0
            StopTimerService.StartRestcommand = 3
            StopTimerService.set_heat_status(TimerStatus.WaitingToStart)
            FireBaseHelper.create_if_file_not_exists(FireBaseHelper.FirebaseJSONFilePath)
            FireBaseHelper.set_json_to_file(RestServicecls.Synced_JSONData, FireBaseHelper.FirebaseJSONFilePath)
            StopTimerService.ResetTimer()
            return RestServicecls._ok({"status": "success", "data": {}}, 200)


        return RestServicecls._err("Unsupported CmdName", 400)
    except Exception as e:
        Logger.app_log.exception("SetLiveHeatDataCommands failed")
        return RestServicecls._err(str(e), 500)


@app.get("/InitFirebaseData")
def InitFirebaseData(URLToSync: str = Query(..., description="Firebase base URL")):
    try:
        FireBaseHelper.EventBaseurl = URLToSync
        RestServicecls.NextSetHeatID = "WaitingToStart"
        StopTimerService.HeatStatus = TimerStatus.WaitingToStart
        FireBaseHelper.DownloadFirebaseToLocal(FireBaseHelper.EventBaseurl + FireBaseHelper.strjson,
                                               FireBaseHelper.FirebaseJSONFilePath)
        JsonData = FireBaseHelper.get_json_from_file(FireBaseHelper.FirebaseJSONFilePath)
        PreviousResultData = FireBaseHelper.FormatHeatresultFiletoProperJSONandRead(FireBaseHelper.WriteHeatResultsPath)
        JsonData = FireBaseHelper.sync_file_with_previous_results(JsonData, PreviousResultData)
        FireBaseHelper.StartSyncingfullData(JsonData, JsonData)
        FireBaseHelper.LoadSwimmerTable()
        return RestServicecls._ok({'HeatDetails': "OK"})
    except Exception:
        Logger.app_log.exception("InitFirebaseData failed")
        return RestServicecls._ok({'HeatDetails': "NOK"})


@app.get("/SetLiveHeatCommands")
async def SetLiveHeatCommands(request: Request):
    try:
        commandname = await RestServicecls._get_param(request, 'CmdName', '')
        command_return_data: Dict[str, Any] = {}

        if commandname == 'CurrentBitAlocation':
            command_return_data = {
                'SIDE_A_SwBits': getattr(StopTimerService, "SIDE_A_SwBits", []),
                'SIDE_B_SwBits': getattr(StopTimerService, "SIDE_B_SwBits", []),
            }

        elif commandname == 'SetBitAlocation':
            req_side_a = await RestServicecls._get_param(request, 'SIDE_A_SwBits', '')
            req_side_b = await RestServicecls._get_param(request, 'SIDE_B_SwBits', '')
            primery_side = await RestServicecls._get_param(request, 'PrimerySide', 'PrimeryA')
            StopTimerService.SIDE_A_SwBits = [int(x) for x in str(req_side_a).split(",") if x]
            StopTimerService.SIDE_B_SwBits = [int(x) for x in str(req_side_b).split(",") if x]
            StopTimerService.MODSwitchBits = (
                StopTimerService.SIDE_B_SwBits if primery_side == "PrimeryB" else StopTimerService.SIDE_A_SwBits
            )

        elif commandname == 'StopWatchSwStatus':
            command_return_data = {'StopWatchSwStatus': ModbusLibcls.StopWatchSwStatus}

        elif commandname == 'showQRDisplay':
            hide_cmd = await RestServicecls._get_param(request, 'HideCmd', '0')
            RestServicecls.TimerState = "State"
            RestServicecls.TimerStateMessage = "HideQR" if str(hide_cmd) == '1' else "ShowQR"
            command_return_data = {'cmd': hide_cmd}

        elif commandname == 'GetMeetInfo':
            data = RestServicecls.Synced_JSONData or {}
            command_return_data = {
                'MeetName': data.get('MeetName', ''),
                'Boards': data.get('Boards', {}),
                'MeetAddress': data.get('MeetAddress', ''),
                'MeetDate': data.get('MeetDate', ''),
            }

        elif commandname == 'GetHeatInfo':
            text = RestServicecls.NextSetHeatID
            event_id = RestServicecls._parse_event_id_from_heat_name(
                text, (RestServicecls.Synced_JSONData or {}).get('EventList', [])
            )
            command_return_data = {'HeatName': RestServicecls.NextSetHeatID, 'EventID': event_id}

        elif commandname == 'LiveBoard':
            text = RestServicecls.NextSetHeatID
            data = RestServicecls.Synced_JSONData or {}
            event_id = RestServicecls._parse_event_id_from_heat_name(text, data.get('EventList', []))
            heat_data = RestServicecls._safe_heat_display()
            if not heat_data:
                return RestServicecls._err("No heat loaded", 404)
            sw_names = [b.swimmername for b in heat_data.SwimerBoardDetails]
            clubs = [b['ClubName'] for b in data["EventDetails"][data["EventList"][event_id-1]]["HeatList"][text]["BoardList"]]

            # clubs = RestServicecls._get_swimmer_clubs(sw_names, data)
            board_status = RestServicecls._build_board_status_and_time(heat_data)
            command_return_data = {
                'SwNames': sw_names,
                'Club': clubs,
                'BoardStatusAndTime': board_status,
                'EventID': event_id,
                'HeatName': RestServicecls.NextSetHeatID,
            }

        elif commandname == 'GetSwNames':
            heat_data = RestServicecls._safe_heat_display()
            if not heat_data:
                return RestServicecls._err("No heat loaded", 404)
            sw_names = [b.swimmername for b in heat_data.SwimerBoardDetails]
            clubs = RestServicecls._get_swimmer_clubs(sw_names, RestServicecls.Synced_JSONData or {})
            command_return_data = {'SwNames': sw_names, 'Club': clubs}

        elif commandname == 'GetBoardStatusAndTime':
            heat_data = RestServicecls._safe_heat_display()
            if not heat_data:
                return RestServicecls._err("No heat loaded", 404)
            command_return_data = {'BoardStatusAndTime': RestServicecls._build_board_status_and_time(heat_data)}

        elif commandname == 'get_heat_status':
            command_return_data = {'BoardTimeings': ['Tim1', 'Sw2']}  # Placeholder

        elif commandname == 'GetRestIP':
            command_return_data = RestServicecls.GetRestIP()

        elif commandname == 'GetRunningHeatData':
            command_return_data = RestServicecls.Synced_JSONData

        elif commandname == 'SetFBPathtoSync':
            URLToSync = await RestServicecls._get_param(request, 'URLToSync', '')
            FireBaseHelper.EventBaseurl = URLToSync

        elif commandname == 'SyncToSwimmerTable':
            URLToSync = await RestServicecls._get_param(request, 'URLToSync', '')
            FireBaseHelper.EventBaseurl = URLToSync

        elif commandname == 'GetAllHeatIDsFromFile':
            command_return_data = JsonHelper.GetAllHeatIDsFromFile(RestServicecls.Synced_JSONData or {})

        elif commandname == 'InitTimerFromFirebase':
            RestServicecls.InitStatus = 1
            URLToSync = await RestServicecls._get_param(request, 'URLToSync', '')
            OverWriteOption = int(await RestServicecls._get_param(request, 'OverWriteOption', '0'))
            FireBaseHelper.EventBaseurl = URLToSync
            RestServicecls.LoaDataFromFirebaseData(URLToSync, OverWriteOption)

        elif commandname == 'ResetTimer':
            RestServicecls.Synced_JSONData = RestServicecls.InitTimerStart()

        elif commandname == 'InitTimerFromLocalFile':
            RestServicecls.InitStatus = 1
            HeatFileName = await RestServicecls._get_param(request, 'HeatFileName', '')
            OverWriteOption = int(await RestServicecls._get_param(request, 'OverWriteOption', '0'))
            RestServicecls.LoadDataFromLocalFile(HeatFileName, OverWriteOption)

        elif commandname == 'InitHeatFromLocalDisk':
            RestServicecls.InitStatus = 1
            HeatFileDiskpath = await RestServicecls._get_param(request, 'HeatFileDiskpath', '')
            OverWriteOption = int(await RestServicecls._get_param(request, 'OverWriteOption', '0'))
            RestServicecls.LoadDataFromLocalFile("", OverWriteOption, HeatFileDiskpath)

        elif commandname == 'SaveHeatFileToLocalFile':
            RestServicecls.InitStatus = 2
            HeatData = await RestServicecls._get_param(request, 'HeatData', '{}')
            FileNametoSave = await RestServicecls._get_param(request, 'FileNametoSave', '')
            return RestServicecls.SaveHeatFileToLocalFile(HeatData, FileNametoSave)

        elif commandname == 'ReadHeatFromLocalFile':
            HeatFileName = await RestServicecls._get_param(request, 'HeatFileName', '')
            command_return_data = RestServicecls.ReadHeatFromLocalFile(HeatFileName)

        elif commandname == 'AutoFindHeat':
            RestServicecls.AutoFindHeat = int(await RestServicecls._get_param(request, 'AutoCmd', '1'))
            StopTimerService.StartRestcommand = 3
            StopTimerService.set_heat_status(TimerStatus.WaitingToStart)
            StopTimerService.ResetTimer()

        elif commandname == 'SetNextHeat':
            RestServicecls.AutoFindHeat = 0
            HeatName = await RestServicecls._get_param(request, 'HeatName', '')
            RestServicecls.NextSetHeatID = HeatName                        
            EventName = HeatName.rsplit("_", 1)[0]
            heatDataDisplay = JsonHelper.GetHeatDataDisplay( HeatName,EventName, RestServicecls.Synced_JSONData)
            StopTimerService.ResetTimer()
            StopTimerService.PrepareHeat(heatDataDisplay)
            StopTimerService.SetHeatStatus(TimerStatus.loadedToStart)
            # StopTimerService.ResetTimer()
            # StopTimerService.set_heat_status(TimerStatus.WaitingToStart)
            # StopTimerService.ResetTimer()

        elif commandname == 'HeatCommand':  # 1-Start, 2-Pause, 3-Stop, 4-Repeat
            HeatcmdValue = int(await RestServicecls._get_param(request, 'HeatCmdValue', '3'))
            # StopTimerService.ResetTimer()
            StopTimerService.StartRestcommand = HeatcmdValue

        elif commandname == 'SwimmerNameDispCmd':  # SwBoardID & SwNameValue
            SwBoardID = int(await RestServicecls._get_param(request, 'SwBoardID', '-1'))
            SwNameValue = await RestServicecls._get_param(request, 'SwNameValue', '')
            heat_data = RestServicecls._safe_heat_display()
            if heat_data and 0 <= SwBoardID < len(heat_data.SwimerBoardDetails):
                heat_data.SwimerBoardDetails[SwBoardID].swimmername = SwNameValue
                Logger.app_log.info(f"{commandname}-{SwBoardID}-{SwNameValue}")

        elif commandname == 'SwimmerTimeDispCmd':  # SwBoardID & SwTimeValue
            SwBoardID = int(await RestServicecls._get_param(request, 'SwBoardID', '-1'))
            SwTimeValue = float(await RestServicecls._get_param(request, 'SwTimeValue', '0'))
            heat_data = RestServicecls._safe_heat_display()
            if heat_data and 0 <= SwBoardID < len(heat_data.SwimerBoardDetails):
                heat_data.SwimerBoardDetails[SwBoardID].timerValue = SwTimeValue
                Logger.app_log.info(f"{commandname}-{SwBoardID}-{SwTimeValue}")

        elif commandname == 'SwimmerStatusCmd':  # SwBoardID & SwStatusCmdValue
            SwBoardID = int(await RestServicecls._get_param(request, 'SwBoardID', '-1'))
            SwStatusCmdValue = int(await RestServicecls._get_param(request, 'SwStatusCmdValue', '0'))
            heat_data = RestServicecls._safe_heat_display()
            if heat_data and 0 <= SwBoardID < len(heat_data.SwimerBoardDetails):
                heat_data.SwimerBoardDetails[SwBoardID].swimerStatus = SwStatusCmdValue
                Logger.app_log.info(f"{commandname}-{SwBoardID}-{SwStatusCmdValue}")

        elif commandname == 'BoardTimerCmd':  # SwBoardID & BoardTimerCmdValue
            SwBoardID = int(await RestServicecls._get_param(request, 'SwBoardID', '-1'))
            BoardTimerCmdValue = int(await RestServicecls._get_param(request, 'BoardTimerCmdValue', '0'))
            heat_data = RestServicecls._safe_heat_display()
            if heat_data and 0 <= SwBoardID < len(heat_data.SwimerBoardDetails):
                heat_data.SwimerBoardDetails[SwBoardID].RestBoardTimerCmd = BoardTimerCmdValue
                Logger.app_log.info(f"{commandname}-{SwBoardID}-{BoardTimerCmdValue}")

        else:
            Logger.app_log.info("Unknown command: %s", commandname)

        return RestServicecls._ok({'commandname': commandname, 'commandReturnData': command_return_data})
    except Exception:
        Logger.app_log.exception("SetLiveHeatCommands failed")
        return RestServicecls._err("Internal error", 500)


@app.post("/SetLiveHeatDetails")
async def SetLiveHeatDetails(request: Request):
    try:
        data = await request.json()
        return RestServicecls._ok({"received": True, "size": len(data) if isinstance(data, dict) else 0})
    except Exception as ex:
        Logger.app_log.exception("SetLiveHeatDetails failed")
        return RestServicecls._err(str(ex), 500)


@app.get("/LiveTimer")
def LiveTimer():
    heat_data = RestServicecls._safe_heat_display()
    if not heat_data:
        return RestServicecls._err("No heat loaded", 404)
    boards_as_dicts = [vars(b) for b in heat_data.SwimerBoardDetails]