import { app } from "./ibookworm.js";

app.extends("PureTextEditor",
["editor"],
(scope)=>{
    scope.types = app.accept_types("*");

    let editarea = app.dom("textarea.-fullscreen");
    editarea.remove();
    scope.enter = function() {
        this.Layout = app.m("editor").Layout;
        let workspace = this.Layout.get("workspace").wrapper;
        workspace.clear();
        workspace.append(editarea);
    };
    scope.load = function(data) {
        console.log(data);
        this.Layout.get("title").set(data.title);
        // TODO: save data into caching, for offline mode
        editarea.element.value = data.content || "";
    };
    scope.save = function() {
        return editarea.element.value;
    };
});