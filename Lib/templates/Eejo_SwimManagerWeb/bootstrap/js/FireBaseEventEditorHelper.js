let NumberofEventsperSw = 3;
let Meetdteails
function ReloadData(datatoRefresh) {
  NumberofEventsper = document.getElementById("txt_NoOF_Events");
  if (NumberofEventsper && NumberofEventsper.value != 0) {
    NumberofEventsperSw = parseInt(NumberofEventsper.value);
  }


  switch (datatoRefresh) {

    case "SwDetails":
      GenerateSwimmersTable(MeetUpdatedData.SwimmerDetails)
      break;
    case "Groups":
      tblGroups = document.getElementById('tblGroups');
      Availablegroups.length = 0;
      for (let i = 1; i < tblGroups.rows.length; i++) {
        rowindex = tblGroups.rows[i].id.replace("tblgroupRow", "");
        GroupName = document.getElementById("GrpNamecell" + rowindex);
        if (GroupName.value != "") {
          Availablegroups.push(GroupName.value);
        }
      }

      tblEvents = document.getElementById('tblEvents');
      for (let i = 1; i < tblEvents.rows.length; i++) {
        rowindex = tblEvents.rows[i].id.replace("tblEventsRow", "");
        EventGroupcellSelector = document.getElementById("EventGroupcell" + rowindex);
        var selectedGroup = EventGroupcellSelector.value;
        EventGroupcellSelector.innerHTML = "";
        Availablegroups.forEach(Group => {
          var newGroup = document.createElement("option"); // Create a new option            
          newGroup.value = Group; // Set the value
          newGroup.text = Group; // Set the text        
          EventGroupcellSelector.add(newGroup);
        });
        EventGroupcellSelector.value = selectedGroup;
      }
      break;

    case "Heats":
      //GenerateHeatList
      let Heatcounter = 0;
      let HeatList = [];

      tblSwimmers = document.getElementById('tblSwDetails');
      SwimmerDetailsArray = [];
      for (let i = 1; i < tblSwimmers.rows.length; i++) {
        rowindex = tblSwimmers.rows[i].id.replace("tblSwimmersRow", "")
        tblSwSelectedEvents = document.getElementById('tblSwSelectedEvents' + rowindex);
        for (let j = 0; j < tblSwSelectedEvents.rows.length - 1; j++) {
          var SwimmersAvailablecellChecked = document.getElementById("SwimmersAvailablecell" + rowindex + "_" + j).checked;
          if (SwimmersAvailablecellChecked) {
            SwimmersNamecell = document.getElementById("SwimmersNamecell" + rowindex).value;
            var SwimmersEventBestTime = document.getElementById("SwimmersEventBestTime" + rowindex + "_" + j).value;
            var EventSelector = document.getElementById("SwimmersEventSelector" + rowindex + "_" + j);
            SwimmerDetailsArray.push({ 'SwName': SwimmersNamecell, 'Swevents': EventSelector.value, 'SwimmersEventBestTime': parseFloat(SwimmersEventBestTime) })
          }
        }
      }
      //Meetdteails.Boards

      // AvailableEvents.forEach(eventname => {
      for (let EventCounter = 0; EventCounter < AvailableEvents.length; EventCounter++) {
        eventname = AvailableEvents[EventCounter];
        SwimmersList = [];

        SwimmerDetailsArray.forEach(SwimerDetail => {
          if (SwimerDetail.Swevents == eventname) {
            SwimmersList.push(SwimerDetail);
          }
        });
        //Sort SwimmersList.

        for (let i = 0; i < SwimmersList.length - 1; i++) {
          for (let j = 0; j < SwimmersList.length - i - 1; j++) {
            if (SwimmersList[j].SwimmersEventBestTime > SwimmersList[j + 1].SwimmersEventBestTime) {
              let temp = SwimmersList[j];
              SwimmersList[j] = SwimmersList[j + 1];
              SwimmersList[j + 1] = temp;
            }
          }
        }

        BoardCount = parseInt(document.getElementById("tblMeet_txtBoards").value);
        let NoofHeats = Math.ceil(SwimmersList.length / BoardCount);
        //i=HeatList.length ;
        for (let i = 0; i < NoofHeats; i++) {
          Boardinfo = []
          HeatDetails = { 'ID': eventname + "_" + (i + 1), 'Boardinfo': Boardinfo };
          HeatList.push(HeatDetails);
        }
        let j = 0;

        for (let i = 0; i < SwimmersList.length; i++) {

          if (j == NoofHeats) {
            j = 0
          }

          HeatList[Heatcounter + j].Boardinfo.push({ 'BoardID': (Boardinfo.length), 'BoardStatus': 0, 'SwimStatus': 0, 'SwimTimings': 0, 'SwimerID': SwimmersList[i].SwName, 'SwimerName': SwimmersList[i].SwName });
          j++;


        }
        Heatcounter = Heatcounter + NoofHeats;
      }
      HeatList.forEach(heatlst => {

        // function customSortArray(N, k) {
        // Create the array [N+1, N+2, ..., N+k]
        const arr = heatlst.Boardinfo;
        let k = heatlst.Boardinfo.length;

        // Get indices for the first part: odd indices from the end (in reverse)
        const firstPartIndices = [];
        for (let i = k - 2; i >= 0; i -= 2) {
          firstPartIndices.push(i);
        }

        // Get the remaining indices
        const secondPartIndices = [];
        for (let i = 0; i < k; i++) {
          if (!firstPartIndices.includes(i)) {
            secondPartIndices.push(i);
          }
        }

        // Build the sorted array
        const sortedArray = [...firstPartIndices, ...secondPartIndices].map(i => arr[i]);

        for (let i = 0; i < sortedArray.length; i++) {
          sortedArray[i].BoardID = i;
        }
        heatlst.Boardinfo = sortedArray;


        //     return sortedArray;
        // }

        // // Example usage:
        // const result = customSortArray(100, 10);
        // console.log(result); // Output: [109, 107, 105, 103, 101, 102, 104, 106, 108, 110]
        console.log(heatlst);


      });

      GenerateHeatDetailsTable(HeatList)

      break;

    case "Events":
      tblEvents = document.getElementById('tblEvents');
      AvailableEvents.length = 0;
      for (let i = 1; i < tblEvents.rows.length; i++) {
        rowindex = tblEvents.rows[i].id.replace("tblEventsRow", "");
        EventName = document.getElementById("EventDistencecell" + rowindex).value + "_" +
          document.getElementById("EventStrokecell" + rowindex).value + "_" +
          document.getElementById("EventGroupcell" + rowindex).value + "_" +
          document.getElementById("EventGendercell" + rowindex).value;

        AvailableEvents.push(EventName);
      }

      tblSwDetails = document.getElementById('tblSwDetails');
      for (let i = 1; i < tblSwDetails.rows.length; i++) {
        rowindex = tblSwDetails.rows[i].id.replace("tblSwimmersRow", "");
        tblSwSelectedEvents = document.getElementById("tblSwSelectedEvents" + rowindex);

        if (tblSwSelectedEvents != null) {
          for (let j = 0; j <= tblSwSelectedEvents.rows.length; j++) {
            var SwimmersEventSelector = document.getElementById("SwimmersEventSelector" + rowindex + "_" + j);
            if (SwimmersEventSelector != null) {
              var selectedEvent = SwimmersEventSelector.value;
              SwimmersEventSelector.options.length = 0;
              AvailableEvents.forEach(SwEvent => {
                var newEvent = document.createElement("option"); // Create a new option            
                newEvent.value = SwEvent; // Set the value
                newEvent.text = SwEvent; // Set the text        
                SwimmersEventSelector.add(newEvent);
              });
              SwimmersEventSelector.value = selectedEvent;
            }
          }
        }
      }

      break;

    default:
      break;
  }
}
function AddGroupRow(index, GroupDetail) {
  // var index = 100;
  tblGroups = document.getElementById('tblGroups');
  var tblgroupRow = tblGroups.insertRow()
  tblgroupRow.draggable = true;
  tblgroupRow.ondragstart = function () { startDrag() };
  tblgroupRow.ondragover = function () { dragover() };

  tblgroupRow.id = "tblgroupRow" + index;
  GrpCheckcell = tblgroupRow.insertCell();

  GrpCheckcell.innerHTML = "<input  type='Checkbox' id ='GrpCheckcell" + index + "'>";
  var GrpCheckcellchkbox = document.getElementById('GrpCheckcell' + index)
  GrpCheckcellchkbox.addEventListener("change",
    function () {

      if (GrpCheckcellchkbox.checked == true) {
        GroupsSlectedRows.push(GrpCheckcellchkbox.id.replace("GrpCheckcell", ""));
      }
      else {
        GroupsSlectedRows.pop(GrpCheckcellchkbox.id.replace("GrpCheckcell", ""))
      }

    });

  Grpslnocell = tblgroupRow.insertCell();
  Grpslnocell.innerHTML = (index + 1);

  var GrpNamecell = tblgroupRow.insertCell();
  GrpNamecell.innerHTML = "<input class='form-control' id ='GrpNamecell" + index + "'>";
  document.getElementById('GrpNamecell' + index).value = GroupDetail.GroupName;

  var GrpFromcell = tblgroupRow.insertCell();
  GrpFromcell.innerHTML = "<input class='form-control' type='date' id ='GrpFromcellvar" + index + "'>";
  document.getElementById('GrpFromcellvar' + index).value = GroupDetail.FromDate;

  var GrpTocell = tblgroupRow.insertCell();
  GrpTocell.innerHTML = "<input class='form-control' type='date' id ='GrpTocellvar" + index + "'>";
  document.getElementById('GrpTocellvar' + index).value = GroupDetail.ToDate;

}


