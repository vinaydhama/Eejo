
function CaptureMeetTable(MeetUpdatedData) {
  try {
    const meetNameEl    = getEl("tblMeet_MeetName",    { required: true, desc: "Meet Name" });
    const meetAddrEl    = getEl("tblMeet_MeetAddress", { required: true, desc: "Meet Address" });
    const meetDateEl    = getEl("tblMeetDate",         { required: true, desc: "Meet Date" });
    const boardsEl      = getEl("tblMeet_txtBoards",   { required: true, desc: "Boards count" });

    // If any required element is missing, bail out with a warning but return the input unchanged.
    if (!meetNameEl || !meetAddrEl || !meetDateEl || !boardsEl) {
      log.warn("CaptureMeetTable: Missing required inputs; returning original MeetUpdatedData.");
      return MeetUpdatedData;
    }

    const meetName = normalizeStr(meetNameEl.value);
    const meetAddr = normalizeStr(meetAddrEl.value);
    const meetDate = normalizeStr(meetDateEl.value);

    // Boards: keep as string if downstream expects string; otherwise parseInt.
    const boardsValue = toInt(boardsEl.value, 1);
    const boards = boardsValue > 0 ? boardsValue : 1;

    MeetUpdatedData.MeetName   = meetName;
    MeetUpdatedData.MeetAddress= meetAddr;
    MeetUpdatedData.MeetDate   = meetDate;
    MeetUpdatedData.Boards     = boards;

    log.info("CaptureMeetTable: captured.", { meetName, meetAddr, meetDate, boards });
    return MeetUpdatedData;
  } catch (err) {
    log.error("CaptureMeetTable: fatal error.", err);
    return MeetUpdatedData;
  }
}

function CaptureSwDetailsTable(MeetUpdatedData) {
  try {
    const tblSwimmers = getEl('tblSwDetails', { required: true, desc: "Swimmers table" });
    if (!tblSwimmers) {
      log.warn("CaptureSwDetailsTable: tblSwDetails missing.");
      return MeetUpdatedData;
    }

    // Ensure SwimmerDetails is an object, not an array.
    if (!MeetUpdatedData.SwimmerDetails || typeof MeetUpdatedData.SwimmerDetails !== 'object' || Array.isArray(MeetUpdatedData.SwimmerDetails)) {
      MeetUpdatedData.SwimmerDetails = {};
    } else {
      // Clear previous entries safely
      Object.keys(MeetUpdatedData.SwimmerDetails).forEach(k => delete MeetUpdatedData.SwimmerDetails[k]);
    }

    for (let i = 0; i < tblSwimmers.rows.length - 1; i++) {
      const nameEl   = getEl("SwimmersNamecell" + i);
      const dobEl = getEl("SwimmersDOBcell" + i);
      const groupEl  = getEl("SwimmerGroupCell" + i);
      const clubEl   = getEl("SwimmerClubCell" + i);
      const clubElShort   = getEl("SwimmerClubShortCell" + i);
      const genderEl = getEl("SwimmerGenderCell" + i);
      const tblSel   = getEl("tblSwSelectedEvents" + i);
      const clubShort  = normalizeStr(clubElShort?.value);
      const SwaName  = normalizeStr(nameEl?.value);
      const dob = normalizeStr(dobEl?.value);
      const RegTimeEl = getEl("SwimmerRegTimeCell" + i);
      const RegTimeElstr = normalizeStr(RegTimeEl?.value);
      const preview_local = getEl("SwimmerPhotoPreview_local" + i);
      let PhotoPath_Local = "";
      
      if (preview_local) {
        PhotoPath_Local = preview_local.src;
      }

      const preview_fb = getEl("SwimmerPhotoPreviewFB" + i);
      let PhotoPath_FB = "";
      if (preview_fb) {
        PhotoPath_FB = preview_fb.src;
      }
      const SwGroup  = normalizeStr(groupEl?.value);
      const SwClub   = normalizeStr(clubEl?.value);
      const Gender   = normalizeStr(genderEl?.value);

      if (!SwaName) {
        log.warn("CaptureSwDetailsTable: Missing swimmer name; skipping row.", { rowIndex: i });
        continue;
      }

      const EventList = [];
      if (tblSel) {
        for (let j = 0; j < tblSel.rows.length - 1; j++) {
          const availId = "SwimmersAvailablecell" + i + "_" + j;
          const bestId  = "SwimmersEventBestTime" + i + "_" + j;
          const evSelId = "SwimmersEventSelector" + i + "_" + j;

          const availEl = getEl(availId);
          const bestEl  = getEl(bestId);
          const evSel   = getEl(evSelId);

          const Available   = !!(availEl?.checked);
          const BestTimeings= normalizeStr(bestEl?.value);
          const EventName   = normalizeStr(evSel?.value);

          // Only push if an event name exists (you can relax this if desired)
          if (EventName) {
            EventList.push({ 'Available': Available, 'BestTimeings': BestTimeings, 'EventName': EventName });
          } else {
            log.debug("CaptureSwDetailsTable: Empty event name; entry suppressed.", { rowIndex: i, evRow: j });
          }
        }
      } else {
        log.debug("CaptureSwDetailsTable: No selected-events table for swimmer.", { rowIndex: i });
      }

      MeetUpdatedData.SwimmerDetails[SwaName] = {
        'Name': SwaName,
        'DOB': dob,
        'Group': SwGroup,
        'Gender': Gender,
        'Events': EventList,
        'Club': SwClub,
        'ClubShort':clubShort,
       'PhotoPath_FB': PhotoPath_FB,
        'RegTime': RegTimeElstr,
       'PhotoPath_Local': PhotoPath_Local,

        // Placeholder; fill if you have a source
      };
    }

    log.info("CaptureSwDetailsTable: captured.", { swimmersCount: Object.keys(MeetUpdatedData.SwimmerDetails).length });
    return MeetUpdatedData;
  } catch (err) {
    log.error("CaptureSwDetailsTable: fatal error.", err);
    return MeetUpdatedData;
  }
}


