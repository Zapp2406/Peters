// Berliner Mietspiegel-Tool – Frontend-Logik

function initTabs() {
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
    });
  });
}

function baueMerkmalgruppen() {
  const container = document.getElementById("merkmalgruppen");
  (window.MERKMALGRUPPEN || []).forEach((gruppe) => {
    const div = document.createElement("div");
    div.className = "spannengruppe";
    div.dataset.gruppeId = gruppe.id;

    const titel = document.createElement("h4");
    titel.textContent = gruppe.name;
    div.appendChild(titel);

    const spalten = document.createElement("div");
    spalten.className = "spannengruppe-spalten";

    ["minus", "plus"].forEach((seite) => {
      const spalte = document.createElement("div");
      spalte.className = `spannenspalte spannenspalte-${seite}`;

      const kopf = document.createElement("div");
      kopf.className = "spannenspalte-kopf";
      const anzahlSpan = document.createElement("span");
      anzahlSpan.className = `anzahl-${seite}`;
      anzahlSpan.textContent = "0";
      kopf.textContent = seite === "plus" ? "Spannenerhöhend (+) — " : "Spannenmindernd (−) — ";
      kopf.appendChild(anzahlSpan);
      spalte.appendChild(kopf);

      (gruppe[seite] || []).forEach((text, idx) => {
        const label = document.createElement("label");
        label.className = "merkmal-checkbox";
        const cb = document.createElement("input");
        cb.type = "checkbox";
        cb.className = `merkmal-${seite}`;
        cb.dataset.gruppeId = gruppe.id;
        cb.id = `${gruppe.id}-${seite}-${idx}`;
        cb.addEventListener("change", () => aktualisiereAnzahl(gruppe.id));
        label.appendChild(cb);
        const span = document.createElement("span");
        span.textContent = " " + text;
        label.appendChild(span);
        spalte.appendChild(label);
      });
      spalten.appendChild(spalte);
    });

    div.appendChild(spalten);
    container.appendChild(div);
  });
}

function aktualisiereAnzahl(gruppeId) {
  const div = document.querySelector(`.spannengruppe[data-gruppe-id="${gruppeId}"]`);
  const plus = div.querySelectorAll(".merkmal-plus:checked").length;
  const minus = div.querySelectorAll(".merkmal-minus:checked").length;
  div.querySelector(".anzahl-plus").textContent = plus;
  div.querySelector(".anzahl-minus").textContent = minus;
}

function sammleMerkmale() {
  const ergebnis = {};
  document.querySelectorAll("#merkmalgruppen .spannengruppe").forEach((div) => {
    const gid = div.dataset.gruppeId;
    ergebnis[gid] = {
      plus: div.querySelectorAll(".merkmal-plus:checked").length,
      minus: div.querySelectorAll(".merkmal-minus:checked").length,
    };
  });
  return ergebnis;
}

function initStrassenAutocomplete() {
  const input = document.getElementById("strasse");
  const box = document.getElementById("strasse-vorschlaege");
  const bezirkSelect = document.getElementById("bezirk");
  let timer;

  input.addEventListener("input", () => {
    clearTimeout(timer);
    const q = input.value.trim();
    if (q.length < 2) {
      box.style.display = "none";
      return;
    }
    timer = setTimeout(async () => {
      const res = await fetch(`/api/strassen?q=${encodeURIComponent(q)}`);
      const strassen = await res.json();
      box.innerHTML = "";
      strassen.forEach((s) => {
        const d = document.createElement("div");
        d.textContent = s;
        d.addEventListener("click", async () => {
          input.value = s;
          box.style.display = "none";
          await ladeBezirke(s);
        });
        box.appendChild(d);
      });
      box.style.display = strassen.length ? "block" : "none";
    }, 200);
  });

  document.addEventListener("click", (e) => {
    if (e.target !== input) box.style.display = "none";
  });

  async function ladeBezirke(strasse) {
    const res = await fetch(`/api/bezirke?strasse=${encodeURIComponent(strasse)}`);
    const bezirke = await res.json();
    bezirkSelect.innerHTML = '<option value="">– automatisch –</option>';
    bezirke.forEach((b) => {
      const opt = document.createElement("option");
      opt.value = b;
      opt.textContent = b;
      bezirkSelect.appendChild(opt);
    });
  }
}

