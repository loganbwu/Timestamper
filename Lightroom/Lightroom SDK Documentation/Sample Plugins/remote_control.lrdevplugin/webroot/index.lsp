<%
	local catalog = import "LrApplication".activeCatalog()
	local photo = catalog:getTargetPhoto()
	local imageId = photo and photo.localIdentifier

	local prefs = import "LrPrefs".prefsForPlugin()
					
	local onlySlideshow
	local onlyCapture
	local onlyKeywords = prefs.allowEditKeywords
						and not prefs.allowViewPhotos
						and not prefs.allowTriggerCapture

	local onlyNav = prefs.allowSwitchPhotos 
				and (onlyKeywords or not prefs.allowEditKeywords)
				and not prefs.allowSwitchViewModes 
				and not prefs.allowTriggerCapture
%>

<html>
<title>Lightroom Remote</title>
<head>
<meta content='width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0' name='viewport' />
<meta name="viewport" content="width=device-width" />
<style>

body {
	background-color:#333333;
	font-family:verdana,tahoma,sans-serif;
	color:white;
	margin:0;
}
a {
	text-decoration:none;
	color:white;
	font-size:4em;
}
.header {
	width:100%;
	background-color:black;
	padding:0.5em;
	margin-bottom:1px;
}

.photo {
/*	max-width:100%;*/
/*	max-height: 90%;*/
<% if not prefs.allowEditKeywords then %>
	width:100%;
<% end %>
<% if prefs.allowEditKeywords and prefs.allowViewPhotos then %>
	position:absolute;
	text-align:right;
	float:right;
	margin:1em;
<% end %>
}

.keywordPanel {
	color:#cccccc;
	background-color:#555555;
	border:solid 1px #333333;
	font-size:0.8em;
	width:28em;
	text-align:left;
	margin-left:auto;
	margin-right:auto;
	padding-top:0.2em;
	padding-right:1.3em;
	padding-left:1.3em;
	padding-bottom:0;
}

textarea {
	font-family:verdana,tahoma,sans-serif;
	color:#ffffff;
	background-color:#666666;
	border:solid 1px #444444;
}

.submit {
	width:30%;
	color:#cccccc;
	background-color:#5A5A5A;
	border: solid 1px #444444;
}


.buttonGrid {
	background-color:#555555;
}

.buttonGrid button {
	font-family:verdana,tahoma,sans-serif;
<% if prefs.allowEditKeywords and not prefs.allowViewPhotos then %>
	font-size:1.8em;
<% else %>
	font-size:1em;
<% end %>
	width:6em;
	line-height:1.8em;
	margin:0.35em;
	border:0.1em solid #333333;
	background:#666666;
	color:#e6e6e6;
}

.smallButtonGrid {
	margin:.2em;
<% if prefs.allowEditKeywords and prefs.allowViewPhotos then %>
	display:none;
<% end %>
}

.smallButtonGrid button {
	font-family:verdana,tahoma,sans-serif;
<% if prefs.allowEditKeywords and prefs.allowViewPhotos then %>
	font-size:0.8em;
<% else %>
	font-size:1.1em;
<% end %>
	width:6em;
	line-height:1.6em;
	margin:0.5em;
	padding:0.3em;
	border:0.1em solid #333333;
	background:#eeeeee;
	color:333333;
}

.buttonGrid button.up {
	background:#666666;
	color:#e6e6e6;
}

.buttonGrid button.dn {
	background:#eeeeee;
	color:333333;
}

</style>

<script>

function makeHttpObject() {
  try {return new XMLHttpRequest();}
  catch (error) {}
  try {return new ActiveXObject("Msxml2.XMLHTTP");}
  catch (error) {}
  try {return new ActiveXObject("Microsoft.XMLHTTP");}
  catch (error) {}

  throw new Error("Could not create HTTP request object.");
}

//------------------------------------------------------------------------------

function changeKeyword( action, keyword ) {
	var uri = "/?command=" + action + "&keywords=" + keyword;
	//alert( uri );
	var request = makeHttpObject();
	request.open("GET", uri, false );
	request.send(null);
}

