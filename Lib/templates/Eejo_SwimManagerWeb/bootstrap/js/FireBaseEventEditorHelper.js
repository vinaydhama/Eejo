
/* =========================
   FireBaseEventEditorHelper.js
   (Refactored with defensive checks, logs and error handlers)
   ========================= */

// ---------- Common helpers & logging ----------

const LOG_PREFIX = "[EventEditor]";

const log = {
  debug: (...args) => console.debug(LOG_PREFIX, ...args),
  info:  (...args) => console.info(LOG_PREFIX, ...args),
  warn:  (...args) => console.warn(LOG_PREFIX, ...args),
  error: (...args) => console.error(LOG_PREFIX, ...args),
};

// Safe DOM getter with presence checks
function getEl(id, { required = false, desc = id } = {}) {
  try {
    const el = document.getElementById(id);
    if (!el) {
      const msg = `Missing DOM element: ${desc} (#${id})`;
      required ? log.error(msg) : log.warn(msg);
    }
    return el;
  } catch (err) {
    log.error("getEl failed.", { id, desc, required }, err);
    return null;
  }
}

// Ensure table has TBODY; create if missing
function ensureTBody(table) {
  try {
    if (!table) return null;
    let body = table.tBodies[0];
    if (!body) {
      body = document.createElement('tbody');
      table.appendChild(body);
      log.debug("Created TBODY for", table.id || table);
    }
    return body;
  } catch (err) {
    log.error("ensureTBody failed.", { table }, err);
    return null;
  }
}

// Safe parse integer with fallback
function toInt(value, fallback = 0) {
  const n = Number.parseInt(value, 10);
  return Number.isNaN(n) ? fallback : n;
}

// Defensive check for string with underscore partition
function splitBeforeLastUnderscore(id) {
  if (typeof id !== 'string') return { ok: false, prefix: null, lastIndex: -1 };
  const lastIdx = id.lastIndexOf('_');
  if (lastIdx <= 0) {
    return { ok: false, prefix: null, lastIndex: lastIdx };
  }
  return { ok: true, prefix: id.slice(0, lastIdx), lastIndex: lastIdx };
}

// Normalize string: trim; if not string, return empty string
function normalizeStr(s) {
  return typeof s === 'string' ? s.trim() : '';
}

// ---------- Globals (kept from original file) ----------
let NumberofEventsperSw = 3;
// let Meetdteails;
let lastEvent = -1;

// ---------- Original functionality with defensive updates ----------

