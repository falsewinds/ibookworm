/*------------------------------------------------------------*\
 * IBookwormApp
\*------------------------------------------------------------*/
class IBookwormApp {
    constructor() {
        this.typelist = {};
        this.modules = {};
        this.builds = [];
        this.callbacks = [];
        this.loaded = false;
        this.runned = false;
    };

    svg(tag, clss=[], attrs={}) {
        if (!this.loaded) { return null; }
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
        if (!this.loaded) { return null; }
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
    doms(layout) {
        let elements = [], root = {
            "appendChild": (e) => { elements.push(e); }
        }, queue = [{
            "parnet": root,
            "children": (layout instanceof Array) ? layout : [layout]
        }];
        while (queue.length>0) {
            let q = queue.shift();
            console.log(q);
        }
        return elements;
    };

    freeze(clip) {
        this.style_overflow = document.body.style.overflow;
        document.body.style.overflow = "hidden";
        // TODO: create cover with clip
        if (this.cover_svg==null) {
            this.cover_svg = this.svg("svg","-cover");
            this.cover_svg.appendChild(this.svg("rect",[],{
                "x": 0, "y": 0, "width": 100, "height": 100,
                "fill": "rgba(0,0,0,0.65)"
            }))
        }
        let w = window.innerWidth, h = window.innerHeight;
        this.cover_svg.setAttributeNS(null,"width",w);
        this.cover_svg.setAttributeNS(null,"height",h);
        let rect = this.cover_svg.querySelector("rect");
        rect.setAttributeNS(null,"width",w);
        rect.setAttributeNS(null,"height",h);
        document.body.appendChild(this.cover_svg);
    };
    defreeze() {
        document.body.removeChild(this.cover_svg);
        document.body.style.overflow = this.style_overflow;
    };

    dialog(caption,fields) {
        this.freeze();
        if (this.dialogue==null) {
            // Create Dialog Element
            this.dialog_element = this.dom("div","-dialog");
            this.dialog_element.style.zIndex = 1000;
            this.dialog_element.style.visibility = "hidden";
            let form = this.dom("form","-center"),
                area = this.dom("div","-fields"),
                btns = this.dom("div","-buttons"),
                btn_submit = this.dom("button",["confirm"],"Confirm"),
                btn_cancel = this.dom("button",["cancel"],"Cancel");
            form.appendChild(area);
            form.appendChild(btns);
            btns.appendChild(btn_submit);
            btns.appendChild(btn_cancel);
            this.dialog_element.appendChild(form);
            document.body.appendChild(this.dialog_element);
        }
        let form = this.dialog_element.querySelector("form"),
            area = form.querySelector(".-fields"),
            first = null;
        // Clear all content
        area.innerHTML = "";
        // TODO: for f in fields, setup field
        fields.forEach((f,i)=>{
            let tag = ("tag" in f) ? f.tag : "input",
                name = ("name" in f) ? f.name : "field"+i,
                e = this.dom(tag,[]);
            e.setAttribute("name",name);
            if ("attr" in f) {
                for(let k in f.attr) {
                    e.setAttribute(k,f.attr[k]);
                }
            }
            if (i==0) {
                first = e;
                e.setAttribute("autofocus","autofocus");
            }
            if ("title" in f) {
                let lbl = this.dom("label");
                lbl.setAttribute("kj-label",f.title);
                lbl.appendChild(e);
                area.appendChild(lbl);
            } else { area.appendChild(e); }
        });
        let w = this.dialog_element.offsetWidth,
            h = this.dialog_element.offsetHeight,
            mh = (window.innerWidth - w) / 2,
            mv = (window.innerHeight - h) / 4;
        this.dialog_element.style.margin = mv+"px "+mh+"px";
        return new Promise((suc,rej)=>{
            this.dialog_element.style.visibility = "visible";
            if (first!=null) { first.focus(); }
            form.addEventListener("submit",(e)=>{
                e.preventDefault();
                this.dialog_element.style.visibility = "hidden";
                this.defreeze();
                let confirmed = e.submitter.classList.contains("confirm");
                if (confirmed) {
                    let fs = area.querySelectorAll("input,select,textarea"),
                        max = fs.length, formdata = {};
                    for(let i=0;i<max;i++) {
                        let fe = fs[i],
                            n = fe.getAttribute("name");
                        if (typeof n == "string") {
                            formdata[n] = fe.value;
                        }
                    }
                    suc(formdata);
                } else { rej(e); }
            });
        });
    }

    extends(key,dep,init) {
        this.builds.push({
            "key": key,
            "dependency": (dep instanceof Array) ? dep : [dep],
            "initialize": (typeof init == "function") ? init : ()=>init
        });
        if (this.loaded) { this.build(); }
    };

    ready(callback) {
        if (this.loaded) {
            console.log(this.loaded);
            callback.apply(this,[this]);
            return;
        }
        this.callbacks.push(callback);
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

    build() {
        const ENDPOINT = "IBOOKWORM.XYZ";
        this.builds.push(ENDPOINT);
        let builds = 0, loaded = 0;
        while (this.builds.length>0) {
            let m = this.builds.shift();
            if (m==ENDPOINT) {
                if (this.builds.length<=0) { break; }
                if (builds==0) {
                    console.error(
                        "Following module(s) dependency is missing!",
                        this.builds);
                    break;
                }
                loaded += builds;
                builds = 0;
                this.builds.push(ENDPOINT);
                continue;
            }
            let d = m.dependency.filter((mk)=>(mk in this.modules));
            if (d.length>0) {
                this.builds.push(m)
                continue;
            }
            let scope = {};
            m.initialize(scope,this);
            scope.types?.forEach((tk)=>{
                if (!(tk in this.typelist)) {
                    this.typelist[tk] = [];
                }
                this.typelist[tk].push(m.key);
            });
            this.modules[m.key] = scope;
            builds++;
        }
        console.log("[IBookwormApp] "+loaded+" module(s) loaded.");
    };

    setup() {
        let nav = document.querySelector("nav");
        if (nav!=null) {
            let last = 0, hider = null;
            window.addEventListener("scroll",()=>{
                if (hider!=null) { clearTimeout(hider); }
                let y = window.scrollY, dy = y - last;
                last = y;
                if (y<48) {
                    nav.classList.remove("hidden");
                } else if (dy>0) {
                    nav.classList.add("hidden");
                } else {
                    nav.classList.remove("hidden");
                    hider = setTimeout(()=>{
                        nav.classList.add("hidden");
                    },2000);
                }
            });
        }
    }

    run() {
        if (this.runned) { return; }
        window.addEventListener("beforeunload",()=>{
            console.log("beforeunload",this);
        });
        window.addEventListener("load",()=>{
            if (this.loaded) { return; }
            console.log("readyState: "+document.readyState);
            if (document.readyState=="complete") {
                this.loaded = true;
                this.build();
                this.callbacks.forEach((f)=>{
                    f.apply(this,[this]);
                });
                this.callbacks = [];
                this.setup();
            }
        });
        this.runned = true;
    };
};

export const app = new IBookwormApp();