function AddSwimmerRow(index, SwDetails) {

  // ClearTable('tblSwDetails');

  tblSwimmers = document.getElementById('tblSwDetails');

  // for (let i = 0; i < SwimmerDetails.length; i++) {
  var tblSwimmersRow = tblSwimmers.insertRow()
  tblSwimmersRow.setAttribute('draggable', 'true');
  tblSwimmersRow.ondragstart = function () { startDrag() };
  tblSwimmersRow.ondragover = function () { dragover() };

  SwimmersCheckboxcell = tblSwimmersRow.insertCell();
  SwimmersCheckboxcell.innerHTML = "<input type='Checkbox' id ='SwimmersCheckboxcell" + index + "'>";
  document.getElementById('SwimmersCheckboxcell' + index).checked = true;


  SwimmersCheckboxcell.addEventListener("change",
    function () {
      var Checkcellchkbox = document.getElementById('SwimmersCheckboxcell' + index);

      tblSwSelectedEvent = document.getElementById("tblSwSelectedEvents" + index);
      for (let j = 0; j < tblSwSelectedEvent.rows.length - 1; j++) {
        document.getElementById("SwimmersAvailablecell" + index + "_" + j).checked = Checkcellchkbox.checked;
      }

      if (Checkcellchkbox.checked == true) {
        SwDetailsSlectedRows.push(Checkcellchkbox.id.replace("SwimmersCheckboxcell", ""));
      }
      else {
        SwDetailsSlectedRows.pop(Checkcellchkbox.id.replace("SwimmersCheckboxcell", ""))
      }

    });


  tblSwimmersRow.id = "tblSwimmersRow" + index;
  Swimmersslnocell = tblSwimmersRow.insertCell();
  Swimmersslnocell.innerHTML = (index + 1);

  SwimmersNamecell = tblSwimmersRow.insertCell();
  SwimmersNamecell.innerHTML = "<input class='form-control' id ='SwimmersNamecell" + index + "'>";
  document.getElementById("SwimmersNamecell" + index).value = SwDetails.Name;


  var SwimmerGroupCell = tblSwimmersRow.insertCell();
  SwimmerGroupCell.innerHTML = "<input class='form-control' id ='SwimmerGroupCell" + index + "'>";


  var SwimmerClubCell = tblSwimmersRow.insertCell();
  SwimmerClubCell.innerHTML = "<input class='form-control' type='text' id ='SwimmerClubCell" + index + "'>";

  //document.getElementById("SwimmerGroupCell" + i).value = new Date(DOB.substring(0, 4),DOB.substring(4, 6),DOB.substring(6, 8));
  document.getElementById("SwimmerGroupCell" + index).value = SwDetails.Group;

  var tblSwSelectedEvents = document.createElement("TABLE");
  tblSwSelectedEvents.id = "tblSwSelectedEvents" + index;

  var header = tblSwSelectedEvents.createTHead();

  var row = header.insertRow();
  var cell = row.insertCell();
  cell.innerHTML = "<b> Event Name. <b> ";
  var cell = row.insertCell();
  cell.innerHTML = "<b> Best Timeings <b>";
  var cell = row.insertCell();
  cell.innerHTML = "<b>  Available  <b>";
  var cell = row.insertCell();
  cell.innerHTML = "<button onclick=AppendRow('" + tblSwSelectedEvents.id + "','tblSwimmersRow')><i class='fa fa-fw fa-plus'></i></button> <button onclick=DeleteRows('" + tblSwSelectedEvents.id + "','tblSwSelectedEvents','tblSwimmersRow')><i class='fa fa-fw fa-minus'></i></button>"


  var SwimmersEventcell = tblSwimmersRow.insertCell();
  SwimmersEventcell.appendChild(tblSwSelectedEvents);
  for (let j = 0; j < NumberofEventsperSw; j++) {
    AddSwEventRow(tblSwSelectedEvents.id);
  }

}