function ReloadData(datatoRefresh) {
  try {
    const NumberofEventsper = getEl("txt_NoOF_Events");
    if (NumberofEventsper) {
      const val = toInt(NumberofEventsper.value, NumberofEventsperSw);
      if (val > 0) {
        NumberofEventsperSw = val;
        log.debug("NumberofEventsperSw set to", NumberofEventsperSw);
      } else {
        log.warn("Invalid NumberofEventsperSw input; keeping previous.", { input: NumberofEventsper.value });
      }
    }

    switch (datatoRefresh) {
      case "SwDetails":
        try {
          GenerateSwimmersTable(MeetUpdatedData?.SwimmerDetails ?? {});
          log.info("ReloadData: SwDetails refreshed.");
        } catch (err) {
          log.error("GenerateSwimmersTable failed.", err);
        }
        break;

      case "Groups":
        try {
          const tblGroups = getEl('tblGroups', { required: true });
          if (!tblGroups) return;
          Availablegroups.length = 0;
          for (let i = 1; i < tblGroups.rows.length; i++) {
            const rowindex = (tblGroups.rows[i].id || "").replace("tblgroupRow", "");
            const GroupNameEl = getEl("GrpIDcell" + rowindex);
            const value = normalizeStr(GroupNameEl?.value);
            if (value) Availablegroups.push(value);
          }

          const tblEvents = getEl('tblEvents', { required: true });
          if (!tblEvents) return;
          for (let i = 1; i < tblEvents.rows.length; i++) {
            const rowindex = (tblEvents.rows[i].id || "").replace("tblEventsRow", "");
            const sel = getEl("EventGroupcell" + rowindex);
            if (!sel) continue;
            const selectedGroup = sel.value;
            sel.innerHTML = "";
            Availablegroups.forEach(Group => {
              const opt = document.createElement("option");
              opt.value = Group; opt.text = Group;
              sel.add(opt);
            });
            sel.value = selectedGroup;
          }
          log.info("ReloadData: Groups refreshed.", { groups: Availablegroups.length });
        } catch (err) {
          log.error("ReloadData Groups branch failed.", err);
        }
        break;

        case "Heat":

        
// case "Heats":
//   try {
//     // ----------------- helpers -----------------
//     const parseTime = (val) => {
//       if (val == null) return null;
//       const s = String(val).trim();
//       if (!s) return null;

//       // mm:ss.hh or m:ss
//       const m = s.match(/^(\d+):(\d+(?:\.\d+)?)$/);
//       if (m) {
//         const mins = parseInt(m[1], 10);
//         const secs = parseFloat(m[2]);
//         const total = mins * 60 + secs;
//         return Number.isFinite(total) ? total : null;
//       }

//       // plain seconds
//       const n = parseFloat(s);
//       return Number.isFinite(n) ? n : null;
//     };

//     const compareTimesAscNullLast = (a, b) => {
//       const x = a?.SwimmersEventBestTime;
//       const y = b?.SwimmersEventBestTime;
//       const fx = Number.isFinite(x);
//       const fy = Number.isFinite(y);
//       if (fx && fy) return x - y;
//       if (fx && !fy) return -1;  // valid < null
//       if (!fx && fy) return 1;   // null > valid
//       return 0; // both null
//     };

//     const heatDictToArray = (heatDict) => {
//       // Flatten and order by (eventID, heat number parsed from key)
//       // Assumes heatID = `${eventID}_${heatNumber}`
//       return Object.values(heatDict)
//         .sort((a, b) => {
//           const [ea, ha] = String(a.ID).split("_");
//           const [eb, hb] = String(b.ID).split("_");
//           if (ea !== eb) return ea.localeCompare(eb);
//           return (parseInt(ha, 10) || 0) - (parseInt(hb, 10) || 0);
//         });
//     };

//     // -------------- collect swimmers --------------
//     // Dictionaries requested:
//     const EventDetailsDict = {}; // eventID -> { EventID, EventName?, Boards, HeatsCount, ... }
//     const HeatListDict = {};     // heatID  -> { ID, EventID, Boardinfo, HeatStatus, LaneOffset }

//     const tblSwimmers = getEl('tblSwDetails', { required: true });
//     const SwimmerDetailsArray = [];

//     if (!tblSwimmers) return;

//     for (let i = 1; i < tblSwimmers.rows.length; i++) {
//       const rowindex = (tblSwimmers.rows[i].id || "").replace("tblSwimmersRow", "");
//       const tblSwSelectedEvents = getEl('tblSwSelectedEvents' + rowindex);
//       if (!tblSwSelectedEvents) continue;

//       for (let j = 0; j < tblSwSelectedEvents.rows.length - 1; j++) {
//         const availId = "SwimmersAvailablecell" + rowindex + "_" + j;
//         const nameId  = "SwimmersNamecell" + rowindex;
//         const timeId  = "SwimmersEventBestTime" + rowindex + "_" + j;
//         const eventSelId = "SwimmersEventSelector" + rowindex + "_" + j;

//         const checked = !!getEl(availId)?.checked;
//         if (!checked) continue;

//         const nameRaw = getEl(nameId)?.value ?? "";
//         const timeRaw = getEl(timeId)?.value;
//         const EventSelector = getEl(eventSelId);

//         // normalizeStr may be your utility; guard if absent
//         const SwimmersNamecell = (typeof normalizeStr === 'function')
//           ? normalizeStr(nameRaw)
//           : String(nameRaw).trim();

//         const parsedTime = parseTime(
//           (typeof normalizeStr === 'function')
//             ? normalizeStr(timeRaw)
//             : timeRaw
//         );

//         if (EventSelector && SwimmersNamecell) {
//           SwimmerDetailsArray.push({
//             SwName: SwimmersNamecell,
//             Swevents: EventSelector.value,          // treat value as eventID
//             SwimmersEventBestTime: parsedTime // null allowed (sorted last)
//           });
//         }
//       }
//     }

//     // -------------- setup lanes/heats --------------
//     const boardsInputEl = getEl("tblMeet_txtBoards");
//     const boardCount = toInt(boardsInputEl?.value, 1);
//     const BoardsPerHeat = boardCount > 0 ? boardCount : 1;

//     const startsAtZero = !!getEl("BoardStartsFromZero")?.checked; // guard

//     // -------------- per-event processing --------------
//     for (let EventCounter = 0; EventCounter < AvailableEvents.length; EventCounter++) {
//       const eventID = AvailableEvents[EventCounter]; // using as eventID key
//       const SwimmersList = SwimmerDetailsArray.filter(sd => sd.Swevents === eventID);

//       // sort ascending (fastest first), nulls last
//       SwimmersList.sort(compareTimesAscNullLast);

//       const HeatsCount = Math.ceil(SwimmersList.length / BoardsPerHeat);

//       // Record event details in dictionary
//       EventDetailsDict[eventID] = {
//         EventID: eventID,
//         Boards: BoardsPerHeat,
//         HeatsCount: HeatsCount,
//         EntriesCount: SwimmersList.length
//         // Add other fields if you have (e.g., stroke, distance, gender, age group)
//       };

//       // create heats for this event in dictionary
//       for (let h = 0; h < HeatsCount; h++) {
//         const heatID = `${eventID}_${h + 1}`;
//         HeatListDict[heatID] = {
//           ID: heatID,
//           EventID: eventID,
//           Boardinfo: [],
//           HeatStatus: 0,
//           LaneOffset: startsAtZero ? 0 : 1 // preserve lane base
//         };
//       }

//       // distribute swimmers round-robin across heats (existing behavior)
//       let j = 0; // which heat index within this event
//       for (let i = 0; i < SwimmersList.length; i++) {
//         if (j === HeatsCount) j = 0;
//         const currentHeatID = `${eventID}_${j + 1}`;
//         const boardinfo = HeatListDict[currentHeatID].Boardinfo;

//         // lane number while inserting
//         const laneIndex = boardinfo.length; // zero-based index in this heat
//         const laneNumber = laneIndex + (startsAtZero ? 0 : 1);

//         boardinfo.push({
//           BoardID: laneNumber,    // respect 0/1-based at insert
//           BoardStatus: 0,
//           SwimStatus: 0,
//           SwimTimings: 0,
//           SwimerID: SwimmersList[i].SwName,  // TODO: real unique ID if available
//           SwimerName: SwimmersList[i].SwName,
//           SeedTime: SwimmersList[i].SwimmersEventBestTime // keep number seconds or null
//         });
//         j++;
//       }
//     }

//     // ----------- lane reordering (preserve lane base) -----------
//     Object.values(HeatListDict).forEach(heat => {
//       const arr = Array.isArray(heat.Boardinfo) ? heat.Boardinfo : [];
//       const k = arr.length;

//       // Retain original pattern
//       const firstPartIndices = [];
//       for (let i = k - 2; i >= 0; i -= 2) firstPartIndices.push(i);

//       const set = new Set(firstPartIndices);
//       const secondPartIndices = [];
//       for (let i = 0; i < k; i++) if (!set.has(i)) secondPartIndices.push(i);

//       const sortedArray = [...firstPartIndices, ...secondPartIndices]
//         .map(i => arr[i])
//         .filter(Boolean);

//       const base = heat.LaneOffset ?? 0; // 0 for zero-based, 1 for one-based
//       for (let i = 0; i < sortedArray.length; i++) {
//         sortedArray[i].BoardID = i + base; // preserve offset
//       }

//       heat.Boardinfo = sortedArray;
//       log.debug("Heat lane arrangement computed.", heat);
//     });

//     // ---------- render (adapter for legacy UI expecting arrays) ----------
//     const HeatListArray = heatDictToArray(HeatListDict);
//     GenerateHeatDetailsTable(HeatListArray);

//     // Optionally expose the dictionaries globally or return them
//     // window.EventDetailsDict = EventDetailsDict;
//     // window.HeatListDict = HeatListDict;

//     log.info("ReloadData: Heats recalculated with dictionary structures.");
//   } catch (err) {
//     log.error("ReloadData Heats branch failed.", err);
//   }
 

//           break;

      case "Heats":
        try {
          // GenerateHeatList
          let Heatcounter = 0;
          const HeatList = [];
          const tblSwimmers = getEl('tblSwDetails', { required: true });
          const SwimmerDetailsArray = [];

          if (!tblSwimmers) return;

          for (let i = 1; i < tblSwimmers.rows.length; i++) {
            const rowindex = (tblSwimmers.rows[i].id || "").replace("tblSwimmersRow", "");
            const tblSwSelectedEvents = getEl('tblSwSelectedEvents' + rowindex);
            if (!tblSwSelectedEvents) continue;

            for (let j = 0; j < tblSwSelectedEvents.rows.length - 1; j++) {
              const availId = "SwimmersAvailablecell" + rowindex + "_" + j;
              const nameId  = "SwimmersNamecell" + rowindex;
              const timeId  = "SwimmersEventBestTime" + rowindex + "_" + j;
              const eventSelId = "SwimmersEventSelector" + rowindex + "_" + j;

              const checked = !!getEl(availId)?.checked;
              if (checked) {
                const SwimmersNamecell = normalizeStr(getEl(nameId)?.value);
                const SwimmersEventBestTime = normalizeStr(getEl(timeId)?.value);
                const EventSelector = getEl(eventSelId);
                const bestTimeNum = parseFloat(SwimmersEventBestTime);
                const safeTime = Number.isFinite(bestTimeNum) ? bestTimeNum : Number.POSITIVE_INFINITY;

                if (EventSelector && SwimmersNamecell) {
                  SwimmerDetailsArray.push({
                    'SwName': SwimmersNamecell,
                    'Swevents': EventSelector.value,
                    'SwimmersEventBestTime': safeTime
                  });
                }
              }
            }
          }

          for (let EventCounter = 0; EventCounter < AvailableEvents.length; EventCounter++) {
            const eventname = AvailableEvents[EventCounter];
            const SwimmersList = [];

            SwimmerDetailsArray.forEach(SwimerDetail => {
              if (SwimerDetail.Swevents === eventname) {
                SwimmersList.push(SwimerDetail);
              }
            });

            // Sort SwimmersList by best time (ascending)
            for (let i = 0; i < SwimmersList.length - 1; i++) {
              for (let j = 0; j < SwimmersList.length - i - 1; j++) {
                if (SwimmersList[j].SwimmersEventBestTime > SwimmersList[j + 1].SwimmersEventBestTime) {
                  const temp = SwimmersList[j];
                  SwimmersList[j] = SwimmersList[j + 1];
                  SwimmersList[j + 1] = temp;
                }
              }
            }

            const boardsInputEl = getEl("tblMeet_txtBoards");
            const boardCount = toInt(boardsInputEl?.value, 1);
            const BoardCount = boardCount > 0 ? boardCount : 1;
            const BoardStartsFromZero = getEl("BoardStartsFromZero");
            


            const NoofHeats = Math.ceil(SwimmersList.length / BoardCount);

            for (let i = 0; i < NoofHeats; i++) {
              const Boardinfo = [];
              const HeatDetails = { 'ID': eventname + "_" + (i + 1), 'Boardinfo': Boardinfo, 'HeatStatus': 0  };
              HeatList.push(HeatDetails);
            }

            let j = 0;
            for (let i = 0; i < SwimmersList.length; i++) {
              if (j === NoofHeats) j = 0;
              const boardinfo = HeatList[Heatcounter + j].Boardinfo;
              let  LineID=  boardinfo.length;

              if (!BoardStartsFromZero.checked) LineID=LineID +1
              
              boardinfo.push({
                'BoardID': LineID,
                'BoardStatus': 0,
                'SwimStatus': 0,
                'SwimTimings': 0,
                'SwimerID': SwimmersList[i].SwName,
                'SwimerName': SwimmersList[i].SwName
              });
              j++;
            }
            Heatcounter = Heatcounter + NoofHeats;
          }

          // Reorder board lanes per original logic with safeguards
          HeatList.forEach(heatlst => {
            const arr = Array.isArray(heatlst.Boardinfo) ? heatlst.Boardinfo : [];
            const k = arr.length;

            const firstPartIndices = [];
            for (let i = k - 2; i >= 0; i -= 2) {
              firstPartIndices.push(i);
            }

            const secondPartIndices = [];
            for (let i = 0; i < k; i++) {
              if (!firstPartIndices.includes(i)) {
                secondPartIndices.push(i);
              }
            }

            const sortedArray = [...firstPartIndices, ...secondPartIndices].map(i => arr[i]).filter(Boolean);
            for (let i = 0; i < sortedArray.length; i++) {
              sortedArray[i].BoardID = i;
            }
            heatlst.Boardinfo = sortedArray;
            log.debug("Heat lane arrangement computed.", heatlst);
          });

          GenerateHeatDetailsTable(HeatList);
          log.info("ReloadData: Heats recalculated.");
        } catch (err) {
          log.error("ReloadData Heats branch failed.", err);
        }
        break;

      case "Events":
        try {
          const tblEvents = getEl('tblEvents', { required: true });
          if (!tblEvents) return;

          AvailableEvents.length = 0;
          for (let i = 1; i < tblEvents.rows.length; i++) {
            const rowindex = (tblEvents.rows[i].id || "").replace("tblEventsRow", "");
            const dist  = normalizeStr(getEl("EventDistencecell" + rowindex)?.value);
            const stroke= normalizeStr(getEl("EventStrokecell"   + rowindex)?.value);
            const group = normalizeStr(getEl("EventGroupcell"    + rowindex)?.value);
            const gender= normalizeStr(getEl("EventGendercell"   + rowindex)?.value);
            const name  = `${dist}_${stroke}_${group}_${gender}`;
            AvailableEvents.push(name);
          }

          const tblSwDetails = getEl('tblSwDetails', { required: true });
          if (tblSwDetails) {
            for (let i = 1; i < tblSwDetails.rows.length; i++) {
              const rowindex = (tblSwDetails.rows[i].id || "").replace("tblSwimmersRow", "");
              const tblSwSelectedEvents = getEl("tblSwSelectedEvents" + rowindex);
              if (!tblSwSelectedEvents) continue;

              for (let j = 0; j <= tblSwSelectedEvents.rows.length; j++) {
                const selId = "SwimmersEventSelector" + rowindex + "_" + j;
                const sel = getEl(selId);
                if (!sel) continue;
                const selectedEvent = sel.value;
                sel.options.length = 0;
                AvailableEvents.forEach(SwEvent => {
                  const opt = document.createElement("option");
                  opt.value = SwEvent; opt.text = SwEvent;
                  sel.add(opt);
                });
                sel.value = selectedEvent;
              }
            }
          }

          log.info("ReloadData: Events refreshed.", { count: AvailableEvents.length });
        } catch (err) {
          log.error("ReloadData Events branch failed.", err);
        }
        break;

      default:
        log.warn("ReloadData called with unsupported mode.", { datatoRefresh });
        break;
    }
  } catch (outerErr) {
    log.error("ReloadData fatal error.", { datatoRefresh }, outerErr);
  }
}

