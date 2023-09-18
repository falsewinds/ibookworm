import { dom_wrapper } from "./dom_wrapper.js"

/*------------------------------------------------------------*\
 * Cover SVG
\*------------------------------------------------------------*/
let covered_svg = null, saved_overflow;
function cover(clip) {
    saved_overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    if (covered_svg==null) {
        covered_svg = dom_wrapper.Create([
            "svg.-cover", [
                ["g", [
                    "rect[x=\"0\"][y=\"0\"][fill=\"rgba(0,0,0,0.65)\"]"
                ]]
            ]
        ])[0];
    }
    let w = window.innerWidth, h = window.innerHeight;
    covered_svg.set_attr({ "width": w, "height": h });
    covered_svg.query("rect").set_attr({ "width": w, "height": h });
    document.body.appendChild(covered_svg.element);
}
function discover() {
    document.body.removeChild(covered_svg.element);
    document.body.style.overflow = saved_overflow;
}

/*------------------------------------------------------------*\
 * Dialog
\*------------------------------------------------------------*/
let dialog_wrapper = null;
function get_form_data(form) {
    let fields = form.querySelectorAll("input,select,textarea"),
        formdata = {};
    for(let i=0;i<fields.length;i++) {
        let field = fields[i],
            n = field.getAttribute("name");
        if (typeof n == "string") {
            formdata[n] = field.value;
        }
    }
    return formdata;
};
function show_dialog(caption,inputs,
    buttons = ["confirm","cancel"],
    success = "confirm") {
    cover();
    if (dialog_wrapper==null) {
        dialog_wrapper = dom_wrapper.Create([
            ".-dialog", [
                ".-caption",
                ["form.-center",[
                    ".-fields",
                    ".-buttons"
                ]]
            ]
        ])[0];
        dialog_wrapper.element.style.visibility = "hidden";
    }
    if (dialog_wrapper.element.style.visibility != "hidden") {
        console.error("Dialog is actived!");
    }
    dialog_wrapper.query(".-caption").clear().text(caption);
    dialog_wrapper.query(".-fields").clear()
        .append(inputs.map((input,index)=>{
            let tag = ("tag" in input) ? input.tag : "input",
                name = ("name" in input) ? input.name : "field"+index,
                attr = ("attr" in input) ? input.attr : {};
            attr["name"] = name;
            if (index==0) { attr["kj-first-field"] = "LookAtMe"; }
            let e = new dom_wrapper(tag,null,[],attr,null,null);
            let title = ("title" in input) ? input.title : name,
                lbl = new dom_wrapper("label",null,[],{"kj-label":title},null,null);
            lbl.append(e);
            return lbl;
        }));
    dialog_wrapper.query(".-buttons").clear()
        .append(buttons.map((btn)=>{
            return new dom_wrapper(
                "button", null, [btn],
                { "kj-result": btn },
                btn, null);
        }));
    success = (success instanceof Array) ? success : [success];
    let w = dialog_wrapper.element.offsetWidth,
        h = dialog_wrapper.element.offsetHeight,
        mh = (window.innerWidth - w) / 2,
        mv = (window.innerHeight - h) / 4;
    dialog_wrapper.element.style.margin = mv+"px "+mh+"px";
    dialog_wrapper.element.style.visibility = "visible";
    return new Promise((suc,rej)=>{
        dialog_wrapper.query("*[kj-first-field]")?.element.focus();
        let form = dialog_wrapper.query("form").element;
        let dialog_submit = (e)=>{
            e.preventDefault();
            hide_dialog();
            let result = e.submitter.getAttribute("kj-result");
            if (success.includes(result)) {
                suc(get_form_data(form));
            } else { rej(result); }
            form.removeEventListener("submit",dialog_submit);
            discover();
        };
        form.addEventListener("submit",dialog_submit);
    });
}
function hide_dialog() {
    dialog_wrapper.element.style.visibility = "hidden";
}

/*------------------------------------------------------------*\
 * IBookwormApp : status
\*------------------------------------------------------------*/
let app_status = null;
/*------------------------------------------------------------*\
 * IBookwormApp : module
\*------------------------------------------------------------*/
let module_waiting_list = [],
    module_loaded = {},
    module_index_map = {};
function load_module() {
    const ENDPOINT = "IBOOKWORM.XYZ";
    module_waiting_list.push(ENDPOINT);
    let builds = 0, loaded = 0;
    while (module_waiting_list.length>0) {
        let m = module_waiting_list.shift();
        if (m==ENDPOINT) {
            if (module_waiting_list.length<=0) { break; }
            if (builds==0) {
                console.error(
                    "Following module(s) dependency is missing!",
                    module_waiting_list);
                break;
            }
            loaded += builds;
            builds = 0;
            module_waiting_list.push(ENDPOINT);
            continue;
        }
        let d = m.dependency.filter((mk)=>(mk in module_loaded));
        if (d.length>0) {
            this.builds.push(m)
            continue;
        }
        let scope = {};
        m.initialize(scope,this);
        scope.types?.forEach((tk)=>{
            if (!(tk in module_index_map)) {
                module_index_map[tk] = [];
            }
            module_index_map[tk].push(m.key);
        });
        module_loaded[m.key] = scope;
        builds++;
    }
    console.log("[IBookwormApp] "+loaded+" module(s) loaded.");
}