function toggleButton(el) {
	if ( el.className == "dn" || el.name == "smallButton" ) {
		el.className = "up"
		changeKeyword( "removeKeywords", el.innerText )
	} else {
		el.className = "dn"
		changeKeyword( "addKeywords", el.innerText )
	}
}

//------------------------------------------------------------------------------

var currentPhotoId = "<%= imageId %>";
var currentKeywords = null;

function setKeywords( keywords ) {

	if ( keywords == null )
		keywords = "";

	if ( currentKeywords == keywords )
		return;

	currentKeywords = keywords;
	var field = document.getElementsByName("keywords")[0];
	if ( field ) 
		field.value = keywords;

	keywords = keywords.split(',');	
	var keywordNames = [];
	
	for( var i in keywords ) {
		keywordNames[ keywords[ i ] ] = true;
	}

	var els = document.getElementsByName("largeButton");
	
	for( var i in els ) {
		var el = els[ i ];
		var name = el.innerText;
		if ( keywordNames[ name ] ) {
			keywordNames[ name ] = false;
			el.className = "dn";
		}
		else {
			el.className = "up";
		}
	}

	var smallButtons = document.getElementsByName("smallButton");
	
	var smallButtonIndex = 0;
	for( var n in keywordNames ) {
		if ( n && n != "" && keywordNames[ n ] ) {
			smallButtons[ smallButtonIndex ].innerHTML = n;
			smallButtons[ smallButtonIndex ].style.display = "";
			smallButtonIndex++;
			if ( smallButtonIndex > smallButtons.length )
				break;
		}
	}
	
	while( smallButtonIndex < smallButtons.length ) {
		smallButtons[ smallButtonIndex ].style.display = "none";
		smallButtons[ smallButtonIndex ].innerHTML = "-";
		smallButtonIndex++;
	}
}


function getKeywords() {
	var request = makeHttpObject();
	request.open("GET", "/?command=getKeywords", false );
	request.send(null);
	var keywords = request.responseText;
	setKeywords( keywords );
}

function checkForSelectionChange() {

	var request = makeHttpObject();
	request.open("GET", "/?command=getCurrentPhotoId", false );
	request.send(null);
	var id = request.responseText;
	
	if ( currentPhotoId == null || currentPhotoId == "" ) {
		currentPhotoId = id;
	} else if ( currentPhotoId != id ) {
		currentPhotoId = id;
		var img = document.getElementsByName("photo")[0];
		if ( img ) {
			img.src = "?command=getThumbnail&imageId=" + id + "&width=" + thumbSize + "&height=" + thumbSize;
			getKeywords();
		}
	}
}

// poll for selection changes in LR
window.setInterval( checkForSelectionChange, 500 );

// poll for keyword changes in LR
window.setInterval( getKeywords, 500 );

window.onload = function() {
	getKeywords();
}

//------------------------------------------------------------------------------

function CMD( command ) {
	var request = makeHttpObject();
	request.open("GET", "/?command=" + command, false );
	request.send(null);
}

//------------------------------------------------------------------------------

document.onkeydown = function( e ) {
    e = e || window.event;
    if (e.keyCode == '37') {
		CMD( 'previousPhoto' );
	} else if (e.keyCode == '39') {
		CMD( 'nextPhoto' );
    }
}

//------------------------------------------------------------------------------

var screenW = window.innerWidth;
var screenH = window.innerHeight;
var thumbSize = (screenW < screenH ) ? screenW : screenH;

<% if prefs.allowEditKeywords then %>
thumbSize /= 3;
screenW /= 3;
screenH /= 3;
<% end %>

</script>

</head>
<body>

<% if prefs.showHeader then %>
<div class="header">
	<img src="images/header_logo_public.png" width="257" height="43" />
</div>
<% end %>

<% if prefs.allowViewPhotos then %>
	<center>
		<% if prefs.allowSwitchPhotos then %>
		<a href="javascript:CMD('nextPhoto')">
		<% end %>
			<script>
			document.write( '<img name="photo" class="photo" border="0" src="?command=getThumbnail&imageId=<%= imageId %>&width=' + thumbSize + '&height=' + thumbSize + '"/>' );
			</script>
		<% if prefs.allowSwitchPhotos then %>
		</a>
		<% end %>
	</center>
<% end %>