function AddGroupRow(index, GroupDetail) {
  try {
    const tblGroups = getEl('tblGroups', { required: true });
    if (!tblGroups) return;

    let tblGroupsBody = tblGroups.tBodies[0];
    if (!tblGroupsBody) {
      tblGroupsBody = document.createElement('tbody');
      tblGroups.appendChild(tblGroupsBody);
    }

    const tblgroupRow = tblGroupsBody.insertRow();
    tblgroupRow.draggable = true;
    tblgroupRow.ondragstart = function () { startDrag() };
    tblgroupRow.ondragover  = function () { dragover() };
    tblgroupRow.id = "tblgroupRow" + index;

    let GrpCheckcell = tblgroupRow.insertCell();
    GrpCheckcell.innerHTML = "<input type='Checkbox' id ='GrpCheckcell" + index + "'>";
    const GrpCheckcellchkbox = getEl('GrpCheckcell' + index);
    if (GrpCheckcellchkbox) {
      GrpCheckcellchkbox.addEventListener("change",
        function () {
          if (GrpCheckcellchkbox.checked === true) {
            GroupsSlectedRows.push(GrpCheckcellchkbox.id.replace("GrpCheckcell", ""));
          } else {
            GroupsSlectedRows.pop(GrpCheckcellchkbox.id.replace("GrpCheckcell", ""));
          }
        });
    }

    let Grpslnocell = tblgroupRow.insertCell();
    Grpslnocell.innerHTML = (index + 1);

    let GrpIDcell = tblgroupRow.insertCell();
    GrpIDcell.innerHTML = "<input class='form-control' id ='GrpIDcell" + index + "'>";
    const grpID = getEl('GrpIDcell' + index);
    if (grpID) grpID.value = GroupDetail?.GroupID ?? "";


    let GrpNamecell = tblgroupRow.insertCell();
    GrpNamecell.innerHTML = "<input class='form-control' id ='GrpNamecell" + index + "'>";
    const grpNameEl = getEl('GrpNamecell' + index);
    if (grpNameEl) grpNameEl.value = GroupDetail?.GroupName ?? "";

    let GrpFromcell = tblgroupRow.insertCell();
    GrpFromcell.innerHTML = "<input class='form-control' type='date' id ='GrpFromcellvar" + index + "'>";
    const fromEl = getEl('GrpFromcellvar' + index);
    if (fromEl) fromEl.value = GroupDetail?.FromDate ?? "";

    let GrpTocell = tblgroupRow.insertCell();
    GrpTocell.innerHTML = "<input class='form-control' type='date' id ='GrpTocellvar" + index + "'>";
    const toEl = getEl('GrpTocellvar' + index);
    if (toEl) toEl.value = GroupDetail?.ToDate ?? "";

    log.debug("AddGroupRow completed.", { index });
  } catch (err) {
    log.error("AddGroupRow failed.", { index, GroupDetail }, err);
  }
}

function AddSwimmerRow(index, SwDetails) {
  try {
    const tblSwimmers = getEl('tblSwDetails', { required: true });
    if (!tblSwimmers) return;

    let tblSwimmersBody = tblSwimmers.tBodies[0];
    if (!tblSwimmersBody) {
      tblSwimmersBody = document.createElement('tbody');
      tblSwimmers.appendChild(tblSwimmersBody);
    }

    const tblSwimmersRow = tblSwimmers.insertRow();
    tblSwimmersRow.setAttribute('draggable', 'true');
    tblSwimmersRow.ondragstart = function () { startDrag() };
    tblSwimmersRow.ondragover  = function () { dragover() };

    let SwimmersCheckboxcell = tblSwimmersRow.insertCell();
    SwimmersCheckboxcell.innerHTML = "<input type='Checkbox' id ='SwimmersCheckboxcell" + index + "'>";
    const SwimmersCheckbox = getEl('SwimmersCheckboxcell' + index);
    if (SwimmersCheckbox) {
      SwimmersCheckbox.checked = true;
      SwimmersCheckbox.addEventListener("change", function () {
        const Checkcellchkbox = getEl('SwimmersCheckboxcell' + index);
        const tblSwSelectedEvent = getEl("tblSwSelectedEvents" + index);
        if (Checkcellchkbox && tblSwSelectedEvent) {
          for (let j = 0; j < tblSwSelectedEvent.rows.length - 1; j++) {
            const avail = getEl("SwimmersAvailablecell" + index + "_" + j);
            if (avail) avail.checked = Checkcellchkbox.checked;
          }
        }
        if (Checkcellchkbox?.checked === true) {
          SwDetailsSlectedRows.push(Checkcellchkbox.id.replace("SwimmersCheckboxcell", ""));
        } else {
          SwDetailsSlectedRows.pop(Checkcellchkbox.id.replace("SwimmersCheckboxcell", ""));
        }
      });
    }

    tblSwimmersRow.id = "tblSwimmersRow" + index;

    let Swimmersslnocell = tblSwimmersRow.insertCell();
    Swimmersslnocell.innerHTML = (index + 1);

    let SwimmersNamecell = tblSwimmersRow.insertCell();
    SwimmersNamecell.innerHTML = "<input class='form-control' id ='SwimmersNamecell" + index + "'>";
    const nameEl = getEl("SwimmersNamecell" + index);
    if (nameEl) nameEl.value = SwDetails?.Name ?? "";

    let SwimmerGroupCell = tblSwimmersRow.insertCell();
    SwimmerGroupCell.innerHTML = "<input class='form-control' id ='SwimmerGroupCell" + index + "'>";
    const groupEl = getEl("SwimmerGroupCell" + index);
    if (groupEl) groupEl.value = SwDetails?.Group ?? "";

    let SwimmerClubCell = tblSwimmersRow.insertCell();
    SwimmerClubCell.innerHTML = "<input class='form-control' type='text' id ='SwimmerClubCell" + index + "'>";

    // Selected Events table
    const tblSwSelectedEvents = document.createElement("TABLE");
    tblSwSelectedEvents.id = "tblSwSelectedEvents" + index;

    const header = tblSwSelectedEvents.createTHead();
    let row = header.insertRow();
    let cell = row.insertCell(); cell.innerHTML = "<b> Event Name. <b>";
    cell = row.insertCell(); cell.innerHTML = "<b> Best Timeings <b>";
    cell = row.insertCell(); cell.innerHTML = "<b> Available <b>";
    cell = row.insertCell();
    cell.innerHTML =
      "<button onclick=AppendRow('" + tblSwSelectedEvents.id + "','tblSwimmersRow')><i class='fa fa-fw fa-plus'></i></button> " +
      "<button onclick=DeleteRows('" + tblSwSelectedEvents.id + "','tblSwSelectedEvents','tblSwimmersRow')><i class='fa fa-fw fa-minus'></i></button>";

    const SwimmersEventcell = tblSwimmersRow.insertCell();
    SwimmersEventcell.appendChild(tblSwSelectedEvents);

    for (let j = 0; j < NumberofEventsperSw; j++) {
      AddSwEventRow(tblSwSelectedEvents.id);
    }

    const table = getEl("tblSwDetails");
    if (table) {
      try { SetTableNavigation(table); }
      catch (navErr) { log.warn("SetTableNavigation failed for tblSwDetails.", navErr); }
    }

    log.debug("AddSwimmerRow completed.", { index });
  } catch (err) {
    log.error("AddSwimmerRow failed.", { index, SwDetails }, err);
  }
}

function AddSwEventRow(EventTableName) {
  try {
    const index = EventTableName.replace("tblSwSelectedEvents", "");
    const tbl = getEl(EventTableName, { required: true });
    if (!tbl) return;

    const j = tbl.rows.length;
    const body = ensureTBody(tbl);
    if (!body) return;

    const tblSwlistRow = tbl.insertRow();

    // Event selector
    const SelCell = tblSwlistRow.insertCell();
    const selId = `SwimmersEventSelector${index}_${j}`;
    SelCell.innerHTML = `<select id='${selId}'></select>`;
    const sel = getEl(selId);
    if (sel && Array.isArray(AvailableEvents) && AvailableEvents.length > 0) {
      AvailableEvents.forEach(SwEvent => {
        const opt = document.createElement("option");
        opt.value = SwEvent; opt.text = SwEvent;
        sel.add(opt);
      });
    }
    const selRefill = getEl(selId);
    if (selRefill) selRefill.value = "";

    // Best time
    const timeCell = tblSwlistRow.insertCell();
    const timeId = `SwimmersEventBestTime${index}_${j}`;
    timeCell.innerHTML = `<input class='form-control' id='${timeId}'>`;
    const timeInput = getEl(timeId);
    if (timeInput) {
      timeInput.value = "00:00:00";
      try { setTimeinputValidation(timeInput, false); }
      catch (err) { log.warn("setTimeinputValidation failed.", { timeId }, err); }
    }

    // Availability
    const availCell = tblSwlistRow.insertCell();
    const availId = `SwimmersAvailablecell${index}_${j}`;
    availCell.innerHTML = `<input type='Checkbox' id='${availId}'>`;
    const avail = getEl(availId);
    if (avail) avail.checked = true;

    const table = getEl(tbl.id);
    if (table) {
      try { SetTableNavigation(table); }
      catch (navErr) { log.warn("SetTableNavigation failed in AddSwEventRow.", { tableId: tbl.id }, navErr); }
    }

    log.debug("AddSwEventRow appended.", { EventTableName, index, j });
  } catch (err) {
    log.error("AddSwEventRow failed.", { EventTableName }, err);
  }
}

