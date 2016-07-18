window.onload = function(){

    var url = "/popads.net";
    var secs = 5;
    var currentTime;
    var videoele;
    var script;

    $.ajax({
         url:url,
         crossDomain: true,
         error: function(){
             setTimeout(interrupt, secs * 1000);
         }
    });


    function interrupt(){
        $("#message").removeClass("hidden");
        videoele = $("#videodiv").remove();
        script = $("script").remove();
    }

    $( "#reloadvid" ).click(function() {
            $.ajax({
                 url:url,
                 crossDomain: true,
                 success: function(){
                       $("#message").addClass("hidden");
                       $('body').append(videoele);
                       $('body').append(script);
                 },
                 error: function(){
                     $("#alert").removeClass("hidden");

                 }
            });
    });
};


