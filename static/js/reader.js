import { app } from "./ibookworm.js";

app.extends("SimpleReader",
["viewer"],
(scope,ap)=>{
    //scope.types = [ "article" ];
    scope.compress = function(json) {
        return atob(JSON.stringify(json));
    };
    scope.decompress = function(data) {
        return JSON.parse(btoa(data));
    };
});