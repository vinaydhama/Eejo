let DQMsg = ["", "AB", "DQ", "DNC", "ES"];
let HeatStatus= ["To be Started","in Progress", "On Hold", "Completed"];
let ReporTitles=["Heat List", "Heat Results", "IC Clubwise", "Club Wise Entry", "Club Wise Result", "IC Group wise","Event Results" ]

let GroupInfoDict={};

    function buildTable({ containerId, columns, rows, TableID, TableTitle }) {
        const container = document.getElementById(containerId);
        const spacer = document.createElement("div");
        spacer.className = "print-spacer-header";
        container.appendChild(spacer);

        const table = document.createElement('table');
        table.classList.add("report-table");
        container.appendChild(table);
        table.id = TableID;
        const thead = document.createElement('thead');
        let headRow = document.createElement('tr');
        TitleCell = headRow.insertCell()
        TitleCell.innerHTML = `<h4><b> <br> ${TableTitle}</b></h4>`;
        TitleCell.colSpan = columns.length;
        // TitleCell.style.backgroundColor = "rgb(160, 160, 160)";

        thead.appendChild(headRow);

        table.appendChild(thead);

        headRow = document.createElement('tr');
        columns.forEach(col => { const th = document.createElement('th'); th.textContent = col; headRow.appendChild(th); });
        thead.appendChild(headRow);
        table.appendChild(thead);

        const tbody = document.createElement('tbody');
        rows.forEach(r => { const tr = document.createElement('tr'); r.forEach(cell => { const td = document.createElement('td'); td.textContent = cell; tr.appendChild(td); }); tbody.appendChild(tr); });
        table.appendChild(tbody);

      }



function CountNoOfEvents(s) {
  return (s.match(/;/g) || []).length;
}


function calculateAge(birthDate) {
  let age =0;
  try {
    const today = new Date();
  const dob = new Date(birthDate);

  age = today.getFullYear() - dob.getFullYear();

  // Adjust if birthday hasn't occurred yet this year
  const hasNotHadBirthday =
    today.getMonth() < dob.getMonth() ||
    (today.getMonth() === dob.getMonth() && today.getDate() < dob.getDate());

  if (hasNotHadBirthday) {
    age--;
  }

  } catch (error) {
    
  }
  finally{
  return age;
  }
}

// Example usage:
// console.log(calculateAge('1990-12-23')); // Output: 35 (as of Dec 23, 2025)


/**
 * Replace the text between ":" and the next ";" for each entry,
 * using values from `replacements`. If `replacements` is empty or
 * doesn't have enough items, fill missing ones with "NT".
 *
 * @param {string} input - Semicolon-separated entries: "Name : value;Name : value;..."
 * @param {Array<string|number>} replacements - New values for each entry, by index.
 * @param {object} [opts]
 * @param {boolean} [opts.keepSpacing=true] - Keep " : " spacing.
 * @returns {string}
 */
function replaceWithArrayOrNT(input, replacements, opts = { keepSpacing: true }) {
  const keepSpacing = opts.keepSpacing !== false;
  const parts = input.split(';'); // keeps trailing empty after last ';'
  const endsWithSemicolon = /\;\s*$/.test(input);

  const out = parts.map((segment, i) => {
    if (!segment.trim()) return ''; // skip the trailing empty segment
    const colonIdx = segment.indexOf(':');
    if (colonIdx === -1) return segment.trim(); // no colon → return as-is

    const namePart = segment.slice(0, colonIdx).trim();
    const replacement = (Array.isArray(replacements) && i < replacements.length && replacements[i] != null && replacements[i] !== '')
      ? String(replacements[i])
      : 'NT';

    const glue = keepSpacing ? ' : ' : ':';
    return `${namePart}${glue}${replacement}`;
  }).filter(Boolean);

  return out.join(';') + (endsWithSemicolon ? ';' : '');
}



// const raw = "50 Free Style G04 Boys : 00:37.970;50 Butterfly G04 Boys : 00:43.840;50 Breaststroke G04 Boys : 00:48.810;";

// // 1) Empty array → all become "NT"
// console.log(replaceWithArrayOrNT(raw, []));
// // "50 Free Style G04 Boys : NT;50 Butterfly G04 Boys : NT;50 Breaststroke G04 Boys : NT;"

// // 2) Half-filled array → rest become "NT"
// console.log(replaceWithArrayOrNT(raw, ['37.97s']));
// // "50 Free Style G04 Boys : 37.97s;50 Butterfly G04 Boys : NT;50 Breaststroke G04 Boys : NT;"

