import { app } from "./ibookworm.js";

app.extends("SimpleReader",
[],
(scope,ap)=>{
    scope.types = [ "article:viewer" ];
    scope.compress = function(json) {
        return atob(JSON.stringify(json));
    };
    scope.decompress = function(data) {
        return JSON.parse(btoa(data));
    };
});