/*------------------------------------------------------------*\
 * IBookwormApp : delay_call
\*------------------------------------------------------------*/
let callback_waiting_list = [];
function delay_call(ap) {
    let called = 0;
    while (callback_waiting_list.length>0) {
        let callback = callback_waiting_list.shift();
        callback?.apply(ap,[ap]);
        called++;
    }
    console.log("[IBookwormApp] "+called+" function(s) called.");
}

/*------------------------------------------------------------*\
 * IBookwormApp : HEADER control
\*------------------------------------------------------------*/
const header_loop_text = [
    "I, Bookworm.",
    "我，書蟲。",
    "俺、本の虫。"
];
let svg_dialogue = undefined, next_loop = null;
function start_header_loop(sec) {
    if (svg_dialogue===undefined) {
        svg_dialogue = document.querySelector("header svg.dialogue text");
    }
    if (svg_dialogue===null) { return; }
    next_loop = setTimeout(()=>{
        let next = header_loop_text.indexOf(svg_dialogue.textContent);
        if (next<0) { next = 0; }
        else { next = (next+1) % header_loop_text.length; }
        svg_dialogue.textContent = header_loop_text[next];
        start_header_loop(Math.random()*30+30);
    },sec*100);
}
function stop_header_loop() {
    clearTimeout(next_loop);
}

/*------------------------------------------------------------*\
 * IBookwormApp : NAV control
\*------------------------------------------------------------*/
function trigger_nav_with_scroll(height = 48) {
    let nav = document.querySelector("nav");
    if (nav==null) { return; }
    let last = 0, hider = null;
    window.addEventListener("scroll",()=>{
        if (hider!=null) { clearTimeout(hider); }
        let y = window.scrollY, dy = y - last;
        last = y;
        if (y<height) {
            nav.classList.remove("hidden");
        } else if (dy>0) {
            nav.classList.add("hidden");
        } else {
            nav.classList.remove("hidden");
            hider = setTimeout(()=>{
                nav.classList.add("hidden");
                hider = null;
            },2000);
        }
    });
}

/*------------------------------------------------------------*\
 * IBookwormApp
\*------------------------------------------------------------*/
class IBookwormApp {
    constructor() {
        this.dialog = show_dialog;
    };

    svg(tag, clss=[], attrs={}) {
        if (app_status!="loaded") { return null; }
        let e = document.createElementNS("http://www.w3.org/2000/svg",tag);
        if (clss instanceof Array) {
            clss.forEach((c)=>{ e.classList.add(c); });
        } else if (typeof clss == "string") {
            e.classList.add(clss);
        } else { console.error("invalid clss!",clss); }
        for(let k in attrs) {
            e.setAttributeNS(null,k,attrs[k]);
        }
        return e;
    }
    dom(tag, clss=[], text=null) {
        if (app_status!="loaded") { return null; }
        let e = document.createElement(tag);
        if (clss instanceof Array) {
            clss.forEach((c)=>{ e.classList.add(c); });
        } else if (typeof clss == "string") {
            e.classList.add(clss);
        } else { console.error("invalid clss!",clss); }
        if (text!=null) {
            e.appendChild(document.createTextNode(text));
        }
        if (e.listen) { console.log(e.listen); }
        e.listen = function() {
            this.addEventListener.apply(this,arguments);
            return this;
        };
        return e;
    };

    extends(key,dep,init) {
        module_waiting_list.push({
            "key": key,
            "dependency": (dep instanceof Array) ? dep : [dep],
            "initialize": (typeof init == "function") ? init : ()=>init
        });
        if (app_loaded) { load_module(); }
    };

    ready(callback) {
        if (app_status=="loaded") {
            callback.apply(this,[this]);
            return;
        }
        callback_waiting_list.push(callback);
    };

    async post(url,data) {
        return fetch(url,{
            "method": "POST",
            "body": JSON.stringify(data),
            "headers": {
                "Content-Type": "application/json"
            }
        }).then((resp)=>{
            return resp.json();
        });
    };

    speak(text) {
        if (svg_dialogue==null) { return; }
        if (app_status!="loaded") { return; }
        if (text==null) {
            start_header_loop(Math.random()*30+30);
            return;
        }
        svg_dialogue.textContent = text;
        stop_header_loop();
    };

    ctrl_nav(show) {
        if (app_status!="loaded") { return; }
        let nav = document.querySelector("nav");
        if (nav!=null) {
            if (show===true) { nav.classList.add("hidden"); }
            else { nav.classList.remove("hidden"); }
        }
    };
    show_nav() { this.ctrl_nav(true); };
    hide_nav() { this.ctrl_nav(false); };

    run() {
        if (app_status!=null) { return; }
        window.addEventListener("beforeunload",()=>{
            console.log("beforeunload",this);
        });
        let loader = ()=>{
            if (app_status=="loaded") { return; }
            if (document.readyState!="complete") { return; }
            start_header_loop(Math.random()*30+30);
            trigger_nav_with_scroll(48);
            app_status = "loaded";
            load_module();
            delay_call(this);
            window.removeEventListener("load",loader);
        };
        window.addEventListener("load",loader);
        app_status = "before_load"
    };
};

export const app = new IBookwormApp();