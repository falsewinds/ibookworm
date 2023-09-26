import { dom_wrapper } from "./dom_wrapper.js"
import { locate_element, Layout } from "./dom_layout.js"

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
let dialog_wrapper = null, dialog_caching = {};
function is_cached(key,data) {
    let jsonstr = JSON.stringify(data), cached = false;
    if (key in dialog_caching) {
        cached = (dialog_caching[key]==jsonstr);
    }
    if (!cached) { dialog_caching[key] = jsonstr; }
    return cached;
}
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
async function show_dialog(caption, fields, buttons, success, validater) {
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
    if (!is_cached("fields",fields)) {
        dialog_wrapper.query(".-fields").clear()
            .append(fields.map((field,index)=>{
                let tag = ("tag" in field) ? field.tag : "input",
                    name = ("name" in field) ? field.name : "field"+index,
                    attr = ("attr" in field) ? field.attr : {};
                attr["name"] = name;
                if (index==0) { attr["kj-first-field"] = "LookAtMe"; }
                let e = new dom_wrapper(tag,null,[],attr,null,null);
                if (tag=="select" && "options" in field) {
                    let opts = field.options;
                    for(let k in opts) {
                        e.append(new dom_wrapper(
                            "option",null,[],
                            {"value":k},opts[k],null));
                    }
                }
                let title = ("title" in field) ? field.title : name,
                    lbl = new dom_wrapper("label",null,[],{"kj-label":title},null,null);
                lbl.append(e);
                return lbl;
            }));
    }
    if (!is_cached("buttons",buttons)) {
        dialog_wrapper.query(".-buttons").clear()
            .append(buttons.map((btn)=>{
                return new dom_wrapper(
                    "button", null, [btn],
                    { "kj-result": btn },
                    btn, null);
            }));
    }
    success = (success instanceof Array) ? success : [success];
    let w = dialog_wrapper.element.offsetWidth,
        h = dialog_wrapper.element.offsetHeight,
        mh = (window.innerWidth - w) / 2,
        mv = (window.innerHeight - h) / 4;
    dialog_wrapper.element.style.margin = mv+"px "+mh+"px";
    dialog_wrapper.element.style.visibility = "visible";
    if (typeof validater != "function") { validater = ()=>true; }
    return new Promise((suc,rej)=>{
        dialog_wrapper.query("*[kj-first-field]")?.element.focus();
        let form = dialog_wrapper.query("form").element;
        let dialog_submit = (e)=>{
            e.preventDefault();
            let result = e.submitter.getAttribute("kj-result");
            if (success.includes(result)) {
                let fd = get_form_data(form);
                if (!validater(fd)) { return; }
                suc(fd);
            } else { rej(result); }
            dialog_wrapper.element.style.visibility = "hidden";
            form.removeEventListener("submit",dialog_submit);
            discover();
        };
        form.addEventListener("submit",dialog_submit);
    });
}

/*------------------------------------------------------------*\
 * Menu
\*------------------------------------------------------------*/
let menus = {};
function create_menu(key,items) {
    if (key in menus) { return; }
    let menu = new dom_wrapper(".-menu");
    menu.element.style.visibility = "hidden";
    menu.listen("menu_submit",(e)=>{
        menu.element.style.visibility = "hidden";
        if (e?.detail==null) {
            menu?.__reject?.("No item select");
            return;
        }
        let item = e.detail?.item,
            callback = e.detail?.callback;
        if (typeof callback == "function") {
            callback.apply(item,[menu.element]);
        }
        menu?.__resolve?.(item);
    });
    menu.append(items.map((it)=>{
        if (it=="-") { return new dom_wrapper(".-separater"); }
        let menuitem = new dom_wrapper(".-menuitem"),
            callback = () => true;
        switch (typeof it) {
        case "string":
            menuitem.text(it);
            break;
        case "object":
            if ("title" in it) { menuitem.text(it.title); }
            if (typeof it.callback == "function") {
                callback = it.callback;
            }
            break;
        }
        menuitem.listen("click",function(e) {
            menu.element.dispatchEvent(new CustomEvent("menu_submit",{
                "detail": {
                    "item": this,
                    "callback": callback
                }
            }))
        });
        return menuitem.element;
    }));
    menus[key] = menu;
}
async function show_menu(key,target,dir) {
    if (!(key in menus)) { return Promise.reject("No Menu."); }
    let menu = menus[key];
    if (menu.element.style.visibility != "hidden") {
        menu.element.dispatchEvent(new CustomEvent("menu_submit"));
        return Promise.reject("Menu is actived.");
    }
    if (typeof target == "string") { target = document.querySelector(target); }
    if (!(target instanceof HTMLElement)) {
        //console.error("Menu should has HTMLElement parent!");
        return Promise.reject("Menu should has HTMLElement parent!");
    }
    // TODO: calculate target position & menu position
    locate_element(menu.element,target,dir);
    return new Promise((suc,rej)=>{
        menu.__resolve = suc;
        menu.__reject = rej;
        menu.element.style.visibility = "visible";
    });
}

/*------------------------------------------------------------*\
 * Notify
\*------------------------------------------------------------*/

