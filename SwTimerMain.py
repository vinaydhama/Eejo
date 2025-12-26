
"""
Asyncio orchestration for Eejo timer system.
Key features:
- Starts FastAPI (Uvicorn) and the static web server as non-blocking asyncio tasks.
- Offloads blocking operations (webserver.start, Modbus I/O, Firebase file ops) to threads.
- Cloud writes are queued (asyncio.Queue) so the control loop doesn't block.
- Graceful shutdown via stop_event and task cancellation.
"""
import asyncio
import signal
from typing import Dict, Optional
import uvicorn

# Project imports
from Lib.StopwatchLib import StopTimerService
from Lib.WebServerLib import WebServer
from Lib.RestServicesLib import RestServicecls
from Lib.JsonLib import JsonHelper
from Lib.SwimDataHolder import TimerStatus
from Lib.LogerService import Logger
from Lib.FirebaseHelper import FireBaseHelper
from Lib.ModbusLib import ModbusLibcls
from Lib.UtilityFunctions import UtilityFunctions

# -----------------------------------------------------------------------------
# Shared runtime state
# -----------------------------------------------------------------------------
current_heat: Dict[str, Optional[object]] = {"HeatID": None, "EventID": None, "display": None}

# Preserve flags/vars from original code
RestServicecls.SetStartTimercmd = 1
CompletedHeatList = []
ExecutedHeat = ""
Updateddata = ""
HeatID = ""
EventID = ""

# Cloud write queue (async)
cloud_queue: asyncio.Queue = asyncio.Queue()

# Hold the web server instance (created in initialize_services)
web_server: Optional[WebServer] = None

# -----------------------------------------------------------------------------
# Async helpers for blocking calls
# -----------------------------------------------------------------------------
async def run_rest_server(stop_event: asyncio.Event) -> None:
    """
    Run FastAPI (Uvicorn) inside the current asyncio event loop.
    Shuts down when stop_event is set.
    """
    config = uvicorn.Config(
        RestServicecls.app,
        host=RestServicecls.host_name,
        port=RestServicecls.port,
        log_level="info",
        reload=False,  # keep False when embedding into an asyncio program
        # workers=1,    # if you ever add workers, they won't share in-process state
    )
    server = uvicorn.Server(config)

    # Print the actual IP and port
    ip = RestServicecls.GetRestIP()
    UtilityFunctions.logScreenMsg(f"FastAPI server running at http://{ip}:{RestServicecls.port}")

    server_task = asyncio.create_task(server.serve(), name="uvicorn_serve")
    try:
        await stop_event.wait()
    finally:
        server.should_exit = True
        await server_task


async def run_web_server() -> None:
    """
    Start the blocking web server in a background thread (non-blocking to event loop).
    Requires web_server to be initialized in initialize_services().
    """
    if web_server is None:
        raise RuntimeError("Web server not initialized. Call initialize_services() first.")
    # Run WebServer.start() (which calls serve_forever()) in a thread
    await asyncio.to_thread(web_server.start)


async def modbus_polling_loop(stop_event: asyncio.Event) -> None:
    """
    Poll Modbus in an async-friendly loop, using exponential backoff on failures.
    """
    backoff = 0.5
    while not stop_event.is_set():
        try:
            # Run blocking Modbus call in a thread
            await asyncio.to_thread(ModbusLibcls.GetStopWatchStatus)
            await asyncio.sleep(0.1)
            backoff = 0.5  # reset backoff on success
        except Exception as e:
            UtilityFunctions.logScreenMsg(f"Modbus read failed: {e}")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 5.0)


