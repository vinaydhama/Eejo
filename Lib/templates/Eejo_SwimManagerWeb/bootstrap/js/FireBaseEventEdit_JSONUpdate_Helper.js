
async function ingestModifiedText(baseUrl, modifiedText) {
  const res = await fetch(`${baseUrl}/UpdateParam`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ modifiedText })
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// Usage
// const modifiedText = await (await fetch("/path/to/Shivamogga_Swim_Meet_2025.txt")).text();
// ingestModifiedText("http://localhost:5002", `Boards 9 BoardSettings IOSettings Side-A 7 20 ...`)
//   .then(console.log)



  
async function setMeetHeader(baseUrl, { MeetName, MeetDate, MeetAddress }) {
  const updates = [];
  if (MeetName !== undefined) updates.push({ path: "MeetName", value: MeetName });
  if (MeetDate !== undefined) updates.push({ path: "MeetDate", value: MeetDate });
  if (MeetAddress !== undefined) updates.push({ path: "MeetAddress", value: MeetAddress });

  for (const u of updates) {
    const res = await fetch(`${baseUrl}/UpdateParam`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(u)
    });
    if (!res.ok) throw new Error(await res.text());
  }
}

// Usage
// setMeetHeader("http://localhost:5002", {
//   MeetName: "Shivamogga_Swim_Meet_2025_R2",
//   MeetDate: "2025-11-30",
//   MeetAddress: "Shivamogga Sports Complex - Pool A"
// });



async function setCommParam(baseUrl, key, value) {
  const path = `BoardSettings.CommSettings.${key}`;
  const res = await fetch(`${baseUrl}/UpdateParam`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path, value })
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// // Usage examples
// setCommParam("http://localhost:5002", "COM_Windows", "COM7");        // e.g., change port
// setCommParam("http://localhost:5002", "COM_Pi", "/dev/ttyUSB1");     // e.g., change Pi device
// setCommParam("http://localhost:5002", "Baud", 57600);
// setCommParam("http://localhost:5002", "Parity", "E");



async function setIOSide(baseUrl, sideKey, arr) {
  const path = `BoardSettings.IOSettings.${sideKey}`; // "Side-A" or "Side-B"
  const res = await fetch(`${baseUrl}/UpdateParam`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path, value: arr })
  });
  if (!res.ok) throw new Error(await res.text());
}

async function setPrimarySide(baseUrl, isBPrimary) {
  const path = "BoardSettings.IOSettings.PrimerySide";
  const res = await fetch(`${baseUrl}/UpdateParam`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path, value: !!isBPrimary }) // true/false
  });
  if (!res.ok) throw new Error(await res.text());
}

// Usage
// setIOSide("http://localhost:5002", "Side-A", [7,20,18,21,22,1,2,3,4,5]);
// setIOSide("http://localhost:5002", "Side-B", [23,22,20,18,19,21,7,6,4,2,3,5]);



async function setHeatBoardField(baseUrl, eventID, heatIndexOrId, boardIndex, field, value) {
  const payload = typeof heatIndexOrId === "string"
    ? { eventID, heatID: heatIndexOrId, pathUnderHeat: `BoardList[${boardIndex}].${field}`, value }
    : { eventID, heatIndex: heatIndexOrId, pathUnderHeat: `BoardList[${boardIndex}].${field}`, value };

  const res = await fetch(`${baseUrl}/UpdateParam`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// Usage examples:
// by heatIndex (0-based)
// setHeatBoardField("http://localhost:5002", "50_FS_G03_B", 0, 1, "SwimerName", "Alice K.")
//   .catch(console.error);

// by heatID (e.g., "50_FS_G03_B_1" if present)
// setHeatBoardField("http://localhost:5002", "50_FS_G03_B", "50_FS_G03_B_1", 1, "SwimTimings", 29.87)
//   .then(console.log);


  
async function replaceHeatList(baseUrl, eventID, newHeatListArr) {
  // absolute path using event index is handled inside the API; you can set directly with a global path:
  const res = await fetch(`${baseUrl}/UpdateParam`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path: `EventDetails`, value: null }) // ensure EventDetails exists
  }); if (!res.ok) { /* ignore if already exists */ }

  // safer approach: find event via relative update (we’ll set HeatList on heatIndex=0 and then overwrite via absolute path)
  const res2 = await fetch(`${baseUrl}/UpdateParam`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ eventID, heatIndex: 0, pathUnderHeat: "__noop__", value: "" })
  }); // ensures event is located; server just no-ops
  if (!res2.ok) throw new Error(await res2.text());

  // Finally: set via absolute path
  const res3 = await fetch(`${baseUrl}/UpdateParam`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path: `EventDetails`, value: undefined }) // optional prep
  }); // ignore

  // Direct set using absolute path + JSON Pointer is also supported
  const res4 = await fetch(`${baseUrl}/UpdateParam`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path: `/EventDetails/${eventID}/HeatList`, value: newHeatListArr })
  });
  if (!res4.ok) throw new Error(await res4.text());
  return res4.json();
}