<table border="0" width="100%" cellpadding="0" cellspacing="0" style="position:absolute;bottom:0;" >
<tr>
	<% if prefs.allowTriggerCapture or prefs.allowSwitchViewModes then %>
	<td width="33%" valign="middle">
		<% if prefs.allowTriggerCapture then %>
			<a href="javascript:CMD('triggerCapture')"><img border="0" src="images/capture_button.png" valign="middle" /></a>
		<% end %>
		<% if prefs.allowSwitchViewModes then %>
			<a href="javascript:CMD('gridView')"><img border="0" src="images/grid.png" valign="middle"/></a>
			<a href="javascript:CMD('loupeView')"><img border="0" src="images/loupe.png" valign="middle"/></a>
		<% end %>
	</td>
	<% end %>

	<% if prefs.allowEditKeywords then
		if onlyKeywords then
		%>
		<div class="buttonGrid" >
		<% else %>
		<div class="buttonGrid" style="width:50%;float:left;" >
		<% end %>
			<button name="largeButton" onclick="toggleButton(this)">Katie</button>
			<button name="largeButton" onclick="toggleButton(this)">Milo</button>
			<button name="largeButton" onclick="toggleButton(this)">Benjamin</button>
			<button name="largeButton" onclick="toggleButton(this)">Ben</button>
			<button name="largeButton" onclick="toggleButton(this)">Jesse</button>
			<button name="largeButton" onclick="toggleButton(this)">Andy</button>
			<button name="largeButton" onclick="toggleButton(this)">Brian</button>
			<button name="largeButton" onclick="toggleButton(this)">Baichao</button>
			<button name="largeButton" onclick="toggleButton(this)">Chet</button>
			<button name="largeButton" onclick="toggleButton(this)">Craig</button>
			<button name="largeButton" onclick="toggleButton(this)">Dave</button>
			<button name="largeButton" onclick="toggleButton(this)">Eric</button>
			<button name="largeButton" onclick="toggleButton(this)">Flep</button>
			<button name="largeButton" onclick="toggleButton(this)">George</button>
			<button name="largeButton" onclick="toggleButton(this)">Henry</button>
			<button name="largeButton" onclick="toggleButton(this)">Jianping</button>
			<button name="largeButton" onclick="toggleButton(this)">Julie</button>
			<button name="largeButton" onclick="toggleButton(this)">Kids</button>
			<button name="largeButton" onclick="toggleButton(this)">Paul</button>
			<button name="largeButton" onclick="toggleButton(this)">PhilC</button>
			<button name="largeButton" onclick="toggleButton(this)">PhilL</button>
			<button name="largeButton" onclick="toggleButton(this)">Simon</button>
			<button name="largeButton" onclick="toggleButton(this)">Tom</button>
			<button name="largeButton" onclick="toggleButton(this)">City</button>
			<button name="largeButton" onclick="toggleButton(this)">Forest</button>
			<button name="largeButton" onclick="toggleButton(this)">Flowers</button>
			<button name="largeButton" onclick="toggleButton(this)">Landscape</button>
			<button name="largeButton" onclick="toggleButton(this)">Night</button>
			<button name="largeButton" onclick="toggleButton(this)">River</button>
			<button name="largeButton" onclick="toggleButton(this)">Trees</button>
		</div>
		<br/>
		<% if onlyKeywords then %>
		<div class="smallButtonGrid" >
		<% else %>
		<div class="smallButtonGrid" style="width:50%;float:left;" >
		<% end %>
			<button name="smallButton" onclick="toggleButton(this)"></button>
			<button name="smallButton" onclick="toggleButton(this)"></button>
			<button name="smallButton" onclick="toggleButton(this)"></button>
			<button name="smallButton" onclick="toggleButton(this)"></button>
			<button name="smallButton" onclick="toggleButton(this)"></button>
			<button name="smallButton" onclick="toggleButton(this)"></button>
			<button name="smallButton" onclick="toggleButton(this)"></button>
			<button name="smallButton" onclick="toggleButton(this)"></button>
			<button name="smallButton" onclick="toggleButton(this)"></button>
			<button name="smallButton" onclick="toggleButton(this)"></button>
			<button name="smallButton" onclick="toggleButton(this)"></button>
		</div>
		<% 
			--else
			if prefs.allowViewPhotos then
		%>
		<td width="33%" valign="middle">
			<div class="keywordPanel" >
				<form action="/?command=addKeywords" method="POST">
				Keywords
				<textarea rows="3" style="width:100%;" name="keywords"></textarea>
				<div style="text-align:right"><input type="submit" value="Save" class="submit" /></div>
				</form>
			</div>
		</td>
	<% 
		end 
	end %>
	
	<td valign="middle" align="<%= onlyNav and 'center' or 'right' %>" style="padding-right:4px;" >
	<% if prefs.allowControlSlideshow or prefs.allowSwitchPhotos then %>
		<table border="0" cellspacing="0" cellpadding="0">
			<tr>
				<td><a href="javascript:CMD('previousPhoto')"><img border="0" src="images/slideshow_previous.png"/></a></td>
				<% if prefs.allowControlSlideshow then %>
				<td><a href="javascript:CMD('startSlideshow')"><img border="0" src="images/slideshow_play.png"/></a></td>
				<% end %>
				<td><a href="javascript:CMD('nextPhoto')"><img border="0" src="images/slideshow_next.png"/></a></td>
			</tr>
		</table>
	<% else %>
	<%if prefs.allowControlSlideshow then %>	
	<div style="background-color:#000000;">
	<% end %>
	<% if prefs.allowSwitchPhotos then %>
		<a href="javascript:CMD('previousPhoto')"><img border="0" src="images/previous.png" valign="middle"/></a>
	<% end %>
	<% if prefs.allowControlSlideshow then %>
		<a href="javascript:CMD('startSlideshow')"><img border="0" src="images/play.png" valign="middle"/></a>
		<a href="javascript:CMD('stopSlideshow')"><img border="0" src="images/pause.png" valign="middle"/></a>
	<% end %>
	<% if prefs.allowSwitchPhotos then %>
		<a href="javascript:CMD('nextPhoto')"><img border="0" src="images/next.png" valign="middle"/></a>
	<% end %>		
	<% if prefs.allowControlSlideshow then %>
	</div>
	<% end end %>
	</td>