function formatEuro(wert) {
  if (wert === null || wert === undefined || Number.isNaN(wert)) return "–";
  return wert.toLocaleString("de-DE", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " €";
}

function statusKlasse(status) {
  if (!status) return "";
  if (status.includes("über Vergleichsmiete")) return "status-ok";
  if (status.includes("Erhöhung bis")) return "status-warn";
  return "status-bad";
}

// Spiegelt die Kappungsgrenzen-Logik aus mietspiegel/berechnung.py, damit die
// Dropdown-Auswahl (Unter-/Mittel-/Oberwert) clientseitig ohne erneuten
// Server-Aufruf neu gerechnet werden kann.
function berechneMieteVergleich(mieteAlt, mieteNeuGesamt, kappungsgrenze) {
  if (mieteAlt === null || mieteAlt === undefined || mieteAlt === "") {
    return { mieteNeuGesamt, maxNeu: mieteNeuGesamt, erhoehung: null, erhoehungProzent: null, status: null };
  }
  const kappungsgrenzeMiete = mieteAlt * (1 + kappungsgrenze);
  const maxNeu = Math.min(mieteNeuGesamt, kappungsgrenzeMiete);
  const erhoehung = Math.max(0, Math.round((maxNeu - mieteAlt) * 100) / 100);
  const erhoehungProzent = Math.round((erhoehung / mieteAlt) * 1000) / 10;
  let status;
  if (mieteAlt >= mieteNeuGesamt) {
    status = "über Vergleichsmiete (keine Erhöhung möglich)";
  } else if (erhoehung <= 0) {
    status = "im Rahmen (Kappungsgrenze bereits ausgeschöpft)";
  } else {
    status = "Erhöhung bis zur Vergleichsmiete/Kappungsgrenze möglich";
  }
  return { mieteNeuGesamt, maxNeu, erhoehung, erhoehungProzent, status };
}

async function ladeLageplan(strasse, hausnummer, bezirkCode) {
  const el = document.getElementById("lageplan");
  if (!el) return;
  el.innerHTML = '<p class="hinweis">Lageplan wird geladen…</p>';
  try {
    const suchtext = `${strasse} ${hausnummer}, Berlin, Germany`;
    const url = `https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&countrycodes=de&q=${encodeURIComponent(suchtext)}`;
    const res = await fetch(url, { headers: { Accept: "application/json" } });
    if (!res.ok) throw new Error("Geocoding fehlgeschlagen");
    const treffer = await res.json();
    if (!treffer.length) {
      el.innerHTML = '<p class="hinweis">Für diese Adresse konnte kein Lageplan gefunden werden.</p>';
      return;
    }
    const lat = parseFloat(treffer[0].lat);
    const lon = parseFloat(treffer[0].lon);
    const delta = 0.003;
    const bbox = [lon - delta, lat - delta, lon + delta, lat + delta].join(",");
    el.innerHTML = `
      <iframe title="Lageplan" width="100%" height="260" style="border:1px solid var(--border); border-radius:6px;"
        src="https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&marker=${lat},${lon}&layer=mapnik"></iframe>
      <p class="hinweis"><a href="https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=17/${lat}/${lon}"
        target="_blank" rel="noopener">Größere Karte auf OpenStreetMap öffnen</a></p>
    `;
  } catch (err) {
    el.innerHTML = '<p class="hinweis">Lageplan konnte nicht geladen werden (keine Verbindung zu OpenStreetMap?).</p>';
  }
}

function renderEinzelErgebnis(e) {
  const box = document.getElementById("ergebnis-einzel");
  box.classList.add("zeigen");
  if (e.fehler) {
    box.innerHTML = `<p class="fehler">${e.fehler}</p>`;
    return;
  }

  const merkmaleHtml = e.merkmale
    .map(
      (m) =>
        `<tr><td>${m.gruppe_name}</td><td>${m.anzahl_plus}</td><td>${m.anzahl_minus}</td>` +
        `<td>${m.ueberwiegt}</td><td>${m.anteil_prozent > 0 ? "+" : ""}${m.anteil_prozent}%</td></tr>`
    )
    .join("");

  const dropdownOptionen = [
    { label: `Unterwert (${e.unterwert_qm} €/m²)`, wert: e.unterwert_qm },
    { label: `Mittelwert (${e.mittelwert_qm} €/m²)`, wert: e.mittelwert_qm, selected: true },
    { label: `Oberwert (${e.oberwert_qm} €/m²)`, wert: e.oberwert_qm },
  ];
  if (e.netto_merkmal_prozent) {
    dropdownOptionen.push({
      label: `Berechnet mit Spannenmerkmalen (${e.vergleichsmiete_qm} €/m²)`,
      wert: e.vergleichsmiete_qm,
    });
  }

  box.innerHTML = `
    <h3>${e.strasse} ${e.hausnummer}, ${e.bezirk} — Wohnlage: ${e.wohnlage} (${e.gebiet === "O" ? "Ost" : "West"})</h3>
    <p class="hinweis">Bezugsfertigkeit: ${e.bezugsfertigkeit_kategorie} · ${e.groesse_qm} m²</p>

    <div id="lageplan" class="lageplan"></div>

    <div class="kennzahlen kennzahlen-klein">
      <div class="kennzahl"><div class="label">Unterwert €/m²</div><div class="wert">${e.unterwert_qm}</div></div>
      <div class="kennzahl"><div class="label">Mittelwert €/m²</div><div class="wert">${e.mittelwert_qm}</div></div>
      <div class="kennzahl"><div class="label">Oberwert €/m²</div><div class="wert">${e.oberwert_qm}</div></div>
    </div>

    <div class="miete-vergleich">
      <div class="miete-box">
        <div class="label">Miete alt</div>
        <div class="wert" id="miete-alt-wert">${formatEuro(e.ist_nettokaltmiete_gesamt)}</div>
      </div>
      <div class="miete-box miete-box-neu">
        <div class="label">Miete neu nach Mietspiegel</div>
        <select id="miete-neu-wahl">
          ${dropdownOptionen
            .map((o) => `<option value="${o.wert}" ${o.selected ? "selected" : ""}>${o.label}</option>`)
            .join("")}
        </select>
        <div class="wert" id="miete-neu-wert"></div>
      </div>
      <div class="miete-box miete-box-erhoehung">
        <div class="label">Mieterhöhung</div>
        <div class="wert" id="mieterhoehung-wert"></div>
        <div class="hinweis" id="kappung-hinweis"></div>
      </div>
    </div>
    <p id="status-zeile"></p>

    <h4>Spannenmerkmale-Ergebnis</h4>
    <table>
      <thead><tr><th>Merkmalgruppe</th><th>+</th><th>-</th><th>Überwiegt</th><th>Anteil</th></tr></thead>
      <tbody>${merkmaleHtml}</tbody>
    </table>
    ${(e.hinweise || []).map((h) => `<p class="hinweis">ℹ️ ${h}</p>`).join("")}
  `;

  const dropdown = document.getElementById("miete-neu-wahl");
  const aktualisiereMieteVergleich = () => {
    const mieteNeuQm = parseFloat(dropdown.value);
    const mieteNeuGesamt = Math.round(mieteNeuQm * e.groesse_qm * 100) / 100;
    const ergebnis = berechneMieteVergleich(e.ist_nettokaltmiete_gesamt, mieteNeuGesamt, e.kappungsgrenze);
    document.getElementById("miete-neu-wert").textContent = formatEuro(mieteNeuGesamt);
    document.getElementById("mieterhoehung-wert").textContent =
      ergebnis.erhoehung === null ? "–" : `${formatEuro(ergebnis.erhoehung)} (${ergebnis.erhoehungProzent}%)`;
    document.getElementById("kappung-hinweis").textContent =
      ergebnis.maxNeu !== undefined && ergebnis.maxNeu < mieteNeuGesamt
        ? "gedeckelt durch Kappungsgrenze"
        : "";
    const statusZeile = document.getElementById("status-zeile");
    statusZeile.innerHTML = ergebnis.status
      ? `<span class="status-badge ${statusKlasse(ergebnis.status)}">${ergebnis.status}</span>`
      : "";
  };
  dropdown.addEventListener("change", aktualisiereMieteVergleich);
  aktualisiereMieteVergleich();

  ladeLageplan(e.strasse, e.hausnummer, e.bezirk);
}

function initFormEinzel() {
  document.getElementById("form-einzel").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const payload = {
      strasse: document.getElementById("strasse").value,
      hausnummer: document.getElementById("hausnummer").value,
      bezirk: document.getElementById("bezirk").value,
      groesse_qm: document.getElementById("groesse_qm").value,
      baujahr: document.getElementById("baujahr").value,
      ist_nettokaltmiete_gesamt: document.getElementById("ist_miete").value,
      kappungsgrenze: document.getElementById("kappungsgrenze").value,
      merkmale: sammleMerkmale(),
    };
    const res = await fetch("/api/berechnung", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    renderEinzelErgebnis(await res.json());
  });
}