async function setLiveBoardTiming(baseUrl, boardIndex, timing) {
  const path = `LiveBoard.BoardList[${boardIndex}].SwimTimings`;
  const res = await fetch(`${baseUrl}/UpdateParam`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path,    body: JSON.stringify({ path, value: timing })
  })  });
  if (!res.ok) throw new Error(await res.text());
  }

  
async function setSwimmerDetail(baseUrl, swimmerKey, field, value) {
  const safeKey = swimmerKey.replace(/~/g, "~0").replace(/\//g, "~1"); // JSON Pointer escaping
  const path = `/SwimmerDetails/${safeKey}/${field}`;
  const res = await fetch(`${baseUrl}/UpdateParam`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path, value })
  });
  if (!res.ok) throw new Error(await res.text());
}

// Usage
// setSwimmerDetail("http://localhost:5002", "Vihann Shetty V", "Club", "Golden Fins Sports Club")
//   .catch(console.error);



let BASE_URL = "";

// Small fetch wrapper
async function apiPostUpdateParam(body) {
  const res = await fetch(`${BASE_URL}/UpdateParam`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`UpdateParam failed: ${res.status} ${errText}`);
  }
  return res.json();
}

// Current JSON (for locating indices)
async function getCurrentData() {
  const res = await fetch(`${BASE_URL}/SetLiveHeatCommands?CmdName=GetRunningHeatData`);
  if (!res.ok) throw new Error(`GetRunningHeatData failed: ${res.status}`);
  return res.json();
}

// Find event index by eventID in EventDetails[]
// function findEventIndex(data, eventID) {
//   const evs = Array.isArray(data.EventDetails) ? data.EventDetails : [];
//   return evs.findIndex(ev => ev && ev.eventID === eventID);
// }


function findEventIndex(data, eventID) {
  const src = data?.EventDetails;

  if (Array.isArray(src)) {
    // Original behavior for arrays
    return src.findIndex(ev => ev?.eventID === eventID);
  }

  if (src && typeof src === 'object') {
    // If keys are eventID, find index by key order
    if (Object.prototype.hasOwnProperty.call(src, eventID)) {
      return Object.keys(src).findIndex(k => k === eventID);
    }
    // Otherwise, search values by their ev.eventID
    const values = Object.values(src);
    return values.findIndex(ev => ev?.eventID === eventID);
  }

  return -1;
}


// Find heat index inside one event (by HeatID)
function findHeatIndex(evObj, heatID) {
  const heats = Array.isArray(evObj.HeatList) ? evObj.HeatList : [];
  return heats.findIndex(h => h && h.HeatID === heatID);
}

