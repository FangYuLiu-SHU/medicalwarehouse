(() => {
    if($.cookie("name") !== "testAccount") {
        location.href="/";
    }
})()