$(document).ready(function () {
    checkCookie();
});

function checkCookie() {
    let cookieArr = document.cookie.split(";");
    try {
        for (let i = 0; i < cookieArr.length; i++) {
            let logIn = cookieArr[i].match('mytoken')

            if (logIn) { // 로그인 상태 //
                let loginBtn = document.querySelector(".btn-login");
                loginBtn.innerHTML = "로그아웃";
                loginBtn.addEventListener("click", logOut);

                let signupBtn = document.querySelector(".btn-mypg");
                signupBtn.style.display = 'none';
            }
        }
    } catch (e) {

    }
}

function logOut() {
    document.cookie = "mytoken=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    window.location.href = "/"
}

