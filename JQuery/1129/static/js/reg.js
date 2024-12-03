/**
 * Created by zongjuan.wang on 2016/7/6.
 */

$(document).ready(function(){
    $("#submit").click(function(){
        var u=document.getElementById("uName");
        if(u.validity.valueMissing==true){
            u.setCustomValidity("昵称不能为空");
        }
        else if(u.validity.patternMismatch==true){
            u.setCustomValidity("昵称必须是6~10位的英文和数字");
        }
        else{
            u.setCustomValidity("");
        }

        var pwd=document.getElementById("pwd");
        if(pwd.validity.valueMissing==true){
            pwd.setCustomValidity("密码不能为空");
        }
        else if(pwd.validity.patternMismatch==true){
            pwd.setCustomValidity("密码必须是6~16位的英文和数字");
        }
        else{
            pwd.setCustomValidity("");
        }

        var email=document.getElementById("email");
        if(email.validity.valueMissing==true){
            email.setCustomValidity("邮箱不能为空");
        }
        else if(email.validity.typeMismatch==true){
            email.setCustomValidity("邮箱格式不正确");
        }
        else{
            email.setCustomValidity("");
        }

    })
})

