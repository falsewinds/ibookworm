import { dom_wrapper } from "./dom_wrapper.js"

class LayoutElement {
    constructor(elem,methods) {
        this.element = elem;
        this.wrapper = new dom_wrapper(elem);
        if (typeof methods == "object") {
            for(let m in methods) {
                let callback = methods[m];
                this[m] = function() {
                    callback.apply(this.wrapper,arguments);
                };
            }
        }
    };
};

class Layout {
    constructor() {
        this.regions = {};
    };

    initialize(reg_cfg) {
        this.regions = {};
        for(let key in reg_cfg) {
            this.set(key,reg_cfg[key]);
        }
    };
    set(key,cfg) {
        let elem = null;
        if (typeof cfg == "object") {
            if (cfg instanceof HTMLElement) {
                elem = cfg;
                cfg = {};
            } else if ("element" in cfg) {
                elem = cfg["element"];
                if (typeof elem == "string") {
                    elem = document.querySelector(elem);
                }
            }
        } else if (typeof cfg == "string") {
            elem = document.querySelector(cfg);
            cfg = {};
        }
        if (!(elem instanceof HTMLElement)) {
            console.error("No a HTMLElement!",elem);
            return;
        }
        let wrapper = new LayoutElement(elem,cfg?.methods);
        /*if ("methods" in cfg) {
            for(let method in  cfg.methods) {
                //wrapper[method] = cfg.methods[method];
                wrapper.set_method(method,cfg.methods[method]);
            }
        }*/
        this.regions[key] = wrapper;
        return wrapper;
    };

    get(key) {
        if (key in this.regions) { return this.regions[key]; }
        return null;
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
        pbox = pivot.getBoundingClientRect();
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
            case "right1":
            case "bottom1":
                dict[k] = pbox[k] + off;
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