async def cloud_writer(stop_event: asyncio.Event) -> None:
    """
    Process cloud write tasks (Firebase & local file updates) via an asyncio queue.
    """
    while not stop_event.is_set():
        try:
            task = await asyncio.wait_for(cloud_queue.get(), timeout=0.5)
        except asyncio.TimeoutError:
            continue

        try:
            if task["type"] == "heat_results":
                Heatdata = task["Heatdata"]
                heatindex = task["heatindex"]
                eventIndex = task["eventIndex"]

                # Local file appends (blocking)
                await asyncio.to_thread(FireBaseHelper.append_json_line_async, FireBaseHelper.WriteHeatResultsPath, Heatdata)
                await asyncio.to_thread(FireBaseHelper.AppendSwimmerResults, FireBaseHelper.WriteSwimmerTablePath, Heatdata)

                # Remote update (blocking / slower)
                await asyncio.to_thread(FireBaseHelper.UpdateHeatResultToFirebase, Heatdata, heatindex, eventIndex)

            else:
                Logger.app_log.warning(f"Unknown cloud task: {task}")
        except Exception as e:
            Logger.app_log.exception(f"Cloud writer failed: {e}")
        finally:
            cloud_queue.task_done()


async def initialize_services() -> None:
    """
    Initialize Modbus, sync JSON, and prepare (but do not start) the web server.
    This function must return quickly to allow tasks (rest/web/modbus/control) to be scheduled.
    """
    global web_server

    # Connect Modbus device (wrap blocking init)
    try:
        await asyncio.to_thread(ModbusLibcls.ConnecttoDevice)  # if ConnecttoDevice needs params, pass them from Board settings
        UtilityFunctions.logScreenMsg("Modbus device connected.")
    except Exception as e:
        UtilityFunctions.logScreenMsg(f"Modbus device connect failed: {e}")

    # Initialize synced JSON / timer start
    RestServicecls.Synced_JSONData = await asyncio.to_thread(RestServicecls.InitTimerStart)

    # Prepare web server instance (do not start here)
    ip = await asyncio.to_thread(RestServicecls.GetRestIP)
    web_server = WebServer(host=ip, port=WebServer.PORT)
    UtilityFunctions.logScreenMsg(f"Web server prepared at http://{web_server.host}:{web_server.port}")



import asyncio

# Optional: a small helper to stringify TimerStatus safely
def _safe_status_str(status) -> str:
    try:
        return str(status)
    except Exception:
        return "UnknownStatus"

