let LastUpdatedBoard = 0;
let ScreenShotinited = 0;
let MaxBoardLength = 0;
let SwNames = [];
let SwClub = [];
let InitDone = 0;
let IntiSmallSwNames = true;
let IntiBigSwNames = true;


// Sort Related
async function CreateTimerTable(TblID) {

  let SwNamesRes = await FetchValuesFromTimer('GetSwNames');
  // document.getElementById("HeatNameDisp").innerHTML="<b>"+SwNames.HeatName+ " </b>";
  MaxBoardLength = SwNamesRes.SwNames.length;
  SwNames = SwNamesRes.SwNames;
  SwClub= SwNamesRes.Club; 

  BoarTbl = document.getElementById(TblID)
  if (BoarTbl) {
    if (MaxBoardLength != BoarTbl.rows.length) {
      BoarTbl.innerHTML = "";
      for (let index = 1; index <= (MaxBoardLength); index++) {
        addCustomRow(index, TblID);
      }
    }
  }
}

function MoveElementwithAnimation(Etop, Eleft, Eid) {
  return new Promise((resolve, reject) => {
    let y = 0
    setTimeout(() => {

      MoveElement(Etop, Eleft, Eid)

      console.log('Loop completed.')
      resolve(y)
    }, 250)
  })
}


function MoveElement(Etop, Eleft, Eid) {
  let moveDir = 0;
  let elem = document.getElementById(Eid);
  if (elem) {
    let eheight = elem.clientHeight;
    let curOffsetTop = elem.offsetTop;
    let curOffsetLeft = elem.offsetLeft;
    elem.style.top = Etop + 'px';
  }
}

function SortBoardByTime(timerData) {
  const tmparray = timerData;
  let newRank = []
  for (let i = 0; i < tmparray.length - 1; i++) {
    for (let j = 0; j < tmparray.length - i - 1; j++) {
      if (tmparray[j].Time > tmparray[j + 1].Time) {
        let temp = tmparray[j];
        tmparray[j] = tmparray[j + 1];
        tmparray[j + 1] = temp;
      }
    }
  }

  for (let i = 0; i < tmparray.length; i++) {
    newRank.push(tmparray[i].BoardID);
  }
  return newRank
}


async function MoveNext(proposedpos) {
  for (let i = 0; i < proposedpos.length; i++) {
    let Eid = "Board" + proposedpos[i];
    // let elem = document.getElementById(Eid);
    let Etop = (elem.clientHeight + 10) * (i);
    let Eleft = 0;
    const result = await MoveElementwithAnimation(Etop, Eleft, Eid);

  }
}


// Display Related

async function UpdateBoardNum(count) {
  for (var i = 1; i <= count; i++) {
    elem = document.getElementById("Linetxt" + (i));
    if (elem) {
      elem.innerHTML = i;
    }
    elemrank = document.getElementById("SwRank" + (i));

    if (elemrank) {
      elemrank.innerHTML = 0;
    }
  }

}

