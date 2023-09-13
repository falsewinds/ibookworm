/*------------------------------------------------------------*\
 * IBookwormApp
\*------------------------------------------------------------*/
class IBookwormApp {
    constructor() {
        this.typelist = {};
        this.modules = {};
        this.builds = [];
    };

    run() {
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
        console.log(this);
    };

    extends(key,dep,init) {
        this.builds.push({
            "key": key,
            "dependency": (dep instanceof Array) ? dep : [dep],
            "initialize": (typeof init == "function") ? init : ()=>init
        });
    };
};

export const app = new IBookwormApp();