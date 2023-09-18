
const NON_STANDARD_DICTIONARY = {
    "svg": "http://www.w3.org/2000/svg",
    "g": "http://www.w3.org/2000/svg",
    "line": "http://www.w3.org/2000/svg",
    "rect": "http://www.w3.org/2000/svg",
    "circle": "http://www.w3.org/2000/svg",
    "path": "http://www.w3.org/2000/svg"
};

function css_selector_parse(css,wrap) {
    if (typeof css != "string") { return null; }
    let get_and_clear = (rgxp)=>{
        let ms = [], m, str = css;
        while ((m=rgxp.exec(css)) != null) {
            //console.log(m);
            let m_str = m[0];
            ms.push(m_str);
            str.replace(m_str,"");
        }
        css = css.replace(rgxp,"");
        return ms;
    };
    const id_rgxp = /#[A-z0-9-_]+/g,
        cls_rgxp = /\.[0-9A-z-_][^\.\[\]]+/g,
        attr_rgxp = /\[[A-z0-9-_][^\[\]]+=\"[.][^\[\]]+\"|[A-z0-9-_][^\[\]]+\]/g,
        attr_kv_rgxp = /\[([A-z0-9\-\_]+)=\"(.+)\"\]/g;
    // parse
    let attr = get_and_clear(attr_rgxp),
        cls = get_and_clear(cls_rgxp),
        id = get_and_clear(id_rgxp),
        tag = css.length>0 ? css : "div",
        e, std = true;
    if (tag in NON_STANDARD_DICTIONARY) {
        e = document.createElementNS(
            NON_STANDARD_DICTIONARY[tag],tag);
        std = false;
    } else { e = document.createElement(tag); }
    wrap.standard = std;
    if (id.length>0) { e.id = id[0].substring(1); }
    cls.forEach((c)=>{ e.classList.add(c.substring(1)); });
    let setter = std ? e.setAttribute : e.setAttributeNS,
        wrapper = std ? (k,v)=>[k,v] : (k,v)=>[null,k,v];
    attr.forEach((a)=>{
        attr_kv_rgxp.lastIndex = 0;
        let m = attr_kv_rgxp.exec(a), args;
        if (m==null) {
            let k = a.substr(1,a.length-2);
            args = wrapper(k,k);
        } else { args = wrapper(m[1],m[2]); }
        setter.apply(e,args);
    });
    return e;
}

function parse_arg_to_dict(args) {
    let dict = {}, caller = arguments.caller;
    switch (args.length) {
    case 0:
        break;
    case 1:
        let obj = args[0];
        if (obj==null) { break; }
        if (typeof obj != "object") { break; }
        for(let k in obj) { dict[k] = obj[k]; }
        break;
    case 2:
        let k = args[0], v = args[1];
        switch (typeof k) {
        case "function":
            let ak = k.apply(caller,[]);
            if (typeof ak == "string") {
                dict[ak] = v;
            } else {
                console.error("No attribute key returned.",ak);
            }
            break;
        case "string":
            dict[k] = v;
            break;
        default:
            console.error("Not attribute key.",k);
            break;
        }
    }
    return dict;
}

class dom_wrapper {
    constructor() {
        let present = true;
        this.standard = true;
        switch (arguments.length) {
        case 6:
            let tag = arguments[0];
            if (tag in NON_STANDARD_DICTIONARY) {
                this.standard = false;
                this.element = document.createElementNS(
                    NON_STANDARD_DICTIONARY[tag],tag);
            } else { this.element = document.createElement(tag); }
            if (arguments[1]!=null) { this.element.id = arguments[1]; }
            this.add_class(arguments[2]);
            this.set_attr(arguments[3]);
            this.text(arguments[4]);
            this.listen(arguments[5]);
            break;
        default:
            let css = arguments[0], args = arguments.length;
            switch (typeof css) {
            case "string":
                this.element = css_selector_parse(css,this);
                break;
            case "object":
                if (css instanceof HTMLElement) {
                    this.element = css;
                    present = false;
                    break;
                }
                if (css instanceof Element) {
                    this.element = css;
                    this.standard = false;
                    present = false;
                    break;
                }
                if (css instanceof Array) {
                    console.warn("Array should use dom_wrapper.Create method.");
                    this.element = document.createElement("div");
                    this.insert(dom_wrapper.Create(css));
                    break;
                }
                this.element = document.createElement(css?.tag || "div");
                this.add_class(css?.classes);
                this.set_attr(css?.attributes);
                this.text(css?.content);
                this.listen(css.listeners);
                const prefix = [ "listen:", "on" ];
                for(let k in css) {
                    prefix.forEach((p)=>{
                        if (k.startsWith(p)) {
                            let ev = k.substring(p.length);
                            this.listen(ev,css[k]);
                        }
                    });
                }
                break;
            default:
                this.element = document.createElement("div");
                break;
            }
            if (present && this.element.id) {
                let type = this.standard ? HTMLElement : Element;
                let exists = document.querySelector("#"+this.element.id);
                if (exists instanceof type) {
                    present = false;
                    // TODO: copy all classes & attributes to exists
                    this.element = exists;
                }
            }
            //if (args>1) { this.text(arguments[1]); }
            //if (args>2) { this.listen(arguments[2]); }
            break;
        }
        if (present) { document.body.appendChild(this.element); }
    };

    add_class(c) {
        if (c==null) { return this; }
        c = (c instanceof Array) ? c : [c];
        let left = c.reduce((lef,cn)=>{
            switch (typeof cn) {
            case "string":
                this.element.classList.add(cn);
                break;
            case "function":
                cn = cn.apply(this.element,[]);
                if (typeof cn == "string") {
                    this.element.classList.add(cn);
                } else {
                    lef.push(cn);
                }
                break;
            default:
                lef.push(cn);
                break;
            }
            return lef;
        },[]);
        if (left.length>0) {
            console.warn("ignore following class:",left);
        }
        return this;
    };
    remove_class(c) {
        if (c==null) { return this; }
        c = (c instanceof Array) ? c : [c];
        c.forEach((cn)=>{ this.element.classList.remove(cn); });
        return this;
    };

    set_attr() {
        let attrs = parse_arg_to_dict(arguments);
        let get_str = (s)=>{
            if (typeof s == "function") {
                console.log(s);
                s = s.apply(this.element,[]);
            }
            if (typeof s == "number") { s = s.toString(); }
            if (typeof s != "string") { return null; }
            return s;
        };
        let setter = this.element.setAttribute,
            arg_wrapper = (k,v) => [k,v];
        if (!this.standard) {
            setter = this.element.setAttributeNS;
            arg_wrapper = (k,v) => [null,k,v];
        }
        for (let k in attrs) {
            let v = attrs[k], val = get_str(v);
            if (val==null) {
                console.warn("ignore invalid value.",k,v);
                continue;
            }
            setter.apply(this.element,arg_wrapper(k,val));
        }
        return this;
    };
    remove_attr(ks) {
        if (ks==null) { return this; }
        ks = (ks instanceof Array) ? ks : [ks];
        let setter = this.element.removeAttribute,
            arg_wrapper = (k) => [k];
        if (!this.standard) {
            setter = this.element.removeAttributeNS;
            arg_wrapper = (k) => [null,k];
        }
        let left = ks.reduce((lef,k)=>{
            let ak = get_str(k);
            if (ak!=null) {
                setter.apply(this.element,arg_wrapper(ak));
            } else { left.push(k); }
            return lef;
        },[]);
        if (left.length>0) {
            console.warn("ignore following attribute:",left);
        }
        return this;
    };

    listen() {
        let events = parse_arg_to_dict(arguments);
        for(let k in events) {
            let v = events[k];
            if (typeof v != "function") {
                try { v = new Funcion(v); }
                catch (e) { console.error(e); }
            }
            if (typeof v != "function") { continue; }
            this.element.addEventListener(k,v);
        }
        //this.element.addEventListener.apply(this.element,arguments);
        return this;
    };

    clear() {
        if (this.standard) { this.element.innerHTML = ""; }
        else { this.element.textContent = ""; }
        return this;
    };

    text(puretext) {
        if (puretext==null) { return this; }
        let t = document.createTextNode(puretext);
        this.element.appendChild(t);
        return this;
    };

    insert(elem,before) {
        if (elem==null) {
            console.error("Not a HTMLELement!");
            return this;
        }
        // Prepare before HTMLElement
        if (typeof before == "number") {
            if (before<this.element.children.length) {
                before = this.element.children[before];
            }
        } else if (before instanceof dom_wrapper) {
            before = before.element;
        }
        if (elem instanceof Array) {
            elem.forEach((e)=>{ this.insert(e,before); });
            return this;
        }
        // Prepare elem
        let type = this.standard ? HTMLElement : Element;
        switch (typeof elem) {
        case "string":
            elem = new dom_wrapper(elem).element;
            break;
        case "object":
            if (elem instanceof type) { break; }
            if (elem instanceof dom_wrapper) {
                elem = elem.element;
                break;
            }
            elem = new dom_wrapper(elem).element;
            break;
        case "function":
            elem = elem.apply(this,[this.element,before]);
            break;
        default:
            break;
        }
        if (!(elem instanceof type)) {
            console.error("Not a valid element!",elem);
            return this;
        }
        // appendChild if before is not HTMLElement
        if (before instanceof type) {
            this.element.insertBefore(elem,before);
        } else {
            this.element.appendChild(elem);
        }
        return this;
    };
    append(elem) { this.insert(elem,null); };

    query(css) {
        let es = this.element.querySelectorAll(css),
            rets = [], type = this.standard ? HTMLElement : Element;
        for(let i=0;i<es.length;i++) {
            let e = es[i];
            if (e instanceof type) {
                rets.push(new dom_wrapper(e));
            }
        }
        if (rets.length<=0) { return null; }
        if (rets.length==1) { return rets[0]; }
        return rets;
    };
    get(css) { return this.query(css); };

    static Create(tree) {
        function is_branch(node) {
            if (!(node instanceof Array)) { return false; }
            if (node.length != 2) { return false; }
            return (typeof node[0] == "string" && node[1] instanceof Array);
        };
        let results = [], queue = [],
            root = { "append": (e)=>{ results.push(e); } };
        // check Tree root is single or mutiple
        switch (tree.length) {
        case 0:
            break;
        case 1:
            queue.push({
                "node": tree[0],
                "parent": root
            });
            break;
        case 2:
            if (is_branch(tree)) {
                queue.push({
                    "node": tree,
                    "parent": root
                });
                break;
            }
        default:
            tree.forEach((n)=>{
                queue.push({
                    "node": n,
                    "parent": root
                });
            });
            break;
        }
        // solving queue to create DOM Tree.
        while (queue.length>0) {
            let q = queue.shift();
            if (typeof q.node == "string") {
                q.parent.append(q.node);
                continue;
            }
            if (!(q.node instanceof Array)) {
                console.warn(q);
                continue;
            }
            if (is_branch(q.node)) {
                let e = new dom_wrapper(q.node[0]);
                q.parent.append(e);
                q.node[1].forEach((n)=>{
                    queue.push({
                        "node": n,
                        "parent": e
                    });
                });
                continue;
            }
            console.warn(q);
        }
        return results;
    };
};

export { dom_wrapper };