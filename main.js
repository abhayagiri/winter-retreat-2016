$(document).ready(function() {

  var player = $("#jquery-jplayer");
  var playerContainer = $("#jquery-jplayer-container");

  player.jPlayer({
    swfPath: "Web/lib/jplayer",
    supplied: "mp3",
    solution: "html, flash",
    wmode: "window",
    errorAlerts: true,
    cssSelectorAncestor: "#jquery-jplayer-container",
    useStateClassSkin: true,
    autoBlur: false,
    smoothPlayBar: true,
    keyEnabled: false,
    remainingDuration: true,
    toggleDuration: true
  });

  player.bind($.jPlayer.event.pause, function(event) {
    if (event.jPlayer.status.currentTime == 0) {
      playerContainer.fadeOut();
    }
  });

  player.bind($.jPlayer.event.ended, function(event) {
    playerContainer.fadeOut();
  });

  function playAudio(url, title, time) {
//    console.log(["playAudio", url, title, time]);
    playerContainer.fadeIn();
    player.jPlayer("setMedia", {
      title: title,
      mp3: url
    }).jPlayer("play", time);
  }

  $('a[href$=".mp3"]').on('click', function(event) {
    event.preventDefault();
    var a = $(event.currentTarget);
    var href = a.attr('href');
    var title = a.attr('title');
    var skipMatches = a.text().match(/^([0-9]+):([0-9]+)$/);
    if (skipMatches) {
      var time = Number(skipMatches[1]) * 60 + Number(skipMatches[2]);
    } else {
      var time = 0;
    }
    playAudio(href, title, time);
  });


})
