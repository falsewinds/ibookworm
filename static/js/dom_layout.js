import { dom_wrapper } from "./dom_wrapper.js"

class LayoutElement {
    constructor(elem,methods) {
        if (elem.length==1) {
            this.element = elem[0];
            this.wrapper = new dom_wrapper(elem[0]);
            if (typeof methods == "object") {
                for(let m in methods) {
                    let callback = methods[m];
                    this[m] = function() {
                        return callback.apply(this.wrapper,arguments);
                    };
                }
            }
        } else {
            this.elements = elem;
            this.wrappers = elem.map(e=>new dom_wrapper(e));
            if (typeof methods == "object") {
                for(let m in methods) {
                    let callback = methods[m], args = arguments;
                    this[m] = function() {
                        return this.wrappers.map((w)=>{
                            return callback.apply(w,args);
                        });
                    };
                }
            }
        }
    };
};

class Layout {
    constructor(cfg) {
        this.regions = {};
        for(let key in cfg) { this.set(key,cfg[key]); }
        this.shortcuts = {};
        window.addEventListener("keydown",(e)=>{
            let identifier = ["alt","ctrl","shift"].reduce((trigger,k)=>{
                if (e[k+"Key"]) { trigger.push(k); }
                return trigger;
            },[]);
            identifier.push(e.key.toLowerCase());
            identifier = identifier.join("+");
            if (identifier in this.shortcuts) {
                let shortcut = this.shortcuts[identifier],
                    ret = shortcut.apply(e.target,[e]);
                if (ret!==true) { e.preventDefault(); }
            }
        });
    };
    set(key,cfg) {
        let elem = null;
        if (typeof cfg == "object") {
            if (cfg instanceof Array) {
                elem = cfg;
                cfg = {};
            } else if (cfg instanceof dom_wrapper) {
                elem = [cfg.element];
                cfg = {};
            } else if (cfg instanceof HTMLElement) {
                elem = [cfg];
                cfg = {};
            } else if ("element" in cfg) {
                elem = cfg["element"];
                if (typeof elem == "string") {
                    elem = [...document.querySelectorAll(elem)];
                }
            }
        } else if (typeof cfg == "string") {
            elem = [...document.querySelectorAll(cfg)];
            cfg = {};
        }
        elem = elem.reduce((htmls,item)=>{
            if (item instanceof HTMLElement) {
                htmls.push(item);
            } else {
                console.warn("No a HTMLElement!",item);
            }
            return htmls;
        },[]);
        if (elem.length<=0) {
            console.error("No matching HTMLElement!");
            return;
        }
        let wrapper = new LayoutElement(elem,cfg?.methods);
        this.regions[key] = wrapper;
        return wrapper;
    };

    get(key) {
        if (key in this.regions) { return this.regions[key]; }
        return null;
    };

    on(shortcut,callback) {
        this.shortcuts[shortcut] = callback;
    };
};

/*------------------------------------------------------------*\
 * locate_element
\*------------------------------------------------------------*/
const direction_map = {
    " top": "h_center top",
    " left": "v_center left",
    " right": "v_center right",
    " bottom": "h_center botoom",
    "top": "top h_center",
    "top left": "top left",
    "top right": "top right",
    "top center": "top h_center",
    "left": "left v_center",
    "left top": "left top",
    "left bottom": "left bottom",
    "left center": "left v_center",
    "right": "right v_center",
    "right top": "right top",
    "right bottom": "right bottom",
    "right center": "right v_center",
    "bottom": "bottom h_center",
    "bottom left": "bottom left",
    "bottom right": "bottom right",
    "bottom center": "bottom h_center",
    "center top": "h_center top",
    "center left": "v_center left",
    "center right": "v_center right",
    "center bottom": "h_center botoom",
}

function calculate_area(position,w,h) {
    let x = ("left" in position) ? position.left : position.right - w,
        y = ("top" in position) ? position.top : position.bottom - h,
        oh = 0, ov = 0;
    if (x<0) { oh += -x; }
    if (x+w>window.innerWidth) { oh += (x+w) - window.innerWidth; }
    if (y<0) { ov += -y; }
    if ((y+h)>window.innerHeight) { ov += (y+h) - window.innerWidth; }
    return (oh*h)+(ov*w)-(oh*ov);
}

function sort_by_area(l1,l2) {
    if (l1.area==l2.area) { return 0; }
    return (l1.area<l2.area) ? 1 : -1;
}

function locate_element(elem,pivot,args,offset = [4,0]) {
    if (!(elem instanceof HTMLElement)) { return; }
    if (!(pivot instanceof HTMLElement)) { pivot = document.body; }
    let ebox = elem.getBoundingClientRect(),
        pbox = pivot.getBoundingClientRect(),
        ww = window.innerWidth, wh = window.innerHeight;
    args = (args instanceof Array) ? args : [args];
    let locator = args.map((arg)=>{
        let weight = arg.toLowerCase?.();
        if (weight in direction_map) {
            weight = direction_map[weight];
        } else {
            return { "area": ebox.width * ebox.height };
        }
        let position = weight.split(" ").reduce((dict,k,i)=>{
            let off = isNaN(offset[i]) ? 0 : parseFloat(offset[i]);
            switch (k+i) {
            case "top1":
            case "left1":
                dict[k] = pbox[k] + off;
                break;
            case "right1":
                dict[k] = (ww-pbox[k]) + off;
                break;
            case "bottom1":
                dict[k] = (wh-pbox[k]) + off;
                break;
            case "top0":    dict["bottom"] = pbox["top"] + off; break;
            case "left0":   dict["right"] = pbox["left"] + off; break;
            case "right0":  dict["left"] = pbox["right"] + off; break;
            case "bottom0": dict["top"] = pbox["bottom"] + off; break;
            case "h_center0":
            case "h_center1":
                dict["left"] = pbox.left + (pbox.width - ebox.width) / 2;
                break;
            case "v_center0":
            case "v_center1":
                dict["top"] = pbox.top + (pbox.height - ebox.height) / 2;
                break;
            }
            return dict;
        },{});
        return {
            "area": calculate_area(position,ebox.width,ebox.height),
            "position": position
        };
    }).sort(sort_by_area)[0].position;
    ["top","left","right","bottom"].forEach((k)=>{
        elem.style[k] = (k in locator) ? (locator[k]+"px") : "auto";
    });
}

export { Layout, locate_element };