async def control_loop(stop_event: asyncio.Event) -> None:
    """
    Orchestrates the timer status state machine in an async loop.
    Keeps each iteration resilient and non-blocking.
    """
    last_heartbeat = 0.0

    while not stop_event.is_set():
        try:
            # Heartbeat every ~5s to prove liveness
            now = asyncio.get_event_loop().time()
            if now - last_heartbeat > 5.0:
                Logger.app_log.debug("control_loop heartbeat: alive")
                last_heartbeat = now

            # ---- Readiness guard (robust) ----
            data_ready = isinstance(RestServicecls.Synced_JSONData, dict) and len(RestServicecls.Synced_JSONData) > 0
            if not data_ready or RestServicecls.InitStatus != 0:
                RestServicecls.TimerState = "Busy"
                RestServicecls.TimerStateMessage = "Waiting for Heat File to be loaded"
                await asyncio.sleep(0.2)
                continue

            # ---- Get current status (robust) ----
            try:
                HeatStatus = await asyncio.to_thread(StopTimerService.getHeatStatus)
            except Exception as e:
                Logger.app_log.exception(f"control_loop: getHeatStatus failed: {e}")
                # fall back to Busy and retry shortly
                RestServicecls.TimerState = "Busy"
                RestServicecls.TimerStateMessage = "Timer status unavailable, retrying..."
                await asyncio.sleep(0.2)
                continue

            # ---- Update public state text ----
            if not RestServicecls.Synced_JSONData:
                RestServicecls.TimerState = "Busy"
                RestServicecls.TimerStateMessage = "Waiting for Heat File to be loaded"
            else:
                RestServicecls.TimerState = "State"
                RestServicecls.TimerStateMessage = _safe_status_str(HeatStatus)

            # -----------------------------
            # State machine
            # -----------------------------
            # print(HeatStatus)
            if HeatStatus in (TimerStatus.WaitingToStart, TimerStatus.Stoped):
                Logger.app_log.info("control_loop: Waiting to start next heat")
                

                # Get next heat ID
                try:
                    HeatID, EventID = await asyncio.to_thread(RestServicecls.GetNextHeatID, RestServicecls.Synced_JSONData)
                except Exception as e:
                    Logger.app_log.exception(f"GetNextHeatID failed: {e}")
                    await asyncio.sleep(0.2)
                    continue

                if HeatID != "WaitingToStart":
                    Logger.app_log.info("control_loop: Loaded Heat %s", HeatID)
                    # Get HeatDataDisplay
                    try:
                        heatDataDisplay = await asyncio.to_thread(JsonHelper.GetHeatDataDisplay, HeatID, EventID, RestServicecls.Synced_JSONData)
                    except Exception as e:
                        Logger.app_log.exception(f"GetHeatDataDisplay failed: {e}")
                        heatDataDisplay = None

                    if heatDataDisplay is None:
                        try:
                            await asyncio.to_thread(StopTimerService.SetHeatStatus, TimerStatus.Stoped)
                        except Exception:
                            Logger.app_log.exception("SetHeatStatus(TimerStatus.Stoped) failed")
                        RestServicecls.TimerState = "Busy"
                        RestServicecls.TimerStateMessage = "No heats found"
                    else:
                        # Prepare the heat
                        try:
                            await asyncio.to_thread(StopTimerService.ResetTimer)
                            await asyncio.to_thread(StopTimerService.PrepareHeat, heatDataDisplay)
                            # await asyncio.to_thread(StopTimerService.PrepareHeat, heatDataDisplay)

                            # StopTimerServicecls.SetHeatStatus(TimerStatus.loadedToStart)
                        except Exception as e:
                            Logger.app_log.exception(f"Reset/PrepareHeat failed: {e}")
                            await asyncio.sleep(0.2)
                            continue

                        current_heat["HeatID"] = HeatID
                        current_heat["EventID"] = EventID
                        current_heat["display"] = heatDataDisplay
                        try:
                            await asyncio.to_thread(StopTimerService.SetHeatStatus, TimerStatus.loadedToStart)
                            # StopTimerService.HeatStatus =  TimerStatus.loadedToStart
                            # print (StopTimerService.getHeatStatus())

                        except Exception:
                            Logger.app_log.exception("SetHeatStatus(TimerStatus.loadedToStart) failed")
                else: 
                    UtilityFunctions.logScreenMsg("control_loop: No heats found")

            elif HeatStatus == TimerStatus.Completed:
                ch = current_heat.copy()
                if not ch.get("HeatID") or not ch.get("display"):
                    Logger.app_log.exception("control_loop: Completed reached but current heat is undefined.")
                    try:
                        await asyncio.to_thread(StopTimerService.SetHeatStatus, TimerStatus.WaitingToStart)
                    except Exception:
                        Logger.app_log.exception("SetHeatStatus(TimerStatus.WaitingToStart) failed")
                    await asyncio.sleep(0.05)
                    continue

                # Prepare results to local JSON DB
                try:
                    RestServicecls.Synced_JSONData, Heatdata, heatindex, eventIndex = await asyncio.to_thread(
                        FireBaseHelper.PrepareHeatResultstoLocalJSONDB,
                        ch["HeatID"], ch["display"], RestServicecls.Synced_JSONData
                    )
                except Exception as e:
                    Logger.app_log.exception(f"PrepareHeatResultstoLocalJSONDB failed: {e}")
                    try:
                        await asyncio.to_thread(StopTimerService.SetHeatStatus, TimerStatus.WaitingToStart)
                    except Exception:
                        Logger.app_log.exception("SetHeatStatus(TimerStatus.WaitingToStart) failed")
                    await asyncio.sleep(0.1)
                    continue

                RestServicecls.TimerState = "Busy"
                RestServicecls.TimerStateMessage = "Updating Result To Cloud"

                # Offload to cloud writer
                try:
                    await cloud_queue.put({
                        "type": "heat_results",
                        "Heatdata": Heatdata,
                        "heatindex": heatindex,
                        "eventIndex": eventIndex
                    })
                except Exception as e:
                    Logger.app_log.exception(f"cloud_queue.put failed: {e}")

                # Move to next heat
                try:
                    await asyncio.to_thread(StopTimerService.SetHeatStatus, TimerStatus.WaitingToStart)
                except Exception:
                    Logger.app_log.exception("SetHeatStatus(TimerStatus.WaitingToStart) failed")

            elif HeatStatus in (
                TimerStatus.loadedToStart,
                TimerStatus.InProgress,
                TimerStatus.WaitBeforeLoad,
                TimerStatus.ResetbeforeStart,
            ):
                # One tick of RunTimer
                try:
                    await asyncio.to_thread(StopTimerService.RunTimer)
                except Exception as e:
                    Logger.app_log.exception(f"RunTimer failed: {e}")

                await asyncio.sleep(0.05)  # Prevent tight loop

            else:
                # Unknown state; log and soft-recover
                s = _safe_status_str(HeatStatus)
                Logger.app_log.warning(f"control_loop: Unknown HeatStatus={s}; soft-recovering")
                await asyncio.sleep(0.2)

        except asyncio.CancelledError:
            # This is expected on shutdown; re-raise to let task exit cleanly
            raise
        except BaseException as ex:
            # Catch any non-CancelledError BaseException (rare, but can stop loop)
            Logger.app_log.exception(f"control_loop: fatal error {ex}; continuing", exc_info=True)
            await asyncio.sleep(0.5)
            continue