// Spalten, die in der generischen Tabelle nicht 1:1 übernommen werden,
// weil sie stattdessen als interaktive Miete-neu/Mieterhöhung-Zellen
// gerendert werden.
const SPEZIAL_SPALTEN = ["Miete neu (Mietspiegel, mit Spannenmerkmalen) €", "Mieterhöhung €", "Mieterhöhung %"];

function renderListenErgebnis(daten) {
  const box = document.getElementById("ergebnis-liste");
  if (daten.fehler) {
    box.innerHTML = `<p class="fehler">${daten.fehler}</p>`;
    return;
  }
  if (!daten.zeilen || !daten.zeilen.length) {
    box.innerHTML = "<p>Keine Zeilen verarbeitet.</p>";
    return;
  }
  const alleSpalten = Object.keys(daten.zeilen[0]);
  const anzeigeSpalten = alleSpalten.filter((s) => !SPEZIAL_SPALTEN.includes(s));
  const head =
    anzeigeSpalten.map((s) => `<th>${s}</th>`).join("") +
    `<th>Miete neu nach Mietspiegel</th><th>Mieterhöhung</th>`;

  const rows = daten.zeilen
    .map((z, i) => {
      const roh = (daten.ergebnisse || [])[i] || {};
      const statusKl = statusKlasse(z["Status"] || "");
      const zellen = anzeigeSpalten
        .map((s) => {
          let v = z[s];
          if (v === null || v === undefined) v = "";
          if (s === "Status" && v) return `<td><span class="status-badge ${statusKl}">${v}</span></td>`;
          return `<td>${v}</td>`;
        })
        .join("");

      let mieteNeuZelle = "<td>–</td>";
      let erhoehungZelle = "<td>–</td>";
      if (roh.unterwert_qm != null && roh.groesse_qm != null) {
        const optionen = [
          { label: "Unterwert", wert: roh.unterwert_qm },
          { label: "Mittelwert", wert: roh.mittelwert_qm, selected: true },
          { label: "Oberwert", wert: roh.oberwert_qm },
        ];
        mieteNeuZelle = `
          <td class="zelle-miete-neu">
            <select class="miete-neu-wahl-liste" data-index="${i}">
              ${optionen
                .map((o) => `<option value="${o.wert}" ${o.selected ? "selected" : ""}>${o.label}</option>`)
                .join("")}
            </select>
            <div class="wert-klein" data-miete-neu="${i}"></div>
          </td>`;
        erhoehungZelle = `<td><span data-erhoehung="${i}"></span></td>`;
      }
      return `<tr>${zellen}${mieteNeuZelle}${erhoehungZelle}</tr>`;
    })
    .join("");

  box.innerHTML = `
    <p>${daten.anzahl} Einheiten verarbeitet.</p>
    <div class="tabelle-wrapper">
      <table><thead><tr>${head}</tr></thead><tbody>${rows}</tbody></table>
    </div>
    <button id="mieterliste-export">Als Excel exportieren</button>
  `;

  document.querySelectorAll(".miete-neu-wahl-liste").forEach((select) => {
    const i = select.dataset.index;
    const roh = (daten.ergebnisse || [])[i];
    const aktualisiere = () => {
      const mieteNeuQm = parseFloat(select.value);
      const mieteNeuGesamt = Math.round(mieteNeuQm * roh.groesse_qm * 100) / 100;
      const ergebnis = berechneMieteVergleich(roh.ist_nettokaltmiete_gesamt, mieteNeuGesamt, roh.kappungsgrenze);
      document.querySelector(`[data-miete-neu="${i}"]`).textContent = formatEuro(mieteNeuGesamt);
      const erhoehungEl = document.querySelector(`[data-erhoehung="${i}"]`);
      erhoehungEl.textContent =
        ergebnis.erhoehung === null ? "–" : `${formatEuro(ergebnis.erhoehung)} (${ergebnis.erhoehungProzent}%)`;
    };
    select.addEventListener("change", aktualisiere);
    aktualisiere();
  });

  document.getElementById("mieterliste-export").addEventListener("click", () => {
    window.location.href = "/api/mieterliste/export";
  });
}

function initFormListe() {
  document.getElementById("form-liste").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const datei = document.getElementById("mieterliste-datei").files[0];
    if (!datei) return;
    const formData = new FormData();
    formData.append("datei", datei);
    formData.append("kappungsgrenze", document.getElementById("kappungsgrenze-liste").value);
    const box = document.getElementById("ergebnis-liste");
    box.innerHTML = "<p>Datei wird verarbeitet…</p>";
    const res = await fetch("/api/mieterliste/upload", { method: "POST", body: formData });
    renderListenErgebnis(await res.json());
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  baueMerkmalgruppen();
  initStrassenAutocomplete();
  initFormEinzel();
  initFormListe();
});