// JSON Pointer escaping for keys containing "~" or "/"
function pointerEscape(s) {
  return String(s).replace(/~/g, "~0").replace(/\//g, "~1");
}


/**
 * Update one or more fields on an event (EventDetails[idx]) using absolute path.
 * @param {string} eventID - e.g., "50_FS_G03_B"
 * @param {object} patch - e.g., { eventName: "Finals G03 B", eventStatus: 1 }
 */
async function updateEventDetails(eventID, patch) {
  const data =  MeetUpdatedData;//MeetUpdatedData;//await getCurrentData;;
  const evIndex = findEventIndex(data, eventID);
  if (evIndex < 0) throw new Error(`eventID '${eventID}' not found`);

  // For each key in patch, send an UpdateParam with the right path
  for (const [key, value] of Object.entries(patch)) {
    // Option A: dot/bracket path
    const path = `EventDetails[${evIndex}].${key}`;

    // Option B: JSON Pointer (safer if keys contain special chars)
    // const path = `/EventDetails/${evIndex}/${pointerEscape(key)}`;

    await apiPostUpdateParam({ path, value });
  }
}

// // --- Usage examples ---
// updateEventDetails("50_FS_G03_B", { eventName: "Heats - Group G03 Boys", eventStatus: 1 })
//   .then(console.log)


  
/**
 * Replace the whole HeatList array under a given event.
 * @param {string} eventID
 * @param {Array<object>} newHeatList - array of heat objects: { HeatID, BoardList, HeatNotes, ... }
 */
async function replaceHeatList(eventID, newHeatList) {
  const data = MeetUpdatedData;//await getCurrentData;();
  const evIndex = findEventIndex(data, eventID);
  if (evIndex < 0) throw new Error(`eventID '${eventID}' not found`);

  // Dot/bracket:
  const path = `EventDetails[${evIndex}].HeatList`;

  // JSON Pointer alternative:
  // const path = `/EventDetails/${evIndex}/HeatList`;

  await apiPostUpdateParam({ path, value: newHeatList });
}

// --- Usage (example shape) ---
const newHeatListExample = [
  {
    HeatID: "50_FS_G02_B_1",
    BoardList: [
      { BoardID: 1, BoardStatus: 0, SwimStatus: 0, SwimTimings: 0, SwimerID: "E03B_1_1", SwimerName: "Alice" },
      { BoardID: 2, BoardStatus: 0, SwimStatus: 0, SwimTimings: 0, SwimerID: "E03B_1_2", SwimerName: "Bob" }
    ],
    HeatNotes: "Updated @ control desk"
  },
  {
    HeatID: "50_FS_G02_B_2",
    BoardList: [],
       HeatNotes: ""
  }
];

// replaceHeatList("50_FS_G03_B", newHeatListExample)
//   .then(console.log)


  
/**
 * Update a field inside one heat (BoardList item, HeatNotes, etc.).
 * @param {string} eventID
 * @param {number|string} heatIndexOrId - 0-based index OR actual HeatID string
 * @param {string} pathUnderHeat - e.g., "BoardList[1].SwimerName" or "HeatNotes"
 * @param {*} value
 */
async function patchHeat(eventID, heatIndexOrId, pathUnderHeat, value) {
  const payload = typeof heatIndexOrId === "string"
    ? { eventID, heatID: heatIndexOrId, pathUnderHeat, value }
    : { eventID, heatIndex: heatIndexOrId, pathUnderHeat, value };

  return apiPostUpdateParam(payload);
}

// --- Usage examples ---
// Set swimmer name on board index 1 of heat #0 (first heat) in 50_FS_G03_B:
// patchHeat("50_FS_G03_B", 0, "BoardList[1].SwimerName", "Charlie Z")
//   .then(console.log)
//   .catch(console.error);

// // If you prefer referencing by HeatID:
// patchHeat("50_FS_G03_B", "50_FS_G03_B_1", "HeatNotes", "Call-up done")
//   .then(console.log)

  
/**
 * Add or replace one heat inside HeatList, then write the full array back.
 * @param {string} eventID
 * @param {object} heatObj - must include HeatID
 */
// async function updateHeat(eventID, heatObj) {
//   const data = MeetUpdatedData;//await getCurrentData;();
//   const evIndex = findEventIndex(data, eventID);
//   if (evIndex < 0) throw new Error(`eventID '${eventID}' not found`);
//   const ev = data.EventDetails[evIndex];
//     const heats = Array.isArray(ev.HeatList) ? ev.HeatList.slice() : [];

//   const idx = findHeatIndex(ev, heatObj.HeatID);
//   if (idx >= 0) {
//     heats[idx] = heatObj;            // replace existing
//   } else {
//     heats.push(heatObj);             // add new
//   }
//   await replaceHeatList(eventID, heats);
// }



// Assumes these exist somewhere in your codebase:
// - MeetUpdatedData
// - replaceHeatList(eventID, newHeatList)
// - findEventIndex(data, eventID)           // only used if EventDetails is an array
// - findHeatIndex(ev, heatID)               // only used if HeatList is an array

async function updateHeat(eventID, heatObj) {
  const data = MeetUpdatedData; // if you later switch to live fetch, keep it awaited here

  if (!data || !data.EventDetails) {
    throw new Error("updateHeat: EventDetails missing from data");
  }

  const events = data.EventDetails;

  // --- CASE 1: EventDetails is an ARRAY ---
  if (Array.isArray(events)) {
    const evIndex = findEventIndex(data, eventID);
    if (evIndex < 0) throw new Error(`eventID '${eventID}' not found`);
    const ev = events[evIndex];

    const hl = ev?.HeatList;
    // If HeatList is an array -> replace/push, then pass array to replaceHeatList
    if (Array.isArray(hl)) {
      const heats = hl.slice();
      const idx = findHeatIndex(ev, heatObj.HeatID);
      if (idx >= 0) {
        heats[idx] = heatObj; // replace existing
      } else {
        heats.push(heatObj);  // add new
      }
      await replaceHeatList(eventID, heats);
      return;
    }

    // If HeatList is a dict -> upsert in dict and pass dict to replaceHeatList
    if (hl && typeof hl === "object") {
      const heats = { ...hl, [heatObj.HeatID]: heatObj };
      await replaceHeatList(eventID, heats);
      return;
    }

    // If HeatList missing -> initialize as array with the new heat (or dict, your choice)
    await replaceHeatList(eventID, [heatObj]); // or: { [heatObj.HeatID]: heatObj }
    return;
  }

  // --- CASE 2: EventDetails is a DICT keyed by eventID ---
  if (events && typeof events === "object") {
    const ev = events[eventID];
    if (!ev) {
      throw new Error(`eventID '${eventID}' not found`);
    }

    const hl = ev.HeatList;

    // If HeatList is an array -> replace/push, pass array to replaceHeatList
    if (Array.isArray(hl)) {
      const heats = hl.slice();
      const idx = heats.findIndex(h => h && h.HeatID === heatObj.HeatID);
      if (idx >= 0) {
        heats[idx] = heatObj;
      } else {
        heats.push(heatObj);
      }
      await replaceHeatList(eventID, heats);
      return;
    }

    // If HeatList is a dict -> upsert key, pass dict to replaceHeatList
    if (hl && typeof hl === "object") {
      const heats = { ...hl, [heatObj.HeatID]: heatObj };
      await replaceHeatList(eventID, heats);
      return;
    }

    // If HeatList missing -> initialize; choose the shape you want to standardize on
    await replaceHeatList(eventID, { [heatObj.HeatID]: heatObj }); // or: [heatObj]
    return;
  }

  // Unknown structure
  throw new Error("updateHeat: Unexpected EventDetails structure (neither array nor object)");
}



/**
 * Remove a heat by HeatID, then write the full array back.
 */

// Assumes these exist somewhere in your codebase:
// - MeetUpdatedData
// - replaceHeatList(eventID, newHeatList)
// - findEventIndex(data, eventID)           // only used if EventDetails is an array
// - findHeatIndex(ev, heatID)               // only used if HeatList is an array

async function removeHeat(eventID, heatID) {
  const data = MeetUpdatedData; // if you switch to live fetch later, await it here

  if (!data || !data.EventDetails) {
    throw new Error("removeHeat: EventDetails missing from data");
  }

  const events = data.EventDetails;

  // --- CASE 1: EventDetails is an ARRAY ---
  if (Array.isArray(events)) {
    const evIndex = findEventIndex(data, eventID);
    if (evIndex < 0) throw new Error(`eventID '${eventID}' not found`);
    const ev = events[evIndex];
    const hl = ev?.HeatList;

    // HeatList is an ARRAY
    if (Array.isArray(hl)) {
      const heats = hl.slice();
      const idx = findHeatIndex(ev, heatID);
      if (idx < 0) throw new Error(`heatID '${heatID}' not found`);
      heats.splice(idx, 1);
      await replaceHeatList(eventID, heats);
      return;
    }

    // HeatList is a DICT
    if (hl && typeof hl === "object") {
      if (!Object.prototype.hasOwnProperty.call(hl, heatID)) {
        throw new Error(`heatID '${heatID}' not found`);
      }
      const { [heatID]: _removed, ...rest } = hl;
      await replaceHeatList(eventID, rest);
      return;
    }

    // HeatList missing or unexpected
    throw new Error(`removeHeat: HeatList missing for eventID '${eventID}'`);
  }

  // --- CASE 2: EventDetails is a DICT keyed by eventID ---
  if (events && typeof events === "object") {
    const ev = events[eventID];
    if (!ev) throw new Error(`eventID '${eventID}' not found`);
    const hl = ev.HeatList;

    // HeatList is an ARRAY
    if (Array.isArray(hl)) {
      const heats = hl.slice();
      const idx = heats.findIndex(h => h && h.HeatID === heatID);
      if (idx < 0) throw new Error(`heatID '${heatID}' not found`);
      heats.splice(idx, 1);
      await replaceHeatList(eventID, heats);
      return;
    }

    // HeatList is a DICT
    if (hl && typeof hl === "object") {
      if (!Object.prototype.hasOwnProperty.call(hl, heatID)) {
        throw new Error(`heatID '${heatID}' not found`);
      }
      const { [heatID]: _removed, ...rest } = hl;
      await replaceHeatList(eventID, rest);
      return;
    }

    // HeatList missing or unexpected
    throw new Error(`removeHeat: HeatList missing for eventID '${eventID}'`);
  }

  // Unknown structure
  throw new Error("removeHeat: Unexpected EventDetails structure (neither array nor object)");
}


// // --- Usage ---
// updateHeat("50_FS_G03_B", {
//   HeatID: "50_FS_G03_B_4",
//   BoardList: [],
//   HeatNotes: "Newly added heat"
// }).catch(console.error);

// removeHeat("50_FS_G03_B", "50_FS_G03_B_2")

 function GetSelectedRows (TableName, idprefixChkbox, RowPrefix) {
  let  SlectedRows = [];
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

    // let retryCount = 0;
    // const MAX_RETRIES = 5;
    // while (SlectedRows.length !== 0 && retryCount <= MAX_RETRIES) {
    //   retryCount++;
    //   for (let i = 0; i < SlectedRows.length; i++) {
    //     const rowEl = getEl(RowPrefix + SlectedRows[i]);
    //     if (!rowEl) continue;
    //     const rowIndex = rowEl.rowIndex;
    //     try {
    //       tbl.deleteRow(rowIndex);
    //       const idx = SlectedRows.indexOf(SlectedRows[i]);
    //       if (idx !== -1) SlectedRows.splice(idx, 1);
    //     } catch (delErr) {
    //       log.warn("Row deletion failed; will retry.", { TableName, rowIndex }, delErr);
    //     }
    //   }

    log.info("Selected Rows .", { TableName });

    
  } catch (err) {
    log.error("DeleteRows fatal error.", { TableName }, err);
  }
return SlectedRows;
 }



