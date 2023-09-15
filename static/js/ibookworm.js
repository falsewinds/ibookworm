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

    dom(tag,clss) {
        if (!this.loaded) { return; }
        let e = document.createElement(tag);
        if (clss instanceof Array) {
            clss.forEach((c)=>{ e.classList.add(c); });
        } else if (typeof clss == "string") {
            e.classList.add(clss);
        } else { console.error("invalid clss!",clss); }
        return e;
    };

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
                "content-type": "application/json"
            }
        }).then((resp)=>resp.json());
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
                this.build();
                this.callbacks.forEach((f)=>{
                    f.apply(this,[this]);
                });
                this.callbacks = [];
                this.setup();
                this.loaded = true;
            }
        });
        this.runned = true;
    };
};

export const app = new IBookwormApp();