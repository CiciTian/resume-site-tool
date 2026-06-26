/*
 * Shared renderer for all templates.
 *
 * Reads window.RESUME_DATA (the fixed schema written by the generator) and
 * fills in whatever contract elements a template chooses to include. Every
 * lookup is null-guarded, so each template's index.html only needs the
 * sections it wants — order, styling and which sections appear are the
 * template's call; this file just supplies the data.
 */
(function () {
  "use strict";

  var data = window.RESUME_DATA || {};
  var profile = data.profile || {};

  function esc(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function setField(name, value) {
    document.querySelectorAll('[data-field="' + name + '"]').forEach(function (node) {
      if (value) {
        node.textContent = value;
      } else {
        // Hide empty optional fields rather than leaving blank gaps.
        node.style.display = "none";
      }
    });
  }

  function fill(id, html) {
    var node = document.getElementById(id);
    if (!node) return;
    if (html && html.trim()) {
      node.innerHTML = html;
    } else {
      // Remove an empty section (and its wrapper section, if marked) cleanly.
      var section = node.closest("[data-optional]");
      if (section) section.remove();
      else node.remove();
    }
  }

  function list(items, render) {
    return (items || []).map(render).join("");
  }

  // --- string fields -------------------------------------------------------
  setField("name", profile.name);
  setField("headline", profile.headline);
  setField("location", profile.location);
  setField("summary", profile.summary);
  setField("contactNote", data.contact_note);

  document.title = (profile.name || "Personal Website") + " | Personal Website";
  var metaDesc = document.querySelector('meta[name="description"]');
  if (metaDesc) metaDesc.setAttribute("content", profile.summary || profile.headline || "");

  var initials = document.getElementById("profileInitials");
  if (initials) {
    initials.textContent = (profile.name || "")
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map(function (w) { return w[0].toUpperCase(); })
      .join("");
  }

  // --- collections ---------------------------------------------------------
  fill("statGrid", list(data.stats, function (s) {
    return (
      '<article class="stat-card"><strong>' + esc(s.value) +
      "</strong><span>" + esc(s.label) + "</span></article>"
    );
  }));

  fill("focusTags", list(data.focus_tags, function (t) {
    return "<span>" + esc(t) + "</span>";
  }));

  fill("contactGrid", list(data.contacts, function (c) {
    var inner =
      "<span>" + esc(c.label) + "</span><strong>" + esc(c.value) + "</strong>";
    if (c.href) {
      return (
        '<a class="contact-card" href="' + esc(c.href) +
        '" target="_blank" rel="noreferrer">' + inner + "</a>"
      );
    }
    return '<div class="contact-card">' + inner + "</div>";
  }));

  fill("experienceList", list(data.experience, function (item) {
    var meta = [item.organization, item.location].filter(Boolean).join(" · ");
    var bullets = list(item.bullets, function (b) {
      return "<li>" + esc(b) + "</li>";
    });
    return (
      '<article class="timeline-item">' +
      '<div class="timeline-date">' + esc(item.period) + "</div>" +
      '<div class="timeline-content"><p>' + esc(meta) + "</p>" +
      "<h3>" + esc(item.role) + "</h3>" +
      (bullets ? "<ul>" + bullets + "</ul>" : "") +
      "</div></article>"
    );
  }));

  fill("projectList", list(data.projects, function (p) {
    var tech = list(p.technologies, function (t) {
      return "<span>" + esc(t) + "</span>";
    });
    var title = p.link
      ? '<a href="' + esc(p.link) + '" target="_blank" rel="noreferrer">' +
        esc(p.name) + "</a>"
      : esc(p.name);
    return (
      '<article class="outcome-card"><span>' + esc(p.type) + "</span>" +
      "<h3>" + title + "</h3><p>" + esc(p.description) + "</p>" +
      (tech ? '<div class="tech-row">' + tech + "</div>" : "") +
      "</article>"
    );
  }));

  fill("publicationList", data.publications && data.publications.length
    ? "<h3>Publications</h3><ol>" +
        list(data.publications, function (p) { return "<li>" + esc(p) + "</li>"; }) +
        "</ol>"
    : "");

  fill("awardList", data.awards && data.awards.length
    ? "<h3>Awards</h3><ul>" +
        list(data.awards, function (a) { return "<li>" + esc(a) + "</li>"; }) +
        "</ul>"
    : "");

  fill("educationList", list(data.education, function (item) {
    var details = list(item.details, function (d) { return "<li>" + esc(d) + "</li>"; });
    return (
      '<article class="education-card"><span>' + esc(item.period) + "</span>" +
      "<h3>" + esc(item.school) + "</h3><p>" + esc(item.degree) + "</p>" +
      (details ? "<ul>" + details + "</ul>" : "") +
      "</article>"
    );
  }));

  fill("skillList", list(data.skills, function (group) {
    return (
      '<article class="skill-group"><h3>' + esc(group.group) + "</h3><div>" +
      list(group.items, function (i) { return "<span>" + esc(i) + "</span>"; }) +
      "</div></article>"
    );
  }));

  var year = document.getElementById("year");
  if (year) year.textContent = new Date().getFullYear();
})();
