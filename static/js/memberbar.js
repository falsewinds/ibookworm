import { app } from "./ibookworm.js";

app.extends("MemberTools",[],()=>{
    let member_tool = app.dom(".icon").listen("click",()=>{
        app.menu("membermenu",
            ["My Page","Settings","-","Logout"],
            member_tool.element,
            "bottom right"
        ).then((e)=>{
            switch(e.textContent) {
            case "My Page":
                if (location.pathname!="/me/") {
                    location.href = "/me/";
                }
                break;
            case "Logout":
                location.href = "/logout";
                break;
            case "Settings":
                break;
            }
        }).catch(()=>{});
    });
    let p = document.querySelector("nav > .-wrapper");
    if (p!=null) { p.appendChild(member_tool.element); }
    else { member_tool.add_class("-floating"); }
});