async def main() -> None:
    """
    Entry point: set up services, create tasks, and manage lifecycle.
    """
    stop_event = asyncio.Event()

    # Graceful shutdown via signals (POSIX). On Windows, KeyboardInterrupt still works.
    loop = asyncio.get_running_loop()
    for sig in (getattr(signal, "SIGINT", None), getattr(signal, "SIGTERM", None)):
        if sig is not None:
            try:
                loop.add_signal_handler(sig, stop_event.set)
            except NotImplementedError:
                # add_signal_handler may not be available on some platforms (e.g., some Windows setups)
                pass

    # Initialize services (binding sockets, Modbus connection, initial JSON sync)
    await initialize_services()  # returns quickly now

    # Start servers & workers as asyncio tasks
    tasks = [
        asyncio.create_task(run_rest_server(stop_event), name="rest_server"),
        asyncio.create_task(run_web_server(), name="web_server"),
        asyncio.create_task(modbus_polling_loop(stop_event), name="modbus_polling"),
        asyncio.create_task(cloud_writer(stop_event), name="cloud_writer"),
        asyncio.create_task(control_loop(stop_event), name="control_loop"),
    ]

    UtilityFunctions.logScreenMsg("Async system started. Press Ctrl+C to stop.")

    # Wait for stop signal
    try:
        await stop_event.wait()
    except KeyboardInterrupt:
        pass
    finally:
        # Begin shutdown: cancel running tasks
        UtilityFunctions.logScreenMsg("Shutting down...")
        for t in tasks:
            t.cancel()

        # Drain cloud queue gracefully (optional timeout)
        try:
            await asyncio.wait_for(cloud_queue.join(), timeout=5.0)
        except asyncio.TimeoutError:
            Logger.app_log.warning("Cloud queue did not drain before shutdown.")

        # Ensure tasks finish/cancel cleanly
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for name, res in zip([t.get_name() for t in tasks], results):
            if isinstance(res, Exception) and not isinstance(res, asyncio.CancelledError):
                Logger.app_log.exception("Task %s ended with error: %s", name, res)

        # Stop web server if running
        if web_server is not None:
            await asyncio.to_thread(web_server.stop)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stoped")