// // 3) Fully filled
// console.log(replaceWithArrayOrNT(raw, ['37.97s','43.84s','48.81s']));
// // "50 Free Style G04 Boys : 37.97s;50 Butterfly G04 Boys : 43.84s;50 Breaststroke G04 Boys : 48.81s;"




function formatSwimmingEvent(input) {
    const strokeMap = {
      FS: "Free Style",
      BK: "Back stroke",
      BRS: "Breaststroke",
      FLY: "Butterfly",
      IM: "Individual Medley",
      IMRelay: "Individual Medley Relay",
      FSRelay: "Free Style Relay",
      KB: "Kick Board"
    };
  
    const genderMap = {
      B: "Boys",
      G: "Girls"
    };
  
    const parts = input.split("_");
    const result = [];
  
    for (let i = 0; i < parts.length; i++) {
      let part = parts[i];  
      if (i === 0) {
        if (part!=""){
        result.push(part+ " " ); // Add "M" prefix to first part
        }
      } else if (GroupInfoDict[part]) {
        result.push(part +": (" + GroupInfoDict[part] + ")");
      }

      else if (strokeMap[part]) {
        result.push(strokeMap[part]);
      } else if (genderMap[part]) {
        result.push(genderMap[part]);
      } else if (i === parts.length - 1 && /^\d+$/.test(part)) {
        result.push(`<b> <br> Heat-${part} </b>`);
      } else {
        result.push(part);
      }
    }
  
    return result.join(" ");
  }



function convertToSeconds(timeStr) {
    // Split into minutes:seconds.milliseconds
    const [minSec, millis] = timeStr.split('.');
    const [minutes, seconds] = minSec.split(':').map(Number);
    const milliseconds = Number(millis);

    // Convert to total seconds
    const totalSeconds = (minutes * 60) + seconds + (milliseconds / 1000);

    // Round to 3 decimal places
    return totalSeconds.toFixed(3);
}

function ConvertTime(sec)
{
    ConvertedTime="";
    mins = sec / 60          
    
    sec = sec % 60
    ConvertedTime=  String(parseInt(mins)).padStart(2, '0') + ":" + sec.toFixed(3).padStart(6, '0');

    return ConvertedTime
}
function DisplayQRCode(QRMesage)
{
const qrcode = new QRCode(document.getElementById('qrcode'), {
    text: QRMesage,
    width: 100,
    height: 100,
    colorDark : '#008',
    colorLight : '#ffe',
    correctLevel : QRCode.CorrectLevel.H
  });
}

function GetEejoHostID() {
    urlString= window.location.href;
    // urlString= "http://192.168.0.101:8000/EejoPages/MeetEditor.html"
    HostID = urlString.substring(urlString.indexOf("/")+2, urlString.lastIndexOf(':'));
    return HostID;
  }

function TakeResultScreenShot(docid,imageName) {
//   const canvas = document.getElementById("myCanvas");

html2canvas(document.getElementById(docid)).then(function(canvas) {
    canvas.se
const dataURL = canvas.toDataURL("image/jpeg"); // Or "image/jpeg", "image/webp"

const link = document.createElement("a");
link.download = imageName+".jpeg"; // Or any desired filename
link.href = dataURL;
document.body.appendChild(link);
link.click();
document.body.removeChild(link);
})
}

function WriteLog(mesagetoWrite)
{
    var fso = new ActiveXObject("Scripting.FileSystemObject");
var a = fso.CreateTextFile("c:\\temp\\testfile.txt", true);
a.WriteLine(mesagetoWrite);
a.Close();
}
function downloadFile(filename, content, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a); // Append to body to make it clickable
    a.click();
    document.body.removeChild(a); // Clean up
    
    URL.revokeObjectURL(url); // Release the object URL
}



function createTable(tableName,data) {
  // const data = [
  //   ["Name", "Department", "Location"],
  //   ["Vinay", "HMI", "Bangalore"],
  //   ["Shishir Saxena", "Management", "Bangalore"],
  //   ["Ashish Mangla", "Executive", "Bangalore"]
  // ];

  const table = document.createElement(tableName);

  data.forEach((rowData, rowIndex) => {
    const row = table.insertRow();
    rowData.forEach(cellData => {
      const cell = rowIndex === 0 ? document.createElement("th") : document.createElement("td");
      cell.textContent = cellData;
      row.appendChild(cell);
    });
  });

  document.getElementById("tableContainer").appendChild(table);
}







  async function generatePDF() {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();

    // Example logo (Base64 PNG) � replace with your own
    // const logo = 'data:image/png;base64,'; // truncated
    

    const totalPages = 70;

    for (let i = 1; i <= totalPages; i++) {
      // Add logo to header
      // doc.addImage(logo, 'PNG', 20, 10, 30, 15); // x, y, width, height

      // Add header text
      doc.setFontSize(12);
      doc.text("Event Report � Company Name", 60, 20);

      // Footer
      doc.setFontSize(10);
      doc.text(`Page ${i} of ${totalPages}`, 105, 285, { align: "center" });
      doc.text("Confidential", 20, 285);

      // Page content
      doc.setFontSize(14);
      doc.text(`Content for Page ${i}`, 20, 40);

      if (i < totalPages) doc.addPage();
    }

    doc.save("event-report.pdf");
  }


