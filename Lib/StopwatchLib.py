
# StopwatchLib.py (backward-compatible facade + instance impl + error handling)
from __future__ import annotations

import time
import datetime
from typing import List, Optional, ClassVar, Callable, Any, Tuple

from Lib.SwimDataHolder import TimerStatus, SwimerBoardDetail, HeatDataDisplay
from Lib.LogerService import Logger
from Lib.ModbusLib import ModbusLibcls


# ---------------------------------------------------------------------------
# Error-handling decorator
# ---------------------------------------------------------------------------
def safe_call(default_return: Any = None) -> Callable:
    """
    Decorator to wrap methods with try/except, log the exception, and
    optionally return a default value to keep the system running.

    Usage:
        @safe_call()                  # for methods that return None
        @safe_call(default_return=0)  # for methods that must return a value
    """
    def _wrap(func: Callable) -> Callable:
        def _inner(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as ex:
                # Method identification
                qualname = getattr(func, "__qualname__", func.__name__)
                Logger.app_log.exception(f"Exception in {qualname}", exc_info=True)
                return default_return
        return _inner
    return _wrap


class StopTimerService:
    """
    Instance-based implementation of the swim heat stopwatch.
    A singleton facade preserves the legacy class-level API for compatibility.

    Compatibility guarantees:
      - Class attributes: HeatStatus, StartRestcommand, heatDataDisplay,
        SIDE_A_SwBits, SIDE_B_SwBits, StopWatchInputPins, MODSwitchBits remain accessible.
      - Class methods (PascalCase): ResetTimer, PrepareHeat, RunTimer,
        SetHeatStatus, getHeatStatus, GetHeatStartTime remain callable.
      - Snake_case class methods added: set_heat_status(), reset_timer_cls(),
        prepare_heat_cls(), run_tick_cls(), get_heat_status_cls().
    """

    # ---- Singleton holder for facade ----
    _singleton: ClassVar[Optional["StopTimerService"]] = None

    # ---- Compatibility: class attributes used by other modules ----
    HeatStatus: ClassVar[TimerStatus] = TimerStatus.Stoped
    StartRestcommand: ClassVar[int] = 0
    heatDataDisplay: ClassVar[HeatDataDisplay] = HeatDataDisplay()

    # Side/bit mappings (class-level so REST can set them directly)
    SIDE_A_SwBits: ClassVar[List[int]] = [7, 20, 18, 21, 22, 22, 21, 6, 4, 2, 0, 0]
    SIDE_B_SwBits: ClassVar[List[int]] = [-1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11, -12, -13]
    StopWatchInputPins: ClassVar[List[int]] = []  # used by RestServicesLib to set primary side
    MODSwitchBits: ClassVar[List[int]] = [19, 23, 18, 20, 22, 21, 7, 6, 4, 2, 0, 0]

    # ---- Instance configuration constants ----
    START_PIN_BIT_INDEX: int = 0
    SHORT_LATCH_THRESHOLD: int = 3
    LONG_LATCH_THRESHOLD: int = 60

    CMD_PAUSE = 1
    CMD_CONTINUE = 2
    CMD_DISABLE = 3
    CMD_BYPASS = 4

    LOW_FREQ_TONES = [0, 100, 740, 800, 1000, 2300, 2600, 3000, 3100, 3600, 3700, 4100, 4200]
    BOARD_FREQ = [3600] * 11

    # ---- Instance state ----
    @safe_call()
    def __init__(self, heat_display: Optional[HeatDataDisplay] = None) -> None:
        # Use class-level heatDataDisplay for compatibility
        if heat_display is not None:
            StopTimerService.heatDataDisplay = heat_display
        self.heat_display: HeatDataDisplay = StopTimerService.heatDataDisplay

        # Mirror HeatStatus/StartRestcommand class vars
        self.previous_state: TimerStatus = StopTimerService.HeatStatus
        self.start_time_epoch: float = 0.0
        self.start_pin_status: int = 0
        self.start_latch: int = 0
        self.start_latch_counter: int = 0
        self.latched_boards: List[int] = []

    # -------------------------------------------------------------------------
    # Modern instance methods (snake_case)
    # -------------------------------------------------------------------------
    @safe_call()
    def reset_timer(self) -> None:
        Logger.app_log.debug("ResetTimer Started")
        self.start_time_epoch = 0.0
        self.start_pin_status = 0
        self.start_latch = 0
        self.start_latch_counter = 0
        StopTimerService.SetHeatStatus(TimerStatus.Stoped)  # keep class attr in sync
        

        for idx, board in enumerate(self.heat_display.SwimerBoardDetails):
            try:
                board.StopWatchInputPinsLatchStatus = 0
                board.LockTime = 0
                board.timerValue = 0
                print(f"Reset Timer board {idx}")
            except Exception as ex:
                Logger.app_log.exception(f"ResetTimer board state failed (board={idx})", exc_info=True)

    @safe_call()
    def prepare_heat(self, heat_display: Optional[HeatDataDisplay] = None) -> None:
        Logger.app_log.debug("PrepareHeat Started")
        if heat_display is not None:
            self.heat_display = heat_display
            StopTimerService.heatDataDisplay = heat_display  # sync class attr
        for i, _board in enumerate(self.heat_display.SwimerBoardDetails):
            bit = self._board_bit_index(i)
            Logger.app_log.info(f"Board {i} mapped to MODSwitchBits index {bit}")

    @staticmethod
    @safe_call(default_return="0:0:0.000")
    def time_convert(seconds: float) -> str:
        mins = int(seconds) // 60
        sec = seconds % 60
        hours = mins // 60
        mins = mins % 60
        return f"{hours}:{mins}:{sec:.3f}"

    @safe_call(default_return=TimerStatus.Stoped)
    def get_heat_status(self) -> TimerStatus:
        # Source of truth: class attribute (keeps legacy writers working)
        return StopTimerService.HeatStatus

    @safe_call()
    def set_heat_status(self, status: TimerStatus) -> None:
        StopTimerService.HeatStatus=status

    @safe_call()
    def set_command(self, value: int) -> None:
        StopTimerService.StartRestcommand = value

    @safe_call()
    def run_tick(self) -> None:
        """
        One processing tick; call repeatedly from a loop.
        """
        self._read_start_pin()
        self._handle_start_logic()
        self._process_boards()
        self._update_timers()
        self._derive_heat_status()

        if StopTimerService.HeatStatus == TimerStatus.WaitBeforeLoad:
            now = datetime.datetime.now()
            self.heat_display.HeatEndTime = int(now.strftime("%Y%m%d%H%M%S"))

        # self._play_tones(StopTimerService.HeatStatus)

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------
    @safe_call(default_return=0)
    def _board_bit_index(self, board_idx: int) -> int:
        arr_idx = board_idx + 1  # first entry is START bit
        if arr_idx < len(StopTimerService.MODSwitchBits):
            return StopTimerService.MODSwitchBits[arr_idx]
        return 0

    @safe_call()
    def _read_start_pin(self) -> None:
        bits = StopTimerService.MODSwitchBits
        bit_index = bits[self.START_PIN_BIT_INDEX] if bits else 0
        if bit_index != 0 and len(ModbusLibcls.StopWatchSwStatus) > bit_index:
            self.start_pin_status = ModbusLibcls.StopWatchSwStatus[bit_index]
        else:
            self.start_pin_status = 0

    @safe_call()
    def _handle_start_logic(self) -> None:
        if self.start_pin_status == 1 or StopTimerService.StartRestcommand == 1:
            if StopTimerService.StartRestcommand == 1 and StopTimerService.HeatStatus == TimerStatus.loadedToStart:
                self.start_latch = 1
                now = datetime.datetime.now()
                self.heat_display.HeatStartTime = int(now.strftime("%Y%m%d%H%M%S"))
                StopTimerService.StartRestcommand = 0

            if StopTimerService.HeatStatus == TimerStatus.loadedToStart and self.start_latch == 0:
                if self.start_latch_counter >= self.SHORT_LATCH_THRESHOLD:
                    self.start_latch = 1
                    now = datetime.datetime.now()
                    self.heat_display.HeatStartTime = int(now.strftime("%Y%m%d%H%M%S"))
                    Logger.app_log.info("Start Timer Latched")
                else:
                    self.start_latch_counter += 1

        elif StopTimerService.HeatStatus == TimerStatus.WaitBeforeLoad:
            self.start_latch = 0
            self.start_latch_counter += 1
            if self.start_latch_counter > 2:
                # StopTimerService.HeatStatus = TimerStatus.ResetbeforeStart 
                StopTimerService.SetHeatStatus(TimerStatus.ResetbeforeStart)               

        elif StopTimerService.StartRestcommand == 1:
            StopTimerService.SetHeatStatus(TimerStatus.ResetbeforeStart)
            StopTimerService.StartRestcommand = 0

        elif StopTimerService.HeatStatus == TimerStatus.ResetbeforeStart:
            self.start_latch_counter = 0
            self.start_latch = 0
            StopTimerService.StartRestcommand = 0
            StopTimerService.SetHeatStatus(TimerStatus.Completed)

        elif StopTimerService.StartRestcommand == 4:
            now = datetime.datetime.now()
            self.heat_display.HeatEndTime = int(now.strftime("%Y%m%d%H%M%S"))
            StopTimerService.SetHeatStatus(TimerStatus.Completed)

        else:
            self.start_latch_counter = 0

    @safe_call()
    def _process_boards(self) -> None:
        for board_idx, board in enumerate(self.heat_display.SwimerBoardDetails):
            try:
                bit_index = self._board_bit_index(board_idx)

                if bit_index != 0 and len(ModbusLibcls.StopWatchSwStatus) > bit_index:
                    board.StopWatchInputPinsStatus = ModbusLibcls.StopWatchSwStatus[bit_index]
                else:
                    board.StopWatchInputPinsStatus = 0

                if (board.swimerStatus != 0 and self.start_latch==1):
                    board.LockTime = 0


                if (board.swimerStatus != 0 and self.start_latch==1):
                    board.LockTime = 1
                    board.timerValue = 0
                    continue

                if board.RestBoardTimerCmd == 0:
                    if board.StopWatchInputPinsStatus == 1:
                        if board.StopWatchInputPinsLatchCounter >= self.SHORT_LATCH_THRESHOLD:
                            if (board.StopWatchInputPinsLatchStatus == 0 and self.start_latch==1):
                                print(f"{time.time()} Board {board_idx} Latched (bit {bit_index})")
                                board.StopWatchInputPinsLatchStatus = 1
                                board.LockTime = 1
                        else:
                            board.StopWatchInputPinsLatchCounter += 1
                    else:
                        board.StopWatchInputPinsLatchCounter = 0

                elif board.RestBoardTimerCmd == self.CMD_PAUSE:
                    if board.StopWatchInputPinsLatchStatus == 0:
                        print(f"{time.time()} Board {board_idx} Latched via PAUSE (bit {bit_index})")
                    board.StopWatchInputPinsLatchStatus = 1
                    board.LockTime = 1

                elif board.RestBoardTimerCmd == self.CMD_CONTINUE:
                    if board.swimerStatus == 0:
                        board.LockTime = 0

                elif board.RestBoardTimerCmd == self.CMD_DISABLE:
                    board.LockTime = 1
                    board.timerValue = 0

                elif board.RestBoardTimerCmd == self.CMD_BYPASS:
                    if board.swimerStatus == 0:
                        board.LockTime = 0

                else:
                    board.LockTime = 1

            except Exception as ex:
                Logger.app_log.exception(f"_process_boards failed (board={board_idx})", exc_info=True)

    @safe_call()
    def _update_timers(self) -> None:
        if self.start_latch == 1 and self.start_time_epoch == 0.0:
            self.start_time_epoch = round(time.time(), 3)
            print("Timer Started")
            StopTimerService.SetHeatStatus(TimerStatus.InProgress)

        if self.start_latch == 1 and self.start_time_epoch > 0.0:
            for idx, board in enumerate(self.heat_display.SwimerBoardDetails):
                try:
                    if board.RestBoardTimerCmd == 0:
                        if board.StopWatchInputPinsLatchStatus == 1 and board.LockTime == 0:
                            board.timerValue = round(time.time() - self.start_time_epoch, 3)
                            msg = f"Board {board.boardId} Time Latched @{self.time_convert(board.timerValue)}"
                            print(msg)
                            Logger.app_log.info(msg)
                            board.LockTime = 1
                        elif board.LockTime == 0:
                            board.timerValue = round(time.time() - self.start_time_epoch, 3)

                    elif board.RestBoardTimerCmd == self.CMD_PAUSE:
                        if board.LockTime == 0:
                            board.timerValue = round(time.time() - self.start_time_epoch, 3)
                            board.LockTime = 1
                            board.StopWatchInputPinsLatchStatus=1

                    elif board.RestBoardTimerCmd == self.CMD_CONTINUE:
                        if board.swimerStatus == 0:
                            board.LockTime = 0
                            board.StopWatchInputPinsLatchStatus=0
                            board.timerValue = round(time.time() - self.start_time_epoch, 3)
                            

                    elif board.RestBoardTimerCmd == self.CMD_DISABLE:
                        board.LockTime = 1
                        board.timerValue = 0
                        board.StopWatchInputPinsLatchStatus=0

                    elif board.RestBoardTimerCmd == self.CMD_BYPASS:
                        if board.swimerStatus == 0:
                            board.timerValue = round(time.time() - self.start_time_epoch, 3)

                except Exception as ex:
                    Logger.app_log.exception(f"_update_timers failed (board={idx})", exc_info=True)

    @safe_call()
    def _derive_heat_status(self) -> None:
        # Default to WaitBeforeLoad if all active swimmers are locked; InProgress otherwise
         if (self.start_latch == 1):
            if ( StopTimerService.StartRestcommand != 4):
             
                for board in self.heat_display.SwimerBoardDetails:
                    if board.swimerStatus == 0:
                        if board.LockTime != 0:
                            StopTimerService.SetHeatStatus(TimerStatus.WaitBeforeLoad)
                        else:
                            StopTimerService.SetHeatStatus(TimerStatus.InProgress)
                            break
                    else:
                        StopTimerService.SetHeatStatus(TimerStatus.WaitBeforeLoad)
            else:
                    StopTimerService.SetHeatStatus(TimerStatus.Completed)
                    StopTimerService.StartRestcommand = 0



    @safe_call()
    def _play_tones(self, heat_state: TimerStatus) -> None:
        register_address = 0

        if heat_state == TimerStatus.InProgress:
            for board_idx, board in enumerate(self.heat_display.SwimerBoardDetails):
                try:
                    if board.LockTime == 1 and board_idx not in self.latched_boards:
                        ModbusLibcls.WriteRegisters(register_address, [self.BOARD_FREQ[board_idx], 0])
                        print(f" Playing Board {board_idx}")
                        self.latched_boards.append(board_idx)
                except Exception as ex:
                    Logger.app_log.exception("Tone write failed for board", exc_info=True)

        if self.previous_state != heat_state:
            self.latched_boards = []
            self.previous_state = heat_state

        try:
            if heat_state == TimerStatus.WaitingToStart:
                ModbusLibcls.WriteRegisters(register_address, [4, 500])
            elif heat_state == TimerStatus.InProgress:
                ModbusLibcls.WriteRegisters(register_address, [100, 500])
            elif heat_state == TimerStatus.Completed:
                ModbusLibcls.WriteRegisters(register_address, [2300, 100])
            elif heat_state == TimerStatus.loadedToStart:
                ModbusLibcls.WriteRegisters(register_address, [4, 500])
            elif heat_state == TimerStatus.WaitBeforeLoad:
                ModbusLibcls.WriteRegisters(register_address, [self.BOARD_FREQ[0], 50])
        except Exception as ex:
            Logger.app_log.exception("Tone write failed (global)", exc_info=True)

    # -------------------------------------------------------------------------
    # Facade: backward-compatible class API
    # -------------------------------------------------------------------------
    @classmethod
    @safe_call(default_return=None)
    def get_instance(cls) -> "StopTimerService":
        if cls._singleton is None:
            cls._singleton = StopTimerService()
        # ensure instance reflects class-level heat display
        cls._singleton.heat_display = StopTimerService.heatDataDisplay
        return cls._singleton

    # Old PascalCase names preserved
    @classmethod
    @safe_call()
    def ResetTimer(cls) -> None:
        cls.get_instance().reset_timer()

    @classmethod
    @safe_call()
    def PrepareHeat(cls, heat_display: HeatDataDisplay) -> None:
        cls.get_instance().prepare_heat(heat_display)

    @classmethod
    @safe_call()
    def RunTimer(cls) -> None:
        cls.get_instance().run_tick()

    @classmethod
    @safe_call()
    def SetHeatStatus(cls, status: TimerStatus) -> None:
        cls.get_instance().set_heat_status(status)
        cls.get_instance().heatDataDisplay.HeatStatus= status


    @classmethod
    @safe_call(default_return=0)
    def GetHeatStartTime(cls) -> int:
        """
        Kept for compatibility with original code.
        Returns HeatStartTime as an integer timestamp (YYYYMMDDHHMMSS).
        """
        return cls.get_instance().heat_display.HeatStartTime

    @classmethod
    @safe_call(default_return=TimerStatus.Stoped)
    def getHeatStatus(cls) -> TimerStatus:
        # Original mixed-case method name preserved
        return cls.get_instance().get_heat_status()

    # Snake_case class methods for mixed usage in other modules
    @classmethod
    @safe_call()
    def set_heat_status(cls, status: TimerStatus) -> None:
        StopTimerService.HeatStatus = status
        cls.SetHeatStatus(status)

    @classmethod
    @safe_call()
    def reset_timer_cls(cls) -> None:
        cls.ResetTimer()

    @classmethod
    @safe_call()
    def prepare_heat_cls(cls, heat_display: HeatDataDisplay) -> None:
        cls.PrepareHeat(heat_display)

    @classmethod
    @safe_call()
    def run_tick_cls(cls) -> None:
        cls.RunTimer()

    @classmethod
    @safe_call(default_return=TimerStatus.Stoped)
    def get_heat_status_cls(cls) -> TimerStatus:
        Logger.app_log.info("get_heat_status_cls called")