function AppendRow(TableName, idprefix, tblindex = 0) {
  try {
    const grptab = getEl(TableName, { required: true });
    if (!grptab) return;

    let Rowindextoadd = 0;
    for (let i = 0; i <= grptab.rows.length; i++) {
      if (!grptab.rows[idprefix + i]) {
        Rowindextoadd = i;
        break;
      }
    }

    switch (TableName) {
      case "tblSwlist0":
        {
          let Heat = {};
          AddSwList(Heat, tblindex, 0);
        }
        break;

      case "tblSwDetails":
        {
          const SwDetails = { 'Name': "", 'Group': "" };
          AddSwimmerRow(Rowindextoadd, SwDetails);
        }
        break;

      case "tblGroups":
        {
          const GroupDetails = { 'GroupName': "", 'Year': "" };
          AddGroupRow(Rowindextoadd, GroupDetails);
        }
        break;

      case "tblEvents":
        {
          const Swevent = " _ _ _ ";
          AddEventRow(Rowindextoadd, Swevent);
        }
        break;

      case "tblHeatDetails":
        {
          const Boardinfo = [{
            'BoardID': 0, 'BoardStatus': 0, 'SwimStatus': 0, 'SwimTimings': 0,
            'SwimerID': " ", 'SwimerName': " "
          }];
          const HeatDetails = { 'ID': "", 'Boardinfo': Boardinfo };
          AddHeatRow(Rowindextoadd, HeatDetails);
        }
        break;

      default:
        if (TableName.includes("tblSwSelectedEvents")) {
          AddSwEventRow(TableName);
        }
        break;
    }
  } catch (err) {
    log.error("AppendRow failed.", { TableName, idprefix, tblindex }, err);
  }
}




// Helper: normalize various inputs to "HH:MM"
function normalizeTime(value) {
  if (value == null) return '';
  const s = String(value).trim();

  // Accept "HH:MM"  // Accept "HH:MM" or "HH:MM:SS" ? keep HH:MM
  const iso = /^(\d{2}):(\d{2})(?::\d{2})?$/.exec(s);
  if (iso) return `${iso[1]}:${iso[2]}`;

  // Optional: convert "h:mm AM/PM" ? 24h
  const ampm = s.match(/^(\d{1,2}):(\d{2})\s*([APap][Mm])$/);
  if (ampm) {
    let h = parseInt(ampm[1], 10);
    const mm = ampm[2];
    const mer = ampm[3].toUpperCase();
    if (mer === 'PM' && h !== 12) h += 12;
    if (mer === 'AM' && h === 12) h = 0;
    return `${String(h).padStart(2, '0')}:${mm}`;
  }

  return ''; // Unknown format ? leave blank
}

// May not be required, to add Heat as it's calculated out of Sw name & Event List
// function AddHeatRow(index, Heat) {
//   try {
//     const tblHeatDetails = getEl('tblHeatDetails', { required: true, desc: 'Heat details table' });
//     if (!tblHeatDetails) return;

//     const body = ensureTBody(tblHeatDetails);
//     if (!body) {
//       log.error("Cannot ensure TBODY for tblHeatDetails.");
//       return;
//     }

//     const tblHeatDetailsRow = body.insertRow();
//     tblHeatDetailsRow.id = "tblHeatDetailsRow" + index;

//     const HeatCheckcell = tblHeatDetailsRow.insertCell();
//     HeatCheckcell.classList.add('hide-on-print');
//     HeatCheckcell.innerHTML = `<input type='Checkbox' id ='HeatCheckcell_${index}'>`;

//     // -------- Robust EventID computation --------
//     let EventID = -1;
//     let heatId ="";
//     try {
//       const eventList = Array.isArray(Meetdteails?.EventList) ? Meetdteails.EventList : null;
//       heatId = Heat?.ID;

//       if (!eventList) {
//         log.warn("EventList missing or not an array; cannot compute EventID.", { Meetdteails });
//       } else if (typeof heatId !== 'string' || !heatId.length) {
//         log.warn("Heat.ID not a valid string; cannot compute EventID.", { Heat });
//       } else {
//         const part = splitBeforeLastUnderscore(heatId);
//         if (!part.ok) {
//           log.warn("Heat.ID has no valid underscore partition; using full ID fallback.", { heatId, lastIndex: part.lastIndex });
//         } else {
//           const key = normalizeStr(part.prefix);
//           EventID = eventList.findIndex(ev => normalizeStr(ev) === key);

//           if (EventID === -1) {
//             // Also support EventList being array of objects with ID-like property
//             EventID = eventList.findIndex(ev => {
//               const candidate = (ev?.ID ?? ev?.Id ?? ev?.id);
//               return typeof candidate === 'string' && normalizeStr(candidate) === key;
//             });
//           }

//           if (EventID === -1) {
//             log.info("No matching event found for Heat prefix.", { prefix: key, heatId, totalEvents: eventList.length });
//           } else {
//             log.debug("Matched EventID for Heat.", { EventID, prefix: key, heatId });
//           }
//         }
//       }
//     } catch (err) {
//       EventID = -1;
//       log.error("Failed to compute EventID.", err);
//     }

//     // Heat name cell
//     const HeatNamecell = tblHeatDetailsRow.insertCell();
//     HeatNamecell.classList.add('hide-on-print');
//     HeatNamecell.innerHTML = `<input class='form-control' id ='HeatNamecell${index}'>`;
//     const HeatNamecelltxt = getEl('HeatNamecell' + index);
//     if (HeatNamecelltxt) HeatNamecelltxt.value = normalizeStr(Heat?.ID);

//     // Controls cell & swimmers table
//     const tblSwlist = document.createElement("TABLE");
//     tblSwlist.id = "tblSwlist" + index;

//     const controlsCell = tblHeatDetailsRow.insertCell();
//     controlsCell.id= "controlsCell"+ index;
//     controlsCell.classList.add('hide-on-print');
//     controlsCell.innerHTML =
//       `<button onclick=AppendRow('${tblSwlist.id}','tblSwlistRow_')><i class='fa fa-fw fa-plus'></i></button>` +
//       ` <button onclick=DeleteRows('${tblSwlist.id}','BoardCheckcell_','tblSwlistRow_')><i class='fa fa-fw fa-minus'></i></button>`+
//        `<button onclick=UpdateSelectedData('Events')><i class="fa fa-fw fa-upload"></i></button>`      ;

//     const header = tblSwlist.createTHead();
//     let row = header.insertRow();
//     let cell = row.insertCell();

//     // Header text logic with EventID safety
//     const isSameEvent = (lastEvent === EventID);
//     const heatNumberText = (typeof Heat?.ID === 'string' && Heat.ID.includes('_'))
//       ? Heat.ID.substring(Heat.ID.lastIndexOf('_') + 1)
//       : "?";
//     const eventOrdinal = (EventID >= 0) ? (EventID + 1) : "N/A";

//     let headerText;
//     let highlightNewEvent = false;

//     if (isSameEvent && EventID >= 0) {
//       headerText = `<b style='font-size: 12px'> Event: ${eventOrdinal} Heat : ${heatNumberText}</b>`;
//     } else {
//       lastEvent = EventID;
//       const formatted = (typeof formatSwimmingEvent === 'function')
//         ? formatSwimmingEvent(Heat.ID)
//         : normalizeStr(Heat.ID);
//       headerText = `<b style='font-size: 12px'>Event: ${eventOrdinal} ${formatted}</b>`;
//       highlightNewEvent = true;
//     }

//     cell.innerHTML = headerText;

//     if (highlightNewEvent) {
//       cell.style.backgroundColor = "rgb(100, 100, 100)";
//     }

//       cell.colSpan = 7;




// // Create header row (if needed)
//  row = header.insertRow();

// // (Optional) first two empty cells as in your original code
// cell = row.insertCell();

// // ------------------ Start Time ------------------
// cell = row.insertCell();

// {
//   const inputId = `${heatId}StartTimeInput`;

//   const label = document.createElement('label');
//   label.htmlFor = inputId;
//   label.textContent = 'Start';

//   const br = document.createElement('br');

//   const input = document.createElement('input');
//   input.type = 'time';
//   input.id = inputId;
//   input.name = 'startTime';

//   const val = normalizeTime(Heat?.HeatStartTime ?? '');
//   if (val) input.value = val;

//   cell.append(label, br, input);
// }

// // ------------------ End Time ------------------
// cell = row.insertCell();

// {
//   const inputId = `${heatId}EndTimeInput`;

//   const label = document.createElement('label');
//   label.htmlFor = inputId;
//   label.textContent = 'End';

//   const br = document.createElement('br');

//   const input = document.createElement('input');
//   input.type = 'time';
//   input.id = inputId;
//   input.name = 'endTime';

//   const val = normalizeTime(Heat?.HeatEndTime ?? '');
//   if (val) input.value = val;

//   cell.append(label, br, input);
// }

// // ------------------ Status (select) ------------------
// cell = row.insertCell();

// {
//   const label = document.createElement('label');
//   label.textContent = 'Status';

//   const br = document.createElement('br');

//   const select = document.createElement('select');
//   select.id = `${heatId}SelectHeatStatus`;
//   select.classList.add('dropdown-cell');

//   const statuses = Array.isArray(HeatStatus) ? HeatStatus : [];

//   statuses.forEach((statusText, i) => {
//     const option = document.createElement('option');
//     option.value = String(i);      // values are strings
//     option.textContent = statusText;
//     select.add(option);
//   });

//   // Set selected index from Heat.HeatStatus
//   const idx = Number.parseInt(Heat?.HeatStatus, 10);
//   const validIdx = Number.isInteger(idx) && idx >= 0 && idx < statuses.length;
//   select.value = validIdx ? String(idx) : '0';

//   cell.append(label, br, select);
// }

// // ------------------ Notes ------------------
// cell = row.insertCell();
// // If you want Notes to span two columns, set colSpan here
// cell.colSpan = 3;

// {
//   const inputId = `${heatId}HeatNotes`;

//   const label = document.createElement('label');
//   label.htmlFor = inputId;
//   label.textContent = 'Notes';

//   const br = document.createElement('br');