function AddSwEventRow(EventTableName) {
  index = EventTableName.replace("tblSwSelectedEvents", "");
  tblSwSelectedEvents = document.getElementById(EventTableName)
  j = tblSwSelectedEvents.rows.length;
  // j=
  // for (let j = 0; j <NumberofEventsperSw; j++) {
  var tblSwlistRow = tblSwSelectedEvents.insertRow();
  SwimmersEventSelector = tblSwlistRow.insertCell();
  SwimmersEventSelector.innerHTML = "<select id ='SwimmersEventSelector" + index + "_" + j + "'>";
  var EventSelector = document.getElementById("SwimmersEventSelector" + index + "_" + j);
  if (AvailableEvents.length > 0 && EventSelector != null) {
    AvailableEvents.forEach(SwEvent => {
      var newSwEvent = document.createElement("option"); // Create a new option            
      newSwEvent.value = SwEvent; // Set the value
      newSwEvent.text = SwEvent; // Set the text        
      EventSelector.add(newSwEvent);
    });
  }

  document.getElementById("SwimmersEventSelector" + index + "_" + j).value = "";
  SwimmersEventBestTime = tblSwlistRow.insertCell();
  SwimmersEventBestTime.innerHTML = "<input class='form-control' id ='SwimmersEventBestTime" + index + "_" + j + "'>";
  document.getElementById("SwimmersEventBestTime" + index + "_" + j).value = "00:00:00";

  SwimmersAvailablecell = tblSwlistRow.insertCell();
  SwimmersAvailablecell.innerHTML = "<input  type='Checkbox' id ='SwimmersAvailablecell" + index + "_" + j + "'>";
  document.getElementById("SwimmersAvailablecell" + index + "_" + j).checked = true;
  // }
}

