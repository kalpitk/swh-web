!function(t,e){"object"==typeof exports&&"object"==typeof module?module.exports=e():"function"==typeof define&&define.amd?define([],e):"object"==typeof exports?exports.vault=e():(t.swh=t.swh||{},t.swh.vault=e())}(window,function(){return function(t){var e={};function o(r){if(e[r])return e[r].exports;var a=e[r]={i:r,l:!1,exports:{}};return t[r].call(a.exports,a,a.exports,o),a.l=!0,a.exports}return o.m=t,o.c=e,o.d=function(t,e,r){o.o(t,e)||Object.defineProperty(t,e,{enumerable:!0,get:r})},o.r=function(t){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(t,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(t,"__esModule",{value:!0})},o.t=function(t,e){if(1&e&&(t=o(t)),8&e)return t;if(4&e&&"object"==typeof t&&t&&t.__esModule)return t;var r=Object.create(null);if(o.r(r),Object.defineProperty(r,"default",{enumerable:!0,value:t}),2&e&&"string"!=typeof t)for(var a in t)o.d(r,a,function(e){return t[e]}.bind(null,a));return r},o.n=function(t){var e=t&&t.__esModule?function(){return t.default}:function(){return t};return o.d(e,"a",e),e},o.o=function(t,e){return Object.prototype.hasOwnProperty.call(t,e)},o.p="/static/",o(o.s=456)}({211:function(t,e,o){"use strict";o.r(e);o(455);var r=o(35),a='<div class="progress">\n                  <div class="progress-bar progress-bar-success progress-bar-striped"\n                       role="progressbar" aria-valuenow="100" aria-valuemin="0"\n                       aria-valuemax="100" style="width: 100%;height: 100%;">\n                  </div>\n                </div>;',i=5e3,n=void 0;function s(t,e){"new"===e.status?t.css("background-color","rgba(128, 128, 128, 0.5)"):"pending"===e.status?t.css("background-color","rgba(0, 0, 255, 0.5)"):"done"===e.status?t.css("background-color","#5cb85c"):"failed"===e.status&&(t.css("background-color","rgba(255, 0, 0, 0.5)"),t.css("background-image","none")),t.text(e.progress_message||e.status),"new"===e.status||"pending"===e.status?t.addClass("progress-bar-animated"):t.removeClass("progress-bar-striped")}function c(){var t=JSON.parse(localStorage.getItem("swh-vault-cooking-tasks"));if(!t||0===t.length)return $(".swh-vault-table tbody tr").remove(),void(n=setTimeout(c,i));for(var e=[],o={},l=[],d=0;d<t.length;++d){var u=t[d];l.push(u.object_id),o[u.object_id]=u;var f=void 0;f="directory"===u.object_type?Urls.vault_cook_directory(u.object_id):Urls.vault_cook_revision_gitfast(u.object_id),"done"!==u.status&&"failed"!==u.status&&e.push(fetch(f,{credentials:"same-origin"}))}$(".swh-vault-table tbody tr").each(function(t,e){var o=$(e).find(".vault-object-id").data("object-id");-1===$.inArray(o,l)&&$(e).remove()}),Promise.all(e).then(r.b).then(function(t){return Promise.all(t.map(function(t){return t.json()}))}).then(function(e){for(var r=$("#vault-cooking-tasks tbody"),l=0;l<e.length;++l){var d=o[e[l].obj_id];d.status=e[l].status,d.fetch_url=e[l].fetch_url,d.progress_message=e[l].progress_message}for(var u=0;u<t.length;++u){var f=t[u],v=$("#vault-task-"+f.object_id);if(v.length){s(v.find(".progress-bar"),f);var b=v.find(".vault-dl-link");"done"===f.status?b[0].innerHTML='<a class="btn btn-default btn-sm" href="'+f.fetch_url+'"><i class="fa fa-download fa-fw" aria-hidden="true"></i>Download</a>':"failed"===f.status&&(b[0].innerHTML="")}else{var g=void 0;g="directory"===f.object_type?Urls.browse_directory(f.object_id):Urls.browse_revision(f.object_id);var p=$.parseHTML(a)[0];s($(p).find(".progress-bar"),f);var h=void 0;h="directory"===f.object_type?'<tr id="vault-task-'+f.object_id+'" title="Once downloaded, the directory can be extracted with the following command:\n\n$ tar xvzf '+f.object_id+'.tar.gz">':'<tr id="vault-task-'+f.object_id+'"  title="Once downloaded, the git repository can be imported with the following commands:\n\n$ git init\n$ zcat '+f.object_id+'.gitfast.gz | git fast-import">',h+='<td><input type="checkbox" class="vault-task-toggle-selection"/></td>',"directory"===f.object_type?h+='<td style="width: 120px"><i class="fa fa-folder fa-fw" aria-hidden="true"></i>directory</td>':h+='<td style="width: 120px"><i class="octicon octicon-git-commit fa-fw"></i>revision</td>',h+='<td class="vault-object-id" data-object-id="'+f.object_id+'"><a href="'+g+'">'+f.object_id+"</a></td>",h+='<td style="width: 350px">'+p.outerHTML+"</td>";var m="Waiting for download link to be available";"done"===f.status?m='<a class="btn btn-default btn-sm" href="'+f.fetch_url+'"><i class="fa fa-download fa-fw" aria-hidden="true"></i>Download</a>':"failed"===f.status&&(m=""),h+='<td class="vault-dl-link" style="width: 320px">'+m+"</td>",h+="</tr>",r.prepend(h)}}localStorage.setItem("swh-vault-cooking-tasks",JSON.stringify(t)),n=setTimeout(c,i)}).catch(function(){})}function l(){$("#vault-tasks-toggle-selection").change(function(t){$(".vault-task-toggle-selection").prop("checked",t.currentTarget.checked)}),$("#vault-remove-tasks").click(function(){clearTimeout(n);var t=[];$(".swh-vault-table tbody tr").each(function(e,o){if($(o).find(".vault-task-toggle-selection").prop("checked")){var r=$(o).find(".vault-object-id").data("object-id");t.push(r),$(o).remove()}});var e=JSON.parse(localStorage.getItem("swh-vault-cooking-tasks"));e=$.grep(e,function(e){return-1===$.inArray(e.object_id,t)}),localStorage.setItem("swh-vault-cooking-tasks",JSON.stringify(e)),$("#vault-tasks-toggle-selection").prop("checked",!1),n=setTimeout(c,i)}),n=setTimeout(c,i),$(document).on("shown.bs.tab",'a[data-toggle="tab"]',function(t){"Vault"===t.currentTarget.text.trim()&&(clearTimeout(n),c())}),window.onfocus=function(){clearTimeout(n),c()}}function d(t){var e=JSON.parse(localStorage.getItem("swh-vault-cooking-tasks"));if(e||(e=[]),void 0===e.find(function(e){return e.object_type===t.object_type&&e.object_id===t.object_id})){var o=void 0;o="directory"===t.object_type?Urls.vault_cook_directory(t.object_id):Urls.vault_cook_revision_gitfast(t.object_id),t.email&&(o+="?email="+t.email),fetch(o,{credentials:"same-origin",method:"POST"}).then(r.a).then(function(){e.push(t),localStorage.setItem("swh-vault-cooking-tasks",JSON.stringify(e)),$("#vault-cook-directory-modal").modal("hide"),$("#vault-cook-revision-modal").modal("hide"),window.location=Urls.browse_vault()}).catch(function(){$("#vault-cook-directory-modal").modal("hide"),$("#vault-cook-revision-modal").modal("hide")})}else window.location=Urls.browse_vault()}function u(t){return/^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/.test(String(t).toLowerCase())}function f(t){var e=$("#swh-vault-directory-email").val().trim();!e||u(e)?d({object_type:"directory",object_id:t,email:e,status:"new"}):$("#invalid-email-modal").modal("show")}function v(t){var e=$("#swh-vault-revision-email").val().trim();!e||u(e)?d({object_type:"revision",object_id:t,email:e,status:"new"}):$("#invalid-email-modal").modal("show")}function b(){$(document).ready(function(){$(".swh-browse-top-navigation").append($("#vault-cook-directory-modal")),$(".swh-browse-top-navigation").append($("#vault-cook-revision-modal")),$(".swh-browse-top-navigation").append($("#invalid-email-modal"))})}o.d(e,"initUi",function(){return l}),o.d(e,"cookDirectoryArchive",function(){return f}),o.d(e,"cookRevisionArchive",function(){return v}),o.d(e,"initTaskCreationUi",function(){return b})},35:function(t,e,o){"use strict";function r(t){if(!t.ok)throw Error(t.statusText);return t}function a(t){for(var e=0;e<t.length;++e)if(!t[e].ok)throw Error(t[e].statusText);return t}function i(t){return"/static/"+t}o.d(e,"a",function(){return r}),o.d(e,"b",function(){return a}),o.d(e,"c",function(){return i})},455:function(t,e,o){},456:function(t,e,o){t.exports=o(211)}})});
//# vault.298a5648d7e615ef96f1.js.map