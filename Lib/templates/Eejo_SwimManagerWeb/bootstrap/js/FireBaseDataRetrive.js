
FirebaseSwimmersurl = "https://eejo-managerdb-default-rtdb.firebaseio.com/Swimmers.json";

var firebaseData;



function LoadSwNames(data) {

    let NameArray = []
    SwNames = Object.keys(data);

    for (let i = 0; i < (SwNames.length); i++) {
        SwName = data[SwNames[i]];
        NameArray.push({ value: 'opt' + i, text: SwName.Name });
    }
    return NameArray;
}

function LoadMeetNames(data) {
    firebaseData = data;
    let MeetNames = []
    MeeetKeys = Object.keys(data);

    for (let i = 0; i < (MeeetKeys.length); i++) {
        meet = data[MeeetKeys[i]];
        MeetNames.push({ value: meet.MeetName, text: meet.MeetName });
    }

    // data.forEach(meet => {
    //     MeetNames.push({ value: meet.MeetName, text: meet.MeetName });
    // });
    return MeetNames;
}

function LoadHeatFileName(data) {
    let HeatFileNames = []
    for (let i = 0; i < (data.HeatFiles.length); i++) {
        HeatFile = data.HeatFiles[i];
        HeatFileNames.push({ value: HeatFile, text: HeatFile });
    }

    // data.forEach(meet => {
    //     MeetNames.push({ value: meet.MeetName, text: meet.MeetName });
    // });
    return HeatFileNames;
}

function LoadEventNames(data, MeetnameSelected) {
   let EventNames=[];
    // data.forEach(meet => {
    //     if (MeetnameSelected == meet.MeetName) {
            meet.EventDetails.forEach(event => {
                EventNames.push({ value: event.eventName, text: event.eventName });
            });
        // }
    // });
    return EventNames;
}

function ShareEventDetails(MeetDataFirebase, SelectedMeetName, SelectedEventName) {
    let EventToDisplay = [];
    MeetDataFirebase.forEach(meet => {
        if (SelectedMeetName == meet.MeetName) {
            meet.EventDetails.forEach(Swevent => {
                // if (SelectedEventName.length==0 || (SelectedEventName.includes(Swevent.eventName)) )
                //     {
                EventToDisplay.push(Swevent);
                // }
            });

        }
    });
    return EventToDisplay;
}

function UpdateStrokes(SwNamesarray, SwimmerFirebaseData, StrokeArray) {


    SwNames = Object.keys(SwimmerFirebaseData);
    SwNamesarray.forEach(SelSwName => {
    // let NameArray = []

    // for (let i = 0; i < (SwNames.length); i++) {
    //     SwName = data[SwNames[i]];
    //     NameArray.push({ value: 'opt' + i, text: SwName.Name });
    // }
    // .forEach(SwRecord => {.
        
            // if (SelSwName == SwRecord["Name"]) {
                SwimmerFirebaseData[SelSwName].MeetResults.forEach(MeetResult => {
                    if (MeetResult["EventID"] !== "") {
                        var stroketype = MeetResult["EventID"].split("_");
                        var stroketyp = stroketype[0] + "_" + stroketype[1]
                        const foundElement = StrokeArray.find(element => element.value === stroketyp);
                        StroketoAdd = { 'value': stroketyp, 'text': stroketyp };
                        if (foundElement == undefined) {
                            StrokeArray.push(StroketoAdd);
                        }
                    }
                });
            // }
        });
    // });
    return StrokeArray;

}

function GetSwTimeing(data, SwNames, StrokeName) {
    var yValues = 0
    var timevalues = []
    var xValues = 0
    // SwNames.forEach(SwName => {

    for (let i = 0; i < (data.length); i++) {
        if (SwNames.includes(data[i]["Name"])) {
            // xValues = []
            for (let j = 0; j < (data[i]["MeetResults"].length); j++) {
                if (data[i]["MeetResults"][j]["EventID"] !== "") {
                    var stroketypa = data[i]["MeetResults"][j]["EventID"].split("_");
                    var stroketyp = stroketypa[0] + "_" + stroketypa[1]
                    if (stroketyp == StrokeName) {
                        yValues = data[i]["MeetResults"][j]["timeings"];
                        xValues = data[i]["MeetResults"][j]["HeatDateTime"]
                        timevalues.push({ 'Swname': data[i]["Name"], 'timeval': yValues, 'dateval': xValues })
                    }
                }
            }
        }
    }
    // });
    return timevalues;

}
function ExtractMeetInfo(meet) {
    let Meetdetails = {};
    // let Events = [];
    let Heats = [];

    meet.EventDetails.forEach(SwEvent => {
        // Events.push(SwEvent.eventID);
        SwEvent.HeatList.forEach(heat => {
            let Boardinfo = [];
            heat.BoardList.forEach(Board => {
                Boardinfo.push({
                    'BoardID': Board.BoardID, 'BoardStatus': Board.BoardStatus, 'SwimStatus': Board.SwimStatus,
                    'SwimTimings': Board.SwimTimings, 'SwimerID': Board.SwimerID, 'SwimerName': Board.SwimerName
                })
            });
            Heats.push({ 'ID': heat.HeatID, 'Boardinfo': Boardinfo });
        });

    });
    Meetdetails = {
        'CurrentMeet': meet,
        'MeetName': meet.MeetName, 'MeetAddress': meet.MeetAddress, 'MeetDate': meet.MeetDate, 'Boards': meet.Boards,
        'GroupDetails': meet.GroupDetails, 'EventList': meet.EventList, 'HeatList': Heats, 'SwimmerDetails': meet.SwimmerDetails
    };

    return Meetdetails;
}
/* For Event Editor*/

function GetMeetDetails(data, MeetSelected) {
    firebaseData = data;
    // let Meetdetails = {};
    // let Events = [];
    // let Heats = [];    
    // let CurrentMeet;

    // data.forEach(meet => {

    MeeetKeys = Object.keys(data);
    for (let i = 0; i < (MeeetKeys.length); i++) {
        meet = data[MeeetKeys[i]];

        if (MeetSelected == meet.MeetName) {
            return ExtractMeetInfo(meet);
        }
    }

}