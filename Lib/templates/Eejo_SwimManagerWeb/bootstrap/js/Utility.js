
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