function AppendRow(TableName, idprefix) {
  var grptab = document.getElementById(TableName);
  var Rowindextoadd = 0;
  for (let i = 0; i <= document.getElementById(TableName).rows.length; i++) {
    if (!grptab.rows[idprefix + i]) {
      Rowindextoadd = i;
      break;
    }
  }

  switch (TableName) {
    case "tblSwDetails":
      SwDetails = { 'Name': "", 'Group': "" }
      AddSwimmerRow(Rowindextoadd, SwDetails)
      break;

    case "tblGroups":
      GroupDetails = { 'GroupName': "", 'Year': "" }
      AddGroupRow(Rowindextoadd, GroupDetails)
      break;

    case "tblEvents":
      Swevent = " _ _ _ ";
      // Availablegroups= ["G"];
      AddEventRow(Rowindextoadd, Swevent)
      break;


    case "tblHeatDetails":
      Boardinfo = [];
      // for (let i = 0; i <= number (MeetDataFirebase.Boards); i++) {
      Boardinfo.push({ 'BoardID': 0, 'BoardStatus': 0, 'SwimStatus': 0, 'SwimTimings': 0, 'SwimerID': " ", 'SwimerName': " " });

      HeatDetails = { 'ID': "", 'Boardinfo': Boardinfo }
      AddHeatRow(Rowindextoadd, HeatDetails)
      break;

    default:
      if (TableName.includes("tblSwSelectedEvents")) {
        AddSwEventRow(TableName);
      }

      break;
  }
}
// May not be required, ti add Heat as its calculated out of Sw name & Event List

