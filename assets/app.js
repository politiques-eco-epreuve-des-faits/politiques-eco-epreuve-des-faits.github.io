// Chapitre page: tabs, verdict/part filters and search for passages, debate filter.
(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var esc = function (s) { return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); };
  var md = function (s) { return esc(s).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/\*(.+?)\*/g, "<em>$1</em>"); };
  var norm = function (s) { return String(s).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase(); };

  // ---- tabs (keeps the open tab in the URL hash)
  var tabs = Array.prototype.slice.call(document.querySelectorAll(".tab"));
  function openTab(id) {
    tabs.forEach(function (t) {
      var on = t.id === id; t.setAttribute("aria-selected", on);
      document.getElementById(t.getAttribute("aria-controls")).hidden = !on;
    });
  }
  tabs.forEach(function (t) { t.addEventListener("click", function () { openTab(t.id); history.replaceState(null, "", "#" + t.id.slice(2)); }); });
  if (location.hash && document.getElementById("t-" + location.hash.slice(1))) openTab("t-" + location.hash.slice(1));

  // ---- passages
  var V = [["contredit", "Contredit"], ["nuancé", "Nuancé"], ["renforcé", "Renforcé"], ["tient", "Tient"], ["nouveau", "Nouveau"]];
  var vkey = function (v) { return norm(v).replace(/\s+/g, "-"); };
  var data = window.CH6 || [];
  data.forEach(function (e) {
    var m = String(e.section).match(/^(\d)/);
    e._partie = m ? m[1] : "2"; // encadrés and new sections of part 2 have no leading digit
  });
  var state = { v: null, p: null, q: "" };

  function chip(label, n, onClick) {
    var b = document.createElement("button"); b.className = "chip"; b.type = "button"; b.setAttribute("aria-pressed", "false");
    b.innerHTML = esc(label) + (n != null ? '<span class="n">' + n + "</span>" : "");
    b.addEventListener("click", onClick); return b;
  }
  function radioRow(box, items, key) {
    var btns = [];
    var all = chip("Tous", data.length, function () { state[key] = null; sync(); render(); }); box.insertBefore(all, box.querySelector(".search")); btns.push([null, all]);
    items.forEach(function (it) {
      var b = chip(it[1], it[2], function () { state[key] = state[key] === it[0] ? null : it[0]; sync(); render(); });
      box.insertBefore(b, box.querySelector(".search")); btns.push([it[0], b]);
    });
    function sync() { btns.forEach(function (x) { x[1].setAttribute("aria-pressed", String(state[key] === x[0])); }); }
    sync(); return sync;
  }
  var vItems = V.map(function (v) { return [v[0], v[1], data.filter(function (e) { return e.verdict === v[0]; }).length]; }).filter(function (v) { return v[2] > 0; });
  radioRow($("#f-verdict"), vItems, "v");
  var pItems = [["2", "2. Où en est-on ?"], ["3", "3. Quels leviers ?"], ["4", "4. Partis pris"]].map(function (p) {
    return [p[0], p[1], data.filter(function (e) { return e._partie === p[0]; }).length]; });
  radioRow($("#f-partie"), pItems, "p");
  $("#q").addEventListener("input", function (ev) { state.q = norm(ev.target.value.trim()); render(); });

  function card(e) {
    var vk = vkey(e.verdict), label = (V.filter(function (v) { return v[0] === e.verdict; })[0] || [0, e.verdict])[1];
    var refs = (e.references || []).map(function (r) { return "<li>" + md(r) + "</li>"; }).join("");
    return '<article class="card v-' + vk + '" id="' + esc(String(e.id).toLowerCase()) + '">' +
      '<div class="card-h"><span class="pg">' + esc(e.page) + '</span><span>' + esc(e.section) + '</span>' +
      '<span class="badge b-' + vk + '">' + esc(label) + '</span><span class="maj">mise à jour ' + esc(e.maj) + '</span></div>' +
      '<p class="msg">' + md(e.message) + '</p>' +
      '<div class="cols"><div class="col"><h3>Ce que disent les données récentes</h3><p>' + md(e.donnees) + '</p></div>' +
      '<div class="col"><h3>Brouillon proposé</h3><div class="draft"><p>' + md(e.brouillon) + '</p></div>' +
      (refs ? '<details class="refs"><summary>Références à ajouter (' + e.references.length + ')</summary><ul>' + refs + "</ul></details>" : "") +
      "</div></div></article>";
  }
  function render() {
    var out = data.filter(function (e) {
      if (state.v && e.verdict !== state.v) return false;
      if (state.p && e._partie !== state.p) return false;
      if (state.q && norm([e.page, e.section, e.message, e.donnees, e.brouillon].join(" ")).indexOf(state.q) < 0) return false;
      return true;
    });
    $("#count").textContent = out.length + (out.length > 1 ? " passages affichés" : " passage affiché") + " sur " + data.length;
    $("#cards").innerHTML = out.length ? out.map(card).join("") : '<p class="empty">Aucun passage ne correspond à ces filtres.</p>';
  }
  render();

  // ---- debates
  var deb = window.CH6_DEBATS || [];
  var palette = ["#2a4d8f", "#8a5a00", "#1f6b3a", "#7a3e9d", "#a3241d", "#00707a", "#5b6476", "#9c4a1a"];
  var names = []; deb.forEach(function (d) { if (names.indexOf(d.debat) < 0) names.push(d.debat); });
  var color = {}; names.forEach(function (n, i) { color[n] = palette[i % palette.length]; });
  var dsel = null, dbtns = [];
  var dbox = $("#f-debat");
  function dsync() { dbtns.forEach(function (x) { x[1].setAttribute("aria-pressed", String(dsel === x[0])); }); }
  var dall = chip("Tous", deb.length, function () { dsel = null; dsync(); drender(); }); dbox.appendChild(dall); dbtns.push([null, dall]);
  names.forEach(function (n) {
    var b = chip(n, deb.filter(function (d) { return d.debat === n; }).length, function () { dsel = dsel === n ? null : n; dsync(); drender(); });
    b.style.borderColor = color[n]; dbox.appendChild(b); dbtns.push([n, b]);
  });
  dsync();
  function drender() {
    $("#debs").innerHTML = deb.filter(function (d) { return !dsel || d.debat === dsel; }).map(function (d) {
      var same = d.rapport === "soutien";
      return '<div class="deb' + (same ? " same" : "") + '" style="--dc:' + color[d.debat] + '"><div class="t">' + esc(d.debat) + "</div>" +
        (same ? '<div class="same-l">Rejoint la position du manuel</div>' : "") +
        '<p class="pos">' + md(d.position) + '</p><div class="who">' + esc(d.qui) + "</div>" +
        (d.chiffre && d.chiffre !== "—" ? '<div class="fig">' + md(d.chiffre) + "</div>" : "") + "</div>";
    }).join("");
  }
  drender();
})();
