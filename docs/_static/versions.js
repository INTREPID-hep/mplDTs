// Version switcher for the mplDTs documentation.
//
// The list of versions lives in versions.json at the site root; the deploy
// workflow copies it there, and the back-fill of old releases writes it once.
// A local build has no versions.json, and the switcher then does nothing.
(function () {
  "use strict";
  var script = document.currentScript;
  if (!script || !window.fetch) {
    return;
  }
  // <site>/v3.0.1/_static/versions.js or <site>/_static/versions.js
  var here = script.src.replace(/\/_static\/versions\.js.*$/, "");
  var root = here.replace(/\/v[^\/]*$/, "");

  fetch(root + "/versions.json")
    .then(function (response) {
      return response.ok ? response.json() : null;
    })
    .then(function (versions) {
      if (!versions || !versions.length) {
        return;
      }
      var host =
        document.querySelector(".wy-side-nav-search") ||
        document.querySelector(".rst-content") ||
        document.body;
      var select = document.createElement("select");
      select.setAttribute("aria-label", "Documentation version");
      select.style.width = "100%";
      select.style.marginTop = "0.6em";
      versions.forEach(function (entry) {
        var option = document.createElement("option");
        option.value = root + "/" + entry.path + "/";
        option.textContent = entry.name;
        if (window.location.pathname.indexOf("/" + entry.path + "/") !== -1) {
          option.selected = true;
        }
        select.appendChild(option);
      });
      select.addEventListener("change", function () {
        window.location.href = select.value;
      });
      host.appendChild(select);
    })
    .catch(function () {
      /* offline or a local build: no switcher */
    });
})();