// Assumes: CaptureMeetTable, MeetUpdatedData, GetSelectedRows, getEl, normalize,
// getEventPrefix, replaceHeatList, updateHeat, removeHeat are defined elsewhere.

async function UpdateSelectedData(nodeNameToUpdate, tableName, checkboxPrefix, rowPrefix) {
  switch (nodeNameToUpdate) {
    case 'replaceHeatList': {
      // TODO: set eventID appropriately (e.g., from the current selection context)
      const eventID = '50_FS_G02_B'; // example only
      const newHeatList = [];        // build your new list here

      try {
        await replaceHeatList(eventID, newHeatList);
        console.log(`HeatList replaced for ${eventID}`);
      } catch (err) {
        console.error('replaceHeatList failed:', err);
      }
      break;
    }

    case 'updateHeat': {
      const tempMeetUpdatedData = CaptureHeatDetailsTable(MeetUpdatedData);
      const selectedRows = GetSelectedRows(tableName, checkboxPrefix, rowPrefix);

      if (selectedRows.length > 0) {
        for (const rowId of selectedRows) {
          const index = rowId.replace(rowPrefix, '');
          const heatNameEl = getEl('HeatNamecell' + index);
          const heatID = normalizeStr(heatNameEl?.value);      // e.g., "100_FS_G02_B_1"
          const eventID = splitBeforeLastUnderscore(heatID);            // e.g., "100_FS_G02_B"

          // When your data is a DICT keyed by IDs, use key access safely:
          const payload ={ heatID: tempMeetUpdatedData.EventDetails[eventID.prefix].HeatList[heatID]};

            // tempMeetUpdatedData?.[eventID]?.[heatID] ?? {
            //   HeatID: heatID,
            //   BoardList: [],
            //   HeatNotes: ''
            // };

          try {
            await updateHeat(eventID.prefix, heatID, payload);
            console.log(`Updated heat ${heatID} in event ${eventID}`);
          } catch (err) {
            console.error(`updateHeat failed for ${heatID}:`, err);
          }
        }
      }
      break;
    }

    case 'removeHeat': {
      const selectedRows = GetSelectedRows(tableName, checkboxPrefix, rowPrefix);

      for (const rowId of selectedRows) {
        const index = rowId.replace(rowPrefix, '');
        const heatNameEl = getEl('HeatNamecell' + index);
        const heatID = normalize(heatNameEl?.value);
        const eventID = getEventPrefix(heatID);

        try {
          await removeHeat(eventID, heatID);
          console.log(`Removed heat ${heatID} from event ${eventID}`);
        } catch (err) {
          console.error(`removeHeat failed for ${heatID}:`, err);
        }
      }
      break;
    }

    default:
      console.warn('Unknown NodeNametoUpdate:', nodeNameToUpdate);
      break;
  }
}