//   const textarea = document.createElement('textarea');
//   textarea.id = inputId;
//   textarea.name = 'notes';
//   textarea.rows = 2;
//   textarea.value = String(Heat?.HeatNotes ?? '');

//   cell.append(label, br, textarea);


//     row = header.insertRow();
//     let c = row.insertCell(); c.classList.add('hide-on-print'); // blank
//     c = row.insertCell(); c.innerHTML = "<b>Line<b>";
//     c = row.insertCell(); c.classList.add('hide-on-print'); c.innerHTML = "<b>SwimerID.<b>";
//     c = row.insertCell(); c.innerHTML = "<b>Name<b>";
//     c = row.insertCell(); c.innerHTML = "<b>School \\ Club.<b>";
//     c = row.insertCell(); c.innerHTML = "<b>SwimStatus<b>";
//     c = row.insertCell(); c.innerHTML = "<b>SwimTimeings<b>";

//     // Body cell with swimmer list
//     const HeatSwimmerListcell = tblHeatDetailsRow.insertCell();
//     HeatSwimmerListcell.id = 'SwimmersListcell' + index;
//     HeatSwimmerListcell.appendChild(tblSwlist);

//     const boards = Array.isArray(Heat?.Boardinfo) ? Heat.Boardinfo : [];
//     for (let j = 0; j < boards.length; j++) {
//       try {
//         AddSwList(Heat, index, j);
//       } catch (err) {
//         log.error("AddSwList failed for row", { index, j, Heat }, err);
//       }
//     }

//     const table = getEl(tblSwlist.id);
//     if (table) {
//       try { SetTableNavigation(table); }
//       catch (navErr) { log.warn("SetTableNavigation failed.", { tableId: tblSwlist.id }, navErr); }
//     }

//     tblHeatDetailsRow.setAttribute('draggable', 'true');
//     tblHeatDetailsRow.ondragstart = function () { startDrag() };
//     tblHeatDetailsRow.ondragover  = function () { dragover() };

//     log.debug("AddHeatRow completed.", { index, HeatID: Heat?.ID, EventID });
//   }
//   } catch (outerErr) {
//     log.error("AddHeatRow fatal error.", { index, Heat }, outerErr);
//   }
// }



/* ===========================
   GenerateHeatDetailsTable
   - UPDATED: Heats is Dict
   =========================== */
function GenerateHeatDetailsTable(Heats) {
  try {
    ClearTable('tblHeatDetails');

    // Treat Heats (HeatData) as Dict: { [heatKey]: heatObj }
    const entries = Object.entries(Heats ?? {}); // [[key, heat], ...]

    // (Optional) sort by numeric keys to ensure stable order
    // entries.sort((a, b) => {
    //   const na = Number(a[0]), nb = Number(b[0]);
    //   if (!Number.isNaN(na) && !Number.isNaN(nb)) return na - nb;
    //   return String(a[0]).localeCompare(String(b[0]));
    // });

    for (let i = 0; i < entries.length; i++) {
      const [, heat] = entries[i]; // keep original signature: AddHeatRow(i, heat)
      AddHeatRow(i, heat);
    }

    const table = getEl('tblHeatDetails');
    if (table) {
      try { SetTableNavigation(table); }
      catch (navErr) { log.warn("SetTableNavigation failed for tblHeatDetails.", navErr); }
    }

    log.info("GenerateHeatDetailsTable completed.", { count: entries.length });
  } catch (err) {
    log.error("GenerateHeatDetailsTable failed.", err);
  }
}


/* ===========================
   AddHeatRow
   - UPDATED: EventList can be Dict
   =========================== */
function AddHeatRow(index, Heat) {
  try {
    const tblHeatDetails = getEl('tblHeatDetails', { required: true, desc: 'Heat details table' });
    if (!tblHeatDetails) return;

    const body = ensureTBody(tblHeatDetails);
    if (!body) {
      log.error("Cannot ensure TBODY for tblHeatDetails.");
      return;
    }

    const tblHeatDetailsRow = body.insertRow();
    tblHeatDetailsRow.id = "tblHeatDetailsRow" + index;

    const HeatCheckcell = tblHeatDetailsRow.insertCell();
    HeatCheckcell.classList.add('hide-on-print');
    HeatCheckcell.innerHTML = `<input type='Checkbox' id ='HeatCheckcell_${index}'>`;

    // -------- Robust EventID computation (Dict-aware) --------
    let EventID = -1;
    let heatId = "";
    try {
      heatId = Heat?.ID;

      // Normalize EventList to "entries": supports array OR dict
      const eventListRaw = Meetdteails?.EventDetails ?? {};
      const eventEntries = Array.isArray(eventListRaw)
        // Array -> [{ idx, key (string index), value }]
        ? eventListRaw.map((ev, i) => ({ idx: i, key: String(i), value: ev }))
        // Dict -> Object.entries -> [{ idx (iteration order), key, value }]
        : Object.entries(eventListRaw).map(([k, v], i) => ({ idx: i, key: k, value: v }));

      if (eventEntries.length === 0) {
        log.warn("EventList missing or empty; cannot compute EventID.", { Meetdteails });
      } else if (typeof heatId !== 'string' || !heatId.length) {
        log.warn("Heat.ID not a valid string; cannot compute EventID.", { Heat });
      } else {
        const part = splitBeforeLastUnderscore(heatId);
        if (!part.ok) {
          log.warn("Heat.ID has no valid underscore partition; using full ID fallback.", { heatId, lastIndex: part.lastIndex });
        } else {
          const keyPrefix = normalizeStr(part.prefix);

          // Match against primitive strings OR objects with ID/Id/id
          const match = eventEntries.find(({ value }) => {
            if (value == null) return false;
            if (typeof value === 'string') return normalizeStr(value) === keyPrefix;
            const candidate = (value?.ID ?? value?.Id ?? value?.id);
            return typeof candidate === 'string' && normalizeStr(candidate) === keyPrefix;
          });

          if (!match) {
            log.info("No matching event found for Heat prefix.", { prefix: keyPrefix, heatId, totalEvents: eventEntries.length });
          } else {
            EventID = match.idx; // keep ordinal semantics (0-based)
            log.debug("Matched EventID for Heat.", { EventID, prefix: keyPrefix, heatId, eventKey: match.key });
          }
        }
      }
    } catch (err) {
      EventID = -1;
      log.error("Failed to compute EventID.", err);
    }

    // Heat name cell
    const HeatNamecell = tblHeatDetailsRow.insertCell();
    HeatNamecell.classList.add('hide-on-print');
    HeatNamecell.innerHTML = `<input class='form-control' id ='HeatNamecell${index}'>`;

    const HeatNamecelltxt = getEl('HeatNamecell' + index);
    if (HeatNamecelltxt) HeatNamecelltxt.value = normalizeStr(Heat?.ID);

    // Controls cell & swimmers table
    const tblSwlist = document.createElement("TABLE");
    tblSwlist.id = "tblSwlist" + index;

    const controlsCell = tblHeatDetailsRow.insertCell();
    controlsCell.id = "controlsCell" + index;
    controlsCell.classList.add('hide-on-print');
    controlsCell.innerHTML =
      `<button onclick=AppendRow('${tblSwlist.id}','tblSwlistRow_')><i class='fa fa-fw fa-plus'></i></button>` +
      ` <button onclick=DeleteRows('${tblSwlist.id}','BoardCheckcell_','tblSwlistRow_')><i class='fa fa-fw fa-minus'></i></button>` +
      `<button onclick=UpdateSelectedData('Events')><i class="fa fa-fw fa-upload"></i></button>`;

    const header = tblSwlist.createTHead();
    let row = header.insertRow();
    let cell = row.insertCell();

    // Header text logic with EventID safety
    const isSameEvent = (lastEvent === EventID);
    const heatNumberText = (typeof Heat?.ID === 'string' && Heat.ID.includes('_'))
      ? Heat.ID.substring(Heat.ID.lastIndexOf('_') + 1)
      : "?";
    const eventOrdinal = (EventID >= 0) ? (EventID + 1) : "N/A";

    let headerText;
    let highlightNewEvent = false;

    if (isSameEvent && EventID >= 0) {
      headerText = `<b style='font-size: 12px'> Event: ${eventOrdinal} Heat : ${heatNumberText}</b>`;
    } else {
      lastEvent = EventID;
      const formatted = (typeof formatSwimmingEvent === 'function')
        ? formatSwimmingEvent(Heat.ID)
        : normalizeStr(Heat.ID);
      headerText = `<b style='font-size: 12px'>Event: ${eventOrdinal} ${formatted}</b>`;
      highlightNewEvent = true;
    }

    cell.innerHTML = headerText;
    if (highlightNewEvent) {
      cell.style.backgroundColor = "rgb(100, 100, 100)";
    }
    cell.colSpan = 7;

    // Create header row (if needed)
    row = header.insertRow();
    row.classList.add('hide-on-print'); // blank

    // (Optional) first two empty cells as in your original code
    cell = row.insertCell();

    // ---------------------- Start Time ----------------------
    cell = row.insertCell();
    {
      const inputId = `${heatId}StartTimeInput`;
      const label = document.createElement('label');
      label.htmlFor = inputId;
      label.textContent = 'Start';
      const br = document.createElement('br');
      const input = document.createElement('input');
      input.type = 'time';
      input.id = inputId;
      input.name = 'startTime';
      const val = normalizeTime(Heat?.HeatStartTime ?? '');
      if (val) input.value = val;
      cell.append(label, br, input);
    }

    // ---------------------- End Time ------------------------
    cell = row.insertCell();
    {
      const inputId = `${heatId}EndTimeInput`;
      const label = document.createElement('label');
      label.htmlFor = inputId;
      label.textContent = 'End';
      const br = document.createElement('br');
      const input = document.createElement('input');
      input.type = 'time';
      input.id = inputId;
      input.name = 'endTime';
      const val = normalizeTime(Heat?.HeatEndTime ?? '');
      if (val) input.value = val;
      cell.append(label, br, input);
    }

    // ---------------------- Status (select) -----------------
    cell = row.insertCell();
    {
      const label = document.createElement('label');
      label.textContent = 'Status';
      const br = document.createElement('br');
      const select = document.createElement('select');
      select.id = `${heatId}SelectHeatStatus`;
      select.classList.add('dropdown-cell');

      const statuses = Array.isArray(HeatStatus) ? HeatStatus : [];
      statuses.forEach((statusText, i) => {
        const option = document.createElement('option');
        option.value = String(i); // values are strings
        option.textContent = statusText;
        select.add(option);
      });

      // Set selected index from Heat.HeatStatus
      const idx = Number.parseInt(Heat?.HeatStatus, 10);
      const validIdx = Number.isInteger(idx) && idx >= 0 && idx < statuses.length;
      select.value = validIdx ? String(idx) : '0';

      cell.append(label, br, select);
    }

    // ---------------------- Notes ---------------------------
    cell = row.insertCell();
    // If you want Notes to span two columns, set colSpan here
    cell.colSpan = 3;
    {
      const inputId = `${heatId}HeatNotes`;
      const label = document.createElement('label');
      label.htmlFor = inputId;
      label.textContent = 'Notes';
      const br = document.createElement('br');
      const textarea = document.createElement('textarea');
      textarea.id = inputId;
      textarea.name = 'notes';
      textarea.rows = 2;
      textarea.value = String(Heat?.HeatNotes ?? '');
      cell.append(label, br, textarea);

      row = header.insertRow();
      let c = row.insertCell(); c.classList.add('hide-on-print'); // blank

      c = row.insertCell(); c.innerHTML = "<b>Line<b>";
      c = row.insertCell(); c.classList.add('hide-on-print'); c.innerHTML = "<b>SwimerID.<b>";
      c = row.insertCell(); c.innerHTML = "<b>Name<b>";
      c = row.insertCell(); c.innerHTML = "<b>School \\\\ Club.<b>";
      c = row.insertCell(); c.innerHTML = "<b>SwimStatus<b>";
      c = row.insertCell(); c.innerHTML = "<b>SwimTimeings<b>";
    }

    // Body cell with swimmer list
    const HeatSwimmerListcell = tblHeatDetailsRow.insertCell();
    HeatSwimmerListcell.id = 'SwimmersListcell' + index;
    HeatSwimmerListcell.appendChild(tblSwlist);

    // Boardinfo stays array (unchanged). If it ever becomes dict:
    // const boards = Array.isArray(Heat?.Boardinfo) ? Heat.Boardinfo : Object.values(Heat?.Boardinfo ?? {});
    const boards = Array.isArray(Heat?.Boardinfo) ? Heat.Boardinfo : [];
    for (let j = 0; j < boards.length; j++) {
      try {
        AddSwList(Heat, index, j);
      } catch (err) {
        log.error("AddSwList failed for row", { index, j, Heat }, err);
      }
    }

    const table = getEl(tblSwlist.id);
    if (table) {
      try { SetTableNavigation(table); }
      catch (navErr) { log.warn("SetTableNavigation failed.", { tableId: tblSwlist.id }, navErr); }
    }

    tblHeatDetailsRow.setAttribute('draggable', 'true');
    tblHeatDetailsRow.ondragstart = function () { startDrag() };
    tblHeatDetailsRow.ondragover = function () { dragover() };

    log.debug("AddHeatRow completed.", { index, HeatID: Heat?.ID, EventID });
  }
  catch (outerErr) {
    log.error("AddHeatRow fatal error.", { index, Heat }, outerErr);
  }
}