function formatSwimmingEvent(input) {
  const strokeMap = {
    FS: "Free Style",
    BK: "Back stroke",
    BRS: "Breaststroke",
    FLY: "Butterfly",
    IM: "Individual Medley",
    IMRelay: "IMRelay",
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
      result.push(part+ " M" ); // Add "M" prefix to first part
    } else if (strokeMap[part]) {
      result.push(strokeMap[part]);
    } else if (genderMap[part]) {
      result.push(genderMap[part]);
    } else if (i === parts.length - 1 && /^\d+$/.test(part)) {
      result.push(`Heat-${part}`);
    } else {
      result.push(part);
    }
  }

  return result.join(" ");
}


function AddHeatRow(index, Heat) {
  tblHeatDetails = document.getElementById('tblHeatDetails');
  var tblHeatDetailsRow = tblHeatDetails.insertRow()
  tblHeatDetailsRow.id = "tblHeatDetailsRow" + index;
  HeatNumbercell = tblHeatDetailsRow.insertCell();
  HeatNumbercell.innerHTML =  formatSwimmingEvent(Heat.ID);

  HeatNamecell = tblHeatDetailsRow.insertCell();
  HeatNamecell.innerHTML = "<input  class='form-control' id ='HeatNamecell" + index + "'>";
  HeatNamecelltxt = document.getElementById('HeatNamecell' + index);
  HeatNamecelltxt.value = Heat.ID;
  
  

  var tblSwlist = document.createElement("TABLE");
  tblSwlist.id = "tblSwlist" + index;

  var header = tblSwlist.createTHead();
  var row = header.insertRow();
  var cell = row.insertCell();
  cell.innerHTML = "<b>SwimerID.<b>";
  var cell = row.insertCell();
  cell.innerHTML = "<b>Name<b>";
  var cell = row.insertCell();
  cell.innerHTML = "<b>SwimStatus<b>";
  var cell = row.insertCell();
  cell.innerHTML = "<b>SwimTimeings<b>";
  for (let j = 0; j < Heat.Boardinfo.length; j++) {
    var tblSwlistRow = tblSwlist.insertRow();
    tblSwlistRowcell = tblSwlistRow.insertCell()
    tblSwlistRowcell.innerHTML = Heat.Boardinfo[j].SwimerID;
    tblSwlistRowcell = tblSwlistRow.insertCell()
    tblSwlistRowcell.innerHTML = Heat.Boardinfo[j].SwimerName;
    tblSwlistRowcell = tblSwlistRow.insertCell()
    tblSwlistRowcell.innerHTML = Heat.Boardinfo[j].SwimStatus;
    tblSwlistRowcell = tblSwlistRow.insertCell()
    tblSwlistRowcell.innerHTML = "<input class='form-control'value="+ ConvertTime(Heat.Boardinfo[j].SwimTimings)+">" ;
    tblSwlistRow.setAttribute('draggable', 'true');
    tblSwlistRow.ondragstart = function () { startDrag() };
    tblSwlistRow.ondragover = function () { dragover() };
  }

  var HeatSwimmerListcell = tblHeatDetailsRow.insertCell();
  HeatSwimmerListcell.id = 'SwimmersListcell' + index
  HeatSwimmerListcell.appendChild(tblSwlist);

}