function showhideDiv(state, id, BusyMsg = "") {
    try {
if (BusyMsg!="")

{
var BusyMsgobj = document.getElementById("BusyMsg");
BusyMsgobj.innerHTML = BusyMsg
}

var e = document.getElementById(id);
if (e)
    {
if (state==true)
{
    e.style.display ='block'
}
else
{
    e.style.display ='none'
}
    }
// e.style.display = (e.style.display == 'block') ? 'none' : 'block';
} catch (error) {
        
}
}

function ToggleDiv(id)
{
  var e = document.getElementById(id);
  if (e)
    {
  e.style.display = (e.style.display == 'block') ? 'none' : 'block';
    }

}
function showhide(id, BusyMsg = "") {
    if (BusyMsg!="")
        {
        var BusyMsgobj = document.getElementById("BusyMsg");
        BusyMsgobj.innerHTML = BusyMsg
        }
    var e = document.getElementById(id);
if (BusyMsg=="")
    {
        e.style.display = 'none'
    }
    else
    e.style.display = 'block'

    
    // e.style.display = (e.style.display == 'block') ? 'none' : 'block';
}


// For Editor Validation

function setTimeinputValidation (Timeinput, Required= true)
{
  if (!Timeinput) {
    console.warn('Timeinput not found:', `${tblSwlistRowcell.id}input`);
  } else {
    // Ensure it's a text input
    if (Timeinput.tagName === 'INPUT') {
      Timeinput.type = 'text';     
  
    // Input mode (numeric keypad on mobile)
    // Property: camelCase inputMode OR use setAttribute
    Timeinput.inputMode = 'numeric';               // preferred
    // Timeinput.setAttribute('inputmode', 'numeric'); // alternative
    Timeinput.setAttribute('aria-required', 'true');
    // Placeholder (string property works)
    Timeinput.placeholder = 'mm:ss.mmm';
  
    // Pattern for mm:ss.mmm (two digits, colon, two digits, dot, three digits)
    Timeinput.pattern = '^\\d{2}:\\d{2}\\.\\d{3}$'; // escape backslashes in JS strings
  
    // Tooltip for native validation
    Timeinput.title = 'Use mm:ss.mmm (e.g., 00:12.345)';
  
    // Autocomplete off
    Timeinput.setAttribute('autocomplete', 'off');
  
    // ARIA: must use setAttribute
    Timeinput.setAttribute('aria-describedby', 'help');
    Timeinput.required = Required;
    
  Timeinput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault(); // Avoid submitting forms on Enter
      Timeinput.value = normalizeValue(Timeinput.value);
      setValidity(Timeinput);
    }
  });

  // Format on blur
  Timeinput.addEventListener('blur', () => {
    Timeinput.value = normalizeValue(Timeinput.value);
    setValidity(Timeinput);
  });

  // Validate while typing/pasting
  Timeinput.addEventListener('Timeinput', () => {
    setValidity(Timeinput);
  });  
}
  }

}