async function GetTimerStatus() {
  let MaintblDisplay;
  let TimerStatus = await FetchValuesFromTimer('TimerStatus');
  CurrentTime = document.getElementById("CurrentTime");
  if (CurrentTime) {
    const now = new Date();    

CurrentTime.innerHTML = `<b>${now.toDateString()}<br>${now.toLocaleTimeString()}</b>`;

  }
let originalString= TimerStatus.Message;
  const indexOfCharacter = TimerStatus.Message.indexOf('.');
  let trimmedString="";
  if (indexOfCharacter !== -1) {
    trimmedString = TimerStatus.Message.substring(indexOfCharacter + 1);
  } else {
    // If the character is not found, the string remains unchanged
    trimmedString = originalString;
  }

  let elem = document.getElementById("TimerState");
  if (elem) {
    elem.innerHTML = "<b>" + trimmedString + " </b>";
  }

  elem = document.getElementById("TimerState_Pop");
  if (elem) {
    elem.innerHTML = "<b>" + trimmedString + " </b>";
  }

  // console.log(TimerStatus.Message)
  // Check and Refresh Table

  switch (TimerStatus.Message) {
    case 'HideQR':
      HideQR(1);
      break;

    case 'ShowQR':
      HideQR(0);
      break;
    case 'TimerStatus.loadedToStart':
        cleartextnode("Linetxt",MaxBoardLength)

      // cleartextnode("SwName",10);
      
      // UpdateBoardNum(10);
      showhideDiv(true, 'InfoIndicatorpop');

      let MainBoardTbl = document.getElementById("MainBoardTbl");
      if (MaintblDisplay) {
        if (MaxBoardLength != MainBoardTbl.rows.length) {
          IntiBigSwNames = true;
        }
      }
      IntiBigSwNames = true;

      if (IntiBigSwNames) {
        IntiSmallSwNames = true;
        LastUpdatedBoard = 0;
        ScreenShotinited = 0;
        GetHeatInfo();

        CreateTimerTable("MainBoardTbl");

        FillSwNames("SwTimer");
        // GetSwNames("SwTimer","");

        MaintblDisplay = document.getElementById("MaintblDisplay");
        if (MaintblDisplay) {
          MaintblDisplay.setAttribute("style", "width: 100%; height:100% ")
        }
        if (HighlightLastUpdatedBoard) {
          for (let i = 1; i <= MaxBoardLength; i++) {
            Board = document.getElementById("Board" + i);
            // const myDiv = document.getElementById('myDiv');
            if (Board) {
              const computedStyle = window.getComputedStyle(Board);
              const bgColor = computedStyle.backgroundColor;
              //alert('The background color of the div is: ' + bgColor);
              if (bgColor != "rgb(4, 4, 4)") {
                Board.setAttribute("style", "transform: scale(1.0);");
              }
            }
          }
        }
        IntiBigSwNames = false;
      }

      // cleartextnode("SwRank",10);
      //cleartextnode("Board",10);

      // cleartextnode("SwTimer",10);
      // GetSwNames("SwTimer");
      break;

    case 'Busy':
      elem = document.getElementById("Message");
      if (elem) {
        elem.innerHTML = "<b>" + TimerStatus.Message + " </b>";
      }
      showhide('BusyIndicatorpop', TimerStatus.Message);
      break;

    case 'NewHeat':

      // GetHeatInfo();
      // cleartextnode("SwRank",10);
      // cleartextnode("Linetxt",10);
      // cleartextnode("Board",10);
      // cleartextnode("SwName",10);


      // cleartextnode("SwTimer",10);
      // GetSwNames("SwTimer");
      break;
    case 'TimerStatus.InProgress':


      if (IntiSmallSwNames) {
        showhideDiv(false, 'InfoIndicatorpop');
        CreateTimerTable("MainBoardTbl");
        FillSwNames("Linetxt");
        IntiSmallSwNames = false;
        IntiBigSwNames = true;
      }
      // GetSwNames("Linetxt");
      GetBoardStatusAndTime();
      break;
    //UpdateLocalTimer();
    case 'TimerStatus.WaitBeforeLoad':
      GetBoardStatusAndTime();

    case 'TimerStatus.':
      GetBoardStatusAndTime();

      break;
    case 'Updating Result To Cloud':
      HeatNameDisp = document.getElementById("HeatNameDisp");
      CurrentTime = document.getElementById("CurrentTime");
      if (HeatNameDisp) {
        if (CurrentTime) {
          if (ScreenShotinited == 0) {
            TakeResultScreenShot("LiveDispBody", HeatNameDisp.innerText+ "-" + CurrentTime.innerText);
            ScreenShotinited = 1;
          }
        }
        // Example usage:
        //logToFile( 'This is the content of my text file.');
      }
      MaintblDisplay = document.getElementById("MaintblDisplay");
      if (MaintblDisplay) {
        MaintblDisplay.setAttribute("style", "width: 80%; height:80% ")
      }
      break;


    case 'Lostconnection':
    // if lost known status is Heat in progress Keep local timer running to help manual time extraction

    case 'NewEvent':
      // Display Top 10 of last Event

      break;

    default:
      break;
  }
}

