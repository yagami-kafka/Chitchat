
    var loginbtn = document.getElementById("login-form");
    var registerbtn = document.getElementById("register-form");
    var btn = document.getElementById("btn");

    function register(){
        loginbtn.style.left = "-400px";
        registerbtn.style.left = "50px";
        btn.style.left = "110px";
        document.getElementById("registertoggle").style.color = "white";
        document.getElementById("logintoggle").style.color = "black";
    }

    function login(){
        loginbtn.style.left = "50px";
        registerbtn.style.left = "450px";
        btn.style.left = "0px";
        document.getElementById("registertoggle").style.color = "black";
        document.getElementById("logintoggle").style.color = "white";
    }
