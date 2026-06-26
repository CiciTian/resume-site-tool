/* Frontend controller: template pick -> upload+parse -> review -> generate -> preview. */
(function () {
  "use strict";

  var state = { template: null, data: null };

  var els = {
    templates: document.getElementById("templates"),
    file: document.getElementById("file"),
    dropLabel: document.getElementById("dropLabel"),
    parseStatus: document.getElementById("parseStatus"),
    dataCard: document.getElementById("dataCard"),
    dataJson: document.getElementById("dataJson"),
    generate: document.getElementById("generate"),
    genStatus: document.getElementById("genStatus"),
    previewCard: document.getElementById("previewCard"),
    preview: document.getElementById("preview"),
    publishCard: document.getElementById("publishCard"),
    githubUser: document.getElementById("githubUser"),
    githubToken: document.getElementById("githubToken"),
    publish: document.getElementById("publish"),
    publishStatus: document.getElementById("publishStatus"),
    publishResult: document.getElementById("publishResult"),
  };

  function status(node, msg, kind) {
    node.textContent = msg || "";
    node.className = "status" + (kind ? " " + kind : "");
  }

  // 1. Load templates -------------------------------------------------------
  fetch("/api/templates")
    .then(function (r) { return r.json(); })
    .then(function (templates) {
      els.templates.innerHTML = templates
        .map(function (t) {
          return (
            '<button class="template" data-id="' + t.id + '">' +
            "<strong>" + t.name + "</strong><span>" + t.blurb + "</span></button>"
          );
        })
        .join("");
      var first = els.templates.querySelector(".template");
      if (first) selectTemplate(first);
    })
    .catch(function () {
      els.templates.innerHTML = '<p class="status error">Could not load templates.</p>';
    });

  function selectTemplate(btn) {
    state.template = btn.getAttribute("data-id");
    els.templates.querySelectorAll(".template").forEach(function (b) {
      b.classList.toggle("active", b === btn);
    });
  }

  els.templates.addEventListener("click", function (e) {
    var btn = e.target.closest(".template");
    if (btn) selectTemplate(btn);
  });

  // 2. Upload + parse -------------------------------------------------------
  els.file.addEventListener("change", function () {
    var file = els.file.files[0];
    if (!file) return;
    els.dropLabel.textContent = file.name;
    status(els.parseStatus, "Parsing with Claude… this can take a few seconds.", "busy");

    var form = new FormData();
    form.append("file", file);

    fetch("/api/parse", { method: "POST", body: form })
      .then(function (r) {
        return r.json().then(function (body) {
          if (!r.ok) throw new Error(body.detail || "Parse failed.");
          return body;
        });
      })
      .then(function (data) {
        state.data = data;
        els.dataJson.value = JSON.stringify(data, null, 2);
        els.dataCard.hidden = false;
        status(els.parseStatus, "Parsed — review the data below.", "ok");
        els.dataCard.scrollIntoView({ behavior: "smooth" });
      })
      .catch(function (err) {
        status(els.parseStatus, err.message, "error");
      });
  });

  // 3. Generate -------------------------------------------------------------
  els.generate.addEventListener("click", function () {
    if (!state.template) {
      status(els.genStatus, "Pick a template first.", "error");
      return;
    }
    var data;
    try {
      data = JSON.parse(els.dataJson.value);
    } catch (e) {
      status(els.genStatus, "The JSON is invalid: " + e.message, "error");
      return;
    }

    status(els.genStatus, "Generating…", "busy");
    fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ template_id: state.template, data: data }),
    })
      .then(function (r) {
        return r.json().then(function (body) {
          if (!r.ok) throw new Error(body.detail || "Generation failed.");
          return body;
        });
      })
      .then(function (body) {
        status(els.genStatus, "Done.", "ok");
        els.previewCard.hidden = false;
        els.publishCard.hidden = false;
        // cache-bust so the iframe reloads the freshly written site
        els.preview.src = body.preview_url + "?t=" + Date.now();
        els.previewCard.scrollIntoView({ behavior: "smooth" });
      })
      .catch(function (err) {
        status(els.genStatus, err.message, "error");
      });
  });

  // 4. Publish --------------------------------------------------------------
  els.publish.addEventListener("click", function () {
    var username = els.githubUser.value.trim();
    var token = els.githubToken.value.trim();
    if (!username || !token) {
      status(els.publishStatus, "GitHub username and token are required.", "error");
      return;
    }

    status(els.publishStatus, "Publishing to GitHub…", "busy");
    els.publish.disabled = true;
    fetch("/api/publish", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: username, token: token }),
    })
      .then(function (r) {
        return r.json().then(function (body) {
          if (!r.ok) throw new Error(body.detail || "Publish failed.");
          return body;
        });
      })
      .then(function (body) {
        status(els.publishStatus, "Published.", "ok");
        els.publishResult.innerHTML =
          '<a href="' + body.repository_url + '" target="_blank" rel="noreferrer">Repository</a>' +
          '<a href="' + body.pages_url + '" target="_blank" rel="noreferrer">Live site</a>' +
          '<code>' + body.commit_sha.slice(0, 7) + "</code>";
      })
      .catch(function (err) {
        status(els.publishStatus, err.message, "error");
      })
      .finally(function () {
        els.publish.disabled = false;
      });
  });
})();