function CaptureGroupTable(MeetUpdatedData) {
  try {
    const tblGroups = getEl('tblGroups', { required: true, desc: "Groups table" });
    if (!tblGroups) {
      log.warn("CaptureGroupTable: tblGroups missing.");
      return MeetUpdatedData;
    }

    // Ensure container object
    if (typeof MeetUpdatedData !== 'object' || MeetUpdatedData === null) {
      MeetUpdatedData = {};
    }

    // GroupDetails as a DICTIONARY keyed by GroupID
    MeetUpdatedData.GroupDetails = {};
    // Optional: preserve table order of GroupIDs for display
    MeetUpdatedData.GroupOrder = [];

    const normalize = (v) => (typeof normalizeStr === 'function' ? normalizeStr(v) : (v ?? '').toString().trim());

    for (let i = 1; i < tblGroups.rows.length; i++) {
      const rowEl = tblGroups.rows[i];
      const rowId = rowEl.id || "";                  // e.g., "tblgroupRow7"
      const rowindex = rowId.replace("tblgroupRow", "");

      // Try to read an explicit GroupID cell; fallback to rowId or a generated ID
      const GroupIdEl = getEl("GrpIDcell" + rowindex); // <-- adjust if your ID field has a different name
      let GroupID = normalize(GroupIdEl?.value);
      if (!GroupID) {
        // Fallback: use the row id or a generated deterministic ID
        GroupID = rowId || ("GRP_" + rowindex);
      }

      // const GrpIDcell =  getEl("GrpIDcell" + rowindex); 
      const GroupNameEl = getEl("GrpNamecell" + rowindex);
      const FromDateEl  = getEl("GrpFromcellvar" + rowindex);
      const ToDateEl    = getEl("GrpTocellvar" + rowindex);

      // const GroupID = = normalize(GrpIDcell?.value);
      const GroupName = normalize(GroupNameEl?.value);
      const FromDate  = normalize(FromDateEl?.value);
      const ToDate    = normalize(ToDateEl?.value);

      if (GroupID && GroupName && FromDate && ToDate) {
        // Warn if overwriting an existing key
        if (MeetUpdatedData.GroupDetails[GroupName]) {
          log.warn("CaptureGroupTable: Duplicate GroupID; overwriting existing entry.", { GroupID });
          // Remove previous from order to avoid duplicates, then push current
          MeetUpdatedData.GroupOrder = MeetUpdatedData.GroupOrder.filter(id => id !== GroupID);
        }

        // Keep JSON structure the same inside each group
        MeetUpdatedData.GroupDetails[GroupID] = {
          'GroupName': GroupName,
          'FromDate': FromDate,
          'ToDate': ToDate
        };

        MeetUpdatedData.GroupOrder.push(GroupID);
      } else {
        log.debug("CaptureGroupTable: Incomplete group row; skipped.", { rowindex, GroupID, GroupName, FromDate, ToDate });
      }
    }

    const groupsCount = Object.keys(MeetUpdatedData.GroupDetails).length;
    log.info("CaptureGroupTable: captured (GroupDetails as dictionary keyed by GroupID).", {
      groupsCount,
      orderCount: MeetUpdatedData.GroupOrder.length
    });

    return MeetUpdatedData;
  } catch (err) {
    log.error("CaptureGroupTable: fatal error.", err);
    return MeetUpdatedData;
  }
}

