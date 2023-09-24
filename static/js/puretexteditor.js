import { app } from "./ibookworm.js";

app.extends("PureTextEditor",
["editor"],
(scope)=>{
    scope.types = { "includes": ()=>true };
    scope.compress = function(text) {
        return atob(text);
    };
    scope.decompress = function(data) {
        return btoa(data);
    };

    let editarea = app.dom("textarea.-fullscreen");
    editarea.remove();
    scope.initialize = function() {
        // TODO: set shortcut key using app.Layout
        let workspace = app.Layout.get("workspace").wrapper;
        workspace.clear();
        workspace.append(editarea);
    };
    scope.read = function(data) {
        app.Layout.get("title").set(data.title);
        // TODO: save data into caching, for offline mode
        editarea.value = scope.decompress(data.content || "");
    };
});