function AddEventRow(index, Event) {
  tblEvents = document.getElementById('tblEvents');

  var eventID = Event.split("_");
  var StrokeTyp = eventID[1];
  var Distence = eventID[0];
  var Group = eventID[2];
  var Gender = eventID[3];


  var tblEventsRow = tblEvents.insertRow()
  tblEventsRow.id = "tblEventsRow" + index;
  tblEventsRow.setAttribute('draggable', 'true');
  tblEventsRow.ondragstart = function () { startDrag() };
  tblEventsRow.ondragover = function () { dragover() };


  EventCheckcell = tblEventsRow.insertCell();
  EventCheckcell.innerHTML = "<input type='Checkbox' id ='EventCheckcell" + index + "'>";
  Eventslnocell = tblEventsRow.insertCell();
  Eventslnocell.innerHTML = (index + 1);

  var EventCheckcell = document.getElementById('EventCheckcell' + index)
  EventCheckcell.addEventListener("change",
    function () {

      if (EventCheckcell.checked == true) {
        EventsSlectedRows.push(EventCheckcell.id.replace("EventCheckcell", ""));
      }
      else {
        EventsSlectedRows.pop(EventCheckcell.id.replace("EventCheckcell", ""))
      }

    });

  EventGroupcell = tblEventsRow.insertCell();
  EventGroupcell.innerHTML = "<select id ='EventGroupcell" + index + "'>";

  EventGroupcellSelector = document.getElementById('EventGroupcell' + index);
  Availablegroups.forEach(Group => {
    var newGroup = document.createElement("option"); // Create a new option            
    newGroup.value = Group; // Set the value
    newGroup.text = Group; // Set the text        
    EventGroupcellSelector.add(newGroup);
  });
  EventGroupcellSelector.value = Group;

  EventGendercell = tblEventsRow.insertCell();
  EventGendercell.innerHTML = "<select id ='EventGendercell" + index + "'>";
  EventGendercellSelect = document.getElementById('EventGendercell' + index);
  genderArray.forEach(swGender => {
    var newGroup = document.createElement("option"); // Create a new option            
    newGroup.value = swGender; // Set the value
    newGroup.text = swGender; // Set the text        
    EventGendercellSelect.add(newGroup);
  });
  EventGendercellSelect.value = Gender;

  EventStrokecell = tblEventsRow.insertCell();
  EventStrokecell.innerHTML = "<select id ='EventStrokecell" + index + "'>";
  EventStrokecellSelect = document.getElementById('EventStrokecell' + index);
  strokearray.forEach(stroke => {
    var newStroke = document.createElement("option"); // Create a new option            
    newStroke.value = stroke; // Set the value
    newStroke.text = stroke; // Set the text        
    EventStrokecellSelect.add(newStroke);
  });
  EventStrokecellSelect.value = StrokeTyp;


  EventDistencecell = tblEventsRow.insertCell();
  EventDistencecell.innerHTML = "<select id ='EventDistencecell" + index + "'>";
  EventDistencecellSelect = document.getElementById('EventDistencecell' + index);

  distencearray.forEach(dis => {
    var newGroup = document.createElement("option"); // Create a new option            
    newGroup.value = dis; // Set the value
    newGroup.text = dis; // Set the text        
    EventDistencecellSelect.add(newGroup);
  });
  EventDistencecellSelect.value = Distence;
}

function DeleteRows(TableName, idprefixChkbox, RowPrefix, SlectedRows = []) {
  var retryCount = 0;
  var tbl = document.getElementById(TableName)
  if (tbl) {
    for (let i = 1; i < tbl.rows.length; i++) {
      {
        let tblindex = tbl.rows[i].id.replace(RowPrefix, "");
        var selectedchkbox = document.getElementById(idprefixChkbox + tblindex)
        if (selectedchkbox)
          if (selectedchkbox.checked) {
            SlectedRows.push(tblindex);
          }
      }
    }

    while (SlectedRows.length != 0 && retryCount <= 5) {
      retryCount = retryCount + 1;
      for (let i = 0; i < SlectedRows.length; i++) {
        var ss = document.getElementById(TableName).deleteRow(document.getElementById(RowPrefix + SlectedRows[i]).rowIndex);
        var index = SlectedRows.indexOf(SlectedRows[i]);
        if (index !== -1) {
          SlectedRows.splice(index, 1);
        }
      }
    }
  }
}