function AddSwList(Heat, index, j) {
  try {
    // Table element
    const tblSwlist = getEl("tblSwlist" + index, { required: true });
    if (!tblSwlist) return;

    // Source data for this row
    const board = Heat?.Boardinfo?.[j] ?? {};
    const SwimerID = board.SwimerID ?? '';
    let BoardID = board.BoardID ?? 0;   
    const BoardStartsFromZero = getEl("BoardStartsFromZero");
            if (!BoardStartsFromZero.checked) BoardID= BoardID +1
        // index-like code
         // prefer empty string over 0 for text areas
    const Swimerstatus = board.SwimStatus ?? 0;       // index-like code
    const SwimerName = normalizeStr(board.SwimerName ?? '');
    let Club = '';

    // Defensive Meet details lookup
    try {
      const clubObj = Meetdteails?.SwimmerDetails?.[SwimerName];
      Club = normalizeStr(clubObj?.Club ?? '');
    } catch (clubErr) {
      log.warn("Club lookup failed.", { SwimerName }, clubErr);
    }

    // Ensure tbody exists and insert row
    const body = ensureTBody(tblSwlist);
    if (!body) return;
    const tblSwlistRow = body.insertRow();
    tblSwlistRow.id=`tblSwlistRow_${index}_${j}`;
    tblSwlistRow.setAttribute('draggable', 'true');
    tblSwlistRow.addEventListener('dragstart', () => startDrag());
    tblSwlistRow.addEventListener('dragover', () => dragover());

    // ---------------- Checkbox cell ----------------
    let tblSwlistRowcell = tblSwlistRow.insertCell();
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.id = `BoardCheckcell_${index}_${j}`;
    tblSwlistRowcell.classList.add('hide-on-print');
    tblSwlistRowcell.appendChild(checkbox);



    // ---------------- Board (textarea) ----------------
    tblSwlistRowcell = tblSwlistRow.insertCell();
    const BoardIDInput = document.createElement('input');
    BoardIDInput.setAttribute("size", "3")
    BoardIDInput.setAttribute("maxlength", "3")
    BoardIDInput.inputMode = 'numeric';
    // BoardIDInput.classList.add('form-control');
    tblSwlistRowcell.id = `tblSwlist_BoardID_${index}_${j}`;  
    BoardIDInput.value= BoardID;
    tblSwlistRowcell.appendChild(BoardIDInput);

    // tblSwlistRowcell.innerHTML = '<b> '+ BoardID+'</b>';
    
    // ---------------- Swimmer ID (textarea) ----------------
    tblSwlistRowcell = tblSwlistRow.insertCell();
    tblSwlistRowcell.id = `tblSwlist_SwimerID_${index}_${j}`;
    const taId = document.createElement('textarea');
    taId.id = `txtarea_SwimerID_${index}_${j}`;
    taId.style.cssText = 'border:none; outline:none; background:transparent; width:100%; height:60px;';
    taId.value = String(SwimerID);
    tblSwlistRowcell.classList.add('hide-on-print');
    tblSwlistRowcell.appendChild(taId);


    // ---------------- Swimmer Name (textarea) ----------------
    tblSwlistRowcell = tblSwlistRow.insertCell();
    tblSwlistRowcell.id = `tblSwlist_SwimerName_${index}_${j}`;
    const taName = document.createElement('textarea');
    taName.id = `txtarea_SwimerName_${index}_${j}`;
    taName.style.cssText = 'border:none; outline:none; background:transparent; width:100%; height:60px;';
    taName.value = SwimerName;
    tblSwlistRowcell.appendChild(taName);

    // ---------------- Club (textarea) ----------------
    tblSwlistRowcell = tblSwlistRow.insertCell();
    tblSwlistRowcell.id = `tblSwlist_Club_${index}_${j}`;
    const taClub = document.createElement('textarea');
    taClub.style.cssText = 'width:100%; height:60px;';
    taClub.value = Club;
    tblSwlistRowcell.appendChild(taClub);

    // ---------------- Swim Status (select) ----------------
    tblSwlistRowcell = tblSwlistRow.insertCell();
    const select = document.createElement('select');
    select.id = `SwSwimStatus_${index}_${j}`;
    select.classList.add('dropdown-cell');

    const list = Array.isArray(DQMsg) ? DQMsg : [];
    list.forEach((dqText, i) => {
      const option = document.createElement('option');
      option.value = String(i);           // option values are strings in the DOM
      option.textContent = dqText ?? '';  // safe assignment
      select.add(option);
    });

    // Pre-select from data (index-like code)
    {
      const idx = Number.parseInt(Swimerstatus, 10);
      const validIdx = Number.isInteger(idx) && idx >= 0 && idx < select.options.length;
      const desiredValue = validIdx ? String(idx) : (select.options[0]?.value ?? '0');
      select.value = desiredValue;
      // If for any reason the value didn't match, use selectedIndex fallback
      if (select.value !== desiredValue) {
        select.selectedIndex = validIdx ? idx : 0;
      }
    }

    tblSwlistRowcell.appendChild(select);

    // ---------------- Swim Timings (input) ----------------
    tblSwlistRowcell = tblSwlistRow.insertCell();
    tblSwlistRowcell.id = `tblSwlist_SwimTimings_${index}_${j}`;

    const timingInput = document.createElement('input');
    timingInput.classList.add('form-control');
    BoardIDInput.setAttribute("size", "10")
    BoardIDInput.setAttribute("maxlength", "10")
    timingInput.id = `${tblSwlistRowcell.id}input`;

    let val = '';
    if (board.SwimTimings != '00:00.000') val = ConvertTime(board.SwimTimings); // treat zero time as empty

    timingInput.value = val ?? '';

    tblSwlistRowcell.appendChild(timingInput);

    // Timing validation hook
    const Timeinput = getEl(timingInput.id);
    if (Timeinput) {
      try { setTimeinputValidation(Timeinput); }
      catch (err) { log.warn("setTimeinputValidation failed for timing input.", err); }
    }

    log.debug("AddSwList row added.", { index, j, SwimerName, Club });
  } catch (err) {
    log.error("AddSwList failed.", { index, j, Heat }, err);
  }
}