</tr>
</table>


<!--
<div style="width:100%;background-color:#666666;vertical-align:middle;">
<center>

	<% if prefs.allowTriggerCapture then %>
	<a href="javascript:CMD('triggerCapture')"><img border="0" src="images/capture_button.png" valign="middle" /></a>
	<% end %>

	<% if prefs.allowSwitchViewModes then %>
	<a href="javascript:CMD('gridView')"><img border="0" src="images/grid.png" valign="middle"/></a>
	<a href="javascript:CMD('loupeView')"><img border="0" src="images/loupe.png" valign="middle"/></a>
	<% end %>
		
	<% if prefs.allowSwitchPhotos then %>
	<a href="?command=previousPhoto"><img border="0" src="images/previous.png" valign="middle"/></a>
	<a href="?command=nextPhoto"><img border="0" src="images/next.png" valign="middle"/></a>
	<% end %>	

</center>
</div>

<% if prefs.allowEditKeywords then
	if onlyKeywords then
%>
	<div class="buttonGrid">
		<button onclick="toggleButton(this)">Katie</button>
		<button onclick="toggleButton(this)">Milo</button>
		<button onclick="toggleButton(this)">Benjamin</button>
		<button onclick="toggleButton(this)">Ben</button>
		<button onclick="toggleButton(this)">Grandma</button>
		<button onclick="toggleButton(this)">Jesse</button>
		<button onclick="toggleButton(this)">Andy</button>
		<button onclick="toggleButton(this)">Brian</button>
		<button onclick="toggleButton(this)">Chet</button>
		<button onclick="toggleButton(this)">Craig</button>
	</div>
<% else %>
	<div style="width:100%;background-color:#666666;vertical-align:middle;">
		<center>
		<div class="keywordPanel" >
			Keywords
			<textarea rows="4" style="width:100%;" name="keywords"></textarea>
			<div style="text-align:right"><input type="submit" value="Save" class="submit" /></div>
		</div>
		</center>
	</div>
<% end
end %>

<br/>
<br/>

-->

</body>
</html>