/*------------------------------------------------------------*\
 * IBookwormApp : status
\*------------------------------------------------------------*/
let app_status = null;

/*------------------------------------------------------------*\
 * IBookwormApp : module
\*------------------------------------------------------------*/
let module_waiting_list = [],
    module_loaded = {};
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
        let d = m.dependency.filter((mk)=>!(mk in module_loaded));
        if (d.length>0) {
            module_waiting_list.push(m)
            continue;
        }
        let scope = {};
        m.initialize(scope,this);
        module_loaded[m.key] = scope;
        builds++;
    }
    console.log("[IBookwormApp] "+loaded+" module(s) loaded.");
}

/*------------------------------------------------------------*\
 * IBookwormApp : delay_call
\*------------------------------------------------------------*/
const URL_PATH_KEY = [ null, "API", "repository", "doc_id" ]
let callback_waiting_list = [];
async function delay_call(ap) {
    let called = 0;
    let path = location.pathname,
        data = path.split("/").reduce((dict,s,i)=>{
            if (i>=URL_PATH_KEY.length) { return dict; }
            let k = URL_PATH_KEY[i],
                v = (s.length>0) ? s : null;
            if (k!=null && v!=null) { dict[k] = v; }
            return dict;
        },{});
    while (callback_waiting_list.length>0) {
        let cb = callback_waiting_list.shift(),
            ret = cb.callback?.apply(ap,[path,data,ap]);
        if (ret instanceof Promise) {
            await ret
                .then(data=>cb.resolve(data))
                .catch(err=>cb.reject(err));
        }
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
 * Service Worker
\*------------------------------------------------------------*/
async function register_serviceworker(filename) {
    if ("serviceWorker" in navigator) {
        try {
            const reg = await navigator.serviceWorker.register(
                filename, { scope: "/" });
            /*if (registration.installing) {
                console.log("正在安装 Service worker");
            } else if (registration.waiting) {
                console.log("已安装 Service worker installed");
            } else if (registration.active) {
                console.log("激活 Service worker");
            }*/
        } catch (e) { console.error(e); }
    }
}

/*------------------------------------------------------------*\
 * IBookwormApp
\*------------------------------------------------------------*/
class IBookwormApp {
    constructor() {
        register_serviceworker("/worker.js");
        //this.Layout = new Layout();
        //this.Module = null;
        this.actived = [];
    };

    dom(css,text) { return new dom_wrapper(css).text(text); };
    layout(cfg) { return new Layout(cfg); };

    extends(key,dep,init) {
        module_waiting_list.push({
            "key": key,
            "dependency": (dep instanceof Array) ? dep : [dep],
            "initialize": (typeof init == "function") ? init : ()=>init
        });
        if (app_status=="loaded") { load_module(); }
    };
    search(type) {
        let availables = [];
        for(let k in module_loaded) {
            let m = module_loaded[k];
            if (m.types?.includes?.(type)) {
                availables.push(k);
            }
        }
        return availables;
    };
    activate(key) {
        if (!(key in module_loaded)) {
            console.warn("No modules named ["+key+"]");
            return;
        }
        this.actived.push(key);
        module_loaded[key].enter?.();
    };
    deactivate(key) {
        if (!this.actived.includes(key)) {
            return;
        }
        if (!(key in module_loaded)) {
            console.warn("No modules named ["+key+"]");
            return;
        }
        module_loaded[key].leave?.();
    };
    Module(key) {
        if (!this.actived.includes(key)) {
            return null;
        }
        if (!(key in module_loaded)) {
            console.warn("No modules named ["+key+"]");
            return null;
        }
        return module_loaded[key];
    };
    m(k) { return this.Module(k); }

    async ready(callback) {
        if (app_status=="loaded") {
            let ret = callback.apply(this,[this]);
            if (ret instanceof Promise) { return ret; }
            return Promise.resolve();
        }
        let wrapped_callback = {
            "callback": callback
        };
        callback_waiting_list.push(wrapped_callback);
        return new Promise((suc,rej)=>{
            wrapped_callback.resolve = suc;
            wrapped_callback.reject = rej;
        });
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
            //console.log("beforeunload",this);
            for(let i=this.actived.length;i>=0;i++) {
                let a = this.actived[i],
                    m = module_loaded[a];
                if (m.check?.()!==false) {
                    /*e.preventDefault();
                    break;*/
                    return m.checkMessage;
                }
            }
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

    /*----------------------------*\
     * prepare types filter
    \*----------------------------*/
    accept_types() {
        let types = [], any = false;
        for(let i=0;i<arguments.length;i++) {
            let t = arguments[i].toLowerCase?.();
            if (t==null || t.length<=0) { continue; }
            if (t=="*" || t=="any") {
                any = true;
                break;
            }
            types.push(t);
        }
        if (types.length<=0 || any) {
            return { "includes": ()=>true };
        }
        return types;
    };

    /*----------------------------*\
     * UI interface
    \*----------------------------*/

    async dialog(caption,fields,validater) {
        return show_dialog(caption,fields,
            ["confirm","cancel"],"confirm",
            validater);
    };

    async menu(key,items,target,dir) {
        create_menu(key,items);
        return show_menu(key,target,dir);
    };
};

export const app = new IBookwormApp();