function AddEventRow(index, Event) {
  try {
    const tblEvents = getEl('tblEvents', { required: true });
    if (!tblEvents) return;

    const eventID = (Event || "").split("_");
    const StrokeTyp = eventID[1] || "";
    const Distence  = eventID[0] || "";
    const Group     = eventID[2] || "";
    const Gender    = eventID[3] || "";

    let tblEventsBody = tblEvents.tBodies[0];
    if (!tblEventsBody) {
      tblEventsBody = document.createElement('tbody');
      tblEvents.appendChild(tblEventsBody);
    }

    const tblEventsRow = tblEventsBody.insertRow();
    tblEventsRow.id = "tblEventsRow" + index;
    tblEventsRow.setAttribute('draggable', 'true');
    tblEventsRow.ondragstart = function () { startDrag() };
    tblEventsRow.ondragover  = function () { dragover() };

    let EventCheckcell = tblEventsRow.insertCell();
    EventCheckcell.innerHTML = "<input type='Checkbox' id ='EventCheckcell" + index + "'>";
    const EventCheckcellEl = getEl('EventCheckcell' + index);
    if (EventCheckcellEl) {
      EventCheckcellEl.addEventListener("change", function () {
        if (EventCheckcellEl.checked === true) {
          EventsSlectedRows.push(EventCheckcellEl.id.replace("EventCheckcell", ""));
        } else {
          EventsSlectedRows.pop(EventCheckcellEl.id.replace("EventCheckcell", ""));
        }
      });
    }

    let Eventslnocell = tblEventsRow.insertCell();
    Eventslnocell.innerHTML = (index + 1);

    let EventGroupcell = tblEventsRow.insertCell();
    EventGroupcell.innerHTML = "<select id ='EventGroupcell" + index + "'>";
    const EventGroupcellSelector = getEl('EventGroupcell' + index);
    if (EventGroupcellSelector) {
      Availablegroups.forEach(GroupName => {
        const newGroup = document.createElement("option");
        newGroup.value = GroupName; newGroup.text = GroupName;
        EventGroupcellSelector.add(newGroup);
      });
      EventGroupcellSelector.value = Group;
    }

    let EventGendercell = tblEventsRow.insertCell();
    EventGendercell.innerHTML = "<select id ='EventGendercell" + index + "'>";
    const EventGendercellSelect = getEl('EventGendercell' + index);
    if (EventGendercellSelect) {
      genderArray.forEach(swGender => {
        const newGroup = document.createElement("option");
        newGroup.value = swGender; newGroup.text = swGender;
        EventGendercellSelect.add(newGroup);
      });
      EventGendercellSelect.value = Gender;
    }

    let EventStrokecell = tblEventsRow.insertCell();
    EventStrokecell.innerHTML = "<select id ='EventStrokecell" + index + "'>";
    const EventStrokecellSelect = getEl('EventStrokecell' + index);
    if (EventStrokecellSelect) {
      strokearray.forEach(stroke => {
        const newStroke = document.createElement("option");
        newStroke.value = stroke; newStroke.text = stroke;
        EventStrokecellSelect.add(newStroke);
      });
      EventStrokecellSelect.value = StrokeTyp;
    }

    let EventDistencecell = tblEventsRow.insertCell();
    EventDistencecell.innerHTML = "<select id ='EventDistencecell" + index + "'>";
    const EventDistencecellSelect = getEl('EventDistencecell' + index);
    if (EventDistencecellSelect) {
      distencearray.forEach(dis => {
        const newDis = document.createElement("option");
        newDis.value = dis; newDis.text = dis;
        EventDistencecellSelect.add(newDis);
      });
      EventDistencecellSelect.value = Distence;
    }

    log.debug("AddEventRow completed.", { index });
  } catch (err) {
    log.error("AddEventRow failed.", { index, Event }, err);
  }
}

function DeleteRows(TableName, idprefixChkbox, RowPrefix, SlectedRows = []) {
  try {
    const tbl = getEl(TableName, { required: true });
    if (!tbl) return;

    // Collect selected row indices
    for (let i = 1; i < tbl.rows.length; i++) {
      const tblindex = tbl.rows[i]?.id?.replace(RowPrefix, "");
      if (!tblindex && tbl.rows[i]) continue;
      const selectedchkbox = getEl(idprefixChkbox + tblindex);
      if (selectedchkbox?.checked) {
        SlectedRows.push(tblindex);
      }
    }

    let retryCount = 0;
    const MAX_RETRIES = 5;
    while (SlectedRows.length !== 0 && retryCount <= MAX_RETRIES) {
      retryCount++;
      for (let i = 0; i < SlectedRows.length; i++) {
        const rowEl = getEl(RowPrefix + SlectedRows[i]);
        if (!rowEl) continue;
        const rowIndex = rowEl.rowIndex;
        try {
          tbl.deleteRow(rowIndex);
          const idx = SlectedRows.indexOf(SlectedRows[i]);
          if (idx !== -1) SlectedRows.splice(idx, 1);
        } catch (delErr) {
          log.warn("Row deletion failed; will retry.", { TableName, rowIndex }, delErr);
        }
      }
    }

    log.info("DeleteRows completed.", { TableName });
  } catch (err) {
    log.error("DeleteRows fatal error.", { TableName }, err);
  }
}

function GenerateMeetTable(MeetName, MeetAddress, MeetDate, Boards) {
  try {
    const MeetHeaderName = getEl("MeetHeaderName");
    if (MeetHeaderName) {
      MeetHeaderName.innerHTML = " Heat List:" + normalizeStr(MeetName) + " " + normalizeStr(MeetDate);
    }

    const tblMeet = getEl('tblMeet', { required: true });
    if (!tblMeet) return;
    tblMeet.innerHTML = "";

    let row = tblMeet.insertRow();
    let cell = row.insertCell(); cell.innerHTML = "<b>Meet Name:</b> ";
    cell = row.insertCell(); cell.innerHTML = "<input class='form-control' id ='tblMeet_MeetName'>";
    const nameEl = getEl("tblMeet_MeetName"); if (nameEl) nameEl.value = normalizeStr(MeetName);

    row = tblMeet.insertRow();
    cell = row.insertCell(); cell.innerHTML = " <b>Meet Address:</b> ";
    cell = row.insertCell(); cell.innerHTML = "<input class='form-control' id ='tblMeet_MeetAddress'>";
    const addrEl = getEl("tblMeet_MeetAddress"); if (addrEl) addrEl.value = normalizeStr(MeetAddress);

    row = tblMeet.insertRow();
    cell = row.insertCell(); cell.innerHTML = " <b>Meet Date:</b> ";
    cell = row.insertCell(); cell.innerHTML = "<input class='form-control' type='date' id ='tblMeetDate'>";
    const dateEl = getEl("tblMeetDate"); if (dateEl) dateEl.value = normalizeStr(MeetDate);

    row = tblMeet.insertRow();
    cell = row.insertCell(); cell.innerHTML = " <b>Boards:</b> ";
    cell = row.insertCell(); cell.innerHTML = "<input class='form-control' id ='tblMeet_txtBoards'>";
    const boardsEl = getEl("tblMeet_txtBoards"); if (boardsEl) boardsEl.value = Boards;

    row = tblMeet.insertRow();
    cell = row.insertCell(); cell.innerHTML = " <b>No OF Events:</b> ";
    cell = row.insertCell(); cell.innerHTML = "<input class='form-control' id ='txt_NoOF_Events'>";

    row = tblMeet.insertRow();
    cell = row.insertCell(); cell.innerHTML = " <b>Board Starts from 0:</b> ";
    cell = row.insertCell(); cell.innerHTML = "<input type='Checkbox' id ='BoardStartsFromZero'>";

    log.info("GenerateMeetTable completed.", { MeetName, MeetDate, Boards });
  } catch (err) {
    log.error("GenerateMeetTable failed.", { MeetName, MeetAddress, MeetDate, Boards }, err);
  }
}


function GenerateGroupTable(GroupDetails) {
  try {
    ClearTable('tblGroups');

    // Convert dict to entries: [[key, groupObj], ...]
    const entries = Object.entries(GroupDetails ?? {});

    // Optional: sort by numeric keys if needed
    // entries.sort((a, b) => Number(a[0]) - Number(b[0]));

    for (let i = 0; i < entries.length; i++) {
      const [, group] = entries[i]; // keep index for AddGroupRow
      AddGroupRow(i, group);
    }

    const table = getEl('tblGroups');
    if (table) {
      try { SetTableNavigation(table); }
      catch (navErr) { log.warn("SetTableNavigation failed for tblGroups.", navErr); }
    }

    log.info("GenerateGroupTable completed.", { count: entries.length });
  }   catch (err) {
    log.error("GenerateGroupTable failed.", err);
  }
}


function GenerateEventTable(Events) {
  try {
    ClearTable('tblEvents');
    for (let i = 0; i < (Events?.length ?? 0); i++) {
      AddEventRow(i, Events[i]);
    }
    const table = getEl('tblEvents');
    if (table) {
      try { SetTableNavigation(table); }
      catch (navErr) { log.warn("SetTableNavigation failed for tblEvents.", navErr); }
    }
    log.info("GenerateEventTable completed.", { count: Events?.length ?? 0 });
  } catch (err) {
    log.error("GenerateEventTable failed.", err);
  }
}

function SelectAllRows(SelectAllCheckID, TblName, ChkBoxID) {
  try {
    const CheckStatus = !!getEl(SelectAllCheckID)?.checked;
    const tbltoselect = getEl(TblName, { required: true });
    if (!tbltoselect) return;

    for (let index = 0; index < tbltoselect.rows.length - 1; index++) {
      const chkbx = getEl(ChkBoxID + index);
      if (chkbx) chkbx.checked = CheckStatus;
    }

    log.info("SelectAllRows applied.", { SelectAllCheckID, TblName });
  } catch (err) {
    log.error("SelectAllRows failed.", { SelectAllCheckID, TblName, ChkBoxID }, err);
  }
}