function captureSingleHeat(index)
{
  

  // Helpers
    const normalize = (v) => (typeof normalizeStr === 'function' ? normalizeStr(v) : (v ?? '').toString().trim());
    const safeInt = (v, def = 0) => {
      const n = parseInt(v, 10);
      return Number.isFinite(n) ? n : def;
    };
    const safeFloat = (v, def = 0) => {
      const n = parseFloat(v);
      return Number.isFinite(n) ? n : def;
    };
    const getEventPrefix = (heatId) => {
      try {
        if (typeof splitBeforeLastUnderscore === 'function') {
          const part = splitBeforeLastUnderscore(heatId);
          if (part && part.ok) return normalize(part.prefix);
        }
        // Fallback: everything before last underscore
        const s = String(heatId);
        const pos = s.lastIndexOf('_');
        return pos > 0 ? normalize(s.slice(0, pos)) : normalize(s);
      } catch {
        return normalize(heatId);
      }
    };
    
      const heatNameEl = getEl('HeatNamecell' + index);
      const HeatiD = normalize(heatNameEl?.value); // e.g., "100_FS_G02_B_1"
      const tblSwlist = getEl("tblSwlist" + index);

      if (!HeatiD) {
        log.warn("CaptureHeatDetailsTable: Missing HeatID; skipping row.", { index });
        
      }
      else
      {

      // Derive eventID as prefix before the last underscore
      const eventID = getEventPrefix(HeatiD);
      let eventstatuselvalue=0;

      // Ensure event dictionary object exists
      

      if (!MeetUpdatedData.EventDetails[eventID]) {
        const eventstatusel = document.getElementById(`${HeatiD}SelectEventStatus`);
        if (eventstatusel)
        {
  eventstatuselvalue=parseInt(eventstatusel.value);
        }


        MeetUpdatedData.EventDetails[eventID] = {
          "eventID": eventID,
          "eventName": "",     // keep field; fill if you have a source
          "eventStatus": eventstatuselvalue,    // keep field; fill if you have a source
          "HeatList": {}       // HeatList shall be a dictionary keyed by HeatID
        };
      }

      // Build BoardList (lanes) for this heat
      const BoardDetails = [];
      if (!tblSwlist) {
        log.warn("CaptureHeatDetailsTable: Missing swimmers sub-table; heat recorded with empty BoardList.", { index, HeatiD });
      } else {
        // Your table: first rows are headers; data starts at rowIndex = 3
        for (let RowIndex = 3; RowIndex < tblSwlist.rows.length; RowIndex++) {
          const rowCells   = tblSwlist.rows[RowIndex]?.cells;
          const BoardIDEl  = rowCells?.[1]?.firstChild; // lane number displayed (innerText)
          const idEl       = rowCells?.[2]?.firstChild; // swimmer id input
          const nameEl     = rowCells?.[3]?.firstChild; // swimmer name input
          const ClubnameEl   = rowCells?.[4]?.firstChild; // status/Club name selector

          const statusEl   = rowCells?.[5]?.firstChild; // status/DQ selector
          const timeEl     = rowCells?.[6]?.firstChild; // time input
          const timeEl_Bak     = rowCells?.[7]?.firstChild; // time input
          const timeEl_Manual     = rowCells?.[8]?.firstChild; // time input
          const timeEl_FCCAM     = rowCells?.[9]?.firstChild; // time input


          const SwimerID   = normalize(idEl?.value);
          const SwimerName = normalize(nameEl?.value);
          const ClubName = normalize(ClubnameEl?.value);          
          const BoardID    = safeInt(normalize(BoardIDEl?.value), 0);
          const SwimStatus = safeInt(normalize(statusEl?.value), 0);

          // Keep JSON shape the same: default SwimTimings as number 0
          let SwimTimings = 0;
          const SwTimetxt = normalize(timeEl?.value);
          if (SwTimetxt !== "" && SwTimetxt !== "0") {
            try {
              const seconds = convertToSeconds(SwTimetxt); // your helper
              const num = parseFloat(seconds);
              if (Number.isFinite(num)) SwimTimings = num; // numeric seconds
            } catch (tErr) {
              log.warn("CaptureHeatDetailsTable: convertToSeconds failed; using 0.", { SwTimetxt }, tErr);
              SwimTimings = 0;
            }
          }


             // Keep JSON shape the same: default SwimTimings as number 0
          let SwimTimings_Bak = 0;
          const SwTimetxt_Bak = normalize(timeEl_Bak?.value);
          if (SwTimetxt_Bak !== "" && SwTimetxt_Bak !== "0") {
            try {
              const seconds = convertToSeconds(SwTimetxt_Bak); // your helper
              const num = parseFloat(seconds);
              if (Number.isFinite(num)) SwimTimings_Bak = num; // numeric seconds
            } catch (tErr) {
              log.warn("CaptureHeatDetailsTable: convertToSeconds failed; using 0.", { SwTimetxt_Bak }, tErr);
              SwimTimings_Bak = 0;
            }

          }


               // Keep JSON shape the same: default SwimTimings as number 0
          let SwimTimings_Manual = 0;
          const SwTimetxt_Manual = normalize(timeEl_Manual?.value);
          if (SwTimetxt_Manual !== "" && SwTimetxt_Manual !== "0") {
            try {
              const seconds = convertToSeconds(SwTimetxt_Manual); // your helper
              const num = parseFloat(seconds);
              if (Number.isFinite(num)) SwimTimings_Manual = num; // numeric seconds
            } catch (tErr) {
              log.warn("CaptureHeatDetailsTable: convertToSeconds failed; using 0.", { SwTimetxt_Manual }, tErr);
              SwimTimings_Manual = 0;
            }

          }

               // Keep JSON shape the same: default SwimTimings as number 0
          let SwimTimings_FCCAM = 0;
          const SwTimetxt_FCCAM = normalize(timeEl_FCCAM?.value);
          if (SwTimetxt_FCCAM !== "" && SwTimetxt_FCCAM !== "0") {
            try {
              const seconds = convertToSeconds(SwTimetxt_FCCAM); // your helper
              const num = parseFloat(seconds);
              if (Number.isFinite(num)) SwimTimings_FCCAM = num; // numeric seconds
            } catch (tErr) {
              log.warn("CaptureHeatDetailsTable: convertToSeconds failed; using 0.", { SwTimetxt_FCCAM }, tErr);
              SwimTimings_FCCAM = 0;
            }

          }

          // Skip empty lane rows
          if (!SwimerName && !Number.isFinite(BoardID)) continue;

          BoardDetails.push({
            "BoardID": BoardID,
            "BoardStatus": 0,
            "SwimStatus": SwimStatus,
            "SwimTimings": SwimTimings,
            "SwimTimings_Bak": SwimTimings_Bak,
            "SwimTimings_Manual": SwimTimings_Manual,
            "SwimTimings_FCCAM": SwimTimings_FCCAM,            
            "ClubName": ClubName,
            "SwimerID": SwimerID,
            "SwimerName": SwimerName
          });
        }      
      }

      // Heat-level fields from inputs named with HeatID prefix
      let HeatStartTime = "";
      let HeatEndTime   = "";
      let HeatNotes     = "";
      let HeatStatus    = 0;

      let inputfeild = getEl(HeatiD + "StartTimeInput");
      if (inputfeild) HeatStartTime = inputfeild.value ?? "";

      inputfeild = getEl(HeatiD + "SelectHeatStatus");
      if (inputfeild) HeatStatus = safeInt(inputfeild.value, 0);

      inputfeild = getEl(HeatiD + "EndTimeInput");
      if (inputfeild) HeatEndTime = inputfeild.value ?? "";

      inputfeild = getEl(HeatiD + "HeatNotes");
      if (inputfeild) HeatNotes = inputfeild.value ?? "";

      // Write into the HeatList dictionary keyed by HeatID
      MeetUpdatedData.EventDetails[eventID].HeatList[HeatiD] = {
        "BoardList": BoardDetails,
        "HeatEndTime": HeatEndTime,
        "HeatID": HeatiD,
        "HeatStartTime": HeatStartTime,
        "HeatStatus": HeatStatus,
        "HeatNotes": HeatNotes
      };
    }

    // Done
    const eventsCount = Object.keys(MeetUpdatedData.EventDetails).length;

    const totalHeats = Object.values(MeetUpdatedData.EventDetails)
      .reduce((sum, ev) => sum + Object.keys(ev.HeatList || {}).length, 0);

    log.info("CaptureHeatDetailsTable: captured (EventDetails & HeatList as dictionaries).", {
      eventsCount,
      totalHeats
    });
  

}


function CaptureHeatDetailsTable(MeetUpdatedData) {
  try {
    let TempMeetUpdatedData={}
    const tblHeatDetails = getEl('tblHeatDetails', { required: true, desc: "Heat details table" });
    if (!tblHeatDetails) {
      log.warn("CaptureHeatDetailsTable: tblHeatDetails missing.");
      return MeetUpdatedData;
    }

    // Ensure container object
    if (typeof MeetUpdatedData !== 'object' || MeetUpdatedData === null) {
      MeetUpdatedData = {};
    }

    // EventDetails shall be a dictionary keyed by eventID
    MeetUpdatedData.EventDetails = {};
    TempMeetUpdatedData.EventDetails = {};

    

    // Iterate each heat row in the table
    for (let index = 0; index < tblHeatDetails.rows.length - 1; index++) {

      captureSingleHeat(index);
    }
    return MeetUpdatedData;
  
}catch (err) {
    log.error("CaptureHeatDetailsTable: fatal error.", err);
    return MeetUpdatedData;
  }
}