// async function  UpdateSelectedData(NodeNametoUpdate, tableName, CheckboxPrefix,RowPrefix)
// {

// switch (NodeNametoUpdate) {
//   case replaceHeatList:
//     const newHeatListExample = [    ];

//     //await  replaceHeatList("50_FS_G02_B", newHeatListExample)
//   .then(console.log)
  
    
//     break;

//      case updateHeat:
//         let TempMeetUpdatedData=  CaptureMeetTable(MeetUpdatedData);
//         let selectedRows= GetSelectedRows (tableName, CheckboxPrefix,RowPrefix);
        
//         if (selectedRows.length>0)
//         {
//           selectedRows.forEach(element => {
//             index= element.replace(RowPrefix,"");
//             const heatNameEl = getEl('HeatNamecell' + index);
//             const HeatiD = normalize(heatNameEl?.value); // e.g., "100_FS_G02_B_1"
//             const eventID = getEventPrefix(HeatiD);
//             await updateHeat(eventID,HeatiD, TempMeetUpdatedData[eventID][HeatiD] ) .then(console.log)
//           });

//         }

// // // --- Usage ---
// // updateHeat("50_FS_G03_B", {
// //   HeatID: "50_FS_G03_B_4",
// //   BoardList: [],
// //   HeatNotes: "Newly added heat"
// // }).catch(console.error);

//       break;

//       case removeHeat:
//         // removeHeat("50_FS_G03_B", "50_FS_G03_B_2")

//   default:
//     break;
// }

// //   const newHeatListExample = [
// //   {
// //     HeatID: "50_FS_G02_B_1",
// //     BoardList: [
// //       { BoardID: 1, BoardStatus: 0, SwimStatus: 0, SwimTimings: 0, SwimerID: "E03B_1_1", SwimerName: "Alice" },
// //       { BoardID: 2, BoardStatus: 0, SwimStatus: 0, SwimTimings: 0, SwimerID: "E03B_1_2", SwimerName: "Bob" }
// //     ],
// //     HeatNotes: "Updated @ control desk"
// //   },
// //   {
// //     HeatID: "50_FS_G02_B_2",
// //     BoardList: [],
// //        HeatNotes: ""
// //   }



// // ];


// }

// replaceHeatList("50_FS_G03_B", newHeatListExample)