function cleartextnode(NodeName, count) {
  for (var i = 1; i <= count; i++) {
    elem = document.getElementById(NodeName + (i));
    if (elem) {
      elem.innerHTML = "";
    }
  }
}

function InvertRanks(ranks)
{  
  // const ranks = [0, 0, 3, 2, 1, 4, 5];
const inverted = new Array(ranks.length);

for (let i = 0; i < ranks.length; i++) {
    inverted[i] = ranks.indexOf(i);
}

console.log(inverted); // Output: [0, 0, 3, 4, 5, 2, 1]
  return inverted;
}


function SortAndGetRankDescending(ArrayToSort) {
  // Create an array of objects with original index and value
  const indexedArr = ArrayToSort.map((value, index) => ({ value, index }));

  // Sort by value in descending order
  indexedArr.sort((a, b) => b.value - a.value);

  // Assign ranks
  const ranks = Array(ArrayToSort.length);
  let currentRank = 1;

  for (let i = 0; i < indexedArr.length; i++) {
    const { value, index } = indexedArr[i];

    if (value === 0) {
      ranks[index] = 0; // Set rank to 0 if value is 0
      continue;
    }

    if (i > 0 && value === indexedArr[i - 1].value) {
      ranks[index] = ranks[indexedArr[i - 1].index];
    } else {
      ranks[index] = currentRank;
    }

    currentRank++;
  }

  return ranks;
}

function SortAndGetRank(ArrayToSort) {
  // Create an array of objects with original index and value
  const indexedArr = ArrayToSort.map((value, index) => ({ value, index }));

  // Sort by value in descending order
  indexedArr.sort((a, b) => a.value - b.value);

  // Assign ranks
  let ranks = Array(ArrayToSort.length);
  let currentRank = 1;

  for (let i = 0; i < indexedArr.length; i++) {
    const { value, index } = indexedArr[i];

    if (value === 0) {
      ranks[index] = 0; // Set rank to 0 if value is 0
      continue;
    }

    if (i > 0 && value === indexedArr[i - 1].value) {
      ranks[index] = ranks[indexedArr[i - 1].index];
    } else {
      ranks[index] = currentRank;
    }

    currentRank++;
  }

  // console.log("Original Array:", ArrayToSort);
  // console.log("Ranks:", ranks);
  return ranks;
}