function GenerateSwimmersTable(SwimmerDetails) {
  try {
    ClearTable('tblSwDetails');

    const tblSwimmers = getEl('tblSwDetails', { required: true });
    if (!tblSwimmers) return;

    const SwKeys = Object.keys(SwimmerDetails || {});
    for (let i = 0; i < SwKeys.length; i++) {
      const tblSwimmersRow = tblSwimmers.insertRow();
      tblSwimmersRow.setAttribute('draggable', 'true');
      tblSwimmersRow.ondragstart = function () { startDrag() };
      tblSwimmersRow.ondragover  = function () { dragover() };

      let SwimmersCheckboxcell = tblSwimmersRow.insertCell();
      SwimmersCheckboxcell.innerHTML = "<input type='Checkbox' id ='SwimmersCheckboxcell" + i + "'>";
      const chk = getEl('SwimmersCheckboxcell' + i);
      if (chk) {
        chk.checked = true;
        chk.addEventListener("change", function () {
          const Checkcellchkbox = getEl('SwimmersCheckboxcell' + i);
          const tblSwSelectedEvent = getEl("tblSwSelectedEvents" + i);
          if (Checkcellchkbox && tblSwSelectedEvent) {
            for (let j = 0; j < tblSwSelectedEvent.rows.length - 1; j++) {
              const avail = getEl("SwimmersAvailablecell" + i + "_" + j);
              if (avail) avail.checked = Checkcellchkbox.checked;
            }
          }
          if (Checkcellchkbox?.checked === true) {
            SwDetailsSlectedRows.push(Checkcellchkbox.id.replace("SwimmersCheckboxcell", ""));
          } else {
            SwDetailsSlectedRows.pop(Checkcellchkbox.id.replace("SwimmersCheckboxcell", ""));
          }
        });
      }

      tblSwimmersRow.id = "tblSwimmersRow" + i;

      let Swimmersslnocell = tblSwimmersRow.insertCell();
      Swimmersslnocell.innerHTML = (i + 1);

      let SwimmersNamecell = tblSwimmersRow.insertCell();
      SwimmersNamecell.innerHTML = "<input class='form-control' id ='SwimmersNamecell" + i + "'>";
      const nameEl = getEl("SwimmersNamecell" + i);
      if (nameEl) nameEl.value = SwKeys[i];
      


      let SwimmersDOBcell = tblSwimmersRow.insertCell();      
      SwimmersDOBcell.innerHTML = "<input class='form-control'  type='date' id ='SwimmersDOBcell" + i + "'>";
      const dobEl = getEl("SwimmersDOBcell" + i);
      if (dobEl) dobEl.value = SwKeys[i];
      

      let SwimmerGroupCell = tblSwimmersRow.insertCell();
      SwimmerGroupCell.innerHTML = "<input class='form-control' type='text' id ='SwimmerGroupCell" + i + "'>";
      const groupEl = getEl("SwimmerGroupCell" + i);
      if (groupEl) groupEl.value = SwimmerDetails[SwKeys[i]]?.Group ?? "";

      let SwimmerClubCell = tblSwimmersRow.insertCell();
      SwimmerClubCell.innerHTML = "<input class='form-control' type='text' id ='SwimmerClubCell" + i + "'>";
      const clubEl = getEl("SwimmerClubCell" + i);
      if (clubEl) clubEl.value = SwimmerDetails[SwKeys[i]]?.Club ?? "";

      let SwimmerClubShortCell = tblSwimmersRow.insertCell();
      SwimmerClubShortCell.innerHTML = "<input class='form-control' type='text' id ='SwimmerClubShortCell" + i + "'>";
      const clubhortEl = getEl("SwimmerClubShortCell" + i);
      if (clubhortEl) clubhortEl.value = SwimmerDetails[SwKeys[i]]?.Club ?? "";

      let SwimmerGenderCell = tblSwimmersRow.insertCell();
      SwimmerGenderCell.innerHTML = "<input class='form-control' type='text' id ='SwimmerGenderCell" + i + "'>";
      const genderEl = getEl("SwimmerGenderCell" + i);
      if (genderEl) genderEl.value = SwimmerDetails[SwKeys[i]]?.Gender ?? "";

      const tblSwSelectedEvents = document.createElement("TABLE");
      tblSwSelectedEvents.id = "tblSwSelectedEvents" + i;

      const body = ensureTBody(tblSwSelectedEvents);
      const header = tblSwSelectedEvents.createTHead();

      let row = header.insertRow();
      let cell = row.insertCell(); cell.innerHTML = "<b> Event Name. <b>";
      cell = row.insertCell(); cell.innerHTML = "<b> Best Timeings <b>";
      cell = row.insertCell(); cell.innerHTML = "<b> Available <b>";      
      cell = row.insertCell();
      cell.innerHTML = "<button onclick=AppendRow('" + tblSwSelectedEvents.id + "','tblSwimmersRow')><i class='fa fa-fw fa-plus'></i></button>";
      cell = row.insertCell();
      cell.innerHTML = "<button onclick=DeleteRows('" + tblSwSelectedEvents.id + "','tblSwSelectedEvents','tblSwimmersRow')><i class='fa fa-fw fa-minus'></i></button>";

      const SwimmersEventcell = tblSwimmersRow.insertCell();
      SwimmersEventcell.appendChild(tblSwSelectedEvents);

      const AvblEventsFromReg = SwimmerDetails[SwKeys[i]]?.Events?.length ?? 0;
      for (let j = 0; j < NumberofEventsperSw; j++) {
        const tblRow = body.insertRow();
        let SelCell = tblRow.insertCell();
        const selId = "SwimmersEventSelector" + i + "_" + j;
        SelCell.innerHTML = "<select id ='" + selId + "'>";
        const EventSelector = getEl(selId);
        if (Array.isArray(AvailableEvents) && AvailableEvents.length > 0 && EventSelector) {
          AvailableEvents.forEach(SwEvent => {
            const newSwEvent = document.createElement("option");
            newSwEvent.value = SwEvent;
            newSwEvent.text = SwEvent;
            EventSelector.add(newSwEvent);
          });
        }

        let timeCell = tblRow.insertCell();
        const timeId = "SwimmersEventBestTime" + i + "_" + j;
        timeCell.innerHTML = "<input class='form-control' id ='" + timeId + "'>";
        const Timeinput = getEl(timeId);
        if (Timeinput) {
          try { setTimeinputValidation(Timeinput, false); }
          catch (err) { log.warn("setTimeinputValidation failed for swimmer best time.", err); }
        }

        let availCell = tblRow.insertCell();
        const availId = "SwimmersAvailablecell" + i + "_" + j;
        availCell.innerHTML = "<input type='Checkbox' id ='" + availId + "'>";

        // Pre-fill from swimmer data if available
        const ev = SwimmerDetails[SwKeys[i]]?.["Events"]?.[j];
        if (ev !== undefined) {
          const evSel = getEl(selId);
          if (evSel) evSel.value = ev.EventName;

          const bt = getEl(timeId);
          if (bt) bt.value = ev.BestTimeings;

          const av = getEl(availId);
          if (av) av.checked = !!ev.Available;
        }
      }

      const table = getEl(tblSwSelectedEvents.id);
      if (table) {
        try { SetTableNavigation(table); }
        catch (navErr) { log.warn("SetTableNavigation failed for tblSwSelectedEvents.", navErr); }
      }
    }

    const table = getEl("tblSwDetails");
    if (table) {
      try { SetTableNavigation(table); }
      catch (navErr) { log.warn("SetTableNavigation failed for tblSwDetails (post).", navErr); }
    }

    log.info("GenerateSwimmersTable completed.", { count: SwKeys.length });
  } catch (err) {
    log.error("GenerateSwimmersTable failed.", err);
  }
}

// function GenerateHeatDetailsTable(Heats) {
//   try {
//     ClearTable('tblHeatDetails');
//     for (let i = 0; i < (Heats?.length ?? 0); i++) {
//       AddHeatRow(i, Heats[i]);
//     }
//     const table = getEl('tblHeatDetails');
//     if (table) {
//       try { SetTableNavigation(table); }
//       catch (navErr) { log.warn("SetTableNavigation failed for tblHeatDetails.", navErr); }
//     }
//     log.info("GenerateHeatDetailsTable completed.", { count: Heats?.length ?? 0 });
//   } catch (err) {
//        log.error("GenerateHeatDetailsTable failed.", err);
//   }
// }


// function GenerateHeatDetailsTable(Heats) {
//   try {
//     ClearTable('tblHeatDetails');

//     // Heats is now a dict: { [heatKey]: heatObj }
//     const entries = Object.entries(Heats ?? {}); // [[key, heat], ...]

//     // (Optional) If you want a stable numeric order by key, uncomment:
//     // entries.sort((a, b) => {
//     //   const na = Number(a[0]), nb = Number(b[0]);
//     //   if (!Number.isNaN(na) && !Number.isNaN(nb)) return na - nb;
//     //   return String(a[0]).localeCompare(String(b[0]));
//     // });

//     for (let i = 0; i < entries.length; i++) {
//       const [, heat] = entries[i]; // entries[i][1] is the heat object
//       AddHeatRow(i, heat);
//     }

//     const table = getEl('tblHeatDetails');
//     if (table) {
//       try { SetTableNavigation(table); }
//       catch (navErr) { log.warn("SetTableNavigation failed for tblHeatDetails.", navErr); }
//     }

//     log.info("GenerateHeatDetailsTable completed.", { count: entries.length });
//   } catch (err) {
//     log.error("GenerateHeatDetailsTable failed.", err);
//   }
// }