//Time Entry Validator

      // Core format: mm:ss.mmm (string-level validation only)
      const VALID_PATTERN = /^\d{2}:\d{2}\.\d{3}$/;

      // Helpers to clamp ranges
      function clampSeconds(ss) {
        if (isNaN(ss)) return 0;
        return Math.min(59, Math.max(0, ss));
      }
      function clampMillis(ms) {
        if (isNaN(ms)) return 0;
        return Math.min(999, Math.max(0, ms));
      }
      function clampMinutes(mm) {
        // If you want to enforce a maximum minutes, adjust here.
        if (isNaN(mm)) return 0;
        return Math.max(0, mm);
      }

      function normalizeValue(raw) {
        if (!raw) return '';
        const value = raw.trim();

        // Already valid, but we still enforce ranges
        if (VALID_PATTERN.test(value)) {
          const [mm, ssMs] = value.split(':');
          const [ss, ms] = ssMs.split('.');
          const mmN = clampMinutes(parseInt(mm, 10));
          const ssN = clampSeconds(parseInt(ss, 10));
          const msN = clampMillis(parseInt(ms, 10));
          return `${String(mmN).padStart(2, '0')}:${String(ssN).padStart(2, '0')}.${String(msN).padStart(3, '0')}`;
        }

        // 1) seconds.millis (e.g., "12.345", "5.3", "75.999")
        //    NOTE: We keep the "carry into minutes" behavior here.
        const secMs = /^(\d+)(?:\.(\d{1,3}))?$/.exec(value);
        if (secMs) {
          let secs = parseInt(secMs[1], 10);
          let ms = clampMillis(parseInt((secMs[2] || '0').padEnd(3, '0').slice(0, 3), 10));

          const mm = clampMinutes(Math.floor(secs / 60));
          const ss = clampSeconds(secs % 60);

          return `${String(mm).padStart(2, '0')}:${String(ss).padStart(2, '0')}.${String(ms).padStart(3, '0')}`;
        }

        // 2) m:s.ms (e.g., "1:2.3", "03:5.12")
        const msMixed = /^(\d{1,2}):(\d{1,2})\.(\d{1,3})$/.exec(value);
        if (msMixed) {
          const mm = clampMinutes(parseInt(msMixed[1], 10));
          const ss = clampSeconds(parseInt(msMixed[2], 10));
          const ms = clampMillis(parseInt(msMixed[3].padEnd(3, '0').slice(0, 3), 10));
          return `${String(mm).padStart(2, '0')}:${String(ss).padStart(2, '0')}.${String(ms).padStart(3, '0')}`;
        }

        // 3) m.s.ms (e.g., "1.2.3", "01:20.300")
        const msMixed1 = /^(\d{1,2})\.(\d{1,2})\.(\d{1,3})$/.exec(value);
        if (msMixed1) {
          const mm = clampMinutes(parseInt(msMixed1[1], 10));
          const ss = clampSeconds(parseInt(msMixed1[2], 10));
          const ms = clampMillis(parseInt(msMixed1[3].padEnd(3, '0').slice(0, 3), 10));
          return `${String(mm).padStart(2, '0')}:${String(ss).padStart(2, '0')}.${String(ms).padStart(3, '0')}`;
        }

        // 2a) m:s (no milliseconds) -> pad and add .000 (e.g., "1:2" -> "01:02.000")
        const msMissing = /^(\d{1,2}):(\d{1,2})$/.exec(value);
        if (msMissing) {
          const mm = clampMinutes(parseInt(msMissing[1], 10));
          const ss = clampSeconds(parseInt(msMissing[2], 10));
          return `${String(mm).padStart(2, '0')}:${String(ss).padStart(2, '0')}.000`;
        }

        // 3) wrong separator: mm:ss:mmm (colon before ms) or dot/colon mix
        const wrongSep = /^(\d{1,2}):(\d{1,2}):\.$/.exec(value);
        if (wrongSep) {
          const mm = clampMinutes(parseInt(wrongSep[1], 10));
          const ss = clampSeconds(parseInt(wrongSep[2], 10));
          const ms = clampMillis(parseInt(wrongSep[3].padEnd(3, '0').slice(0, 3), 10));
          return `${String(mm).padStart(2, '0')}:${String(ss).padStart(2, '0')}.${String(ms).padStart(3, '0')}`;
        }

        // 4) digits only (length 5–7): assume mm ss mmm -> "0123456" => 01:23.456
        if (/^\d{5,7}$/.test(value)) {
          const d = value.padStart(7, '0');
          const mm = clampMinutes(parseInt(d.slice(0, -5), 10));
          const ss = clampSeconds(parseInt(d.slice(-5, -3), 10));
          const ms = clampMillis(parseInt(d.slice(-3), 10));
          return `${String(mm).padStart(2, '0')}:${String(ss).padStart(2, '0')}.${String(ms).padStart(3, '0')}`;
        }

        // Can't parse: return original so validation can show error
        return value;
      }

      //      // String-level + range-level validity
      function setValidity(el) {
        const v = el.value.trim();
        if (v === '') {
          el.setCustomValidity('');
          return;
        }
        if (!VALID_PATTERN.test(v)) {
          el.setCustomValidity('Use mm:ss.mmm (e.g., 00:12.345)');
          return;
        }
        // Range check: mm>=0, 0<=ss<=59, 0<=ms<=999
        const [mmStr, ssMsStr] = v.split(':');
        const [ssStr, msStr] = ssMsStr.split('.');
        const mm = parseInt(mmStr, 10);
        const ss = parseInt(ssStr, 10);
        const ms = parseInt(msStr, 10);

        if (isNaN(mm) || isNaN(ss) || isNaN(ms)) {
          el.setCustomValidity('Use mm:ss.mmm (e.g., 00:12.345)');
          return;
        }
        if (mm < 0) {
          el.setCustomValidity('Minutes cannot be negative.');
          return;
        }
        if (ss < 0 || ss > 59) {
          el.setCustomValidity('Seconds must be between 00 and 59.');
          return;
        }
        if (ms < 0 || ms > 999) {
          el.setCustomValidity('Milliseconds must be between 000 and 999.');
          return;
        }
        el.setCustomValidity('');
      }


    // Form Navigation Related.

    
  // Configuration: set to true to wrap from last to first row (and vice versa)
  const WRAP_AROUND = false;

  // Focusable elements we support
  const focusablesSelector = 'input:not([disabled]):not([type="hidden"]), textarea:not([disabled]), select:not([disabled]), [contenteditable="true"]';

  // Utility: is element focusable and visible
  function isFocusable(el) {
    if (!el) return false;
    const disabled = el.disabled || el.getAttribute('disabled') !== null;
    // offsetParent === null covers display:none and visibility hidden ancestors
    const hidden = el.hidden || el.offsetParent === null;
    const tabOk = el.tabIndex !== -1;
    return !disabled && !hidden && tabOk;
  }

  // Get the current cell and its column index
  function getCellAndColIndex(el) {
    const cell = el.closest('td, th');
    if (!cell) return { cell: null, colIndex: -1 };
    const row = cell.parentElement;
    // Some rows may have non-cell children; filter by tagName
    const cells = Array.from(row.children).filter(c => c.tagName === 'TD' || c.tagName === 'TH');
    const colIndex = cells.indexOf(cell);
    return { cell, colIndex };
  }

  // Find a focusable target within the given row and column index
  function findFocusableInRow(row, colIndex) {
    const cells = Array.from(row.children).filter(c => c.tagName === 'TD' || c.tagName === 'TH');
    const targetCell = cells[colIndex];
    if (!targetCell) return null;

    // Prefer the first focusable element in that cell
    const candidate = targetCell.querySelector(focusablesSelector);
    return isFocusable(candidate) ? candidate : null;
  }

  // Find body rows (ignore thead/tfoot)
  function getBodyRows(table) {
    // Use all TBODY sections (supports multiple TBODYs)
    const bodies = table.tBodies.length ? Array.from(table.tBodies) : [table.querySelector('tbody')].filter(Boolean);
    return bodies.flatMap(tb => Array.from(tb.rows));
  }


  function SetTableNavigation(table)
  {
    // Keydown handler: move focus in same column
  table.addEventListener('keydown', function (e) {
    const current = document.activeElement;
    if (!current || !table.contains(current)) return;

    const isDown = e.key === 'ArrowDown';
    const isUp = e.key === 'ArrowUp';
    const isHome = e.key === 'Home';
    const isEnd = e.key === 'End';

    // Only handle our keys
    if (!isDown && !isUp && !isHome && !isEnd) return;

    // Stop the page from scrolling on Arrow Up/Down
    e.preventDefault();

    const { colIndex } = getCellAndColIndex(current);
    if (colIndex < 0) return;

    const rowEl = current.closest('tr');
    const bodyRows = getBodyRows(table);
    const rowIndex = bodyRows.indexOf(rowEl);
    if (rowIndex === -1) return;

    let targetIndex = rowIndex;

    if (isHome) {
      targetIndex = 0;
    } else if (isEnd) {
      targetIndex = bodyRows.length - 1;
    } else if (isDown) {
      targetIndex = rowIndex + 1;
    } else if (isUp) {
      targetIndex = rowIndex - 1;
    }

    // Handle wrap-around if enabled
    if (WRAP_AROUND) {
      if (targetIndex < 0) targetIndex = bodyRows.length - 1;
      if (targetIndex >= bodyRows.length) targetIndex = 0;
    }

    // Move stepwise until we find a focusable target in same column
    while (targetIndex >= 0 && targetIndex < bodyRows.length) {
      const target = findFocusableInRow(bodyRows[targetIndex], colIndex);
      if (target) {
        target.focus();
        return;
      }
      // If the cell in that row is not focusable, keep going
      if (isDown || isHome) targetIndex++;
      else if (isUp || isEnd) targetIndex--;
    }
    // If we get here, no target found; do nothing.
  }, { capture: true });

  // Optional: make entire cell clickable to focus the first field inside
  table.addEventListener('click', (e) => {
    const cell = e.target.closest('td, th');
    if (!cell || !table.contains(cell)) return;
    const el = cell.querySelector(focusablesSelector);
    if (isFocusable(el)) {
      el.focus();
    }
  });
  }