function addCustomRow(rankValue, TblID) {
  const table = document.getElementById(TblID); // Adjust selector as needed
  const newRow = document.createElement('tr');
  newRow.className = 'pp';
  newRow.id = `Board${rankValue}`; // Optional: make ID dynamic too

  newRow.innerHTML = `
    <td>
      <span class="info-box-icon" style="margin-bottom: 180%; margin-left: 20%; margin-right:10%;">
        <b id="SwRank${rankValue}" class="ExtraBigRankFont">${rankValue}</b>            
        <b  id="LineID${rankValue}" class="Mediumfont">L:${String(rankValue).padStart(2, '0')}<br></b>
      </span>
    </td>                
    <td ">
      <b class="bigfont" id="Linetxt${rankValue}">Name Of Swimmer</b>
      <span  class="info-box-content" span style="display: inline-block; margin-right: 10px;">
        <b class="ExtraBigFont" id="SwTimer${rankValue}">11:22.33</b>
      </span>
    </td>
  `;

  table.appendChild(newRow);
}
async function GetBoardStatusAndTime() {
  let GetBoardStatusAndTimeRes = await FetchValuesFromTimer('GetBoardStatusAndTime');
  var x = [];
  for (var i = 0; i < GetBoardStatusAndTimeRes.BoardStatusAndTime.length; i++) {
    if (GetBoardStatusAndTimeRes.BoardStatusAndTime[i].Status == 0 && GetBoardStatusAndTimeRes.BoardStatusAndTime[i].LockStatus == 1) {
      x.push(GetBoardStatusAndTimeRes.BoardStatusAndTime[i].Time);
    }
    else {
      x.push(0);
    }
  }

  let RankSortted = SortAndGetRank(x);

  if (HighlightLastUpdatedBoard) {
    for (var i = 0; i < RankSortted.length; i++) {
      elem = document.getElementById("SwRank" + (i + 1))
      if (elem) {
        if (GetBoardStatusAndTimeRes.BoardStatusAndTime[i].Status != 0) {
          elem.innerHTML = '-';
        }
        else {
          elem.innerHTML = RankSortted[i];
        }
      }
    }
    for (var i = 0; i < GetBoardStatusAndTimeRes.BoardStatusAndTime.length; i++) {
      index = GetBoardStatusAndTimeRes.BoardStatusAndTime[i].BoardID;
      elem = document.getElementById("SwTimer" + (index));
      if (elem) {
        if (GetBoardStatusAndTimeRes.BoardStatusAndTime[i].Status != 0) {
          elem.innerHTML = DQMsg[GetBoardStatusAndTimeRes.BoardStatusAndTime[i].Status];
        }
        else {
          elem.innerHTML = ConvertTime(GetBoardStatusAndTimeRes.BoardStatusAndTime[i].Time);
        }
        if (LastUpdatedBoard == 0) {
          Board = document.getElementById("Board" + (GetBoardStatusAndTimeRes.BoardStatusAndTime[i].BoardID));
          Board.setAttribute("style", "transform: scale(1.0);");
        }
      }
      // document.getElementById("SwStatus"+(i+1)).innerText=GetBoardStatusAndTimeRes.BoardStatusAndTime[i].Status;
      if (GetBoardStatusAndTimeRes.BoardStatusAndTime[i].LockStatus == 1) {
        elem = document.getElementById("SwRank" + (index))
        if (elem) {
          if (elem.innerHTML == 0) {
            LastUpdatedBoard = GetBoardStatusAndTimeRes.BoardStatusAndTime[i].BoardID;
            Board = document.getElementById("Board" + (LastUpdatedBoard));
            Board.setAttribute("style", "transform: scale(1.05);Background:Green");
          }
          else if (LastUpdatedBoard != GetBoardStatusAndTimeRes.BoardStatusAndTime[i].BoardID) {
            Board = document.getElementById("Board" + (GetBoardStatusAndTimeRes.BoardStatusAndTime[i].BoardID));
            Board.setAttribute("style", "transform: scale(1.0);");
          }
        }
      }
      else {
        elem = document.getElementById("SwRank" + (index))
        if (elem) {
          elem.innerHTML = 0;
        }
      }
    }
  }
  else {

    for (var i = 0; i <= RankSortted.length; i++) {
      let Rank = RankSortted.indexOf(i + 1);
      let Boardpos = 0;

      const BoarsRank = RankSortted.map((RankSortted, index) => ({
        key: index+1,
        value: RankSortted
      }));     
     
const sortedBoards = BoarsRank.sort((a, b) => {
  if (a.value === 0 && b.value !== 0) return 1;
  if (a.value !== 0 && b.value === 0) return -1;
  return a.value - b.value;
});

//console.log(sorted);

SwKeys = Object.keys(sortedBoards);
      // if (Rank >= 0) {
      //   Boardpos = (i + 1)
      // }
      // else {
      //   Boardpos = (RankSortted.length - i)
      // }
      for (let index = 0; index < sortedBoards.length; index++) {
        let  element = sortedBoards[index];
        let KeyIndex;
        if (element.value!= 0 )
          {
            KeyIndex= element.value;
          }
        else
        {
          KeyIndex= index+1;
        }
        
      
      // sortedBoards.forEach(Board => {        
        let elem = document.getElementById("SwRank" +  (KeyIndex))
        if (elem) {
          elem.innerHTML = element.value;
        }
        elem = document.getElementById("SwTimer" + (KeyIndex))
        if (GetBoardStatusAndTimeRes.BoardStatusAndTime[element.key-1].Status != 0) {
          elem.innerHTML = DQMsg[GetBoardStatusAndTimeRes.BoardStatusAndTime[element.key-1].Status];
        }
        else {
          elem.innerHTML = ConvertTime(GetBoardStatusAndTimeRes.BoardStatusAndTime[element.key-1].Time);
        }
        elem = document.getElementById("Linetxt" + (KeyIndex))
  
        if (elem) {
          elem.innerHTML = SwNames[element.key-1];
        }

        
        elem = document.getElementById("LineID" + (KeyIndex))
  
        if (elem) {
          elem.innerHTML = `L:${String(element.key).padStart(2, '0')}`;
      }
      
      // });

    }
    }
  }

 


}

