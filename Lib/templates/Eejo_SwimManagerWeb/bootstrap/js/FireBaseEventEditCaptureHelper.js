function CaptureMeetTable(MeetUpdatedData) {
  MeetUpdatedData.MeetName = document.getElementById("tblMeet_MeetName").value;
  MeetUpdatedData.MeetAddress = document.getElementById("tblMeet_MeetAddress").value;
  MeetUpdatedData.MeetDate = document.getElementById("tblMeetDate").value;
  MeetUpdatedData.Boards = document.getElementById("tblMeet_txtBoards").value;
  return MeetUpdatedData;
}
// function CaptureSwDetailsTable(MeetUpdatedData)
// {

// }

function CaptureSwDetailsTable(MeetUpdatedData) {

  // ClearTable('tblSwDetails');
  MeetUpdatedData.SwimmerDetails.length=0;

  tblSwimmers = document.getElementById('tblSwDetails');
  
  for (let i = 0; i < tblSwimmers.rows.length-1; i++) {    
    let SwaName= document.getElementById("SwimmersNamecell" + i).value;
    let SwGroup=document.getElementById("SwimmerGroupCell" + i).value;
    let SwClub=document.getElementById("SwimmerClubCell" + i).value;
    var tblSwSelectedEvents = document.getElementById("tblSwSelectedEvents" + i);

    EventList=[];
    BestTimeingsList=[];
    AvailableList=[];

    for (let j = 0; j < tblSwSelectedEvents.rows.length-1; j++) {
      
      var EventSelector = document.getElementById("SwimmersEventSelector" + i + "_" + j);
      
      Available= document.getElementById("SwimmersAvailablecell" + i + "_" + j).checked;
      BestTimeings= document.getElementById("SwimmersEventBestTime" + i + "_" + j).value;
      EventName= document.getElementById("SwimmersEventSelector" + i + "_" + j).value;
      EventList.push({'Available':Available,'BestTimeings': BestTimeings,'EventName':EventName} );
      BestTimeingsList.push();

    }
      MeetUpdatedData.SwimmerDetails[SwaName]=({ 'Name': SwaName ,'Group': SwGroup, 'Events': EventList, 'Club': SwClub });
    
  }
  return MeetUpdatedData;
}

function CaptureGroupTable(MeetUpdatedData) {
  tblGroups = document.getElementById('tblGroups');
  MeetUpdatedData.GroupDetails.length = 0;

  for (let i = 1; i < tblGroups.rows.length; i++) {
    rowindex = tblGroups.rows[i].id.replace("tblgroupRow", "");
    GroupName = document.getElementById("GrpNamecell" + rowindex).value;
    FromDate = document.getElementById("GrpFromcellvar" + rowindex).value;
    ToDate = document.getElementById("GrpTocellvar" + rowindex).value;

    if (GroupName != "" && FromDate != "" && ToDate != "") {
      MeetUpdatedData.GroupDetails.push({ 'GroupName': GroupName, 'FromDate': FromDate, 'ToDate': ToDate });
    }
  }
  return MeetUpdatedData;
}


function CaptureHeatDetailsTable(MeetUpdatedData) {
  tblHeatDetails = document.getElementById('tblHeatDetails');
  MeetUpdatedData.EventDetails.length = 0;
  var EventsDetailsarray = [];
  var HeatDetails = [];
  var EventID = "";

  for (let index = 0; index < tblHeatDetails.rows.length - 1; index++) {
    rowindex = tblHeatDetails.rows[index].id.replace("tblHeatDetailsRow", "");
    var HeatiD = document.getElementById('HeatNamecell' + index).value;
    tblSwlist = document.getElementById("tblSwlist" + index);
    var BoardDetails = [];

    if (EventID == "") {
      EventID = HeatiD.substring(0, HeatiD.lastIndexOf('_'));
    }
    else if (HeatiD.substring(0, HeatiD.lastIndexOf('_')) != EventID) {
      x = JSON.stringify(HeatDetails);
      var ss = JSON.parse(x);
      EventsDetailsarray.push({ "HeatList": ss, "eventID": EventID, "eventName": "", "eventStatus": 0 });
      EventID = HeatiD.substring(0, HeatiD.lastIndexOf('_'));
      HeatDetails.length = 0;
    }

    for (let RowIndex = 1; RowIndex < tblSwlist.rows.length; RowIndex++) {
      // console.log( HeatiD + " " + RowIndex +" "+  RowIndex)   ;
      SwimerID = tblSwlist.rows[RowIndex].cells[0].innerText;
      SwimerName = tblSwlist.rows[RowIndex].cells[1].innerText;
      SwimStatus = tblSwlist.rows[RowIndex].cells[2].innerText;      
      let SwTimetxt= tblSwlist.rows[RowIndex].cells[3].firstChild.value;

      if (SwTimetxt=="0")
        {
          SwimTimings = 12.34;
        }
        else
        {
          SwimTimings = parseFloat(convertToSeconds(SwTimetxt));
        }
      
      BoardDetails.push({
        'BoardID': RowIndex, "BoardStatus": 0, "SwimStatus": 0,
        "SwimTimings": SwimTimings, "SwimerID": SwimerID, "SwimerName": SwimerName
      })
    }
    HeatDetails.push({
      "BoardList": BoardDetails, "HeatEndTime": 11111111111111, "HeatID": HeatiD,
      "HeatStartTime": 11111111111111, "HeatStatus": 0
    });

  }
  if (HeatDetails.length != 0) {
    EventsDetailsarray.push({ "HeatList": HeatDetails, "eventID": EventID, "eventName": "", "eventStatus": 0 });
    EventID = HeatiD.substring(0, HeatiD.lastIndexOf('_'));
  }
  MeetUpdatedData.EventDetails = EventsDetailsarray;
  return MeetUpdatedData;
}  