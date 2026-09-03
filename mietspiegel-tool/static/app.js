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
    div.className = "gruppe";
    div.dataset.gruppeId = gruppe.id;

    const titel = document.createElement("h4");
    titel.textContent = gruppe.name;
    div.appendChild(titel);

    const zeile = document.createElement("div");
    zeile.className = "gruppe-zeile";

    ["plus", "minus"].forEach((seite) => {
      const wrap = document.createElement("details");
      wrap.style.flex = "1";
      const summary = document.createElement("summary");
      const anzahlSpan = document.createElement("span");
      anzahlSpan.className = `anzahl-${seite}`;
      anzahlSpan.textContent = "0";
      summary.textContent = (seite === "plus" ? "Wohnwerterhöhend (+): " : "Wohnwertmindernd (-): ");
      summary.appendChild(anzahlSpan);
      wrap.appendChild(summary);

      (gruppe[seite] || []).forEach((text, idx) => {
        const label = document.createElement("label");
        label.style.flexDirection = "row";
        label.style.fontWeight = "normal";
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
        wrap.appendChild(label);
      });
      zeile.appendChild(wrap);
    });

    div.appendChild(zeile);
    container.appendChild(div);
  });
}

function aktualisiereAnzahl(gruppeId) {
  const div = document.querySelector(`.gruppe[data-gruppe-id="${gruppeId}"]`);
  const plus = div.querySelectorAll(".merkmal-plus:checked").length;
  const minus = div.querySelectorAll(".merkmal-minus:checked").length;
  div.querySelector(".anzahl-plus").textContent = plus;
  div.querySelector(".anzahl-minus").textContent = minus;
}

function sammleMerkmale() {
  const ergebnis = {};
  document.querySelectorAll("#merkmalgruppen .gruppe").forEach((div) => {
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
  if (wert === null || wert === undefined) return "–";
  return wert.toLocaleString("de-DE", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " €";
}

function statusKlasse(status) {
  if (!status) return "";
  if (status.includes("über Vergleichsmiete")) return "status-ok";
  if (status.includes("Erhöhung bis")) return "status-warn";
  return "status-bad";
}

function renderEinzelErgebnis(e) {
  const box = document.getElementById("ergebnis-einzel");
  box.classList.add("zeigen");
  if (e.fehler) {
    box.innerHTML = `<p class="fehler">${e.fehler}</p>`;
    return;
  }

  let statusHtml = "";
  if (e.status) {
    statusHtml = `<p><span class="status-badge ${statusKlasse(e.status)}">${e.status}</span></p>`;
  }

  const merkmaleHtml = e.merkmale
    .map(
      (m) =>
        `<tr><td>${m.gruppe_name}</td><td>${m.anzahl_plus}</td><td>${m.anzahl_minus}</td>` +
        `<td>${m.ueberwiegt}</td><td>${m.anteil_prozent > 0 ? "+" : ""}${m.anteil_prozent}%</td></tr>`
    )
    .join("");

  box.innerHTML = `
    <h3>${e.strasse} ${e.hausnummer}, ${e.bezirk} — Wohnlage: ${e.wohnlage} (${e.gebiet === "O" ? "Ost" : "West"})</h3>
    <p>Bezugsfertigkeit: ${e.bezugsfertigkeit_kategorie} · ${e.groesse_qm} m²</p>
    ${statusHtml}
    <div class="kennzahlen">
      <div class="kennzahl"><div class="label">Unterwert €/m²</div><div class="wert">${e.unterwert_qm}</div></div>
      <div class="kennzahl"><div class="label">Mittelwert €/m²</div><div class="wert">${e.mittelwert_qm}</div></div>
      <div class="kennzahl"><div class="label">Oberwert €/m²</div><div class="wert">${e.oberwert_qm}</div></div>
      <div class="kennzahl"><div class="label">Vergleichsmiete €/m²</div><div class="wert">${e.vergleichsmiete_qm}</div></div>
      <div class="kennzahl"><div class="label">Vergleichsmiete gesamt</div><div class="wert">${formatEuro(e.vergleichsmiete_gesamt)}</div></div>
      ${e.ist_nettokaltmiete_gesamt !== null ? `
      <div class="kennzahl"><div class="label">Ist-Nettokaltmiete</div><div class="wert">${formatEuro(e.ist_nettokaltmiete_gesamt)}</div></div>
      <div class="kennzahl"><div class="label">Differenz</div><div class="wert">${formatEuro(e.differenz_gesamt)} (${e.differenz_prozent}%)</div></div>
      <div class="kennzahl"><div class="label">Max. neue Miete (Kappungsgrenze)</div><div class="wert">${formatEuro(e.max_zulaessige_neue_miete_gesamt)}</div></div>
      <div class="kennzahl"><div class="label">Erhöhungspotential</div><div class="wert">${formatEuro(e.erhoehungspotential_gesamt)} (${e.erhoehungspotential_prozent}%)</div></div>
      ` : ""}
    </div>
    <table>
      <thead><tr><th>Merkmalgruppe</th><th>+</th><th>-</th><th>Überwiegt</th><th>Anteil</th></tr></thead>
      <tbody>${merkmaleHtml}</tbody>
    </table>
    ${(e.hinweise || []).map((h) => `<p class="hinweis">ℹ️ ${h}</p>`).join("")}
  `;
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
  const spalten = Object.keys(daten.zeilen[0]);
  const head = spalten.map((s) => `<th>${s}</th>`).join("");
  const rows = daten.zeilen
    .map((z) => {
      const statusKl = statusKlasse(z["Status"] || "");
      return (
        "<tr>" +
        spalten
          .map((s) => {
            let v = z[s];
            if (v === null || v === undefined) v = "";
            if (s === "Status" && v) return `<td><span class="status-badge ${statusKl}">${v}</span></td>`;
            return `<td>${v}</td>`;
          })
          .join("") +
        "</tr>"
      );
    })
    .join("");

  box.innerHTML = `
    <p>${daten.anzahl} Einheiten verarbeitet.</p>
    <div class="tabelle-wrapper">
      <table><thead><tr>${head}</tr></thead><tbody>${rows}</tbody></table>
    </div>
    <button id="mieterliste-export">Als Excel exportieren</button>
  `;
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