function FillSwNames(ObjPrefixtofill, BoardLength = MaxBoardLength) {
cleartextnode("Linetxt",MaxBoardLength)

  for (var i = 0; i < BoardLength; i++) {
    elem = document.getElementById(ObjPrefixtofill + (i + 1));
    if (elem) {
      elem.innerText = SwNames[i];
    }
  }
}
async function GetSwNames(TblID) {
  let SwNamesRes = await FetchValuesFromTimer('GetSwNames');
  // document.getElementById("HeatNameDisp").innerHTML="<b>"+SwNames.HeatName+ " </b>";
  MaxBoardLength = SwNamesRes.SwNames.length;
}

async function GetHeatInfo() {
  let HeatInfo = await FetchValuesFromTimer('HeatInfo');
  elem = document.getElementById("HeatNameDisp");
  if (elem) {
    elem.innerHTML = "<b>" + HeatInfo.HeatName + " </b>";
  }
}

async function GetMeetInfo() {
  let MeetInfo = await FetchValuesFromTimer('MeetInfo');
  // CreateTimerTable(parseInt(MeetInfo.Boards),)
  elem = document.getElementById("MeetNameDisp");
  if (elem) {
    elem.innerHTML = "<b>" + MeetInfo.MeetName + " </b>";
  }
  elem = document.getElementById("MeetDateDisp");

  if (elem) {

    elem.innerHTML = "<b>" + MeetInfo.MeetDate + " </b>";
  }
  elem = document.getElementById("MeetAddressDisp");

  if (elem) {

    elem.innerHTML = "<b>" + MeetInfo.MeetAddress + " </b>";
  }
}
function HideQR(Hidecmd) {
  if (Hidecmd == 1) {
    showhideDiv(false, 'qrcode');
  }
  else {
    showhideDiv(true, 'qrcode');

  }


}
async function GetRestIP() {
  let RestIP = await FetchValuesFromTimer('GetRestIP');
  // DisplayQRCode(RestIP);
  return RestIP;


}

async function FetchValuesFromTimer(parametertoFetch) {
  try {
    let response;
    let data;

    switch (parametertoFetch) {

      case 'GetRestIP':
        cmdurl = cmdurlwithHost + "/SetLiveHeatCommands?CmdName=GetRestIP";
        response = await fetch(cmdurl);
        data = await response.json();

        return data.commandReturnData;
        bre

        break;
      case 'MeetInfo':
        cmdurl = cmdurlwithHost + "/SetLiveHeatCommands?CmdName=GetMeetInfo";
        response = await fetch(cmdurl);
        data = await response.json();
        return data.commandReturnData;
        break;
      case 'GetSwNames':
        cmdurl = cmdurlwithHost + "/SetLiveHeatCommands?CmdName=GetSwNames";
        response = await fetch(cmdurl);
        data = await response.json();
        return data.commandReturnData;
        break;

      case 'GetBoardStatusAndTime':
        cmdurl = cmdurlwithHost + "/SetLiveHeatCommands?CmdName=GetBoardStatusAndTime";
        response = await fetch(cmdurl);
        data = await response.json();
        return data.commandReturnData;
        break;

      case 'HeatInfo':
        cmdurl = cmdurlwithHost + "/SetLiveHeatCommands?CmdName=GetHeatInfo";
        response = await fetch(cmdurl);
        data = await response.json();
        return data.commandReturnData;
        break;

      case 'TimerStatus':
        cmdurl = cmdurlwithHost + "/GetTimerState";
        response = await fetch(cmdurl);
        data = await response.json();
        return data;
        break;

      default:
        break;
    }

  } catch (error) {
    console.error('Error fetching data:', error);
  }
}