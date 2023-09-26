import { app } from "./ibookworm.js";

app.extends("SimpleReader",
["viewer"],
(scope)=>{
    scope.types = app.accept_types("article");

    scope.enter = function() {
        // Inherit VIEWER module Layout
        this.Layout = app.m("viewer").Layout;
    };
    scope.show = function(doc) {
        this.Layout.get("title").set(doc.title);
        let lines = doc.content.split(/\r?\n/g).map((line)=>{
            return app.dom("p",line);
        });
        this.Layout.get("content").write(lines);
    };
});