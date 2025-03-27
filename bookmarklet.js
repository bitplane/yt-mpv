javascript:(function(){
    window.location.href = window.location.href.replace(
        /^http(s?):\/\//, 
        'x-yt-ulp$1://'
    );
})();