function GenerateMeetTable(MeetName, MeetAddress, MeetDate, Boards) {
  tblMeet = document.getElementById('tblMeet');
  tblMeet.innerHTML = "";

  var tblMeetRow = tblMeet.insertRow();
  tblcell = tblMeetRow.insertCell();
  tblcell.innerHTML = "<b>Meet Name:</b> ";

  tblcell = tblMeetRow.insertCell();
  tblcell.innerHTML = "<input class='form-control' id ='tblMeet_MeetName'>";
  var tblMeet_MeetName = document.getElementById("tblMeet_MeetName");
  tblMeet_MeetName.value = MeetName;

  var tblMeetRow = tblMeet.insertRow();
  tblcell = tblMeetRow.insertCell();
  tblcell.innerHTML = " <b>Meet Address:</b> ";

  tblcell = tblMeetRow.insertCell();
  tblcell.innerHTML = "<input  class='form-control' id ='tblMeet_MeetAddress'>";
  var tblMeet_MeetAddress = document.getElementById("tblMeet_MeetAddress");
  tblMeet_MeetAddress.value = MeetAddress;

  var tblMeetRow = tblMeet.insertRow();
  tblcell = tblMeetRow.insertCell();
  tblcell.innerHTML = " <b>Meet Date:</b> ";

  tblcell = tblMeetRow.insertCell();
  tblcell.innerHTML = "<input  class='form-control' type='date' id ='tblMeetDate'>";
  var tblMeetDate = document.getElementById("tblMeetDate");
  tblMeetDate.value = MeetDate;

  var tblMeetRow = tblMeet.insertRow();
  tblcell = tblMeetRow.insertCell();
  tblcell.innerHTML = " <b>Boards:</b> ";


  tblcell = tblMeetRow.insertCell();
  tblcell.innerHTML = "<input class='form-control' id ='tblMeet_txtBoards'>";

  var tblMeet_txtBoards = document.getElementById("tblMeet_txtBoards");
  tblMeet_txtBoards.value = Boards;


  var tblMeetRow = tblMeet.insertRow();
  tblcell = tblMeetRow.insertCell();
  tblcell.innerHTML = " <b>No OF Events:</b> ";


  tblcell = tblMeetRow.insertCell();
  tblcell.innerHTML = "<input class='form-control' id ='txt_NoOF_Events'>";

  // var tblMeet_txtBoards = document.getElementById("txt_NoOF_Events");
  // tblMeet_txtBoards.value = Boards;
}

function GenerateGroupTable(GroupDetails) {
  ClearTable('tblGroups');
  for (let i = 0; i < GroupDetails.length; i++) {
    AddGroupRow(i, GroupDetails[i]);
  }
}

function GenerateEventTable(Events) {
  ClearTable('tblEvents');
  for (let i = 0; i < Events.length; i++) {
    AddEventRow(i, Events[i]);
  }
}

function SelectAllRows(SelectAllCheckID, TblName, ChkBoxID) {

  CheckStatus = document.getElementById(SelectAllCheckID).checked;
  tbltoselect = document.getElementById(TblName);
  // let Selectedinex=[];

  for (let index = 0; index < tbltoselect.rows.length - 1; index++) {

    var chkbx = document.getElementById(ChkBoxID + index);
    if (chkbx) {
      chkbx.checked = CheckStatus;
    }
  }
}

