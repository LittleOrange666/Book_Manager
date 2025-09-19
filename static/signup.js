let login_btn = document.getElementById("do_login_btn");

login_btn.addEventListener("click", function() {
    let user = document.getElementById("user_id").value;
    let pwd = document.getElementById("password").value;
    let form = new FormData();
    form.append("username", user);
    form.append("password", pwd);
    fetch("/api/signup", {
        method: "POST",
        body: form
    }).then(response => {
        if (response.status === 200) {
            window.location.href = "/";
        } else {
            alert("Signup failed.");
        }
    });
});