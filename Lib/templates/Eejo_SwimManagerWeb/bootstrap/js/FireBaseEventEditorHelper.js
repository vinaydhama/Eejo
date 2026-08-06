/* =========================
   FireBaseEventEditorHelper.js
   (Refactored with defensive checks, logs and error handlers)
   ========================= */

// ---------- Common helpers & logging ----------

const LOG_PREFIX = "[EventEditor]";
let eventEntries;

let AvailableSwimmerID  ;
let AvailableSwimmerNames ;
let AvailableSwimmerClubs ;

const log = {
  debug: (...args) => console.debug(LOG_PREFIX, ...args),
  info: (...args) => console.info(LOG_PREFIX, ...args),
  warn: (...args) => console.warn(LOG_PREFIX, ...args),
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

      case "UpdateHeats":
        //HeatList = GenerateUpdatedHeatList();
        HeatList = ReconcileHeatsBySwimmerNames();
        //function GenerateUpdatedHeatList(existingHeatList = [], swimmerDetails = [], availableEvents = [], boardCount = 1, BoardStartingNumber = true) {
        
        GenerateHeatDetailsTable(HeatList);
        break;

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
            const BoardStartingNumber = getEl("BoardStartingNumber");

            const NoofHeats = Math.ceil(SwimmersList.length / BoardCount);

            for (let i = 0; i < NoofHeats; i++) {
              const Boardinfo = [];
              const HeatDetails = { 'ID': eventname + "_" + (i + 1), 'Boardinfo': Boardinfo, 'HeatStatus': 0  };
              HeatList.push(HeatDetails);
            }

            let j = 0;
            for (let i = 0; i < SwimmersList.length; i++) {
              if (j === NoofHeats) j = 0;
              // const boardinfo = HeatList[Heatcounter + j].Boardinfo;
              let  LineID=   HeatList[Heatcounter + j].Boardinfo.length + Number(BoardStartingNumber.value)              
               HeatList[Heatcounter + j].Boardinfo.push({
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
              sortedArray[i].BoardID =Number(BoardStartingNumber.value)+  i;
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
            const dist = normalizeStr(getEl("EventDistencecell" + rowindex)?.value);
            const stroke = normalizeStr(getEl("EventStrokecell" + rowindex)?.value);
            const group = normalizeStr(getEl("EventGroupcell" + rowindex)?.value);
            const gender = normalizeStr(getEl("EventGendercell" + rowindex)?.value);
            const name = `${dist}_${stroke}_${group}_${gender}`;
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

// ...existing code...
function GenerateUpdatedHeatList() {
  try {
    // work on clone to avoid mutating global
    const meet = JSON.parse(JSON.stringify(MeetUpdatedData || {}));

    const boardsInputEl = getEl("tblMeet_txtBoards");
    const boardCount = toInt(boardsInputEl?.value, 1);
    const BoardCnt = boardCount > 0 ? boardCount : 1;
    const BoardStartingNumber = getEl("BoardStartingNumber");
    const boardStartNum = Number(BoardStartingNumber?.value) || 0;

    // helper to extract existing heats (prefer EventDetails from cloned meet)
    const getExistingHeatArrayLocal = (typeof getExistingHeatArray === 'function')
      ? getExistingHeatArray
      : function () {
          try {
            const ed = meet?.EventDetails;
            if (ed) {
              if (Array.isArray(ed)) {
                return ed.flatMap(ev => {
                  if (!ev) return [];
                  const hl = ev.HeatList;
                  if (Array.isArray(hl)) return hl;
                  if (hl && typeof hl === 'object') return Object.values(hl);
                  if (ev.ID && ev.Boardinfo) return [ev];
                  return [];
                });
              }
              return Object.values(ed).flatMap(ev => {
                if (!ev) return [];
                const hl = ev.HeatList;
                if (Array.isArray(hl)) return hl;
                if (hl && typeof hl === 'object') return Object.values(hl);
                if (ev.ID && ev.Boardinfo) return [ev];
                return [];
              });
            }
            if (Array.isArray(meet?.HeatList)) return meet.HeatList;
            if (meet?.HeatList && typeof meet.HeatList === 'object') return Object.values(meet.HeatList);
            return [];
          } catch (err) {
            log.error("getExistingHeatArrayLocal failed.", err);
            return [];
          }
        };

    // existingHeatList will be resolved further down (avoid duplicate declaration)
    // (deep-clone of source is done later to ensure a single declaration)

    // build swimmer list from UI OR fallback to cloned meet.SwimmerDetails
    const swimmerDetails = [];
    const tblSwimmers = getEl('tblSwDetails', { required: false });
    if (tblSwimmers) {
      for (let i = 1; i < tblSwimmers.rows.length; i++) {
        try {
          const rowindex = (tblSwimmers.rows[i].id || "").replace("tblSwimmersRow", "");
          const tblSwSelectedEvents = getEl('tblSwSelectedEvents' + rowindex);
          if (!tblSwSelectedEvents) continue;
          for (let j = 0; j < tblSwSelectedEvents.rows.length - 1; j++) {
            const availId = "SwimmersAvailablecell" + rowindex + "_" + j;
            if (!getEl(availId)?.checked) continue;
            const name = normalizeStr(getEl("SwimmersNamecell" + rowindex)?.value);
            const ev = getEl("SwimmersEventSelector" + rowindex + "_" + j);
            if (name && ev) swimmerDetails.push({ SwName: name, Swevents: ev.value });
          }
        } catch (e) { /* ignore */ }
      }
    } else if (meet?.SwimmerDetails) {
      try {
        const sd = meet.SwimmerDetails;
        if (Array.isArray(sd)) {
          sd.forEach(s => {
            if (!s) return;
            const name = s?.Name || s?.SwName || s?.SwimerName || "";
            (s?.Events || []).forEach(ev => swimmerDetails.push({ SwName: String(name), Swevents: ev?.EventName || ev?.Event || "" }));
          });
        } else {
          Object.keys(sd || {}).forEach(k => {
            const s = sd[k];
            (s?.Events || []).forEach(ev => swimmerDetails.push({ SwName: String(k), Swevents: ev?.EventName || ev?.Event || "" }));
          });
        }
      } catch (e) { /* ignore */ }
    }

    const availableEvents = Array.isArray(AvailableEvents) && AvailableEvents.length
      ? AvailableEvents
      : (Array.isArray(meet?.EventList) ? meet.EventList : Object.keys(meet?.EventList || {}));

    // defensive helpers
    const ensureArray = (v) => Array.isArray(v) ? v : (v = [], v);
    const safePush = (arr, val, ctx) => {
      if (!Array.isArray(arr)) {
        log.warn("safePush: expected array was not an array; replacing with new array.", { ctx });
        arr = [];
      }
      arr.push(val);
      return arr;
    };

    // ensure existingHeatList is an array
    let existingHeatListRaw = getExistingHeatArrayLocal && typeof getExistingHeatArrayLocal === 'function'
      ? getExistingHeatArrayLocal() : (Array.isArray(meet?.HeatList) ? meet.HeatList : (meet?.HeatList ? Object.values(meet.HeatList) : []));
    const existingHeatList = Array.isArray(existingHeatListRaw) ? JSON.parse(JSON.stringify(existingHeatListRaw)) : JSON.parse(JSON.stringify(Object.values(existingHeatListRaw || {})));

    // swimmersByEvent build (ensure arrays)
    const swimmersByEvent = {};
    (swimmerDetails || []).forEach(s => {
      const en = String(s?.Swevents ?? "");
      if (!Array.isArray(swimmersByEvent[en])) swimmersByEvent[en] = [];
      swimmersByEvent[en].push(String(s?.SwName ?? ""));
    });

    const mergedHeats = [];

    for (let ei = 0; ei < (availableEvents || []).length; ei++) {
      const eventname = availableEvents[ei];
      const newSwimmerIds = Array.from(new Set(swimmersByEvent[eventname] || []));

      // gather oldHeats (deep-cloned)
      let oldHeats = [];
      const evEntry = meet?.EventDetails?.[eventname];
      if (evEntry) {
        try {
          if (Array.isArray(evEntry.HeatList)) oldHeats = JSON.parse(JSON.stringify(evEntry.HeatList));
          else if (evEntry.HeatList && typeof evEntry.HeatList === 'object') oldHeats = JSON.parse(JSON.stringify(Object.values(evEntry.HeatList)));
          else if (evEntry.ID && evEntry.Boardinfo) oldHeats = [JSON.parse(JSON.stringify(evEntry))];
          else if (Array.isArray(evEntry)) oldHeats = JSON.parse(JSON.stringify(evEntry)).flatMap(x => Array.isArray(x?.Boardinfo) ? [x] : []);
        } catch (e) {
          log.warn("Failed to parse evEntry; falling back to scan.", { eventname, err: e });
          oldHeats = [];
        }
      }

      if (!Array.isArray(oldHeats) || oldHeats.length === 0) {
        oldHeats = (existingHeatList || []).filter(h => String(h?.ID || "").startsWith(eventname + "_"))
          .map(h => JSON.parse(JSON.stringify(h || {})));
      }

      // Ensure Boardinfo arrays exist on every heat
      oldHeats.forEach(h => {
        if (!Array.isArray(h.Boardinfo)) h.Boardinfo = [];
      });

      // map existing positions
      //      const existingPositions = {};
      //      oldHeats.forEach((h, hi) => {
      //        (h.Boardinfo || []).forEach((b, bi) => {
      //          const sid = String((b?.SwimerID ?? b?.SwimerName ?? "")).trim();
      //          if (sid) existingPositions[sid] = { hi, bi };
      //        });
      //      });
      // normalize names for robust comparison (trim/case-insensitive)
      const existingPositions = {};
      oldHeats.forEach((h, hi) => {
        (h.Boardinfo || []).forEach((b, bi) => {
          const raw = b?.SwimerID ?? b?.SwimerName ?? "";
          const sid = typeof normalizeStr === 'function' ? normalizeStr(String(raw)) : String(raw).trim();
          if (sid) existingPositions[sid] = { hi, bi, raw };
        });
      });

      log.debug("Reconcile: existingPositions keys", Object.keys(existingPositions).slice(0,20));
 
      // mark removed swimmers
   
      // ensure desired set is normalized the same way
      const desiredSet = new Set((newSwimmerIds || []).map(n => typeof normalizeStr === 'function' ? normalizeStr(String(n)) : String(n).trim()));
      Object.keys(existingPositions).forEach(nsid => {
        if (!desiredSet.has(nsid)) {
          const pos = existingPositions[nsid];
          const heat = oldHeats[pos.hi];
          if (heat && Array.isArray(heat.Boardinfo) && heat.Boardinfo[pos.bi]) {
            const old = heat.Boardinfo[pos.bi].SwimStatus;
            if (old !== 1) {
              heat.Boardinfo[pos.bi].SwimStatus = 1;
              log.info("Reconcile: marked swimmer removed (SwimStatus=1)", { event: eventname, heat: heat.ID, slot: pos, swimmer_normalized: nsid, swimmer_raw: pos.raw });
            } else {
              log.debug("Reconcile: swimmer already marked removed", { swimmer: nsid, heat: heat.ID });
            }
          }
        }
      });
      // helper: find truly empty slot
      function findAvailableSlot() {
        for (let hi = 0; hi < oldHeats.length; hi++) {
          const arr = ensureArray(oldHeats[hi].Boardinfo);
          for (let bi = 0; bi < arr.length; bi++) {
            const b = arr[bi];
            const idEmpty = (((b?.SwimerID ?? "") + (b?.SwimerName ?? "")).trim().length === 0);
            if (idEmpty) return { hi, bi };
          }
          if (arr.length < BoardCnt) return { hi, bi: arr.length };
        }
        return null;
      }

      // compute max index
      let maxIndex = 0;
      oldHeats.forEach(h => {
        try {
          const parts = String(h.ID || "").split("_");
          const n = parseInt(parts[parts.length - 1], 10);
          if (Number.isFinite(n) && n > maxIndex) maxIndex = n;
        } catch (e) { /* ignore */ }
      });

      const placed = new Set(Object.keys(existingPositions).filter(id => newSwimmerIds.includes(id)));
      for (const sid of newSwimmerIds) {
        if (placed.has(sid)) continue;
        const slot = findAvailableSlot();
        if (slot) {
          const h = oldHeats[slot.hi];
          if (!Array.isArray(h.Boardinfo)) h.Boardinfo = [];
          while (h.Boardinfo.length < slot.bi) {
            h.Boardinfo.push({ BoardID: (h.Boardinfo || []).length + boardStartNum, BoardStatus: 0, SwimerID: "", SwimerName: "", SwimStatus: 0, SwimTimings: 0 });
          }
          const existing = h.Boardinfo[slot.bi] || {};
          const wasEmpty = (((existing?.SwimerID ?? "") + (existing?.SwimerName ?? "")).trim().length === 0);
          if (wasEmpty) {
            h.Boardinfo[slot.bi] = {
              BoardID: (existing?.BoardID ?? (slot.bi + boardStartNum)),
              BoardStatus: 0,
              SwimStatus: 0,
              SwimTimings: 0,
              SwimerID: sid,
              SwimerName: sid
            };
            placed.add(sid);
          } else {
            // cannot overwrite -- try next
            continue;
          }
        } else {
        
 // append new heat: create only the single occupied board slot initially
          maxIndex++;
          const newHeatID = `${eventname}_${maxIndex}`;
          const newHeat = { ID: newHeatID, Boardinfo: [], HeatStatus: 0 };
          // create only one occupied slot to avoid extra empty boards
          newHeat.Boardinfo.push({
            BoardID: boardStartNum,
            BoardStatus: 0,
            SwimStatus: 0,
            SwimTimings: 0,
            SwimerID: sid,
            SwimerName: sid
          });
          oldHeats.push(newHeat);
          placed.add(sid);
        }
       
      }

      // ensure BoardID exists but DO NOT renumber existing BoardIDs
      oldHeats.forEach(h => {
        (h.Boardinfo || []).forEach((b, idx) => {
          if (b?.BoardID === undefined || b.BoardID === null) b.BoardID = idx + boardStartNum;
        });
      });

      // finally push into mergedHeats (ensure mergedHeats exists)
      if (!Array.isArray(mergedHeats)) mergedHeats = [];
      mergedHeats.push(...oldHeats);
    }

    // include heats belonging to events not in availableEvents
    const remaining = (existingHeatList || []).filter(h => {
      const en = String(h?.ID || "").split("_")[0];
      return !(availableEvents || []).includes(en);
    }).map(h => ({ ...h, Boardinfo: Array.isArray(h.Boardinfo) ? h.Boardinfo.map(b => ({ ...b })) : [] }));

    mergedHeats.push(...remaining);


const result = {};
    for (let i = 0; i < mergedHeats.length; i++) {
      const heat = mergedHeats[i] || {};
      const key = (heat.ID && String(heat.ID).length) ? String(heat.ID) : `heat_${i}`;
      if (!Object.prototype.hasOwnProperty.call(result, key)) {
        // first occurrence wins
        result[key] = heat;
      } else {
        // duplicate ID: merge board entries (avoid creating multiple suffixed keys)
        try {
          const existing = result[key];
          existing.Boardinfo = Array.isArray(existing.Boardinfo) ? existing.Boardinfo : [];
          const newBoards = Array.isArray(heat.Boardinfo) ? heat.Boardinfo : [];
          newBoards.forEach(nb => {
            const exists = existing.Boardinfo.some(b =>
              String(b?.SwimerID ?? '') === String(nb?.SwimerID ?? '') &&
              (b?.BoardID === nb?.BoardID)
            );
            if (!exists) existing.Boardinfo.push(nb);
          });
        } catch (mergeErr) {
          log.warn("merge duplicate heat failed", { key, idx: i }, mergeErr);
        }
      }
    }
    return result;
  } catch (err) {
    log.error("[GenerateUpdatedHeatList] error", err);

    // Safe fallback: build a deep-copied heat dict without referencing local variables
    const fallback = {};
    try {
      // Prefer helper if available, otherwise read from MeetUpdatedData
      const src = (typeof getExistingHeatArrayLocal === 'function')
        ? (getExistingHeatArrayLocal() || [])
        : (Array.isArray(MeetUpdatedData?.HeatList)
            ? MeetUpdatedData.HeatList
            : (MeetUpdatedData?.HeatList ? Object.values(MeetUpdatedData.HeatList) : []));

      (src || []).forEach((h, i) => {
        try {
          fallback[h?.ID ?? `heat_${i}`] = JSON.parse(JSON.stringify(h || {}));
        } catch (deepErr) {
          // if an individual heat can't be cloned, still include a minimal entry
          fallback[h?.ID ?? `heat_${i}`] = { ID: h?.ID ?? `heat_${i}`, Boardinfo: Array.isArray(h?.Boardinfo) ? h.Boardinfo.map(b => ({ ...b })) : [] };
        }
      });
    } catch (fallbackErr) {
      log.error("[GenerateUpdatedHeatList] fallback build failed", fallbackErr);
    }

    return fallback;
  }
}

// ...existing code...
function ReconcileHeatsBySwimmerNames() {
  try {
    // Deep clone meet to avoid accidental mutation
    const meet = JSON.parse(JSON.stringify(MeetUpdatedData || {}));

    // Board constraints: prefer meet.Boards, fallback to UI control, else 1
    const uiBoards = toInt(getEl("tblMeet_txtBoards")?.value, 0);
    const BoardCnt = Number(meet?.Boards ?? uiBoards) || Math.max(1, uiBoards || 1);

    // Starting board number from UI (fallback 0)
    const boardStartNum = Number(getEl("BoardStartingNumber")?.value) || 0;

    // Build desired swimmer names by event from UI if available, else from meet.SwimmerDetails
    const swimmersByEvent = {};
    const tblSwimmers = getEl('tblSwDetails', { required: false });
    if (tblSwimmers) {
      for (let i = 1; i < tblSwimmers.rows.length; i++) {
        try {
          const rowindex = (tblSwimmers.rows[i].id || "").replace("tblSwimmersRow", "");
          const tblSwSelectedEvents = getEl('tblSwSelectedEvents' + rowindex);
          if (!tblSwSelectedEvents) continue;
          for (let j = 0; j < tblSwSelectedEvents.rows.length - 1; j++) {
            const availId = "SwimmersAvailablecell" + rowindex + "_" + j;
            if (!getEl(availId)?.checked) continue;
            const name = normalizeStr(getEl("SwimmersNamecell" + rowindex)?.value);
            const ev = getEl("SwimmersEventSelector" + rowindex + "_" + j);
            if (name && ev) {
              const en = String(ev.value ?? "");
              swimmersByEvent[en] = swimmersByEvent[en] || [];
              swimmersByEvent[en].push(name);
            }
          }
        } catch (e) { /* ignore row parse errors */ }
      }
    } else if (meet?.SwimmerDetails) {
      try {
        const sd = meet.SwimmerDetails;
        if (Array.isArray(sd)) {
          sd.forEach(s => {
            if (!s) return;
            const name = s?.Name || s?.SwName || s?.SwimerName || "";
            (s?.Events || []).forEach(ev => {
              const en = ev?.EventName || ev?.Event || "";
              if (!en) return;
              swimmersByEvent[en] = swimmersByEvent[en] || [];
              swimmersByEvent[en].push(String(name));
            });
          });
        } else {
          Object.keys(sd || {}).forEach(k => {
            const s = sd[k];
            (s?.Events || []).forEach(ev => {
              const en = ev?.EventName || ev?.Event || "";
              if (!en) return;
              swimmersByEvent[en] = swimmersByEvent[en] || [];
              swimmersByEvent[en].push(String(k));
            });
          });
        }
      } catch (e) { /* ignore */ }
    }

    // Determine available events (preserve order from AvailableEvents if present)
    const availableEvents = Array.isArray(AvailableEvents) && AvailableEvents.length > 0
      ? AvailableEvents.slice()
      : (Array.isArray(meet?.EventList) ? meet.EventList.slice() : Object.keys(meet?.EventList || {}));

    // Get existing heats as array (tolerant shapes + conversion to internal Boardinfo)
    const getExistingRaw = (function () {
      // normalize a heat object to internal expected shape { ID, Boardinfo: [...] , HeatStatus, ... }
      const normalizeHeat = (h) => {
        if (!h || typeof h !== 'object') return null;
        // many feeds use "BoardList" and "HeatID" names -> map them
        const boardList = Array.isArray(h.Boardinfo) ? h.Boardinfo : (Array.isArray(h.BoardList) ? h.BoardList : []);
        const id = h.ID ?? h.HeatID ?? h.heatID ?? h.HeatId ?? null;
        const out = { ...h };
        out.ID = id ?? out.ID ?? out.HeatID ?? out.HeatId ?? '';
        out.Boardinfo = Array.isArray(boardList) ? boardList.map(b => ({ ...b })) : [];
        // keep other heat-level fields as-is (HeatStatus, HeatStartTime etc.)
        return out;
      };

      try {
        let res = [];
        // support multiple possible top-level keys
        const ed = meet?.EventDetails ?? meet?.eventdetails ?? meet?.eventDetails ?? null;

        if (ed && (Array.isArray(ed) ? ed.length > 0 : Object.keys(ed || {}).length > 0)) {
          if (Array.isArray(ed)) {
            res = ed.flatMap(ev => {
              if (!ev) return [];
              // ev.HeatList may be array or dict; convert values to normalized heats
              const hl = ev.HeatList;
              if (Array.isArray(hl)) return hl.map(normalizeHeat).filter(Boolean);
              if (hl && typeof hl === 'object') return Object.values(hl).map(normalizeHeat).filter(Boolean);
              // sometimes event node is actually a heat object
              if (ev.ID || ev.HeatID) return [normalizeHeat(ev)].filter(Boolean);
              return [];
            });
          } else {
            res = Object.values(ed).flatMap(ev => {
              if (!ev) return [];
              const hl = ev.HeatList;
              if (Array.isArray(hl)) return hl.map(normalizeHeat).filter(Boolean);
              if (hl && typeof hl === 'object') return Object.values(hl).map(normalizeHeat).filter(Boolean);
              if (ev.ID || ev.HeatID) return [normalizeHeat(ev)].filter(Boolean);
              return [];
            });
          }
        } else if (ed) {
          // EventDetails exists but empty -> scan meet for heat-like objects
          log.warn("EventDetails present but empty. Scanning meet object for heat-like entries.");
          const found = [];
          const scan = (obj) => {
            if (!obj || typeof obj !== 'object') return;
            if (Array.isArray(obj)) {
              obj.forEach(scan);
              return;
            }
            // heat object may have BoardList/Boardinfo + HeatID/ID
            if ((Array.isArray(obj.BoardList) || Array.isArray(obj.Boardinfo)) && (obj.HeatID || obj.ID)) {
              const nh = normalizeHeat(obj);
              if (nh) found.push(nh);
            }
            Object.values(obj).forEach(scan);
          };
          scan(meet);
          if (found.length) {
            log.info("Found heat-like objects while scanning meet.", { count: found.length });
            return found;
          }
        }

        // fallbacks: meet.HeatList (array or dict)
        if ((!res || res.length === 0) && Array.isArray(meet?.HeatList)) res = meet.HeatList.map(normalizeHeat).filter(Boolean);
        if ((!res || res.length === 0) && meet?.HeatList && typeof meet.HeatList === 'object') res = Object.values(meet.HeatList).map(normalizeHeat).filter(Boolean);

        // Additional fallbacks: original global MeetUpdatedData and any global HeatList
        if ((!res || res.length === 0) && Array.isArray(MeetUpdatedData?.HeatList)) res = MeetUpdatedData.HeatList.map(normalizeHeat).filter(Boolean);
        if ((!res || res.length === 0) && MeetUpdatedData?.HeatList && typeof MeetUpdatedData.HeatList === 'object') res = Object.values(MeetUpdatedData.HeatList).map(normalizeHeat).filter(Boolean);
        if ((!res || res.length === 0) && Array.isArray(window?.HeatList)) res = window.HeatList.map(normalizeHeat).filter(Boolean);
        if ((!res || res.length === 0) && window?.HeatList && typeof window.HeatList === 'object') res = Object.values(window.HeatList).map(normalizeHeat).filter(Boolean);

        if (!res || res.length === 0) {
          log.debug("Reconcile: no heats found in EventDetails/HeatList fallbacks; returning empty array.");
          return [];
        }
        return res;
      } catch (err) {
        log.warn("Reconcile: failed to read existing heatlist, returning empty array.", err);
        return [];
      }
    })();
    const existingHeatList = JSON.parse(JSON.stringify(Array.isArray(getExistingRaw) ? getExistingRaw : Array.from(getExistingRaw || [])));

    // Helper: safe ensure Boardinfo array exists
    existingHeatList.forEach(h => { if (!Array.isArray(h.Boardinfo)) h.Boardinfo = Array.isArray(h?.Boardinfo) ? h.Boardinfo : []; });

    // Work per event
    const mergedHeats = [];

    for (let ei = 0; ei < (availableEvents || []).length; ei++) {
      const eventname = availableEvents[ei];
      const desiredNames = Array.from(new Set((swimmersByEvent[eventname] || []).map(n => String(n)))); // unique

      // Collect oldHeats for this event (clone)
      let oldHeats = existingHeatList.filter(h => String(h?.ID || "").startsWith(eventname + "_")).map(h => JSON.parse(JSON.stringify(h || {})));

      // If none found but meet.EventDetails holds HeatList, prefer that
      if ((!oldHeats || oldHeats.length === 0) && meet?.EventDetails?.[eventname]) {
        const ev = meet.EventDetails[eventname];
        if (Array.isArray(ev?.HeatList)) oldHeats = JSON.parse(JSON.stringify(ev.HeatList));
        else if (ev?.ID && ev?.Boardinfo) oldHeats = [JSON.parse(JSON.stringify(ev))];
      }

      // Ensure Boardinfo arrays
      oldHeats.forEach(h => { if (!Array.isArray(h.Boardinfo)) h.Boardinfo = []; });

      // Map existing positions (name -> {hi, bi})
      const existingPositions = {};
      oldHeats.forEach((h, hi) => {
        (h.Boardinfo || []).forEach((b, bi) => {
          const sid = String((b?.SwimerID ?? b?.SwimerName ?? "")).trim();
          if (sid) existingPositions[sid] = { hi, bi };
        });
      });

      // Mark removed swimmers (present before but not desired now) => SwimStatus = 1
      Object.keys(existingPositions).forEach(sid => {
        if (!desiredNames.includes(sid)) {
          const pos = existingPositions[sid];
          const heat = oldHeats[pos.hi];
          if (heat && Array.isArray(heat.Boardinfo) && heat.Boardinfo[pos.bi]) {
            // Only change SwimStatus, nothing else
            const old = heat.Boardinfo[pos.bi].SwimStatus;
            if (old !== 1) {
              heat.Boardinfo[pos.bi].SwimStatus = 1;
              log.info("Reconcile: marked swimmer removed (SwimStatus=1)", { event: eventname, heat: heat.ID, slot: pos, swimmer: sid });
            }
          }
        }
      });

      // Helper to find slot to insert missing name:
      // Prefer slots where SwimStatus === 1 (placeholder), then truly empty slots (no name), then if a heat has < BoardCnt, use that appended position.
      function findSlotForInsert() {
        // 1) placeholder slots (SwimStatus === 1)
        for (let hi = 0; hi < oldHeats.length; hi++) {
          const arr = oldHeats[hi].Boardinfo || [];
          for (let bi = 0; bi < arr.length; bi++) {
            const b = arr[bi];
            const isPlaceholder = (Number(b?.SwimStatus) === 1);
            if (isPlaceholder) return { hi, bi, replacePlaceholder: true };
          }
        }
        // 2) empty name slots
        for (let hi = 0; hi < oldHeats.length; hi++) {
          const arr = oldHeats[hi].Boardinfo || [];
          for (let bi = 0; bi < arr.length; bi++) {
            const b = arr[bi];
            const idEmpty = (((b?.SwimerID ?? "") + (b?.SwimerName ?? "")).trim().length === 0);
            if (idEmpty) return { hi, bi, replacePlaceholder: false };
          }
        }
        // 3) append to heat with room (< BoardCnt)
        for (let hi = 0; hi < oldHeats.length; hi++) {
          const arr = oldHeats[hi].Boardinfo || [];
          if (arr.length < BoardCnt) return { hi, bi: arr.length, replacePlaceholder: false };
        }
        // none found
        return null;
      }

      // Place missing swimmers (do not overwrite non-placeholder slots)
      const presentSet = new Set(Object.keys(existingPositions));
      for (const name of desiredNames) {
        if (presentSet.has(name)) continue; // already present, leave untouched
        // find slot
        const slot = findSlotForInsert();
        if (slot) {
          const h = oldHeats[slot.hi];
          if (!Array.isArray(h.Boardinfo)) h.Boardinfo = [];
          // Ensure enough length for slot.bi when appending
          while (h.Boardinfo.length < slot.bi) {
            h.Boardinfo.push({
              BoardID: h.Boardinfo.length + boardStartNum,
              BoardStatus: 0,
              SwimStatus: 0,
              SwimTimings: 0,
              SwimerID: "",
              SwimerName: ""
            });
          }
          const existing = h.Boardinfo[slot.bi] || {};
          const currentlyEmpty = (((existing?.SwimerID ?? "") + (existing?.SwimerName ?? "")).trim().length === 0) || Number(existing?.SwimStatus) === 1;
          if (currentlyEmpty) {
            // preserve existing BoardID if any
            h.Boardinfo[slot.bi] = {
              BoardID: (existing?.BoardID ?? (slot.bi + boardStartNum)),
              BoardStatus: existing?.BoardStatus ?? 0,
              SwimStatus: 0,
              SwimTimings: existing?.SwimTimings ?? 0,
              SwimerID: name,
              SwimerName: name
            };
            log.info("Reconcile: inserted missing swimmer into existing heat slot", { event: eventname, heat: h.ID, slot: { hi: slot.hi, bi: slot.bi }, swimmer: name });
            presentSet.add(name);
          } else {
            // shouldn't happen due to find logic, but guard
            log.warn("Reconcile: attempted to insert into non-empty non-placeholder slot; skipping", { event: eventname, heat: h.ID, slot: slot, swimmer: name });
          }
        } else {
          // create new heat(s) as needed
          // determine next max suffix
          let maxIndex = 0;
          oldHeats.forEach(h => {
            try {
              const parts = String(h.ID || "").split("_");
              const n = parseInt(parts[parts.length - 1], 10);
              if (Number.isFinite(n) && n > maxIndex) maxIndex = n;
            } catch (e) { /* ignore */ }
          });
          maxIndex++;
          const newHeatID = `${eventname}_${maxIndex}`;
    
 // build occupied slot with strict defaults and optional ClubName from meet data
          const swimmerClub = (meet?.SwimmerDetails && (meet.SwimmerDetails[name]?.Club || meet.SwimmerDetails[name]?.ClubName)) || "";
          const newHeat = { ID: newHeatID, Boardinfo: [], HeatStatus: 0 };
          newHeat.Boardinfo.push({
            BoardID: boardStartNum,
            BoardStatus: 0,
            SwimStatus: 0,
            SwimTimings: 0,
            ClubName: swimmerClub,
            SwimerID: name,
            SwimerName: name
          });
          oldHeats.push(newHeat);
           log.info("Reconcile: created new heat (single slot) and placed swimmer", { event: eventname, newHeatID, swimmer: name });
           presentSet.add(name);
        }
      }

      // Ensure BoardID exists for entries that lacked one (do not renumber existing BoardIDs)
      oldHeats.forEach(h => {
        (h.Boardinfo || []).forEach((b, idx) => {
          if (b?.BoardID === undefined || b.BoardID === null) b.BoardID = idx + boardStartNum;
        });
      });

      // Append processed event heats
      mergedHeats.push(...oldHeats);
    }

    // Also include heats for events not in availableEvents (leave unchanged)
    const remaining = existingHeatList.filter(h => {
      const en = String(h?.ID || "").split("_")[0];
      return !(availableEvents || []).includes(en);
    }).map(h => JSON.parse(JSON.stringify(h || {})));

    mergedHeats.push(...remaining);
 const result = {};
    for (let i = 0; i < mergedHeats.length; i++) {
      const heat = mergedHeats[i] || {};
      const key = (heat.ID && String(heat.ID).length) ? String(heat.ID) : `heat_${i}`;
      if (!Object.prototype.hasOwnProperty.call(result, key)) {
        result[key] = heat;
      } else {
        // Duplicate ID encountered: merge Boardinfo entries to avoid repeated heats
        try {
          const existing = result[key];
          existing.Boardinfo = Array.isArray(existing.Boardinfo) ? existing.Boardinfo : [];
          const newBoards = Array.isArray(heat.Boardinfo) ? heat.Boardinfo : [];         

          const isEmptyBoard = (b) => !String((b?.SwimerID ?? b?.SwimerName ?? "")).trim();
          newBoards.forEach(nb => {
            if (isEmptyBoard(nb)) return; // don't add empty placeholders
            // avoid duplicate by BoardID or SwimerName
            const dup = existing.Boardinfo.some(b => (b?.BoardID !== undefined && nb?.BoardID !== undefined && b.BoardID === nb.BoardID)
              || (String((b?.SwimerID ?? b?.SwimerName ?? "")).trim() && String((nb?.SwimerID ?? nb?.SwimerName ?? "")).trim()
                  && String(b?.SwimerName ?? b?.SwimerID).trim() === String(nb?.SwimerName ?? nb?.SwimerID).trim()));
            if (!dup) {
              // preserve nb as-is (do not modify other entries' fields)
              existing.Boardinfo.push(nb);
            }
          });

        } catch (mergeErr) {
          log.warn("merge duplicate heat failed", { key, idx: i }, mergeErr);
        }
      }
    }

    log.info("ReconcileHeatsBySwimmerNames completed.", { eventsProcessed: availableEvents.length, totalHeats: Object.keys(result).length });
    return result;
  } catch (err) {
    log.error("ReconcileHeatsBySwimmerNames failed.", err);
    // safe fallback: return deep-copied existing heats
    try {
      const fallbackSrc = Array.isArray(MeetUpdatedData?.HeatList) ? MeetUpdatedData.HeatList : (MeetUpdatedData?.HeatList ? Object.values(MeetUpdatedData.HeatList) : []);
      const fallback = {};
      (fallbackSrc || []).forEach((h, i) => { fallback[h?.ID ?? `heat_${i}`] = JSON.parse(JSON.stringify(h || {})); });
      return fallback;
    } catch (e) {
      return {};
    }
  }
}
//

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
    tblgroupRow.ondragover = function () { dragover() };
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
    tblSwimmersRow.ondragover = function () { dragover() };

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

     let SwimmerIDCell = tblSwimmersRow.insertCell();
      SwimmerIDCell.innerHTML = "<input class='form-control' type='text' id ='SwimmerIDCell" + index + "'>";

      
      
       let SwimmerPhotoCell = tblSwimmersRow.insertCell();
       // Photo preview only. Load image from local path stored in PhotoPath_Local.
       SwimmerPhotoCell.style.display = 'flex';
       SwimmerPhotoCell.style.alignItems = 'center';

       const preview = document.createElement('img');
       preview.id = 'SwimmerPhotoPreview' + index;
       preview.alt = 'Photo';
       preview.style.cssText = 'width:64px;height:64px;object-fit:cover;border:1px solid #ccc;border-radius:4px;';
       // prefer local filesystem path if provided
       preview.src = "http://127.0.0.1:5500/Lib/templates/Eejo_SwimManagerWeb/img/Photo/Screenshot%202026-06-22%20202409.png";
       //  preview.src = SwimmerDetails[SwKeys[i]]?.PhotoPath_Local ?? SwimmerDetails[SwKeys[i]]?.Photo ?? '';
       // graceful fallback: hide image element if no source
       if (!preview.src) preview.style.display = 'none';
       SwimmerPhotoCell.appendChild(preview);

       // keep a hidden input containing the path (so Save/Capture can persist it unchanged)
       const hiddenPath = document.createElement('input');
       hiddenPath.type = 'hidden';
       hiddenPath.id = 'SwimmerPhotoCell' + index;
      // hiddenPath.value = SwimmerDetails[SwKeys[i]]?.PhotoPath_Local ?? SwimmerDetails[SwKeys[i]]?.Photo ?? '';
       SwimmerPhotoCell.appendChild(hiddenPath);

    let SwimmersNamecell = tblSwimmersRow.insertCell();
    SwimmersNamecell.innerHTML = "<input class='form-control' id ='SwimmersNamecell" + index + "'>";
    // const nameEl = getEl("SwimmersNamecell" + index);
    // if (nameEl) nameEl.value = SwDetails?.Name ?? "";

      let SwimmersDOBcell = tblSwimmersRow.insertCell();
      SwimmersDOBcell.innerHTML = "<input class='form-control'  type='date' id ='SwimmersDOBcell" + index + "'>";

    let SwimmerGroupCell = tblSwimmersRow.insertCell();
    SwimmerGroupCell.innerHTML = "<input class='form-control' id ='SwimmerGroupCell" + index + "'>";
    // const groupEl = getEl("SwimmerGroupCell" + index);
    // if (groupEl) groupEl.value = SwDetails?.Group ?? "";

    

      let SwimmerClubCell = tblSwimmersRow.insertCell();
      SwimmerClubCell.innerHTML = "<input class='form-control' type='text' id ='SwimmerClubCell" + index + "'>";
     

      let SwimmerClubShortCell = tblSwimmersRow.insertCell();
      SwimmerClubShortCell.innerHTML = "<input class='form-control' type='text' id ='SwimmerClubShortCell" + index + "'>";
      // tblSwimmersRow.insertCell();
     
      let SwimmerRegTimeCell = tblSwimmersRow.insertCell();
      SwimmerRegTimeCell.innerHTML = "<input class='form-control' type='datetime-local' id ='SwimmerRegTimeCell" + index + "'>";

      let SwimmerGenderCell = tblSwimmersRow.insertCell();
       SwimmerGenderCell.innerHTML = "<input class='form-control' type='text' id ='SwimmerGenderCell" + index + "'>";
      // ensure gender input is populated (keeps ID unchanged)
     
      
    // Selected Events table
    const tblSwSelectedEvents = document.createElement("TABLE");
    tblSwSelectedEvents.id = "tblSwSelectedEvents" + index;

    const header = tblSwSelectedEvents.createTHead();
    let row = header.insertRow();
    let cell = row.insertCell(); cell.innerHTML = "<b> Event Name. <b>";
    cell = row.insertCell(); cell.innerHTML = "<b> Best Timeings <b>";
    cell = row.insertCell(); cell.innerHTML = "<b> Available <b>";
    cell = row.insertCell();

     {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.title = 'Add event';
        btn.innerHTML = "<i class='fa fa-fw fa-plus'></i>";
        btn.addEventListener('click', () => AppendRow(tblSwSelectedEvents.id, 'tblSwimmersRow', index));
        cell.appendChild(btn);
      }
      // create delete button (new cell)
      cell = row.insertCell();
      {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.title = 'Remove event';
        btn.innerHTML = "<i class='fa fa-fw fa-minus'></i>";
        btn.addEventListener('click', () => DeleteRows(tblSwSelectedEvents.id, 'tblSwSelectedEvents', 'tblSwimmersRow'));
        cell.appendChild(btn);
      }

    // cell.innerHTML =
    //   `<button onclick=AppendRow( ${tblSwSelectedEvents.id},'tblSwimmersRow',${index} )><i class='fa fa-fw fa-plus'></i></button> " +
    //   "<button onclick=DeleteRows(${tblSwSelectedEvents.id} ,'tblSwSelectedEvents','tblSwimmersRow')><i class='fa fa-fw fa-minus'></i></button>`

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
    let grptab = getEl(TableName, { required: true });
    if (!grptab) return;

    let Rowindextoadd = 0;
    for (let i = 0; i <= grptab.rows.length; i++) {
      if (!grptab.rows[idprefix + i]) {
        Rowindextoadd = i;
        break;
      }
    }

    if (TableName.indexOf("tblSwlist") !== -1) {
      let Heat = {};
      tblindex = parseInt(TableName.replace("tblSwlist", ""));
      grptab = getEl(TableName, { required: true });


      for (let i = 0; i <= grptab.rows.length; i++) {
        if (!grptab.rows[idprefix + tblindex + "_" + i]) {
          Rowindextoadd = i;
          break;
        }
      }


      AddSwList(Heat, tblindex, Rowindextoadd);
    }




    switch (TableName) {
      // case "tblSwlist0":
      //   {
      //     let Heat = {};
      //     AddSwList(Heat, tblindex, 0);
      //   }
      //   break;

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




function ComputeEventList()
{
    let heatId = "";

   log.warn("Heat ID Computation.", { heatId });
      // Normalize EventList to "entries": supports array OR dict
      const eventListRaw = Meetdteails?.EventDetails ?? {};
       eventEntries = Array.isArray(eventListRaw)
        // Array -> [{ idx, key (string index), value: ev }]
        ? eventListRaw.map((ev, i) => ({ idx: i, key: String(i), value: ev }))
        // Dict -> Object.entries -> [{ idx (iteration order), key, value: ev }]
        : Object.entries(eventListRaw).map(([k, v], i) => ({ idx: i, key: k, value: v }));

fillDatalist(document.getElementById('datalistSWid'),    AvailableSwimmerID);
fillDatalist(document.getElementById('datalistSWname'),  AvailableSwimmerNames);
fillDatalist(document.getElementById('datalistSWclub'),  AvailableSwimmerClubs);


function fillDatalist(listEl, values) {
  // Clear existing options efficiently
  while (listEl.firstChild) listEl.removeChild(listEl.firstChild);

  // Append options via a DocumentFragment (minimize reflow)
  const frag = document.createDocumentFragment();
  for (let i = 0; i < values.length; i++) {
    const opt = document.createElement('option');
    opt.value = String(values[i]);
    frag.appendChild(opt);
  }
  listEl.appendChild(frag);
}



}


/* ===========================
   GenerateHeatDetailsTable
   - UPDATED: Heats is Dict
   =========================== */
function GenerateHeatDetailsTable(Heats) {
  try {
    ClearTable('tblHeatDetails');

    showhide("BusyIndicatorpop", "GenerateHeatDetailsTable");
    showToast("Generating Heat Details" + " in progress…", { type: 'loading', persistent: true });
    
    

    ComputeEventList();
    const entries = Object.entries(Heats ?? {}); // [[key, heat], ...]

    

    for (let i = 0; i < entries.length; i++) {
      const [, heat] = entries[i]; // keep original signature: AddHeatRow(i, heat)
      AddHeatRow(i, heat);
    }

    const table = getEl('tblHeatDetails');
    if (table) {
      try { SetTableNavigation(table); }
      catch (navErr) { log.warn("SetTableNavigation failed for tblHeatDetails.", navErr); }
    }
    showhide("BusyIndicatorpop", "");

    log.info("GenerateHeatDetailsTable completed.", { count: entries.length });
    hideToast();
    showToast("Generating Heat Details" + " is Complete.", { type: 'success' });
  } catch (err) {
    log.error("GenerateHeatDetailsTable failed.", err);
    hideToast();
    showToast("GenerateHeatDetailsTable Request failed:" + err, { type: 'error' });
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
    let newrow= body.insertRow();
    const tblHeatDetailsRow = body.insertRow();
    tblHeatDetailsRow.id = "tblHeatDetailsRow" + index;

    const HeatCheckcell = tblHeatDetailsRow.insertCell();
    HeatCheckcell.classList.add('hide-on-print');
    HeatCheckcell.innerHTML = `<input type='Checkbox' id ='HeatCheckcell_${index}'>`;

    // -------- Robust EventID computation (Dict-aware) --------
    let EventID = -1;
    let EventName = -1;

    let heatId = "";
    try {
      heatId = Heat?.ID;

      if (!Array.isArray(eventEntries) || eventEntries.length === 0) {
        log.warn("EventList missing or empty; cannot compute EventID.", { Meetdteails });
      } else if (typeof heatId !== 'string' || !heatId.length) {
        log.warn("Heat.ID not a valid string; cannot compute EventID.", { Heat });
      } else {
        // compute prefix safely
        const preHeatName = (typeof splitBeforeLastUnderscore === 'function')
          ? splitBeforeLastUnderscore(heatId)
          : { ok: false, prefix: String(heatId || '') };

        const HeatName = preHeatName && preHeatName.ok
          ? normalizeStr(preHeatName.prefix)
          : normalizeStr(String(heatId ?? ''));

        // Match against primitive strings OR objects with ID/Id/id
        const match = (Array.isArray(eventEntries) ? eventEntries : []).find(({ value }) => {
          if (value == null) return false;
          if (typeof value === 'string') return normalizeStr(value) === HeatName;
          const candidate = (value?.ID ?? value?.Id ?? value?.id);
          return typeof candidate === 'string' && normalizeStr(candidate) === HeatName;
        });

        if (!match) {
          EventID = -1;
          log.info("No matching event found for Heat prefix; using fallback.", { prefix: HeatName, heatId, totalEvents: (eventEntries || []).length });
        } else {
          EventID = match.idx; // keep ordinal semantics (0-based)
          log.debug("Matched EventID for Heat.", { EventID, prefix: HeatName, heatId, eventKey: match.key });
        }

        const isSameEvent = (lastEvent === HeatName);
        const heatNumberText = (typeof Heat?.ID === 'string' && Heat.ID.includes('_'))
          ? Heat.ID.substring(Heat.ID.lastIndexOf('_') + 1)
          : "?";

        // safe formatted object: try user formatter only if heatId is valid
        let formatted = { fullname: normalizeStr(String(heatId ?? '')), EventDetailsDict: { EventID: EventID, HeatID: heatNumberText } };
        if (typeof formatSwimmingEvent === 'function' && typeof heatId === 'string' && heatId.length) {
          try { formatted = formatSwimmingEvent(heatId, MeetUpdatedData?.EventList); }
          catch (fmtErr) { log.warn("formatSwimmingEvent failed; using fallback formatted object.", fmtErr); }
        }

        let headerText;
        let highlightNewEvent = false;
        if (isSameEvent && HeatName !== "") {
          headerText = `<b style='font-size: 12px'> Event: ${formatted?.EventDetailsDict?.EventID ?? ''} Heat : ${formatted?.HeatID ?? heatNumberText}</b>`;
        } else {
          lastEvent = HeatName;
          headerText = `<b style='font-size: 12px'>Event: ${formatted?.EventDetailsDict?.EventID ?? ''} ${formatted?.fullname ?? HeatName}</b>`;
          highlightNewEvent = true;
        }

      //  if (!row)
        //  row = header.insertRow();
        
        let titleCell = newrow.insertCell();
        titleCell.colSpan = 2;
        titleCell.innerHTML = headerText;
        if (highlightNewEvent) {
          titleCell.style.backgroundColor = "rgb(100, 100, 100)";
          // let x = newrow.insertCell();
          let cellHeatStatus = newrow.insertCell();
          {
            const label = document.createElement('label');
            label.textContent = 'Status';
            const br = document.createElement('br');
            const select = document.createElement('select');
            select.id = `${heatId}SelectEventStatus`;
            select.classList.add('dropdown-cell');
            const statuses = Array.isArray(HeatStatus) ? HeatStatus : [];
            statuses.forEach((statusText, i) => {
              const option = document.createElement('option');
              option.value = String(i); // values are strings
              option.textContent = statusText;
              select.add(option);
            });

            // Set selected index from Heat.HeatStatus
            let idx = 0;
            let validIdx = 0;
            if (HeatName && HeatName.trim().length > 0) {
              try {
                const evObj = MeetUpdatedData?.EventDetails?.[HeatName];
                idx = Number.parseInt(evObj?.eventStatus ?? '0', 10);
                validIdx = Number.isInteger(idx) && idx >= 0 && idx < statuses.length;
              } catch (e) {
                validIdx = 0;
              }
            }

            select.value = validIdx ? String(idx) : '0';
            cellHeatStatus.append(label, br, select);
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

    const header = tblSwlist.createTHead();

    let row = header.insertRow();

    const controlsCell = row.insertCell();
    controlsCell.id = "controlsCell" + index;
    controlsCell.classList.add('hide-on-print');


    controlsCell.innerHTML = ""; // clear any existing content

    // call after the <select> is created and populated
      // attachReadyToPublishHandler(select, heatId, heatObj, { baseUrl: FirebaseURLToWrite + MeetUpdatedData.FireBaseName + heatId + ".json" || '', busyKey: 'Save to Fire base' });

function attachReadyToPublishHandler(selectEl, heatId, heatObj, { FBBaseURL = window.FirebaseURLToWrite || window.MeetDataFirebaseURL || '', MeeName = MeetUpdatedData?.FireBaseName || '', rowindex, busyKey = 'Save to Fire base' } = {}) {
  if (!selectEl) return;
  try {
    // prevent attaching multiple times
    if (selectEl._readyToPublishAttached) return;
    selectEl._readyToPublishAttached = true;

    selectEl.addEventListener('change', async (ev) => {
      try {
        const sel = ev.target;
        const selectedText = (sel.options[sel.selectedIndex]?.textContent || '').trim().toLowerCase();
        const selectedValue = String(sel.value || '').trim().toLowerCase();
        console.debug(LOG_PREFIX, 'attachReadyToPublishHandler change', { heatId, selectedText, selectedValue });

        const possibleReadyTexts = ['ready to publish', 'ready', 'readytopublish', 'ready_to_publish'];
        const isReady = possibleReadyTexts.includes(selectedText) || possibleReadyTexts.includes(selectedValue);
        if (!isReady) return;

        captureSingleHeat(rowindex)

        let baseUrl = String(FBBaseURL || '') + (MeeName ? (MeeName + '/') : '') + String(heatId || '') + '.json';
        let eventID= splitBeforeLastUnderscore(heatId)?.prefix ?? heatId;
        const payload = MeetUpdatedData.EventDetails[eventID].HeatList[heatId] || {};
        console.info(LOG_PREFIX, 'Ready to publish triggered for', { heatId, url: baseUrl });

        const result = await ExecuteRestLocalCommands(
          baseUrl,
          busyKey,
          '',
          { method: 'PUT', body: JSON.stringify(payload), expectJson: true }
        );

        console.debug(LOG_PREFIX, 'ReadyToPublish PUT result', { heatId, result });

      baseUrl = String(FBBaseURL || '') + (MeeName ? (MeeName + '/') : '')  + 'lastProcessedHeatDetails.json';
        const resultlastHeat = await ExecuteRestLocalCommands(
          baseUrl,
          busyKey,
          '',
          { method: 'PUT', body: JSON.stringify(String(heatId,'')), expectJson: true }
        );

        console.debug(LOG_PREFIX, 'ReadyToPublish PUT result', { heatId, result });


      } catch (err) {
        console.error(LOG_PREFIX, 'ReadyToPublish handler failed', err);
      }
    });
  } catch (outerErr) {
    console.warn(LOG_PREFIX, 'attachReadyToPublishHandler setup failed', { heatId }, outerErr);
  }
}

// helper to create icon button
function makeIconBtn(title, html, onClick) {
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.title = title || '';
  btn.innerHTML = html;
  btn.addEventListener('click', onClick);
  return btn;
}

// create buttons using DOM API (safer than inline onclick)
const tblId = String(tblSwlist.id);
controlsCell.appendChild(makeIconBtn('Add row', "<i class='fa fa-fw fa-plus'></i>", () => AppendRow(tblId, 'tblSwlistRow_', index)));
controlsCell.appendChild(makeIconBtn('Remove selected', "<i class='fa fa-fw fa-minus'></i>", () => DeleteRows(tblId, 'BoardCheckcell_', 'tblSwlistRow_')));
controlsCell.appendChild(makeIconBtn('Upload', "<i class='fa fa-fw fa-upload'></i>", () => UpdateSelectedData('Events')));

    // controlsCell.innerHTML =
    //   `<button onclick=AppendRow('${tblSwlist.id}','tblSwlistRow_',${index})><i class='fa fa-fw fa-plus'></i></button>` +
    //   ` <button onclick=DeleteRows('${tblSwlist.id}','BoardCheckcell_','tblSwlistRow_')><i class='fa fa-fw fa-minus'></i></button>` +
    //   `<button onclick=UpdateSelectedData('Events')><i class="fa fa-fw fa-upload"></i></button>`;

    let cell = row.insertCell();

    // Header text logic with EventID safety
    // compute prefix safely
      const preHeatName = (typeof splitBeforeLastUnderscore === 'function') ? splitBeforeLastUnderscore(heatId) : { ok: false, prefix: String(heatId || '') };
      const HeatName = preHeatName && preHeatName.ok ? normalizeStr(preHeatName.prefix) : normalizeStr(String(heatId ?? ''));

      // match event entry (preserve existing ordinal semantics)
      const match = (Array.isArray(eventEntries) ? eventEntries : []).find(({ value }) => {
        if (value == null) return false;
        if (typeof value === 'string') return normalizeStr(value) === HeatName;
        const candidate = (value?.ID ?? value?.Id ?? value?.id);
        return typeof candidate === 'string' && normalizeStr(candidate) === HeatName;
      });
      if (match) {
        EventID = match.idx;
        log.debug("Matched EventID for Heat.", { EventID, prefix: HeatName, heatId, eventKey: match.key });
      } else {
        EventID = -1;
        if (!HeatName || HeatName.length === 0) log.warn("Heat.ID has no valid underscore partition; using full ID fallback.", { heatId });
      }

      const isSameEvent = (lastEvent === HeatName);
      const heatNumberText = (typeof Heat?.ID === 'string' && Heat.ID.includes('_')) ? Heat.ID.substring(Heat.ID.lastIndexOf('_') + 1) : "?";

      // safe formatted object: try user formatter only if heatId is valid
      let formatted = { fullname: normalizeStr(String(heatId ?? '')), EventDetailsDict: { EventID: EventID, HeatID: heatNumberText } };
     
     
      if (typeof formatSwimmingEvent === 'function' && typeof heatId === 'string' && heatId.length) {
        try { formatted = formatSwimmingEvent(heatId, MeetUpdatedData?.EventList); }
        catch (fmtErr) { log.warn("formatSwimmingEvent failed; using fallback formatted object.", fmtErr); }
      }

      let headerText;
      let highlightNewEvent = false;
      if (isSameEvent && HeatName !== "") {
        headerText = `<b style='font-size: 12px'> Event: ${formatted?.EventDetailsDict?.EventID ?? ''} Heat : ${formatted?.HeatID ?? heatNumberText}</b>`;
      } else {
        lastEvent = HeatName;
        headerText = `<b style='font-size: 12px'>Event: ${formatted?.EventDetailsDict?.EventID ?? ''} ${formatted?.fullname ?? HeatName}</b>`;
        highlightNewEvent = true;
      }

    cell.innerHTML = headerText;
    if (highlightNewEvent) {
      cell.style.backgroundColor = "rgb(100, 100, 100)";
     let cellHeatStatus = row.insertCell();

    {
      const label = document.createElement('label');
      label.textContent = 'Status';
      const br = document.createElement('br');
      const select = document.createElement('select');
      select.id = `${heatId}SelectEventStatus`;
      select.classList.add('dropdown-cell');
      const statuses = Array.isArray(HeatStatus) ? HeatStatus : [];
      statuses.forEach((statusText, i) => {
        const option = document.createElement('option');
        option.value = String(i); // values are strings
        option.textContent = statusText;
        select.add(option);
      });

      // Attach ready-to-publish handler to heat status select as well
      try {
        attachReadyToPublishHandler(select, heatId, Heat, {
          FBBaseURL: (typeof FirebaseURLToWrite !== 'undefined' ? FirebaseURLToWrite : (window.FirebaseURLToWrite || '')),
          MeeName: (MeetUpdatedData?.FireBaseName || ''),index,
          busyKey: 'Save to Fire base'
        });
        console.debug(LOG_PREFIX, 'attachReadyToPublishHandler attached to heat status select', { heatId, selectId: select.id });
      } catch (attachErr) {
        console.warn(LOG_PREFIX, 'Failed to attach ReadyToPublish to heat status select', { heatId }, attachErr);
      }

      // Set selected index from Heat.HeatStatus
      const idx = Number.parseInt(Heat?.HeatStatus, 10);
      const validIdx = Number.isInteger(idx) && idx >= 0 && idx < statuses.length;
      select.value = validIdx ? String(idx) : '0';

      cellHeatStatus.append(label, br, select);
    }


    // const input = document.createElement('input');
    //   input.type = 'text';
    //   const inputId = `${heatId}HeatStatus`;
    //   input.id = inputId;
    //  cellHeatStatus.appendChild(input);
    }
    cell.colSpan = 8;

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
      const val = Heat?.HeatStartTime ?? '';
      //normalizeTime(Heat?.HeatStartTime ?? '');
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
      const val =Heat?.HeatEndTime ?? '';
      // normalizeTime(Heat?.HeatEndTime ?? '');
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

      // Attach ready-to-publish handler to heat status select as well
      try {
        attachReadyToPublishHandler(select, heatId, Heat, {
          FBBaseURL: (typeof FirebaseURLToWrite !== 'undefined' ? FirebaseURLToWrite : (window.FirebaseURLToWrite || '')),
          MeeName: (MeetUpdatedData?.FireBaseName || ''), rowindex:index,
          busyKey: 'Save to Fire base'
        });
        console.debug(LOG_PREFIX, 'attachReadyToPublishHandler attached to heat status select', { heatId, selectId: select.id });
      } catch (attachErr) {
        console.warn(LOG_PREFIX, 'Failed to attach ReadyToPublish to heat status select', { heatId }, attachErr);
      }

      // Set selected index from Heat.HeatStatus
      const idx = Number.parseInt(Heat?.HeatStatus, 10);
      const validIdx = Number.isInteger(idx) && idx >= 0 && idx < statuses.length;
      select.value = validIdx ? String(idx) : '0';

      cell.append(label, br, select);
    }

    // ---------------------- Notes ---------------------------
    cell = row.insertCell();
    // If you want Notes to span two columns, set colSpan here
    cell.colSpan = 6;
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
      c = row.insertCell(); c.innerHTML = "<b>SwimTimeings_M<b>";
      c = row.insertCell(); c.innerHTML = "<b>SwimTimeings_Bak<b>";
      c = row.insertCell(); c.innerHTML = "<b>SwimTimeings_CAM<b>";


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
   
    const Swimerstatus = board.SwimStatus ?? 0;       // index-like code
    const SwimerName = normalizeStr(board.SwimerName ?? '');
    let Club = '';

    // Defensive Meet details lookup
    try {
      const clubObj = Meetdteails?.SwimmerDetails?.[SwimerName];
      Club = normalizeStr(clubObj?.Club ?? '');
      if (Club == "") {
        Club = Heat.Boardinfo.find(s => s.SwimerName === SwimerName)?.ClubName || "Not found";
      }

    } catch (clubErr) {
      log.warn("Club lookup failed.", { SwimerName }, clubErr);
    }

    // Ensure tbody exists and insert row
    const body = ensureTBody(tblSwlist);
    if (!body) return;
    const tblSwlistRow = body.insertRow();
    tblSwlistRow.id = `tblSwlistRow_${index}_${j}`;
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


//     datalist id="datalistSWid"></datalist>
// <datalist id="datalistSWname"></datalist>
// <datalist id="datalistSWclub"></datalist>
    // ---------------- Board (textarea) ----------------
    tblSwlistRowcell = tblSwlistRow.insertCell();
    const BoardIDInput = document.createElement('input');
    BoardIDInput.setAttribute("size", "3")
    BoardIDInput.setAttribute("maxlength", "3")
    BoardIDInput.inputMode = 'numeric';
    // BoardIDInput.classList.add('form-control');
    tblSwlistRowcell.id = `tblSwlist_BoardID_${index}_${j}`;
    BoardIDInput.value = BoardID;
    tblSwlistRowcell.appendChild(BoardIDInput);

    // ---------------- Swimmer ID (textarea) ----------------
    tblSwlistRowcell = tblSwlistRow.insertCell();
    tblSwlistRowcell.id = `tblSwlist_SwimerID_${index}_${j}`;

    const inID = document.createElement('input');
    inID.setAttribute('list', 'datalistSWid');

    inID.setAttribute('placeholder', 'Type to search...');

    tblSwlistRowcell.appendChild(inID);
    // Create sWid element
    // const sWid = document.createElement('datalist');
    // sWid.setAttribute('id', 'sWid');
    // tblSwlistRowcell.appendChild(sWid);

    // AvailableSwimmerID.forEach(SwID => {
    //   const option = document.createElement('option');
    //   option.value = SwID;
    //   sWid.appendChild(option);
    // });
    inID.value = String(SwimerID);
    tblSwlistRowcell.classList.add('hide-on-print');


    // ---------------- Swimmer Name (textarea) ----------------
    tblSwlistRowcell = tblSwlistRow.insertCell();
    tblSwlistRowcell.id = `tblSwlist_SwimerName_${index}_${j}`;

    const inName = document.createElement('input');
    inName.setAttribute('list', 'datalistSWname');
    inName.setAttribute('placeholder', 'Type to search...');

    tblSwlistRowcell.appendChild(inName);
    // Create datalist element
    // const datalistSWname = document.createElement('datalist');
    // datalistSWname.setAttribute('id', 'datalistSWname');
    // tblSwlistRowcell.appendChild(datalistSWname);

    // AvailableSwimmerNames.forEach(SwName => {
    //   const option = document.createElement('option');
    //   option.value = SwName;
    //   datalistSWname.appendChild(option);
    // });
    inName.value = String(SwimerName);
    tblSwlistRowcell.classList.add('hide-on-print');

    // ---------------- Club (textarea) ----------------
    tblSwlistRowcell = tblSwlistRow.insertCell();
    tblSwlistRowcell.id = `tblSwlist_Club_${index}_${j}`;


    // const taClub = document.createElement('textarea');
    // taClub.style.cssText = 'width:100%; height:60px;';
    // taClub.value = Club;



    const inClub = document.createElement('input');
    inClub.setAttribute('list', 'datalistSWclub');
    inClub.setAttribute('placeholder', 'Type to search...');

    tblSwlistRowcell.appendChild(inClub);
    // Create datalist element
    // const datalistSWclub = document.createElement('datalist');
    // datalistSWclub.setAttribute('id', 'datalistSWclub');
    // tblSwlistRowcell.appendChild(datalistSWclub);

    // AvailableSwimmerClubs.forEach(SwClub => {
    //   const option = document.createElement('option');
    //   option.value = SwClub;
    //   datalistSWclub.appendChild(option);
    // });
    inClub.value = String(Club);

    // tblSwlistRowcell.appendChild(inClub);

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
    if (val != "00:00.000" && val != "NaN:000NaN") {
      timingInput.value = val ?? '';
    }
    else {
      timingInput.value = "";
    }

    tblSwlistRowcell.appendChild(timingInput);

    // Timing validation hook
    const Timeinput = getEl(timingInput.id);
    if (Timeinput) {
      try { setTimeinputValidation(Timeinput); }
      catch (err) { log.warn("setTimeinputValidation failed for timing input.", err); }
    }

    
    // ---------------- Swim Timings (input) ----------------
    tblSwlistRowcell = tblSwlistRow.insertCell();
    tblSwlistRowcell.id = `tblSwlist_timingInput_Backup_${index}_${j}`;

    const timingInput_Backup = document.createElement('input');
    timingInput_Backup.classList.add('form-control');
    BoardIDInput.setAttribute("size", "10")
    BoardIDInput.setAttribute("maxlength", "10")
    timingInput_Backup.id = `${tblSwlistRowcell.id}input`;

    let val_backup = '';
    if (board.SwimTimings_Backup != '00:00.000') val_backup = ConvertTime(board.SwimTimings_Backup ?? '00:00.000'); // treat zero time as empty
    if (val_backup != "00:00.000" && val_backup != "NaN:000NaN") {
      timingInput_Backup.value = val_backup ?? '';
    }
    else {
      timingInput_Backup.value = "";
    }

    tblSwlistRowcell.appendChild(timingInput_Backup);

    // Timing validation hook
    const TimeinputBackup = getEl(timingInput_Backup.id);
    if (TimeinputBackup) {
      try { setTimeinputValidation(TimeinputBackup); }
      catch (err) { log.warn("setTimeinputValidation failed for timing input.", err); }
    }


    
    // ---------------- Swim Timings (input) ----------------
    tblSwlistRowcell = tblSwlistRow.insertCell();
    tblSwlistRowcell.id = `tblSwlist_timingInput_Manual_${index}_${j}`;

    const timingInput_Manual = document.createElement('input');
    timingInput_Manual.classList.add('form-control');
    BoardIDInput.setAttribute("size", "10")
    BoardIDInput.setAttribute("maxlength", "10")
    timingInput_Manual.id = `${tblSwlistRowcell.id}input`;

    let val_manual = '';
    if (board.SwimTimings_Backup != '00:00.000') val_manual = ConvertTime(board.SwimTimings_Backup ?? '00:00.000'); // treat zero time as empty
    if (val_manual != "00:00.000" && val_manual != "NaN:000NaN") {
      timingInput_Manual.value = val_manual ?? '';
    }
    else {
      timingInput_Manual.value = "";
    }

    tblSwlistRowcell.appendChild(timingInput_Manual);

    // Timing validation hook
    const TimeinputManual = getEl(timingInput_Manual.id);
    if (TimeinputManual) {
      try { setTimeinputValidation(TimeinputManual); }
      catch (err) { log.warn("setTimeinputValidation failed for timing input.", err); }
    }



    // ---------------- Swim Timings (input) ----------------
    tblSwlistRowcell = tblSwlistRow.insertCell();
    tblSwlistRowcell.id = `tblSwlist_timingInput_FCCAM_${index}_${j}`;

    const timingInput_FCCAM = document.createElement('input');
    timingInput_FCCAM.classList.add('form-control');
    timingInput_FCCAM.setAttribute("size", "10")
    timingInput_FCCAM.setAttribute("maxlength", "10")
    timingInput_FCCAM.id = `${tblSwlistRowcell.id}input`;

    let val_FCCAM = '';
    if (board.SwimTimings_FCCAM != '00:00.000') val_FCCAM = ConvertTime(board.SwimTimings_FCCAM ?? '00:00.000'); // treat zero time as empty
    if (val_FCCAM != "00:00.000" && val_FCCAM != "NaN:000NaN") {
      timingInput_FCCAM.value = val_FCCAM ?? '';
    }
    else {
      timingInput_FCCAM.value = "";
    }

    tblSwlistRowcell.appendChild(timingInput_FCCAM);

    // Timing validation hook
    const TimeinputFCCAM = getEl(timingInput_FCCAM.id);
    if (TimeinputFCCAM) {
      try { setTimeinputValidation(TimeinputFCCAM); }
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
    const Distence = eventID[0] || "";
    const Group = eventID[2] || "";
    const Gender = eventID[3] || "";

    let tblEventsBody = tblEvents.tBodies[0];
    if (!tblEventsBody) {
      tblEventsBody = document.createElement('tbody');
      tblEvents.appendChild(tblEventsBody);
    }

    const tblEventsRow = tblEventsBody.insertRow();
    tblEventsRow.id = "tblEventsRow" + index;
    tblEventsRow.setAttribute('draggable', 'true');
    tblEventsRow.ondragstart = function () { startDrag() };
    tblEventsRow.ondragover = function () { dragover() };

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
    cell = row.insertCell(); cell.innerHTML = "<input type='number' id ='BoardStartingNumber' value='0' class='form-control'>";

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
  } catch (err) {
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
    AvailableSwimmerID = [];
    AvailableSwimmerClubs = [];
    AvailableSwimmerNames = [];

    const tblSwimmers = getEl('tblSwDetails', { required: true });
    if (!tblSwimmers) return;

    const SwKeys = Object.keys(SwimmerDetails || {});
    for (let i = 0; i < SwKeys.length; i++) {
      const tblSwimmersRow = tblSwimmers.insertRow();
      tblSwimmersRow.setAttribute('draggable', 'true');
      tblSwimmersRow.ondragstart = function () { startDrag() };
      tblSwimmersRow.ondragover = function () { dragover() };

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

      
       let SwimmerIDCell = tblSwimmersRow.insertCell();
      SwimmerIDCell.innerHTML = "<input class='form-control' type='text' id ='SwimmerIDCell" + i + "'>";
      const IDEl = getEl("SwimmerIDCell" + i);
      if (IDEl) IDEl.value = SwimmerDetails[SwKeys[i]]?.ID ?? "";


      
       let SwimmerPhotoCell = tblSwimmersRow.insertCell();
       // Photo preview only. Load image from local path stored in PhotoPath_Local.
       SwimmerPhotoCell.style.display = 'flex';
       SwimmerPhotoCell.style.alignItems = 'center';

       const preview_local = document.createElement('img');
       preview_local.id = 'SwimmerPhotoPreview' + i;
       preview_local.alt = 'Photo';
       preview_local.style.cssText = 'width:64px;height:64px;object-fit:cover;border:1px solid #ccc;border-radius:4px;';
       // prefer local filesystem path if provided
       preview_local.src = "http://127.0.0.1:5500/Lib/templates/Eejo_SwimManagerWeb/img/Photo/Screenshot%202026-06-22%20202409.png";
       //  preview.src = SwimmerDetails[SwKeys[i]]?.PhotoPath_Local ?? SwimmerDetails[SwKeys[i]]?.Photo ?? '';
       // graceful fallback: hide image element if no source
       if (!preview_local.src) preview_local.style.display = 'none';
       SwimmerPhotoCell.appendChild(preview_local);

       // keep a hidden input containing the path (so Save/Capture can persist it unchanged)
       const hiddenPath = document.createElement('input');
       hiddenPath.type = 'hidden';
       hiddenPath.id = 'SwimmerPhotoCell' + i;
       hiddenPath.value = SwimmerDetails[SwKeys[i]]?.PhotoPath_Local ?? SwimmerDetails[SwKeys[i]]?.Photo ?? '';
       SwimmerPhotoCell.appendChild(hiddenPath);

       const preview_fb = document.createElement('img');
       preview_fb.id = 'SwimmerPhotoPreviewFB' + i;
       preview_fb.alt = 'Photo';
       preview_fb.style.cssText = 'width:64px;height:64px;object-fit:cover;border:1px solid #ccc;border-radius:4px;';
       // prefer local filesystem path if provided
       preview_fb.src = "http://127.0.0.1:5500/Lib/templates/Eejo_SwimManagerWeb/img/Photo/Screenshot%202026-06-22%20202409.png";
       //  preview.src = SwimmerDetails[SwKeys[i]]?.PhotoPath_Local ?? SwimmerDetails[SwKeys[i]]?.Photo ?? '';
       // graceful fallback: hide image element if no source
       if (!preview_fb.src) preview_fb.style.display = 'none';
       SwimmerPhotoCell.appendChild(preview_fb);

       // keep a hidden input containing the path (so Save/Capture can persist it unchanged)
       const hiddenPathfb = document.createElement('input');
       hiddenPathfb.type = 'hidden';
       hiddenPathfb.id = 'SwimmerPhotoCell' + i;
       hiddenPathfb.value = SwimmerDetails[SwKeys[i]]?.PhotoPath_Local ?? SwimmerDetails[SwKeys[i]]?.Photo ?? '';
       SwimmerPhotoCell.appendChild(hiddenPathfb);


      let SwimmersNamecell = tblSwimmersRow.insertCell();
      SwimmersNamecell.innerHTML = "<input class='form-control' id ='SwimmersNamecell" + i + "'>";
      const nameEl = getEl("SwimmersNamecell" + i);
      if (nameEl) nameEl.value = SwimmerDetails[SwKeys[i]]?.Name ?? "";

      let SwimmersDOBcell = tblSwimmersRow.insertCell();
      SwimmersDOBcell.innerHTML = "<input class='form-control'  type='date' id ='SwimmersDOBcell" + i + "'>";

    let SwimmerGroupCell = tblSwimmersRow.insertCell();
    SwimmerGroupCell.innerHTML = "<input class='form-control' id ='SwimmerGroupCell" + i + "'>";
    const groupEl = getEl("SwimmerGroupCell" + i);
    if (groupEl) groupEl.value = SwimmerDetails[SwKeys[i]]?.Group ?? "";

    

      let SwimmerClubCell = tblSwimmersRow.insertCell();
      SwimmerClubCell.innerHTML = "<input class='form-control' type='text' id ='SwimmerClubCell" + i + "'>";
      const clubEl = getEl("SwimmerClubCell" + i);
      if (clubEl) {
        clubEl.value = SwimmerDetails[SwKeys[i]]?.Club ?? "";
        if (!AvailableSwimmerClubs.includes(clubEl.value)) {
          AvailableSwimmerClubs.push(clubEl.value);
        }
      }

      let SwimmerClubShortCell = tblSwimmersRow.insertCell();
      SwimmerClubShortCell.innerHTML = "<input class='form-control' type='text' id ='SwimmerClubShortCell" + i + "'>";
      const clubhortEl = getEl("SwimmerClubShortCell" + i);
      if (clubhortEl) clubhortEl.value = SwimmerDetails[SwKeys[i]]?.ClubShort ?? "";
      
      
      let SwimmerRegTimeCell = tblSwimmersRow.insertCell();
      SwimmerRegTimeCell.innerHTML = "<input class='form-control' type='datetime-local' id ='SwimmerRegTimeCell" + i + "'>";
      const RegTimeEl = getEl("SwimmerRegTimeCell" + i);
      if (RegTimeEl) {
        const raw = SwimmerDetails[SwKeys[i]]?.RegTime ?? "";
        // use shared utility
        RegTimeEl.value = parseRegTimeToDatetimeLocal(raw) || "";
      }

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

       // replace fragile inline onclick with DOM-created buttons (keeps IDs unchanged)
      {
        // Add button
        const addBtn = document.createElement('button');
        addBtn.type = 'button';
        addBtn.title = 'Add event';
        addBtn.innerHTML = "<i class='fa fa-fw fa-plus'></i>";
        addBtn.addEventListener('click', () => AppendRow(tblSwSelectedEvents.id, 'tblSwimmersRow', i));
        cell.appendChild(addBtn);
      }

      // Create a new cell for delete button
      cell = row.insertCell();
      {
        const delBtn = document.createElement('button');
        delBtn.type = 'button';
        delBtn.title = 'Remove event';
        delBtn.innerHTML = "<i class='fa fa-fw fa-minus'></i>";
        delBtn.addEventListener('click', () => DeleteRows(tblSwSelectedEvents.id, 'tblSwSelectedEvents', 'tblSwimmersRow'));
        cell.appendChild(delBtn);
      }


      // cell.innerHTML = `<button onclick=AppendRow(${tblSwSelectedEvents.id} ,'tblSwimmersRow', ${i} )><i class='fa fa-fw fa-plus'></i></button>`;
      // cell = row.insertCell();
      // cell.innerHTML = `<button onclick=DeleteRows(${tblSwSelectedEvents.id} ,'tblSwSelectedEvents','tblSwimmersRow')><i class='fa fa-fw fa-minus'></i></button>`;

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
          catch (err) { log.warn("setTimeinputValidation failed.", { timeId }, err); }
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

// Utility: parse various human-readable date/time strings into HTML 'datetime-local' value (YYYY-MM-DDTHH:MM)
function parseRegTimeToDatetimeLocal(s) {
  if (!s) return "";
  const str = String(s).trim();
  // already in datetime-local / ISO-ish form
  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(str)) return str;

  // common format: 24-Jun-2026 8:28 PM  (day-mon-year hour:minute [AM|PM])
  const m = str.match(/^(\d{1,2})-(\w{3,})-(\d{4})\s+(\d{1,2}):(\d{2})(?:\s*(AM|PM))?/i);
  if (m) {
    const day = Number(m[1]);
    const monStr = m[2].toLowerCase();
    const year = Number(m[3]);
    let hour = Number(m[4]);
    const minute = Number(m[5]);
    const ampm = (m[6] || '').toUpperCase();
    const months = { jan:0,feb:1,mar:2,apr:3,may:4,jun:5,jul:6,aug:7,sep:8,oct:9,nov:10,dec:11 };
    const mon = months[monStr.substring(0,3)] ?? 0;
    if (ampm === 'PM' && hour < 12) hour += 12;
    if (ampm === 'AM' && hour === 12) hour = 0;
    const d = new Date(year, mon, day, hour, minute, 0);
    if (!isNaN(d)) {
      const pad = n => String(n).padStart(2,'0');
      return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
    }
  }

  // last-resort: use Date parser for other common formats
  const dd = new Date(str);
  if (!isNaN(dd)) {
    const pad = n => String(n).padStart(2,'0');
    return `${dd.getFullYear()}-${pad(dd.getMonth()+1)}-${pad(dd.getDate())}T${pad(dd.getHours())}:${pad(dd.getMinutes())}`;
  }

  return "";
}