function GenerateSwimmersTable(SwimmerDetails) {
  ClearTable('tblSwDetails');
  tblSwimmers = document.getElementById('tblSwDetails');
  SwKeys = Object.keys(SwimmerDetails);
  // NumberofEventsperSw = SwimmerDetails[SwKeys[0]].Events.count
  for (let i = 0; i < SwKeys.length; i++) {
    var tblSwimmersRow = tblSwimmers.insertRow()
    tblSwimmersRow.setAttribute('draggable', 'true');
    tblSwimmersRow.ondragstart = function () { startDrag() };
    tblSwimmersRow.ondragover = function () { dragover() };

    SwimmersCheckboxcell = tblSwimmersRow.insertCell();
    SwimmersCheckboxcell.innerHTML = "<input type='Checkbox' id ='SwimmersCheckboxcell" + i + "'>";
    document.getElementById('SwimmersCheckboxcell' + i).checked = true;

    SwimmersCheckboxcell.addEventListener("change",
      function () {
        var Checkcellchkbox = document.getElementById('SwimmersCheckboxcell' + i);

        tblSwSelectedEvent = document.getElementById("tblSwSelectedEvents" + i);
        for (let j = 0; j < tblSwSelectedEvent.rows.length - 1; j++) {
          document.getElementById("SwimmersAvailablecell" + i + "_" + j).checked = Checkcellchkbox.checked;
        }

        if (Checkcellchkbox.checked == true) {
          SwDetailsSlectedRows.push(Checkcellchkbox.id.replace("SwimmersCheckboxcell", ""));
        }
        else {
          SwDetailsSlectedRows.pop(Checkcellchkbox.id.replace("SwimmersCheckboxcell", ""))
        }
      });

    tblSwimmersRow.id = "tblSwimmersRow" + i;
    Swimmersslnocell = tblSwimmersRow.insertCell();
    Swimmersslnocell.innerHTML = (i + 1);

    SwimmersNamecell = tblSwimmersRow.insertCell();
    SwimmersNamecell.innerHTML = "<input class='form-control' id ='SwimmersNamecell" + i + "'>";
    document.getElementById("SwimmersNamecell" + i).value = SwKeys[i];


    var SwimmerGroupCell = tblSwimmersRow.insertCell();
    SwimmerGroupCell.innerHTML = "<input class='form-control' type='text' id ='SwimmerGroupCell" + i + "'>";
    document.getElementById("SwimmerGroupCell" + i).value = SwimmerDetails[SwKeys[i]].Group

    var SwimmerClubCell = tblSwimmersRow.insertCell();
    SwimmerClubCell.innerHTML = "<input class='form-control' type='text' id ='SwimmerClubCell" + i + "'>";
    document.getElementById("SwimmerClubCell" + i).value = SwimmerDetails[SwKeys[i]].Club


    var tblSwSelectedEvents = document.createElement("TABLE");
    tblSwSelectedEvents.id = "tblSwSelectedEvents" + i;

    var header = tblSwSelectedEvents.createTHead();
    var row = header.insertRow();
    var cell = row.insertCell();
    cell.innerHTML = "<b> Event Name. <b> ";
    var cell = row.insertCell();
    cell.innerHTML = "<b> Best Timeings <b>";
    var cell = row.insertCell();
    cell.innerHTML = "<b>  Available  <b>";
    var cell = row.insertCell();
    cell.innerHTML = "<button onclick=AppendRow('" + tblSwSelectedEvents.id + "','tblSwimmersRow')><i class='fa fa-fw fa-plus'></i></button>"
    var cell = row.insertCell();
    cell.innerHTML = "<button onclick=DeleteRows('" + tblSwSelectedEvents.id + "','tblSwimmersRow')><i class='fa fa-fw fa-minus'></i></button>"

    var SwimmersEventcell = tblSwimmersRow.insertCell();
    SwimmersEventcell.appendChild(tblSwSelectedEvents);
    //SwimmerDetails[SwKeys[i]].Events.length
    AvblEventsFromReg = SwimmerDetails[SwKeys[i]].Events.length;

    for (let j = 0; j < NumberofEventsperSw; j++) {
      var tblSwlistRow = tblSwSelectedEvents.insertRow();
      SwimmersEventSelector = tblSwlistRow.insertCell();
      SwimmersEventSelector.innerHTML = "<select id ='SwimmersEventSelector" + i + "_" + j + "'>";
      var EventSelector = document.getElementById("SwimmersEventSelector" + i + "_" + j);
      if (AvailableEvents.length > 0 && EventSelector != null) {
        AvailableEvents.forEach(SwEvent => {
          var newSwEvent = document.createElement("option"); // Create a new option            
          newSwEvent.value = SwEvent; // Set the value
          newSwEvent.text = SwEvent; // Set the text        
          EventSelector.add(newSwEvent);
        });
      }

      SwimmersEventBestTime = tblSwlistRow.insertCell();

      SwimmersEventBestTime.innerHTML = "<input class='form-control' id ='SwimmersEventBestTime" + i + "_" + j + "'>";
      // if (SwimmerDetails[SwKeys[i]]["Events"][j].BestTimeings !== null)
      //   {
      //   }
      SwimmersAvailablecell = tblSwlistRow.insertCell();
      SwimmersAvailablecell.innerHTML = "<input  type='Checkbox' id ='SwimmersAvailablecell" + i + "_" + j + "'>";
      // if (SwimmerDetails[SwKeys[i]]["Events"][j].BestTimeings !== null)
      //   {
      //   }


      if (SwimmerDetails[SwKeys[i]]["Events"][j] !== undefined) {
        document.getElementById("SwimmersEventSelector" + i + "_" + j).value = SwimmerDetails[SwKeys[i]]["Events"][j].EventName;
        document.getElementById("SwimmersEventBestTime" + i + "_" + j).value = SwimmerDetails[SwKeys[i]]["Events"][j].BestTimeings;
        document.getElementById("SwimmersAvailablecell" + i + "_" + j).checked = SwimmerDetails[SwKeys[i]]["Events"][j].Available;
      }

    }
  }
}

function GenerateHeatDetailsTable(Heats) {
  ClearTable('tblHeatDetails');
  for (let i = 0; i < Heats.length; i++) {
    AddHeatRow(i, Heats[i]);
  }
}